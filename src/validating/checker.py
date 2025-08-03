from .processors import ContextUpdateProcessor, ConfirmationProcessor, AnalysisProcessor


class VulnerabilityChecker:
    """Vulnerability checker responsible for deep verification and confirmation of vulnerabilities
    
    Refactored to directly use project audit data without ContextFactory dependency:
    - Entry layer: VulnerabilityChecker (this class)
    - Processor layer: ContextUpdateProcessor, ConfirmationProcessor, AnalysisProcessor  
    - Data layer: Direct access to project_audit data
    """
    
    def __init__(self, project_audit, lancedb=None, lance_table_name=None):
        """
        初始化漏洞检查器，直接使用项目审计数据
        
        Args:
            project_audit: TreeSitterProjectAudit实例，包含解析后的项目数据
            lancedb: LanceDB实例（可选）
            lance_table_name: Lance表名（可选）
        """
        self.project_audit = project_audit
        self.lancedb = lancedb
        self.lance_table_name = lance_table_name
        
        # 从project_audit获取核心数据
        self.functions = project_audit.functions
        self.functions_to_check = project_audit.functions_to_check
        self.call_trees = project_audit.call_trees
        
        # 创建简化的context_manager对象，只包含必要的数据
        self.context_data = {
            'functions': self.functions,
            'functions_to_check': self.functions_to_check,
            'call_trees': self.call_trees,
            'project_id': project_audit.project_id,
            'project_path': project_audit.project_path,
            'project_audit': project_audit  # 🔧 添加完整的project_audit对象
        }
        
        # 初始化各种处理器，传递简化的context数据
        self.context_update_processor = ContextUpdateProcessor(self.context_data)
        self.analysis_processor = AnalysisProcessor(self.context_data)
        self.confirmation_processor = ConfirmationProcessor(self.analysis_processor)
    
    def check_function_vul(self, task_manager):
        """Execute vulnerability checking
        
        Main public API, maintaining full compatibility with the original interface
        """
        # Execute vulnerability confirmation
        return self.confirmation_processor.execute_vulnerability_confirmation(task_manager)
 