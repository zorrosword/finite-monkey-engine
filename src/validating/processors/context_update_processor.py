from typing import List, Dict, Any
import os
from tqdm import tqdm


class ContextUpdateProcessor:
    """Business flow context update processor"""
    
    def __init__(self, context_data: Dict[str, Any]):
        """
        初始化上下文更新处理器
        
        Args:
            context_data: 包含项目数据的字典，包括functions, functions_to_check等
        """
        self.context_data = context_data
        self.functions = context_data.get('functions', [])
        self.functions_to_check = context_data.get('functions_to_check', [])
        self.call_trees = context_data.get('call_trees', [])
        self.project_id = context_data.get('project_id', '')
        self.project_path = context_data.get('project_path', '')
 