import json
import random
import csv
import sys
import os
import os.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List, Dict, Tuple
from openai_api.openai import extract_structured_json
from prompt_factory.core_prompt import CorePrompt


class BusinessFlowUtils:
    """业务流处理相关的工具函数（已删除mermaid/json相关逻辑）"""
    
    @staticmethod
    def match_functions_from_business_flows(business_flows: List[Dict], functions_to_check: List[Dict]) -> Dict[str, List[Dict]]:
        """根据业务流中的函数匹配functions_to_check中的具体函数
        
        Args:
            business_flows: 业务流列表
            functions_to_check: 项目中要检查的函数列表
            
        Returns:
            Dict[str, List[Dict]]: 匹配后的业务流字典
        """
        matched_flows = {}
        
        # 创建函数名到函数对象的映射，支持多种匹配模式
        function_mapping = {}
        for func in functions_to_check:
            func_name = func['name']
            
            # 完整函数名 (ContractName.functionName)
            function_mapping[func_name] = func
            
            # 纯函数名 (functionName)
            if '.' in func_name:
                pure_func_name = func_name.split('.')[-1]
                if pure_func_name not in function_mapping:
                    function_mapping[pure_func_name] = func
            
            # 合约名匹配 (contractName.functionName)
            contract_name = func.get('contract_name', '')
            if contract_name:
                alt_name = f"{contract_name}.{func_name.split('.')[-1]}"
                function_mapping[alt_name] = func
        
        # 匹配业务流到函数
        for business_flow in business_flows:
            flow_name = business_flow.get('name', f'Business Flow {len(matched_flows) + 1}')
            matched_functions = []
            
            for step in business_flow.get('steps', []):
                step_function = step.get('function', '')
                
                # 尝试多种匹配方式
                matched_func = None
                
                # 1. 直接匹配
                if step_function in function_mapping:
                    matched_func = function_mapping[step_function]
                
                # 2. 模糊匹配（部分匹配）
                if not matched_func:
                    for func_key, func_obj in function_mapping.items():
                        if step_function in func_key or func_key in step_function:
                            matched_func = func_obj
                            break
                
                if matched_func:
                    matched_functions.append(matched_func)
                    print(f"✅ 匹配成功: {step_function} -> {matched_func['name']}")
                else:
                    print(f"⚠️ 未找到匹配函数: {step_function}")
            
            if matched_functions:
                matched_flows[flow_name] = matched_functions
                print(f"   ✅ 业务流 '{flow_name}' 成功匹配 {len(matched_functions)} 个函数")
            else:
                print(f"   ⚠️ 业务流 '{flow_name}' 未匹配到任何函数")
        
        return matched_flows

    @staticmethod
    def identify_contexts(functions_to_check: List[Dict]) -> Dict:
        """
        为 functions_to_check 中的每个函数识别子调用和父调用，
        使用已经包含的调用关系信息。
        
        Returns:
            Dict: 包含每个函数的上游和下游调用关系
        """
        
        # 初始化调用关系映射
        calls = {function["name"]: {"sub_calls": set(), "parent_calls": set()} for function in functions_to_check}
        
        # 构建调用关系
        for function in functions_to_check:
            func_name = function["name"]
            
            # 从现有的calls字段获取调用信息
            if "calls" in function and function["calls"]:
                for called_func in function["calls"]:
                    # 避免自引用
                    if called_func != func_name:
                        calls[func_name]["sub_calls"].add(called_func)
                        # 如果被调用的函数在我们的列表中，添加父调用关系
                        for other_function in functions_to_check:
                            if other_function["name"] == called_func:
                                calls[called_func]["parent_calls"].add(func_name)
                                break
        
        # 转换set为list以便JSON序列化
        result = {}
        for func_name, relations in calls.items():
            result[func_name] = {
                "sub_calls": list(relations["sub_calls"]),
                "parent_calls": list(relations["parent_calls"])
            }
        
        return result

    @staticmethod 
    def extract_contexts_from_project_audit(project_audit):
        """从project_audit中提取上下文信息"""
        
        if not project_audit or not hasattr(project_audit, 'functions_to_check'):
            print("⚠️ project_audit无效或缺少functions_to_check")
            return {}
        
        contexts = {}
        
        # 遍历所有函数，建立调用关系
        for func in project_audit.functions_to_check:
            func_name = func['name']
            contexts[func_name] = {
                'callers': [],  # 调用此函数的函数
                'callees': []   # 此函数调用的函数
            }
        
        # 根据calls信息建立双向关系
        for func in project_audit.functions_to_check:
            func_name = func['name']
            calls = func.get('calls', [])
            
            for called_func_name in calls:
                # 寻找被调用的函数
                for other_func in project_audit.functions_to_check:
                    if other_func['name'] == called_func_name:
                        # func调用other_func，所以other_func的callers包含func
                        contexts[called_func_name]['callers'].append(func_name)
                        # func的callees包含other_func
                        contexts[func_name]['callees'].append(called_func_name)
                        break
        
        return contexts

    @staticmethod
    def get_cross_contract_code(project_audit, function_name: str, function_lists: List[str]) -> str:
        """
        获取跨合约代码
        
        Args:
            project_audit: 项目审计对象
            function_name: 当前函数名
            function_lists: 函数列表
            
        Returns:
            str: 跨合约代码
        """
        if not project_audit or not hasattr(project_audit, 'functions_to_check'):
            return ""
        
        cross_contract_code = []
        current_function = None
        
        # 找到当前函数
        for func in project_audit.functions_to_check:
            if func['name'].split('.')[-1] == function_name:
                current_function = func
                break
        
        if not current_function:
            return ""
        
        current_contract = current_function['contract_name']
        
        # 查找跨合约调用
        for other_func in project_audit.functions_to_check:
            if other_func['contract_name'] != current_contract:
                other_func_name = other_func['name'].split('.')[-1]
                
                # 检查当前函数是否调用了其他合约的函数
                if other_func_name in current_function['content']:
                    cross_contract_code.append(f"// From contract {other_func['contract_name']}:")
                    cross_contract_code.append(other_func['content'])
                    cross_contract_code.append("")
                
                # 检查其他合约的函数是否调用了当前函数
                if function_name in other_func['content']:
                    cross_contract_code.append(f"// Caller from contract {other_func['contract_name']}:")
                    cross_contract_code.append(other_func['content'])
                    cross_contract_code.append("")
        
        return "\n".join(cross_contract_code) 