from context import ContextFactory
from .processors import ContextUpdateProcessor, ConfirmationProcessor, AnalysisProcessor


class VulnerabilityChecker:
    """漏洞检查器，负责深度验证和确认漏洞
    
    重构后的精简版本，使用分层架构设计：
    - 入口层：VulnerabilityChecker（本类）
    - 处理器层：ContextUpdateProcessor, ConfirmationProcessor, AnalysisProcessor  
    - 工具层：ContextFactory（统一接口）
    """
    
    def __init__(self, project_audit, lancedb, lance_table_name):
        self.project_audit = project_audit
        
        # 初始化统一的上下文工厂
        self.context_factory = ContextFactory(project_audit, lancedb, lance_table_name)
        
        # 初始化各种处理器
        self.context_update_processor = ContextUpdateProcessor(self.context_factory.context_manager)
        self.analysis_processor = AnalysisProcessor(self.context_factory.context_manager)
        self.confirmation_processor = ConfirmationProcessor(self.analysis_processor)
    
    def check_function_vul(self, task_manager):
        """更新业务流程上下文并执行漏洞检查
        
        主要的公共API，保持与原来的接口完全兼容
        """
        # 首先更新业务流程上下文
        self.context_update_processor.update_business_flow_context(task_manager)
        
        # 然后执行漏洞确认
        return self.confirmation_processor.execute_vulnerability_confirmation(task_manager)
 