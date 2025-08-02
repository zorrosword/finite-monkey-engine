import os
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from .utils.dialogue_manager import DialogueHistory
from .utils.scan_utils import ScanUtils
from prompt_factory.vul_prompt_common import VulPromptCommon
from prompt_factory.periphery_prompt import PeripheryPrompt
from prompt_factory.core_prompt import CorePrompt
from openai_api.openai import ask_vul, ask_claude
from logging_config import get_logger
import json


class VulnerabilityScanner:
    """漏洞扫描器，负责智能合约代码的漏洞扫描"""
    
    def __init__(self, project_audit):
        self.project_audit = project_audit
        self.logger = get_logger(f"VulnerabilityScanner[{project_audit.project_id}]")
        # 对话历史管理
        self.dialogue_history = DialogueHistory(project_audit.project_id)
    








    def do_scan(self, task_manager, is_gpt4=False, filter_func=None):
        """执行漏洞扫描"""
        # 获取任务列表
        tasks = task_manager.get_task_list()
        if len(tasks) == 0:
            return []

        # 检查是否启用对话模式
        dialogue_mode = os.getenv("ENABLE_DIALOGUE_MODE", "False").lower() == "true"
        
        if dialogue_mode:
            print("🗣️ 对话模式已启用")
            return self._scan_with_dialogue_mode(tasks, task_manager, filter_func, is_gpt4)
        else:
            print("🔄 标准模式运行中")
            return self._scan_standard_mode(tasks, task_manager, filter_func, is_gpt4)

    def _scan_standard_mode(self, tasks, task_manager, filter_func, is_gpt4):
        """标准模式扫描"""
        max_threads = int(os.getenv("MAX_THREADS_OF_SCAN", 5))
        
        def process_task(task):
            self._process_single_task_standard(task, task_manager, filter_func, is_gpt4)
            
        ScanUtils.execute_parallel_scan(tasks, process_task, max_threads)
        return tasks

    def _scan_with_dialogue_mode(self, tasks, task_manager, filter_func, is_gpt4):
        """对话模式扫描"""
        # 按task.name分组任务
        task_groups = ScanUtils.group_tasks_by_name(tasks)
        
        # 清除历史对话记录
        self.dialogue_history.clear()
        
        # 对每组任务进行处理
        max_threads = int(os.getenv("MAX_THREADS_OF_SCAN", 5))
        
        def process_task_group(group_tasks):
            for task in group_tasks:
                self._process_single_task_dialogue(task, task_manager, filter_func, is_gpt4)
        
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = []
            for task_name, group_tasks in task_groups.items():
                future = executor.submit(process_task_group, group_tasks)
                futures.append(future)
            
            with tqdm(total=len(task_groups), desc="Processing task groups") as pbar:
                for future in as_completed(futures):
                    future.result()
                    pbar.update(1)
        
        return tasks









    def _execute_vulnerability_scan(self, task, task_manager, is_gpt4: bool) -> str:
        """执行漏洞扫描（使用任务中已确定的rule）"""
        try:
            # 获取任务的business_flow_code作为代码部分
            business_flow_code = getattr(task, 'business_flow_code', task.content)
            
            # 从任务中获取已经确定的rule（Planning阶段已经分配好的checklist）
            task_rule = getattr(task, 'rule', '')
            rule_key = getattr(task, 'rule_key', '')
            
            # 解析rule（JSON格式）
            rule_list = []
            if task_rule:
                try:
                    rule_list = json.loads(task_rule)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"任务 {task.name} 的rule解析失败: {e}")
                    rule_list = []
            
            # 手动组装prompt（使用任务的具体rule而不是索引）
            assembled_prompt = self._assemble_prompt_with_specific_rule(
                business_flow_code, 
                rule_list, 
                rule_key
            )
            
            if is_gpt4:
                result = ask_vul(assembled_prompt)
            else:
                result = ask_claude(assembled_prompt)
            
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

    def _process_single_task_dialogue(self, task, task_manager, filter_func, is_gpt4):
        """对话模式处理单个任务"""
        # 检查任务是否已经扫描过
        if ScanUtils.is_task_already_scanned(task):
            self.logger.info(f"任务 {task.name} 已经扫描过，跳过")
            return
        
        # 检查是否应该扫描此任务
        if not ScanUtils.should_scan_task(task, filter_func):
            self.logger.info(f"任务 {task.name} 不满足扫描条件，跳过")
            return
        
        # 获取对话历史
        dialogue_context = self.dialogue_history.get_relevant_context(task)
        
        # 执行漏洞扫描
        scan_result = self._execute_vulnerability_scan(task, task_manager, is_gpt4)
        
        # 更新对话历史
        self.dialogue_history.add_scan_result(task, scan_result, None)
    
    def _assemble_prompt_with_specific_rule(self, code: str, rule_list: list, rule_key: str) -> str:
        """使用具体的rule列表组装prompt"""
        # 将rule_list转换为字符串格式
        if rule_list:
            rule_content = f"### {rule_key} Vulnerability Checks:\n"
            for i, rule in enumerate(rule_list, 1):
                rule_content += f"{i}. {rule}\n"
        else:
            rule_content = "### General Vulnerability Checks (no specific rules assigned)"
        
        # 组装完整prompt
        ret_prompt = code + "\n" \
                    + PeripheryPrompt.role_set_solidity_common() + "\n" \
                    + PeripheryPrompt.task_set_blockchain_common() + "\n" \
                    + CorePrompt.core_prompt_assembled() + "\n" \
                    + rule_content + "\n" \
                    + PeripheryPrompt.guidelines() + "\n" \
                    + PeripheryPrompt.jailbreak_prompt()
        
        return ret_prompt 