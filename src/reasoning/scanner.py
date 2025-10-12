import os
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from .utils.scan_utils import ScanUtils
from prompt_factory.vul_prompt_common import VulPromptCommon
from prompt_factory.periphery_prompt import PeripheryPrompt
from prompt_factory.core_prompt import CorePrompt
from prompt_factory.assumption_validation_prompt import AssumptionValidationPrompt
from prompt_factory.prompt_assembler import PromptAssembler
from openai_api.openai import detect_vulnerabilities, analyze_code_assumptions
from logging_config import get_logger
import json


class VulnerabilityScanner:
    """漏洞扫描器，负责智能合约代码的漏洞扫描"""
    
    def __init__(self, project_audit):
        self.project_audit = project_audit
        self.logger = get_logger(f"VulnerabilityScanner[{project_audit.project_id}]")

    def do_scan(self, task_manager, is_gpt4=False, filter_func=None):
        """执行漏洞扫描"""
        # 获取任务列表
        tasks = task_manager.get_task_list()
        if len(tasks) == 0:
            return []

        print("🔄 标准模式运行中")
        return self._scan_standard_mode(tasks, task_manager, filter_func, is_gpt4)

    def _scan_standard_mode(self, tasks, task_manager, filter_func, is_gpt4):
        """标准模式扫描
        
        执行策略：
        1. 按 group 分组任务
        2. 同一个 group 内的任务串行执行（保证同组总结的顺序性）
        3. 不同 group 之间并行执行（提升整体效率）
        """
        max_threads = int(os.getenv("MAX_THREADS_OF_SCAN", 5))
        
        # 按 group 分组任务
        group_dict = {}
        for task in tasks:
            group_uuid = getattr(task, 'group', '') or 'no_group'
            if group_uuid not in group_dict:
                group_dict[group_uuid] = []
            group_dict[group_uuid].append(task)
        
        # 为每个 group 定义处理函数（串行处理 group 内的任务）
        def process_group(group_tasks):
            for task in group_tasks:
                self._process_single_task_standard(task, task_manager, filter_func, is_gpt4)
        
        # 并行处理不同的 group
        group_list = list(group_dict.values())
        ScanUtils.execute_parallel_scan(group_list, process_group, max_threads)
        return tasks

    def _execute_vulnerability_scan(self, task, task_manager, is_gpt4: bool) -> str:
        """执行漏洞扫描（使用任务中已确定的rule）
        
        注意：现在统一使用vulnerability_detection配置(claude4sonnet)，is_gpt4参数已不再使用但保留以兼容
        """
        try:
            # 获取任务的business_flow_code作为代码部分
            business_flow_code = getattr(task, 'business_flow_code', task.content)
            
            # 从任务中获取已经确定的rule（Planning阶段已经分配好的checklist）
            task_rule = getattr(task, 'rule', '')
            rule_key = getattr(task, 'rule_key', '')
            
            # 解析rule
            rule_list = []
            if task_rule:
                # 🎯 assumption_violation类型的任务，rule直接是字符串格式
                if rule_key == "assumption_violation":
                    rule_list = task_rule  # 直接使用字符串
                else:
                    # 其他类型任务，尝试解析JSON格式
                    try:
                        rule_list = json.loads(task_rule)
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"任务 {task.name} 的rule解析失败: {e}")
                        rule_list = []
            
            # 🎯 新增：基于group查询同组已有结果并生成总结（根据环境变量开关控制）
            summary_in_reasoning = os.getenv("SUMMARY_IN_REASONING", "True").lower() == "true"
            group_summary = ""
            if summary_in_reasoning:
                group_summary = self._get_group_results_summary(task, task_manager)
            
            # 手动组装prompt（使用任务的具体rule而不是索引）
            assembled_prompt = self._assemble_prompt_with_specific_rule(
                business_flow_code, 
                rule_list, 
                rule_key
            )
            
            # 🎯 如果启用了同组总结且有总结内容，将其添加到prompt前面
            if summary_in_reasoning and group_summary:
                from prompt_factory.group_summary_prompt import GroupSummaryPrompt
                enhanced_prefix = GroupSummaryPrompt.get_enhanced_reasoning_prompt_prefix()
                assembled_prompt = enhanced_prefix + group_summary + "\n\n" + "=" * 80 + "\n\n" + assembled_prompt
            
            # 🎯 reasoning阶段核心漏洞检测统一使用vulnerability_detection配置(claude4sonnet)
            result = detect_vulnerabilities(assembled_prompt)
            
            # 保存结果
            if hasattr(task, 'id') and task.id:
                task_manager.update_result(task.id, result)
            else:
                self.logger.warning(f"任务 {task.name} 没有ID，无法保存结果")
            
            print(f"✅ 任务 {task.name} 扫描完成，使用rule: {rule_key} ({len(rule_list)}个检查项)")
            return result
        except Exception as e:
            print(f"❌ 漏洞扫描执行失败: {e}")
            return ""

    def _process_single_task_standard(self, task, task_manager, filter_func, is_gpt4):
        """标准模式处理单个任务"""
        # 检查任务是否已经扫描过
        if ScanUtils.is_task_already_scanned(task):
            self.logger.info(f"任务 {task.name} 已经扫描过，跳过")
            return
        
        # 检查是否应该扫描此任务
        if not ScanUtils.should_scan_task(task, filter_func):
            self.logger.info(f"任务 {task.name} 不满足扫描条件，跳过")
            return
        
        # 执行漏洞扫描
        self._execute_vulnerability_scan(task, task_manager, is_gpt4)
    
    def _get_group_results_summary(self, task, task_manager) -> str:
        """获取同组任务的结果总结"""
        try:
            # 获取任务的group UUID
            group_uuid = getattr(task, 'group', None)
            if not group_uuid or group_uuid.strip() == "":
                return ""
            
            # 查询同组中已有结果的任务
            tasks_with_results = task_manager.query_tasks_with_results_by_group(group_uuid)
            if not tasks_with_results:
                return ""
            
            # 排除当前任务自己
            current_task_uuid = getattr(task, 'uuid', None)
            if current_task_uuid:
                tasks_with_results = [t for t in tasks_with_results if t.uuid != current_task_uuid]
            
            if not tasks_with_results:
                return ""
            
            # 使用结果总结器生成总结
            from .utils.group_result_summarizer import GroupResultSummarizer
            summary = GroupResultSummarizer.summarize_group_results(tasks_with_results)
            
            if summary:
                print(f"🔍 为任务 {task.name} 找到 {len(tasks_with_results)} 个同组已完成任务的结果总结")
            
            return summary or ""
        except Exception as e:
            self.logger.warning(f"获取同组结果总结失败: {e}")
            return ""

    def _assemble_prompt_with_specific_rule(self, code: str, rule_list: list, rule_key: str) -> str:
        """使用具体的rule列表组装prompt"""
        
        # 🎯 专门处理assumption_violation类型的任务
        if rule_key == "assumption_violation":
            # 对于assumption验证，rule_list是字符串格式（单个assumption statement）
            # 直接使用专门的assumption验证prompt
            return AssumptionValidationPrompt.get_assumption_validation_prompt(
                code, rule_list
            )
        
        # 🎯 专门处理PURE_SCAN类型的任务
        if rule_key == "PURE_SCAN":
            # 使用pure scan的prompt组装器
            return PromptAssembler.assemble_prompt_pure(code)
        
        # 原有的漏洞扫描逻辑（非assumption类型）
        else:
            rule_content = f"### {rule_key} Vulnerability Checks:\n"
            for i, rule in enumerate(rule_list, 1):
                rule_content += f"{i}. {rule}\n"
        
        # 组装完整prompt
        ret_prompt = code + "\n" \
                    + PeripheryPrompt.role_set_move_common() + "\n" \
                    + PeripheryPrompt.task_set_blockchain_common() + "\n" \
                    + CorePrompt.core_prompt_assembled() + "\n" \
                    + rule_content + "\n" \
                    + PeripheryPrompt.guidelines() + "\n" \
                    + PeripheryPrompt.jailbreak_prompt()
        
        return ret_prompt 