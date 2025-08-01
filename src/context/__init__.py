"""
Context Module - 上下文获取和管理模块

该模块负责管理智能合约审计过程中的上下文获取，包括：
- 上下文管理器 (context_manager)
- 调用树构造器 (使用Tree-sitter版本)
- RAG处理器 (rag_processor)
- 业务流处理器 (business_flow_processor)
- 函数工具 (function_utils)
- 上下文工厂 (context_factory)
"""

from .context_manager import ContextManager
from .rag_processor import RAGProcessor
from .business_flow_processor import BusinessFlowProcessor
from .function_utils import FunctionUtils
from .context_factory import ContextFactory

# 直接使用Tree-sitter版本的CallTreeBuilder
from tree_sitter_parsing import TreeSitterCallTreeBuilder as CallTreeBuilder

__all__ = [
    'ContextManager',
    'CallTreeBuilder',
    'RAGProcessor',
    'BusinessFlowProcessor',
    'FunctionUtils',
    'ContextFactory'
] 