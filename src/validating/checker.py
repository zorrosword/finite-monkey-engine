from context import ContextFactory
from .processors import ContextUpdateProcessor, ConfirmationProcessor, AnalysisProcessor


class VulnerabilityChecker:
    """Vulnerability checker responsible for deep verification and confirmation of vulnerabilities
    
    Simplified version after refactoring, using layered architecture design:
    - Entry layer: VulnerabilityChecker (this class)
    - Processor layer: ContextUpdateProcessor, ConfirmationProcessor, AnalysisProcessor  
    - Utility layer: ContextFactory (unified interface)
    """
    
    def __init__(self, project_audit, lancedb, lance_table_name):
        self.project_audit = project_audit
        
        # Initialize unified context factory
        self.context_factory = ContextFactory(project_audit, lancedb, lance_table_name)
        
        # Initialize various processors
        self.context_update_processor = ContextUpdateProcessor(self.context_factory.context_manager)
        self.analysis_processor = AnalysisProcessor(self.context_factory.context_manager)
        self.confirmation_processor = ConfirmationProcessor(self.analysis_processor)
    
    def check_function_vul(self, task_manager):
        """Update business flow context and execute vulnerability checking
        
        Main public API, maintaining full compatibility with the original interface
        """
        # First update business flow context
        self.context_update_processor.update_business_flow_context(task_manager)
        
        # Then execute vulnerability confirmation
        return self.confirmation_processor.execute_vulnerability_confirmation(task_manager)
 