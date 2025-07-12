from typing import List, Dict, Any, Optional, Tuple
from .context_manager import ContextManager
from .call_tree_builder import CallTreeBuilder
from .rag_processor import RAGProcessor
from .business_flow_processor import BusinessFlowProcessor
from .function_utils import FunctionUtils


class ContextFactory:
    """上下文工厂类，统一管理所有上下文获取逻辑"""
    
    def __init__(self, project_audit=None, lancedb=None, lance_table_name=None):
        """
        初始化上下文工厂
        
        Args:
            project_audit: 项目审计对象
            lancedb: LanceDB数据库连接
            lance_table_name: Lance表名
        """
        self.project_audit = project_audit
        
        # 初始化各个处理器
        self.context_manager = ContextManager(project_audit, lancedb, lance_table_name)
        self.call_tree_builder = CallTreeBuilder()
        self.rag_processor = None  # 延迟初始化
        self.business_flow_processor = BusinessFlowProcessor(project_audit) if project_audit else None
        
    def initialize_rag_processor(self, functions_to_check: List[Dict], db_path: str = "./lancedb", project_id: str = None):
        """
        初始化RAG处理器
        
        Args:
            functions_to_check: 需要处理的函数列表
            db_path: 数据库路径
            project_id: 项目ID
        """
        self.rag_processor = RAGProcessor(functions_to_check, db_path, project_id)
    
    def build_call_trees(self, functions_to_check: List[Dict], max_workers: int = 1) -> List[Dict]:
        """
        构建调用树
        
        Args:
            functions_to_check: 需要分析的函数列表
            max_workers: 最大线程数
            
        Returns:
            List[Dict]: 调用树列表
        """
        return self.call_tree_builder.build_call_trees(functions_to_check, max_workers)
    
    def get_business_flow_context(self, functions_to_check: List[Dict]) -> Tuple[Dict, Dict, Dict]:
        """
        获取业务流上下文
        
        Args:
            functions_to_check: 需要分析的函数列表
            
        Returns:
            Tuple[Dict, Dict, Dict]: (业务流字典, 业务流行信息字典, 业务流上下文字典)
        """
        if not self.business_flow_processor:
            return {}, {}, {}
        
        return self.business_flow_processor.get_all_business_flow(functions_to_check)
    
    def get_related_functions_by_level(self, function_names: List[str], level: int = 3) -> str:
        """
        获取指定层级的相关函数
        
        Args:
            function_names: 函数名列表
            level: 层级深度
            
        Returns:
            str: 拼接后的函数内容
        """
        if not self.project_audit:
            return ""
        
        return self.context_manager.extract_related_functions_by_level(function_names, level)
    
    def get_semantic_context(self, query_contents: List[str]) -> str:
        """
        获取语义上下文
        
        Args:
            query_contents: 查询内容列表
            
        Returns:
            str: 语义上下文
        """
        return self.context_manager.get_additional_context(query_contents)
    
    def get_internet_context(self, required_info: List[str]) -> str:
        """
        获取网络上下文
        
        Args:
            required_info: 需要查询的信息列表
            
        Returns:
            str: 网络上下文
        """
        return self.context_manager.get_additional_internet_info(required_info)
    
    def search_similar_functions(self, query: str, k: int = 5) -> List[Dict]:
        """
        搜索相似函数
        
        Args:
            query: 搜索查询
            k: 返回结果数量
            
        Returns:
            List[Dict]: 相似函数列表
        """
        if not self.rag_processor:
            return []
        
        return self.rag_processor.search_similar_functions(query, k)
    
    def get_function_context(self, function_name: str) -> Optional[Dict]:
        """
        获取特定函数的上下文
        
        Args:
            function_name: 函数名
            
        Returns:
            Dict: 函数上下文，如果未找到则返回None
        """
        if not self.rag_processor:
            return None
        
        return self.rag_processor.get_function_context(function_name)
    
    def get_comprehensive_context(
        self, 
        function_name: str, 
        query_contents: List[str] = None,
        level: int = 3,
        include_semantic: bool = True,
        include_internet: bool = False
    ) -> Dict[str, Any]:
        """
        获取综合上下文信息
        
        Args:
            function_name: 目标函数名
            query_contents: 查询内容列表
            level: 调用树层级
            include_semantic: 是否包含语义搜索
            include_internet: 是否包含网络搜索
            
        Returns:
            Dict: 综合上下文信息
        """
        context = {
            'function_name': function_name,
            'call_tree_context': '',
            'semantic_context': '',
            'internet_context': '',
            'function_details': None,
            'similar_functions': []
        }
        
        # 获取调用树上下文
        if self.project_audit:
            context['call_tree_context'] = self.get_related_functions_by_level([function_name], level)
        
        # 获取函数详情
        context['function_details'] = self.get_function_context(function_name)
        
        # 获取语义上下文
        if include_semantic and query_contents:
            context['semantic_context'] = self.get_semantic_context(query_contents)
        
        # 获取网络上下文
        if include_internet and query_contents:
            context['internet_context'] = self.get_internet_context(query_contents)
        
        # 获取相似函数
        if self.rag_processor:
            context['similar_functions'] = self.search_similar_functions(function_name, k=5)
        
        return context
    
    def get_context_with_retry(self, code_to_be_tested: str, max_retries: int = 3) -> str:
        """
        带重试机制获取上下文
        
        Args:
            code_to_be_tested: 待测试的代码
            max_retries: 最大重试次数
            
        Returns:
            str: 上下文内容
        """
        return self.context_manager.get_context_with_retry(code_to_be_tested, max_retries)
    
    def extract_required_info(self, claude_response: str) -> List[str]:
        """
        从Claude响应中提取所需信息
        
        Args:
            claude_response: Claude的响应内容
            
        Returns:
            List[str]: 提取的信息列表
        """
        return self.context_manager.extract_required_info(claude_response)
    
    def get_file_level_context(self, file_path: str) -> List[Dict]:
        """
        获取文件级别的上下文
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[Dict]: 文件中的函数列表
        """
        if not self.rag_processor:
            return []
        
        return self.rag_processor.get_functions_by_file(file_path)
    
    def get_visibility_context(self, visibility: str) -> List[Dict]:
        """
        获取特定可见性的函数上下文
        
        Args:
            visibility: 可见性（public, private, internal等）
            
        Returns:
            List[Dict]: 指定可见性的函数列表
        """
        if not self.rag_processor:
            return []
        
        return self.rag_processor.get_functions_by_visibility(visibility)
    
    def merge_contexts(self, contexts: List[str]) -> str:
        """
        合并多个上下文
        
        Args:
            contexts: 上下文列表
            
        Returns:
            str: 合并后的上下文
        """
        return FunctionUtils.merge_function_contexts(contexts)
    
    def get_function_dependencies(self, function_name: str, all_functions: List[Dict]) -> List[str]:
        """
        获取函数的依赖关系
        
        Args:
            function_name: 函数名
            all_functions: 所有函数列表
            
        Returns:
            List[str]: 依赖的函数名列表
        """
        target_func = FunctionUtils.get_function_by_name(all_functions, function_name)
        if not target_func:
            return []
        
        return FunctionUtils.get_function_dependencies(target_func, all_functions)
    
    def cleanup(self):
        """清理资源"""
        if self.rag_processor:
            self.rag_processor.delete_table()
        
        # 清理其他资源
        self.context_manager = None
        self.call_tree_builder = None
        self.rag_processor = None
        self.business_flow_processor = None 