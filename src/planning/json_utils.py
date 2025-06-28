import json
import re
from typing import List, Dict


class JsonUtils:
    """JSON处理相关的工具函数"""
    
    @staticmethod
    def extract_filtered_functions(json_string: str) -> List[str]:
        """
        从 JSON 字符串中提取函数名。对于包含句点的函数名和键，只包含最后一个句点后的子字符串。
        键作为返回列表的第一个元素，以相同的方式处理。

        :param json_string: JSON 对象的字符串表示。
        :return: 处理后的键后跟其对应的过滤后的函数名的列表。
        """
        # 清理 JSON 字符串
        json_string = json_string.strip()
        # 移除可能存在的 markdown 代码块标记
        json_string = json_string.replace('```json', '').replace('```', '')
        
        # 尝试找到第一个 { 和最后一个 } 之间的内容
        start_idx = json_string.find('{')
        end_idx = json_string.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_string = json_string[start_idx:end_idx + 1]
        
        try:
            # 加载 JSON 数据到 Python 字典
            data = json.loads(json_string)
            
            # 初始化结果列表
            result_list = []
            
            # 处理字典中的每个键值对
            for key, functions in data.items():
                # 处理键（与函数名相同的方式）
                key = key.split('.')[-1] if '.' in key else key
                result_list.append(key)
                
                # 如果 functions 是字符串，将其转换为单元素列表
                if isinstance(functions, str):
                    functions = [functions]
                
                # 处理函数列表
                if isinstance(functions, list):
                    for function in functions:
                        if isinstance(function, str):
                            # 处理可能包含句点的函数名
                            function_name = function.split('.')[-1] if '.' in function else function
                            result_list.append(function_name)
            
            # 通过转换为集合再转回列表来移除重复项
            return list(set(result_list))
            
        except json.JSONDecodeError as e:
            print(f"JSON 解析错误: {e}")
            return []
        except Exception as e:
            print(f"处理 JSON 时发生错误: {e}")
            return []
    
    @staticmethod
    def extract_results(text: str) -> List[Dict]:
        """提取文本中的结果"""
        if text is None:
            return []
        # 定义一个正则表达式来匹配包含关键字 "result" 的JSON对象
        regex = r'\{.*?\}'

        # 使用正则表达式查找所有匹配项
        matches = re.findall(regex, text)

        # 解析找到的每个匹配项
        json_objects = []
        for match in matches:
            try:
                json_obj = json.loads(match)
                json_objects.append(json_obj)
            except json.JSONDecodeError:
                pass  # 在这里可以处理JSON解析错误

        return json_objects
    
    @staticmethod
    def merge_and_sort_rulesets(high: List[Dict], medium: List[Dict]) -> List[Dict]:
        """根据 sim_score 合并两个规则集"""
        # 合并两个规则集
        combined_ruleset = high + medium
        # 根据 sim_score 按降序排序合并的规则集
        combined_ruleset.sort(key=lambda x: x['sim_score'], reverse=True)
        return combined_ruleset 