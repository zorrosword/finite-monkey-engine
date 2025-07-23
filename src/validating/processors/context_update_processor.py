from typing import List
import os
from tqdm import tqdm

from context.context_manager import ContextManager


class ContextUpdateProcessor:
    """Business flow context update processor"""
    
    def __init__(self, context_manager: ContextManager):
        self.context_manager = context_manager
    
    def update_business_flow_context(self, task_manager):
        """Update business flow context"""
        tasks = task_manager.get_task_list()
        
        for task in tqdm(tasks, desc="Processing tasks for update business_flow_context"):
            if task.score == "1":
                continue
                
            if task.if_business_flow_scan == "1":
                code_to_be_tested = task.business_flow_code
            else:
                code_to_be_tested = task.content

            # Get context based on huge_project setting
            combined_text = self._get_context_with_mode_aware_logic(code_to_be_tested)
            
            if not self._is_valid_context(combined_text):
                print(f"❌ Unable to get valid context, skipping this task")
                continue
                
            # Update the business_flow_context for the task
            task_manager.update_business_flow_context(task.id, combined_text)
            task_manager.update_score(task.id, "1")
    
    def _get_context_with_mode_aware_logic(self, code_to_be_tested: str) -> str:
        """Get context based on huge_project mode setting"""
        huge_project = eval(os.environ.get('HUGE_PROJECT', 'False'))
        
        if huge_project:
            print("🚀 检测到 HUGE_PROJECT=True，只使用 LanceDB RAG 内容，跳过 call tree 上下文")
            # In huge project mode, only use RAG content from LanceDB
            related_functions = self.context_manager.get_related_functions(code_to_be_tested, 5)
            if not related_functions:
                print("⚠️ RAG 搜索未找到相关函数")
                return ""
            
            # Directly use the content from RAG search results
            rag_contents = []
            for func in related_functions:
                func_content = func.get('content', '')
                if func_content.strip():
                    rag_contents.append(f"// Function: {func.get('name', 'Unknown')}\n{func_content}")
            
            combined_text = '\n\n'.join(rag_contents)
            print(f"✅ 从 RAG 获取到 {len(related_functions)} 个相关函数，总长度: {len(combined_text)} 字符")
            return combined_text
        else:
            # Use original logic with call tree extraction and retry
            return self._get_context_with_retry(code_to_be_tested)
    
    def _get_context_with_retry(self, code_to_be_tested: str, max_retries: int = 3) -> str:
        """Get context with retry mechanism (used in normal mode)"""
        retry_count = 0
        combined_text = ""

        while retry_count < max_retries:
            related_functions = self.context_manager.get_related_functions(code_to_be_tested, 5)
            related_functions_names = [func['name'].split('.')[-1] for func in related_functions]
            combined_text = self.context_manager.extract_related_functions_by_level(related_functions_names, 3)
            print(len(str(combined_text).strip()))
            
            if self._is_valid_context(combined_text):
                break  # Exit loop if valid context is obtained
            
            retry_count += 1
            print(f"❌ Extracted context length is less than 10 characters, retrying ({retry_count}/{max_retries})...")
        
        return combined_text
    
    def _is_valid_context(self, context: str) -> bool:
        """Check if context is valid"""
        return len(str(context).strip()) >= 10 