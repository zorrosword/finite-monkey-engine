import os
import json
import re
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List, Dict

from prompt_factory.core_prompt import CorePrompt
from openai_api.openai import common_get_embedding, ask_claude, ask_grok3_deepsearch


class ContextManager:
    """上下文管理器，负责获取和管理分析所需的额外上下文信息"""
    
    def __init__(self, project_audit=None, lancedb=None, lance_table_name=None):
        self.project_audit = project_audit
        self.lancedb = lancedb
        self.lance_table_name = lance_table_name
    
    def get_related_functions(self, query: str, k: int = 3) -> List[Dict]:
        """通过语义搜索获取相关函数"""
        if not self.lancedb or not self.lance_table_name:
            return []
            
        query_embedding = common_get_embedding(query)
        table = self.lancedb.open_table(self.lance_table_name)
        return table.search(query_embedding).limit(k).to_list()
    
    def extract_required_info(self, claude_response: str) -> List[str]:
        """从Claude的响应中提取需要进一步调查的信息"""
        prompt = CorePrompt.extract_required_info_prompt()
        
        extraction_result = ask_claude(prompt.format(response=claude_response))
        if not extraction_result or extraction_result.isspace():
            return []
        
        # 如果响应包含否定短语，返回空列表
        if any(phrase in extraction_result.lower() for phrase in ["no need", "not needed", "no additional", "no more"]):
            return []
        
        return [extraction_result]
    
    def get_additional_context(self, query_contents: List[str]) -> str:
        """获取额外的上下文信息"""
        if not query_contents:
            print("❌ 没有查询内容，无法获取额外上下文")
            return ""
        
        print(f"🔍 正在查询 {len(query_contents)} 条相关信息...")
        related_functions = []
        for query in query_contents:
            results = self.get_related_functions(query, k=10)
            if results:
                print(f"✅ 找到 {len(results)} 个相关函数")
                related_functions.extend(results)
            else:
                print("⚠️ 未找到相关函数")
        
        if related_functions:
            function_names = [func['name'].split('.')[-1] for func in related_functions]
            print(f"📑 正在提取 {len(function_names)} 个函数的上下文...")
            return self.extract_related_functions_by_level(function_names, 3)
        
        print("❌ 未找到任何相关函数")
        return ""
    
    def extract_related_functions_by_level(self, function_names: List[str], level: int) -> str:
        """
        从call_trees中提取指定函数相关的上下游函数信息并扁平化处理
        
        Args:
            function_names: 要分析的函数名列表
            level: 要分析的层级深度
            
        Returns:
            str: 所有相关函数内容的拼接文本
        """
        from .function_utils import FunctionUtils
        return FunctionUtils.extract_related_functions_by_level(
            self.project_audit, 
            function_names, 
            level, 
            return_pairs=False
        )
    
    def get_additional_internet_info(self, required_info: List[str]) -> str:
        """判断是否需要联网搜索并获取网络信息
        
        Args:
            required_info: 需要进一步调查的信息列表
            
        Returns:
            str: 搜索获取的相关信息
        """
        # 检查环境变量是否允许网络搜索
        if os.getenv("ENABLE_INTERNET_SEARCH", "False").lower() != "true":
            print("❌ 网络搜索已禁用")
            return ""
        
        if not required_info:
            print("❌ 没有查询内容，无法进行网络搜索")
            return ""
        
        # 调用Grok3深度搜索
        search_results = []
        for query in required_info:
            try:
                result = ask_grok3_deepsearch(query)
                if result:
                    search_results.append(result)
            except Exception as e:
                print(f"⚠️ 搜索查询 '{query}' 时发生错误: {e}")
        
        if search_results:
            print(f"✅ 成功获取 {len(search_results)} 条网络信息")
            return '\n\n'.join(search_results)
        else:
            print("❌ 未能从网络获取任何相关信息")
            return ""
    
    def get_context_with_retry(self, code_to_be_tested: str, max_retries: int = 3) -> str:
        """带重试机制获取上下文"""
        retry_count = 0
        combined_text = ""

        while retry_count < max_retries:
            related_functions = self.get_related_functions(code_to_be_tested, 5)
            related_functions_names = [func['name'].split('.')[-1] for func in related_functions]
            combined_text = self.extract_related_functions_by_level(related_functions_names, 3)
            print(len(str(combined_text).strip()))
            
            if self.is_valid_context(combined_text):
                break  # 如果获取到有效上下文，就跳出循环
            
            retry_count += 1
            print(f"❌ 提取的上下文长度不足10字符，正在重试 ({retry_count}/{max_retries})...")
        
        return combined_text
    
    def is_valid_context(self, context: str) -> bool:
        """检查上下文是否有效"""
        return len(str(context).strip()) >= 10 