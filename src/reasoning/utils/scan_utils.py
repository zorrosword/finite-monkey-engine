import os
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from prompt_factory.prompt_assembler import PromptAssembler
from prompt_factory.vul_prompt_common import VulPromptCommon
from openai_api.openai import ask_vul, ask_deepseek, ask_claude, cut_reasoning_content


class ScanUtils:
    """扫描相关的工具函数类"""
    
    @staticmethod
    def update_recommendation_for_fine_grained(task_manager, task_id: int, current_index: int):
        """为细粒度扫描更新推荐信息"""
        # 在新的实现中，recommendation已经在planning阶段设置好了，这里不需要再更新
        # 但为了兼容性，保留这个方法，只是不执行实际操作
        print(f"[DEBUG🐞]📋Skipping recommendation update - using pre-set recommendation from planning phase")
        pass
    
    @staticmethod
    def is_task_already_scanned(task) -> bool:
        """检查任务是否已经扫描过"""
        result = task.get_result()
        return result is not None and len(result) > 0 and str(result).strip() != "NOT A VUL IN RES no"
    
    @staticmethod
    def should_scan_task(task, filter_func) -> bool:
        """判断是否应该扫描该任务"""
        return filter_func is None or filter_func(task)
    
    @staticmethod
    def get_code_to_test(task):
        """获取要测试的代码"""
        business_flow_code = task.business_flow_code
        if_business_flow_scan = task.if_business_flow_scan
        function_code = task.content
        
        return business_flow_code if if_business_flow_scan == "1" else function_code
    
    @staticmethod
    def process_scan_response(response_vul: str) -> str:
        """处理扫描响应"""
        return response_vul if response_vul is not None else "no"
    
    @staticmethod
    def execute_parallel_scan(tasks: List, process_func, max_threads: int = 5):
        """执行并行扫描"""
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(process_func, task) for task in tasks]
            
            with tqdm(total=len(tasks), desc="Processing tasks") as pbar:
                for future in as_completed(futures):
                    future.result()
                    pbar.update(1)
    
    @staticmethod
    def group_tasks_by_name(tasks: List) -> Dict[str, List]:
        """按任务名称分组任务"""
        task_groups = {}
        for task in tasks:
            task_groups.setdefault(task.name, []).append(task)
        return task_groups
    
    @staticmethod
    def add_dialogue_history_to_prompt(prompt: str, dialogue_history: List[str]) -> str:
        """将对话历史添加到提示词中"""
        if dialogue_history:
            history_text = "\n\nPreviously Found Vulnerabilities:\n" + "\n".join(dialogue_history)
            prompt += history_text + "\n\nExcluding these vulnerabilities, please continue searching for other potential vulnerabilities."
        return prompt 