from typing import List
from tqdm import tqdm

from ..utils.context_manager import ContextManager


class ContextUpdateProcessor:
    """业务流上下文更新处理器"""
    
    def __init__(self, context_manager: ContextManager):
        self.context_manager = context_manager
    
    def update_business_flow_context(self, task_manager):
        """更新业务流程上下文"""
        tasks = task_manager.get_task_list()
        
        for task in tqdm(tasks, desc="Processing tasks for update business_flow_context"):
            if task.score == "1":
                continue
                
            if task.if_business_flow_scan == "1":
                code_to_be_tested = task.business_flow_code
            else:
                code_to_be_tested = task.content

            # 添加重试逻辑
            combined_text = self._get_context_with_retry(code_to_be_tested)
            
            if not self._is_valid_context(combined_text):
                print(f"❌ 经过多次重试后，仍未能获取有效上下文，跳过该任务")
                continue
                
            # 更新task对应的business_flow_context
            task_manager.update_business_flow_context(task.id, combined_text)
            task_manager.update_score(task.id, "1")
    
    def _get_context_with_retry(self, code_to_be_tested: str, max_retries: int = 3) -> str:
        """带重试机制获取上下文"""
        retry_count = 0
        combined_text = ""

        while retry_count < max_retries:
            related_functions = self.context_manager.get_related_functions(code_to_be_tested, 5)
            related_functions_names = [func['name'].split('.')[-1] for func in related_functions]
            combined_text = self.context_manager.extract_related_functions_by_level(related_functions_names, 3)
            print(len(str(combined_text).strip()))
            
            if self._is_valid_context(combined_text):
                break  # 如果获取到有效上下文，就跳出循环
            
            retry_count += 1
            print(f"❌ 提取的上下文长度不足10字符，正在重试 ({retry_count}/{max_retries})...")
        
        return combined_text
    
    def _is_valid_context(self, context: str) -> bool:
        """检查上下文是否有效"""
        return len(str(context).strip()) >= 10 