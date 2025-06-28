import json
import os
import sys
import os.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List, Dict, Tuple
from library.sgp.utilities.contract_extractor import extract_modifiers_from_code, extract_state_variables_from_code, group_functions_by_contract
from .business_flow_utils import BusinessFlowUtils
from .json_utils import JsonUtils
from .function_utils import FunctionUtils
from .config_utils import ConfigUtils


class BusinessFlowProcessor:
    """业务流处理器，负责处理业务流相关的复杂逻辑"""
    
    def __init__(self, project):
        self.project = project
    
    def get_all_business_flow(self, functions_to_check: List[Dict]) -> Tuple[Dict, Dict, Dict]:
        """
        提取所有函数的业务流
        :param functions_to_check: 要检查的函数列表
        :return: 包含每个合约所有业务流的字典
        """
        grouped_functions = group_functions_by_contract(functions_to_check)
        contexts = BusinessFlowUtils.identify_contexts(functions_to_check)
        
        all_business_flow = {}
        all_business_flow_line = {}
        all_business_flow_context = {}
        
        print("grouped contract count:", len(grouped_functions))
        
        for contract_info in grouped_functions:
            self._process_contract_business_flows(
                contract_info, 
                all_business_flow, 
                all_business_flow_line, 
                all_business_flow_context
            )
        
        return all_business_flow, all_business_flow_line, all_business_flow_context
    
    def _process_contract_business_flows(
        self, 
        contract_info: Dict, 
        all_business_flow: Dict, 
        all_business_flow_line: Dict, 
        all_business_flow_context: Dict
    ):
        """处理单个合约的业务流"""
        print("———————————————————————processing contract_info:", contract_info['contract_name'], "—————————————————————————")
        
        contract_name = contract_info['contract_name']
        functions = contract_info['functions']
        contract_code_without_comments = contract_info['contract_code_without_comment']

        # 初始化合约名字典
        all_business_flow[contract_name] = {}
        all_business_flow_line[contract_name] = {}
        all_business_flow_context[contract_name] = {}

        # 根据语言获取可见性过滤器
        visibility_filter = ConfigUtils.get_visibility_filter_by_language(functions)
        all_public_external_function_names = [
            function['name'].split(".")[1] for function in functions 
            if visibility_filter(function)
        ]

        print("all_public_external_function_names count:", len(all_public_external_function_names))
        print("-----------------asking openai for business flow-----------------")
        
        for public_external_function_name in all_public_external_function_names:
            self._process_function_business_flow(
                public_external_function_name,
                contract_info,
                functions,
                contract_code_without_comments,
                all_public_external_function_names,
                all_business_flow[contract_name],
                all_business_flow_line[contract_name]
            )
    
    def _process_function_business_flow(
        self,
        public_external_function_name: str,
        contract_info: Dict,
        functions: List[Dict],
        contract_code_without_comments: str,
        all_public_external_function_names: List[str],
        contract_business_flow: Dict,
        contract_business_flow_line: Dict
    ):
        """处理单个函数的业务流"""
        print("***public_external_function_name***:", public_external_function_name)
        
        # 获取具体函数代码,判断长度，小于threshold则跳过
        function_code = self._get_function_code(functions, public_external_function_name)
        config = ConfigUtils.get_scan_configuration()
        
        if len(function_code) < config['threshold']:
            print(f"Function code for {public_external_function_name} is too short for <{config['threshold']}, skipping...")
            return
        
        # 获取业务流
        business_flow_list = self._get_business_flow_list(
            public_external_function_name,
            contract_info['contract_name'],
            contract_code_without_comments,
            all_public_external_function_names
        )
        
        if not business_flow_list:
            return

        # 处理业务流响应
        function_lists = self._process_business_flow_response(
            business_flow_list, 
            public_external_function_name
        )
        
        if not function_lists:
            return
        
        print("business_flow_list:", function_lists)
        
        # 提取行信息
        line_info_list = self._extract_function_line_info(function_lists, functions, contract_info['contract_name'])
        
        # 获取拼接后的业务流代码
        ask_business_flow_code = BusinessFlowUtils.extract_and_concatenate_functions_content(
            function_lists, 
            contract_info
        )
        
        # 处理跨合约扩展代码
        ask_business_flow_code = self._enhance_with_cross_contract_code(
            ask_business_flow_code,
            public_external_function_name,
            function_lists,
            config
        )
        
        # 增强业务流代码
        ask_business_flow_code = self._enhance_business_flow_code(
            ask_business_flow_code,
            contract_info
        )
        
        # 保存结果
        contract_business_flow[public_external_function_name] = ask_business_flow_code
        contract_business_flow_line[public_external_function_name] = line_info_list
    
    def _get_function_code(self, functions: List[Dict], function_name: str) -> str:
        """获取函数代码"""
        for func in functions:
            if func['name'].split(".")[1] == function_name:
                return func['content']
        return ""
    
    def _get_business_flow_list(
        self,
        function_name: str,
        contract_name: str,
        contract_code: str,
        all_function_names: List[str]
    ) -> str:
        """获取业务流列表"""
        if "_python" in str(contract_name) and len(all_function_names) == 1:
            key = all_function_names[0]
            data = {key: all_function_names}
            return json.dumps(data)
        else:
            try:
                return BusinessFlowUtils.ask_openai_for_business_flow(function_name, contract_code)
            except Exception as e:
                print(f"获取业务流时出错: {str(e)}")
                return ""
    
    def _process_business_flow_response(self, business_flow_list: str, function_name: str) -> List[str]:
        """处理业务流响应"""
        if not business_flow_list:
            return []
        
        try:
            function_lists = JsonUtils.extract_filtered_functions(business_flow_list)
            # 判断function_lists中是否包含function_name，如果包含，则去掉
            if function_name in function_lists and len(function_lists) > 1:
                function_lists.remove(function_name)
            return function_lists
        except Exception as e:
            print(f"处理业务流响应时出错: {str(e)}")
            return []
    
    def _extract_function_line_info(
        self, 
        function_lists: List[str], 
        functions: List[Dict], 
        contract_name: str
    ) -> List[Tuple[int, int]]:
        """提取函数行信息"""
        def get_function_structure(functions, function_name):
            for func in functions:
                if func['name'] == function_name:
                    return func
            return None
        
        line_info_list = []
        for function in function_lists:
            if str(function) == "-1" or isinstance(function, float):
                continue
            if contract_name is None:
                print("contract_name is None")
                continue
                
            function_name_to_search = contract_name + "." + function
            function_structure = get_function_structure(functions, function_name_to_search)
            if function_structure is not None:
                start_line = function_structure['start_line']
                end_line = function_structure['end_line']
                line_info_list.append((start_line, end_line))
        
        return line_info_list
    
    def _enhance_with_cross_contract_code(
        self,
        business_flow_code: str,
        function_name: str,
        function_lists: List[str],
        config: Dict
    ) -> str:
        """使用跨合约代码增强业务流"""
        if not config['cross_contract_scan']:
            return business_flow_code
        
        try:
            # 获取相关函数的【跨合约】扩展代码
            extended_flow_code_text, related_functions = FunctionUtils.extract_related_functions_by_level(
                self.project, 
                [function_name], 
                3
            )

            # 去重：移除function_lists中已有的函数
            filtered_related_functions = []
            for func_name, func_content in related_functions:
                if func_name not in function_lists:
                    filtered_related_functions.append(func_content)

            # 拼接去重后的函数内容到business_flow_code
            cross_contract_code = "\n".join(filtered_related_functions)
            if cross_contract_code:
                business_flow_code += "\n" + cross_contract_code
        except Exception as e:
            print(f"处理跨合约代码时出错: {str(e)}")
        
        return business_flow_code
    
    def _enhance_business_flow_code(self, business_flow_code: str, contract_info: Dict) -> str:
        """增强业务流代码，添加状态变量和修饰符"""
        try:
            contract_code = contract_info['contract_code_without_comment']
            state_vars = extract_state_variables_from_code(contract_code)
            state_vars_text = '\n'.join(state_vars) if state_vars else ''
            modifiers = extract_modifiers_from_code(contract_code)
            modifiers_text = '\n'.join(modifiers) if modifiers else ''
            return business_flow_code + "\n" + state_vars_text + "\n" + modifiers_text
        except Exception as e:
            print(f"增强业务流代码时出错: {str(e)}")
            return business_flow_code 