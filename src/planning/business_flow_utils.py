import json
import re
import sys
import os.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List, Dict, Tuple
from openai_api.openai import common_ask_for_json
from prompt_factory.core_prompt import CorePrompt


class BusinessFlowUtils:
    """业务流处理相关的工具函数"""
    
    @staticmethod
    def ask_openai_for_business_flow(function_name: str, contract_code_without_comment: str) -> str:
        """询问OpenAI获取业务流"""
        prompt = CorePrompt.ask_openai_for_business_flow_prompt().format(function_name=function_name)
        question = f"""
        {contract_code_without_comment}
        \n
        {prompt}
        """
        return common_ask_for_json(question)
    
    @staticmethod
    def extract_and_concatenate_functions_content(function_lists: List[str], contract_info: Dict) -> str:
        """
        根据函数列表和合约信息提取函数内容并拼接成字符串
        
        :param function_lists: 函数名列表
        :param contract_info: 单个合约信息字典，包含其函数
        :return: 拼接所有函数内容的字符串
        """
        concatenated_content = ""
        
        # 从合约信息中获取函数列表
        functions = contract_info.get("functions", [])
        
        # 创建字典以便通过名称快速访问函数
        function_dict = {str(function["name"]).split(".")[1]: function for function in functions}
        
        # 遍历提供的函数列表中的每个函数名
        for function_name in function_lists:
            # 通过名称查找函数内容
            function_content = function_dict.get(function_name, {}).get("content")
            
            # 如果找到函数内容，则将其追加到拼接的内容字符串中
            if function_content is not None:
                concatenated_content += function_content + "\n"
        
        return concatenated_content.strip()
    
    @staticmethod
    def decode_business_flow_list_from_response(response: str) -> List[str]:
        """从响应中解码业务流列表"""
        # 正则表达式用于匹配形如 {xxxx:[]} 的结果
        pattern = r'({\s*\"[a-zA-Z0-9_]+\"\s*:\s*\[[^\]]*\]\s*})'
        
        # 使用正则表达式找到所有匹配项
        matches = re.findall(pattern, response)
        
        # 初始化一个集合用于去重
        unique_functions = set()
        
        # 遍历所有匹配项
        for match in matches:
            # 尝试将匹配的字符串转换为JSON对象
            try:
                json_obj = json.loads(match)
                # 遍历JSON对象中的所有键（即函数名）
                for key in json_obj:
                    # 将键（函数名）添加到集合中去重
                    unique_functions.add(key)
                    # 遍历对应的值（即函数列表），并将它们也添加到集合中去重
                    for function in json_obj[key]:
                        unique_functions.add(function)
            except json.JSONDecodeError:
                # 如果匹配的字符串不是有效的JSON格式，则忽略错误
                pass
        
        # 将集合转换为列表并返回
        return list(unique_functions)
    
    @staticmethod
    def search_business_flow(
        all_business_flow: Dict, 
        all_business_flow_line: Dict, 
        all_business_flow_context: Dict, 
        function_name: str, 
        contract_name: str
    ) -> Tuple[str, str]:
        """
        根据函数名和合约名搜索业务流代码
        
        :param all_business_flow: 包含所有业务流的字典
        :param function_name: 要搜索的函数名
        :param contract_name: 函数所在的合约名
        :return: 如果找到则返回业务流代码，否则返回表示不存在的消息
        """
        # 检查合约名是否存在于 all_business_flow 字典中
        if contract_name in all_business_flow:
            # 检查函数名是否存在于合约的嵌套字典中
            contract_flows = all_business_flow[contract_name]
            contract_flows_line = all_business_flow_line[contract_name]
            contract_flows_context = all_business_flow_context[contract_name]
            if function_name in contract_flows:
                # 返回函数的业务流代码
                return contract_flows[function_name], contract_flows_line[function_name]
            else:
                # 在合约的业务流中未找到函数名
                return "not found", ""
        else:
            # 在 all_business_flow 字典中未找到合约名
            return "not found", ""
    
    @staticmethod
    def identify_contexts(functions_to_check: List[Dict]) -> Dict:
        """
        为 functions_to_check 中的每个函数识别子调用和父调用，
        仅包括不在同一合约中的调用。
        返回一个字典，函数名作为键，其子调用和父调用作为值，
        包括子调用和父调用的内容。
        """
        contexts = {}
        calls = {function["name"]: {"sub_calls": set(), "parent_calls": set()} for function in functions_to_check}

        for function in functions_to_check:
            function_name = function["name"]
            function_content = function["content"]
            function_contract_name = function["contract_name"]

            for other_function in functions_to_check:
                other_function_name = other_function["name"]
                other_function_content = other_function["content"]
                other_function_contract_name = other_function["contract_name"]

                # 检查其他函数是否不在同一合约中
                if function_contract_name != other_function_contract_name:
                    if function_name.split(".")[1] in other_function_content:
                        calls[function_name]["parent_calls"].add((other_function_name, other_function_content))

                    if other_function_name.split(".")[1] in function_content:
                        calls[function_name]["sub_calls"].add((other_function_name, other_function_content))
        
        for function_name, call_data in calls.items():
            contexts[function_name] = {
                "sub_calls": [{"name": name, "content": content} for name, content in call_data["sub_calls"]],
                "parent_calls": [{"name": name, "content": content} for name, content in call_data["parent_calls"]]
            }

        return contexts 