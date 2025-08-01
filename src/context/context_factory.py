from typing import List, Dict, Any, Optional, Tuple
from .context_manager import ContextManager
from .rag_processor import RAGProcessor
from .business_flow_processor import BusinessFlowProcessor
from .function_utils import FunctionUtils

# 直接使用Tree-sitter版本的CallTreeBuilder
from tree_sitter_parsing import TreeSitterCallTreeBuilder as CallTreeBuilder


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
        
    def initialize_rag_processor(self, functions_to_check: List[Dict], db_path: str = "./lancedb", project_id: str = None, call_trees: List[Dict] = None):
        """
        初始化RAG处理器
        
        Args:
            functions_to_check: 需要处理的函数列表
            db_path: 数据库路径
            project_id: 项目ID
            call_trees: 调用树数据（可选）
        """
        # 如果没有传递call_trees，尝试从project_audit获取
        if call_trees is None and self.project_audit:
            call_trees = getattr(self.project_audit, 'call_trees', [])
        
        self.rag_processor = RAGProcessor(functions_to_check, db_path, project_id, call_trees)
    
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
    
    # ========== 🆕 函数级别多种embedding搜索接口 ==========
    
    def search_functions_by_content(self, query: str, k: int = 5) -> List[Dict]:
        """
        基于函数内容搜索相似函数
        
        Args:
            query: 搜索查询（通常是代码片段）
            k: 返回结果数量
            
        Returns:
            List[Dict]: 相似函数列表
        """
        if not self.rag_processor:
            return []
        
        return self.rag_processor.search_functions_by_content(query, k)
    
    def search_functions_by_name(self, query: str, k: int = 5) -> List[Dict]:
        """
        基于函数名称搜索相似函数
        
        Args:
            query: 搜索查询（合约名+函数名，如"Token.transfer"）
            k: 返回结果数量
            
        Returns:
            List[Dict]: 相似函数列表
        """
        if not self.rag_processor:
            return []
        
        return self.rag_processor.search_functions_by_name(query, k)
    
    def search_functions_by_natural_language(self, query: str, k: int = 5) -> List[Dict]:
        """
        基于自然语言描述搜索相似函数
        
        Args:
            query: 搜索查询（自然语言描述，如"transfer tokens between accounts"）
            k: 返回结果数量
            
        Returns:
            List[Dict]: 相似函数列表
        """
        if not self.rag_processor:
            return []
        
        return self.rag_processor.search_functions_by_natural_language(query, k)
    
    # ========== 🆕 文件级别多种embedding搜索接口 ==========
    
    def search_files_by_content(self, query: str, k: int = 5) -> List[Dict]:
        """
        基于文件内容搜索相似文件
        
        Args:
            query: 搜索查询（文件内容片段）
            k: 返回结果数量
            
        Returns:
            List[Dict]: 相似文件列表
        """
        if not self.rag_processor:
            return []
        
        return self.rag_processor.search_files_by_content(query, k)
    
    def search_files_by_natural_language(self, query: str, k: int = 5) -> List[Dict]:
        """
        基于文件自然语言描述搜索相似文件
        
        Args:
            query: 搜索查询（自然语言描述，如"ERC20 token implementation"）
            k: 返回结果数量
            
        Returns:
            List[Dict]: 相似文件列表
        """
        if not self.rag_processor:
            return []
        
        return self.rag_processor.search_files_by_natural_language(query, k)
    
    def search_similar_files(self, query: str, k: int = 5) -> List[Dict]:
        """
        搜索相似文件（默认使用自然语言描述）
        
        Args:
            query: 搜索查询（文件功能描述）
            k: 返回结果数量
            
        Returns:
            List[Dict]: 相似文件列表
        """
        return self.search_files_by_natural_language(query, k)
    
    # ========== 🆕 综合搜索接口 ==========
    
    def get_comprehensive_function_search_results(self, query: str, k: int = 3) -> Dict[str, List[Dict]]:
        """
        获取函数的综合搜索结果（使用函数表的3种embedding）
        
        Args:
            query: 搜索查询
            k: 每种类型返回的结果数量
            
        Returns:
            Dict: 包含3种搜索结果的字典
        """
        if not self.rag_processor:
            return {}
        
        results = {
            'content_based': self.search_functions_by_content(query, k),
            'name_based': self.search_functions_by_name(query, k),
            'natural_language_based': self.search_functions_by_natural_language(query, k)
        }
        
        return results
    
    def get_comprehensive_file_search_results(self, query: str, k: int = 3) -> Dict[str, List[Dict]]:
        """
        获取文件的综合搜索结果（使用文件表的2种embedding）
        
        Args:
            query: 搜索查询
            k: 每种类型返回的结果数量
            
        Returns:
            Dict: 包含2种搜索结果的字典
        """
        if not self.rag_processor:
            return {}
        
        results = {
            'content_based': self.search_files_by_content(query, k),
            'natural_language_based': self.search_files_by_natural_language(query, k)
        }
        
        return results
    
    def get_comprehensive_search_results(self, query: str, k: int = 3) -> Dict[str, Any]:
        """
        获取全面的综合搜索结果（函数+文件的所有embedding类型）
        
        Args:
            query: 搜索查询
            k: 每种类型返回的结果数量
            
        Returns:
            Dict: 包含所有类型搜索结果的字典
        """
        results = {
            'functions': self.get_comprehensive_function_search_results(query, k),
            'files': self.get_comprehensive_file_search_results(query, k)
        }
        
        return results
    
    # ========== 兼容性方法（保持原有接口） ==========
    
    def search_similar_functions(self, query: str, k: int = 5) -> List[Dict]:
        """
        搜索相似函数（默认使用内容embedding）
        
        Args:
            query: 搜索查询
            k: 返回结果数量
            
        Returns:
            List[Dict]: 相似函数列表
        """
        return self.search_functions_by_content(query, k)
    
    # ========== 数据获取方法 ==========
    
    def get_function_context(self, function_name: str) -> Optional[Dict]:
        """
        获取特定函数的上下文信息
        
        Args:
            function_name: 函数名
            
        Returns:
            Dict: 函数上下文（包含3种embedding），如果未找到则返回None
        """
        if not self.rag_processor:
            return None
        
        return self.rag_processor.get_function_context(function_name)
    
    def get_file_context(self, file_path: str) -> Optional[Dict]:
        """
        获取特定文件的上下文信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict: 文件上下文（包含2种embedding），如果未找到则返回None
        """
        if not self.rag_processor:
            return None
        
        return self.rag_processor.get_file_by_path(file_path)
    
    def get_all_files(self) -> List[Dict]:
        """
        获取所有文件信息
        
        Returns:
            List[Dict]: 所有文件列表
        """
        if not self.rag_processor:
            return []
        
        return self.rag_processor.get_all_files()
    
    def get_file_description(self, file_path: str) -> Optional[Dict]:
        """
        获取文件的自然语言描述
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict: 文件描述信息，如果未找到则返回None
        """
        return self.get_file_context(file_path)
    
    def get_comprehensive_context(
        self, 
        function_name: str, 
        query_contents: List[str] = None,
        level: int = 3,
        include_semantic: bool = True,
        include_internet: bool = False,
        use_all_embedding_types: bool = False
    ) -> Dict[str, Any]:
        """
        获取综合上下文信息
        
        Args:
            function_name: 目标函数名
            query_contents: 查询内容列表
            level: 调用树层级
            include_semantic: 是否包含语义搜索
            include_internet: 是否包含网络搜索
            use_all_embedding_types: 是否使用所有embedding类型进行搜索
            
        Returns:
            Dict: 综合上下文信息
        """
        context = {
            'function_name': function_name,
            'call_tree_context': '',
            'semantic_context': '',
            'internet_context': '',
            'function_details': None,
            'similar_functions': {},
            'related_files': {}
        }
        
        # 获取调用树上下文
        if self.project_audit:
            context['call_tree_context'] = self.get_related_functions_by_level([function_name], level)
        
        # 获取函数详情（包含3种embedding的完整信息）
        context['function_details'] = self.get_function_context(function_name)
        
        # 获取语义上下文
        if include_semantic and query_contents:
            context['semantic_context'] = self.get_semantic_context(query_contents)
        
        # 获取网络上下文
        if include_internet and query_contents:
            context['internet_context'] = self.get_internet_context(query_contents)
        
        # 获取相似函数
        if self.rag_processor:
            if use_all_embedding_types:
                context['similar_functions'] = self.get_comprehensive_function_search_results(function_name, k=3)
                # 同时搜索相关文件
                if context['function_details']:
                    file_path = context['function_details'].get('relative_file_path', '')
                    if file_path:
                        context['related_files'] = self.get_comprehensive_file_search_results(file_path, k=2)
            else:
                context['similar_functions'] = {'content_based': self.search_similar_functions(function_name, k=5)}
        
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
        获取文件级别的上下文（该文件中的所有函数）
        
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
    
    # ========== 数据库管理方法 ==========
    
    def get_all_tables_info(self) -> Optional[Dict[str, Any]]:
        """
        获取所有LanceDB表的信息
        
        Returns:
            Dict: 包含函数表和文件表的信息，如果RAG处理器未初始化则返回None
        """
        if not self.rag_processor:
            return None
        
        return self.rag_processor.get_all_tables_info()
    
    def cleanup(self):
        """清理资源"""
        if self.rag_processor:
            self.rag_processor.delete_all_tables()
        
        # 清理其他资源
        self.context_manager = None
        self.call_tree_builder = None
        self.rag_processor = None
        self.business_flow_processor = None 