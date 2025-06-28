import os
import sys
import os.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from checklist_pipeline.checklist_generator import ChecklistGenerator

# 导入新的处理器模块
from .business_flow_processor import BusinessFlowProcessor
from .planning_processor import PlanningProcessor

'''
根据每个function 的 functionality embbeding 匹配结果 
'''
class PlanningV2(object):
    def __init__(self, project, taskmgr) -> None:
        self.project = project
        self.taskmgr = taskmgr
        self.scan_list_for_larget_context = []
        self.enable_checklist = os.getenv("SCAN_MODE") == "CHECKLIST_PIPELINE"
        self.checklist_generator = ChecklistGenerator() if self.enable_checklist else None
        
        # 初始化处理器
        self.business_flow_processor = BusinessFlowProcessor(project)
        self.planning_processor = PlanningProcessor(project, taskmgr, self.checklist_generator)

    def get_all_business_flow(self, functions_to_check):
        """
        提取所有函数的业务流
        :param functions_to_check: 要检查的函数列表
        :return: 包含每个合约所有业务流的字典
        整体思路：按函数抽取业务流=>按同一个函数提取跨合约上下文并组合成完整的待扫描代码
        """
        return self.business_flow_processor.get_all_business_flow(functions_to_check)

    def do_planning(self):
        """执行规划的核心逻辑"""
        return self.planning_processor.do_planning()
