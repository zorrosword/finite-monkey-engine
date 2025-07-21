import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List, Dict, Tuple
from library.sgp.utilities.contract_extractor import extract_modifiers_from_code, extract_state_variables_from_code, group_functions_by_contract


class BusinessFlowProcessor:
    """业务流处理器，负责处理业务流相关的复杂逻辑"""
    
    def __init__(self, project):
        self.project = project
    
    def get_all_business_flow(self, functions_to_check: List[Dict]) -> Tuple[Dict, Dict, Dict]:
        """
        提取所有函数的业务流
        
        Args:
            functions_to_check: 要检查的函数列表
            
        Returns:
            Tuple[Dict, Dict, Dict]: (业务流字典, 业务流行信息字典, 业务流上下文字典)
        """
        grouped_functions = group_functions_by_contract(functions_to_check)
        # 延迟导入避免循环导入问题
        from planning.business_flow_utils import BusinessFlowUtils
        # 获取跨合约上下文（仅获取跨合约的上下文）
        cross_chain_contexts = BusinessFlowUtils.identify_contexts(functions_to_check)
        
        all_business_flow = {}
        all_business_flow_line = {}
        all_business_flow_context = {}
        
        print("grouped contract count:", len(grouped_functions))
        
        for contract_info in grouped_functions:
            self._process_contract_business_flows(
                contract_info, 
                all_business_flow, 
                all_business_flow_line, 
                all_business_flow_context,
                cross_chain_contexts
            )
        
        return all_business_flow, all_business_flow_line, all_business_flow_context
    
    def _process_contract_business_flows(
        self, 
        contract_info: Dict, 
        all_business_flow: Dict, 
        all_business_flow_line: Dict, 
        all_business_flow_context: Dict,
        cross_chain_contexts: Dict
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
        
        # 填充跨合约上下文信息
        for func in functions:
            func_name = func['name']
            if func_name in cross_chain_contexts:
                func_name_short = func_name.split(".")[-1]
                all_business_flow_context[contract_name][func_name_short] = cross_chain_contexts[func_name]

        # 根据语言获取可见性过滤器
        # visibility_filter = ConfigUtils.get_visibility_filter_by_language(functions)
        all_public_external_function_names = [
            function['name'].split(".")[1] for function in functions 
            if function.get('visibility') in ['public', 'external']  # 简化的可见性过滤
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
        # 延迟导入避免循环导入
        from planning.config_utils import ConfigUtils
        config = ConfigUtils.get_scan_configuration()
        threshold = config['threshold']  # 设置默认阈值
        
        if len(function_code) < threshold:
            print(f"Function code for {public_external_function_name} is too short for <{threshold}, skipping...")
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
        # ask_business_flow_code = BusinessFlowUtils.extract_and_concatenate_functions_content(
        #     function_lists, 
        #     contract_info
        # )
        # 简化的函数内容拼接
        ask_business_flow_code = self._extract_and_concatenate_functions_content(function_lists, contract_info)
        
        # 处理跨合约扩展代码
        config = {}  # 创建一个空配置字典
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
                # 调用真正的OpenAI API获取业务流 - 使用懒加载避免循环导入
                from planning.business_flow_utils import BusinessFlowUtils
                return BusinessFlowUtils.ask_openai_for_business_flow(function_name, contract_code)
            except Exception as e:
                print(f"获取业务流时出错: {str(e)}")
                return ""
    
    def _process_business_flow_response(self, business_flow_list: str, function_name: str) -> List[str]:
        """处理业务流响应"""
        if not business_flow_list:
            return []
        
        try:
            # function_lists = JsonUtils.extract_filtered_functions(business_flow_list)
            # 简化的JSON解析
            try:
                data = json.loads(business_flow_list)
                function_lists = list(data.keys()) if isinstance(data, dict) else []
            except:
                function_lists = []
            
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
    ) -> List[Dict]:
        """提取函数行信息"""
        line_info_list = []
        
        def get_function_structure(functions, function_name):
            for func in functions:
                if func['name'].split(".")[1] == function_name:
                    return {
                        'name': func['name'],
                        'start_line': func['start_line'],
                        'end_line': func['end_line'],
                        'relative_file_path': func['relative_file_path'],
                        'content': func['content']
                    }
            return None
        
        for func_name in function_lists:
            function_structure = get_function_structure(functions, func_name)
            if function_structure:
                line_info_list.append(function_structure)
        
        return line_info_list
    
    def _enhance_with_cross_contract_code(
        self,
        business_flow_code: str,
        function_name: str,
        function_lists: List[str],
        config: Dict
    ) -> str:
        """使用跨合约代码增强业务流"""
        # 如果没有开启跨合约扩展，直接返回原始代码
        if not config.get('switch_business_code_cross_contract_append', False):
            return business_flow_code
        
        # 获取跨合约扩展代码
        from planning.business_flow_utils import BusinessFlowUtils
        cross_contract_code = BusinessFlowUtils.get_cross_contract_code(
            self.project,
            function_name,
            function_lists
        )
        
        if cross_contract_code:
            # 拼接跨合约代码
            enhanced_code = business_flow_code + "\n\n// Cross-contract related code:\n" + cross_contract_code
            return enhanced_code
        
        return business_flow_code
    
    def _enhance_business_flow_code(self, business_flow_code: str, contract_info: Dict) -> str:
        """增强业务流代码"""
        enhanced_code = business_flow_code
        
        # 添加状态变量
        state_variables = extract_state_variables_from_code(contract_info['contract_code_without_comment'])
        if state_variables:
            state_vars_text = "\n".join(state_variables)
            enhanced_code = "// State Variables:\n" + state_vars_text + "\n\n" + enhanced_code
        
        # 添加修饰符
        modifiers = extract_modifiers_from_code(contract_info['contract_code_without_comment'])
        if modifiers:
            modifiers_text = "\n".join(modifiers)
            enhanced_code = enhanced_code + "\n\n// Modifiers:\n" + modifiers_text
        
        return enhanced_code
    
    def get_business_flow_context(self, contract_name: str, function_name: str) -> str:
        """获取业务流上下文"""
        # 从已处理的业务流中获取上下文
        # 这里可以根据需要实现具体的上下文获取逻辑
        return ""
    
    def extract_business_flow_functions(self, business_flow_code: str) -> List[str]:
        """从业务流代码中提取函数名列表"""
        # 实现函数名提取逻辑
        functions = []
        # 这里可以添加正则表达式或其他方法来提取函数名
        return functions
    
    def _extract_and_concatenate_functions_content(self, function_lists: List[str], contract_info: Dict) -> str:
        """提取并拼接函数内容"""
        if not function_lists:
            return ""
        
        functions = contract_info.get('functions', [])
        concatenated_content = []
        
        for function_name in function_lists:
            for func in functions:
                if func['name'].split('.')[-1] == function_name:
                    concatenated_content.append(func['content'])
                    break
        
        return '\n\n'.join(concatenated_content) 