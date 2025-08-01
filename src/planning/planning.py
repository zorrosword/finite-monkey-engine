#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from dao.task_mgr import ProjectTaskMgr
from .planning_processor import PlanningProcessor


class Planning:
    """规划处理器，负责协调各个规划组件"""
    
    def __init__(self, project_audit, taskmgr: ProjectTaskMgr):
        """
        初始化规划处理器
        
        Args:
            project_audit: TreeSitterProjectAudit实例，包含解析后的项目数据
            taskmgr: 项目任务管理器
        """
        self.project_audit = project_audit
        self.taskmgr = taskmgr
        
        # 初始化规划处理器，直接传递project_audit
        self.planning_processor = PlanningProcessor(project_audit, taskmgr)
    
    def initialize_rag_processor(self, lancedb_path, project_id):
        """初始化RAG处理器"""
        return self.planning_processor.initialize_rag_processor(lancedb_path, project_id)
    
    def get_business_flow_context(self, functions_to_check):
        """获取业务流上下文"""
        return self.planning_processor.get_business_flow_context(functions_to_check)
    
    def get_default_business_context(self, functions_to_check):
        """获取默认业务上下文"""
        return self.planning_processor.get_default_business_context(functions_to_check)
    
    def do_planning(self):
        """执行规划处理"""
        return self.planning_processor.do_planning()
    
    def generate_planning_files(self):
        """生成规划文件"""
        return self.planning_processor.generate_planning_files()
    
    def process_for_common_project_mode(self, max_depth: int = 5):
        """处理通用项目模式"""
        return self.planning_processor.process_for_common_project_mode(max_depth)
