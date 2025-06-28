import os
import time
from typing import List, Tuple

from ..utils.context_manager import ContextManager
from ..utils.check_utils import CheckUtils
from prompt_factory.prompt_assembler import PromptAssembler
from openai_api.openai import common_ask_confirmation


class AnalysisProcessor:
    """分析处理器，负责执行具体的漏洞分析逻辑"""
    
    def __init__(self, context_manager: ContextManager):
        self.context_manager = context_manager
    
    def process_task_analysis(self, task, task_manager):
        """处理单个任务的分析"""
        # 用于收集所有分析结果
        analysis_collection = []
        
        starttime = time.time()
        result = task.get_result(False)
        
        print("\n🔍 开始漏洞确认流程...")
        
        # 获取要分析的代码
        code_to_be_tested = CheckUtils.get_code_to_analyze(task)
        print(f"\n📊 分析代码类型: {'业务流程代码' if task.if_business_flow_scan=='1' else '函数代码'}")
        
        # 第一轮分析
        response_final, final_response = self._perform_initial_analysis(
            code_to_be_tested, result, analysis_collection
        )
        
        # 如果初始分析显示无漏洞，直接结束
        if response_final == "no":
            formatted_results = CheckUtils.format_analysis_results(analysis_collection)
            CheckUtils.update_task_results(task_manager, task.id, result, response_final, final_response, formatted_results)
            
            endtime = time.time()
            CheckUtils.print_task_summary(endtime - starttime, 1, response_final)
            return
        
        # 执行多轮确认
        response_final, final_response = self._perform_multi_round_confirmation(
            code_to_be_tested, result, analysis_collection
        )
        
        # 更新结果
        formatted_results = CheckUtils.format_analysis_results(analysis_collection)
        CheckUtils.update_task_results(task_manager, task.id, result, response_final, final_response, formatted_results)
        
        endtime = time.time()
        CheckUtils.print_task_summary(endtime - starttime, len(analysis_collection), response_final)
    
    def _perform_initial_analysis(self, code_to_be_tested: str, result: str, analysis_collection: List) -> Tuple:
        """执行初始分析"""
        print("\n=== 第一轮分析开始 ===")
        print("📝 正在分析潜在漏洞...")
        prompt = PromptAssembler.assemble_vul_check_prompt(code_to_be_tested, result)
        
        initial_response = common_ask_confirmation(prompt)
        if not initial_response or initial_response == "":
            print(f"❌ Error: Empty response received")
            return "not sure", "Empty response"
        
        print("\n📊 Initial Analysis Result Length:")
        print("-" * 80)
        print(len(initial_response))
        print("-" * 80)

        # 收集初始分析结果
        analysis_collection.extend([
            "=== 初始分析结果 ===",
            initial_response
        ])

        # 处理初始响应
        initial_result_status = CheckUtils.process_round_response(initial_response)
        analysis_collection.extend([
            "=== 初始分析状态 ===",
            initial_result_status
        ])

        # 提取所需信息
        required_info = self.context_manager.extract_required_info(initial_response)
        if required_info:
            analysis_collection.append("=== 需要进一步分析的信息 ===")
            analysis_collection.extend(required_info)

        if CheckUtils.should_skip_early(initial_result_status):
            print("\n🛑 Initial analysis shows clear 'no vulnerability' - stopping further analysis")
            return "no", "Analysis stopped after initial round due to clear 'no vulnerability' result"
        
        return None, None  # 继续多轮确认
    
    def _perform_multi_round_confirmation(self, code_to_be_tested: str, result: str, analysis_collection: List) -> Tuple:
        """执行多轮确认分析"""
        # 设置最大确认轮数
        max_rounds = int(os.getenv("MAX_CONFIRMATION_ROUNDS", 3))
        request_per_round = int(os.getenv("REQUESTS_PER_CONFIRMATION_ROUND", 3))
        
        # 按轮次收集结果 - 新的数据结构
        round_results = []  # 每个元素是一轮的结果列表
        
        # 每轮都从原始代码开始，保持轮间独立
        base_code = code_to_be_tested
        
        for round_num in range(max_rounds):
            print(f"\n=== 确认轮次 {round_num + 1}/{max_rounds} (独立轮次) ===")
            
            # 当前轮次的结果
            current_round_results = []
            
            # 每轮从基础代码开始，不依赖前轮结果
            current_code = base_code
            round_context_enhanced = False
            round_has_early_exit = False
            
            # 轮内上下文增强和多次询问
            for request_num in range(request_per_round):
                print(f"\n🔍 第 {round_num + 1} 轮 - 第 {request_num + 1} / {request_per_round} 次询问")
                
                # 轮内上下文增强：从第2次询问开始可以增强上下文
                if request_num > 0 and not round_context_enhanced:
                    current_code = self._enhance_context_within_round(
                        base_code, analysis_collection, round_num
                    )
                    round_context_enhanced = True
                
                # 使用当前上下文进行询问
                sub_round_response = CheckUtils.perform_confirmation_round(
                    current_code, result, round_num, request_num
                )
                
                # 收集分析结果
                analysis_collection.extend([
                    f"=== 第 {round_num + 1} 轮 {request_num + 1} 次询问分析结果 ===",
                    sub_round_response
                ])
                
                # 处理响应结果
                if len(sub_round_response) == 0:
                    print(f"\n❌ 无效的响应: 第 {round_num + 1} 轮 {request_num + 1} 次询问结果为空")
                    continue
                    
                sub_result_status = CheckUtils.process_round_response(sub_round_response)
                analysis_collection.extend([
                    f"=== 第 {round_num + 1} 轮 {request_num + 1} 次分析状态 ===",
                    sub_result_status
                ])
                print(f"第 {round_num + 1} 轮第 {request_num + 1} 次分析状态: {sub_result_status}")
                
                # 添加到当前轮次结果
                current_round_results.append(sub_result_status)
                
                # 检查是否需要提前退出（但使用新逻辑时不立即退出）
                if CheckUtils.should_skip_early(sub_result_status):
                    print(f"\n⚠️ 第 {round_num + 1} 轮第 {request_num + 1} 次发现'无漏洞'结果")
                    round_has_early_exit = True
                    # 注意：这里不立即退出，而是记录状态，让新逻辑来判断
            
            # 将当前轮次的结果添加到总结果中
            if current_round_results:  # 只有当轮次有结果时才添加
                round_results.append(current_round_results)
                print(f"\n📋 第 {round_num + 1} 轮完成，收集到 {len(current_round_results)} 个结果")
            
            # 如果本轮内出现no，记录但不立即退出（让新逻辑判断）
            if round_has_early_exit:
                print(f"\n📝 第 {round_num + 1} 轮出现'无漏洞'结果，继续后续轮次以完整评估")
        
        # 使用新的按轮次分析方法
        print(f"\n🔍 开始使用新的按轮次确认逻辑，共 {len(round_results)} 轮结果")
        return CheckUtils.collect_analysis_results_by_rounds(analysis_collection, round_results)
    
    def _enhance_context_within_round(self, base_code: str, analysis_collection: List, round_num: int) -> str:
        """轮内上下文增强"""
        print(f"\n📈 轮内上下文增强...")
        
        # 基于本轮第一次的结果提取需要的信息
        if len(analysis_collection) >= 2:
            last_response_in_round = analysis_collection[-2]
            required_info = self.context_manager.extract_required_info(last_response_in_round)
            
            if required_info:
                print(f"\n🔍 轮内需要额外信息: {len(required_info)} 项")
                
                # 轮内网络搜索
                internet_info = self.context_manager.get_additional_internet_info(required_info)
                # 轮内上下文获取
                additional_context = self.context_manager.get_additional_context(required_info)
                
                enhanced_context = []
                if internet_info:
                    enhanced_context.extend([
                        "=== Internet Search Results ===",
                        internet_info
                    ])
                    analysis_collection.extend([
                        f"=== 第 {round_num + 1} 轮轮内网络搜索结果 ===",
                        internet_info
                    ])
                
                if additional_context:
                    enhanced_context.extend([
                        "=== Additional Context ===",
                        additional_context
                    ])
                    analysis_collection.extend([
                        f"=== 第 {round_num + 1} 轮轮内额外上下文 ===",
                        additional_context
                    ])
                
                if enhanced_context:
                    enhanced_code = base_code + "\n\n" + "\n\n".join(enhanced_context)
                    print(f"\n📦 轮内上下文增强完成 (总长度: {len(enhanced_code)} 字符)")
                    return enhanced_code
        
        return base_code 