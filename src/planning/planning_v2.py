import json
import random
import time
from typing import List
import requests
from dao.entity import Project_Task
import os, sys
from tqdm import tqdm
import pickle
import csv
from library.sgp.utilities.contract_extractor import extract_modifiers_from_code, extract_state_variables_from_code
from openai_api.openai import *
from prompt_factory.core_prompt import CorePrompt
import re
from checklist_pipeline.checklist_generator import ChecklistGenerator
from prompt_factory.vul_prompt_common import VulPromptCommon

'''
根据每个function 的 functionality embbeding 匹配结果 
'''
class PlanningV2(object):
    def __init__(self, project,taskmgr) -> None:
        self.project = project
        self.taskmgr=taskmgr
        self.scan_list_for_larget_context=[]
        self.enable_checklist = os.getenv("SCAN_MODE") == "CHECKLIST_PIPELINE"
        self.checklist_generator = ChecklistGenerator() if self.enable_checklist else None

    
    def ask_openai_for_business_flow(self,function_name,contract_code_without_comment):
        # prompt=f"""
        # Based on the code above, analyze the business flows that start with the {function_name} function, consisting of multiple function calls. The analysis should adhere to the following requirements:
        # 1. only output the one sub-business flows, and must start from {function_name}.
        # 2. The output business flows should only involve the list of functions of the contract itself (ignoring calls to other contracts or interfaces, as well as events).
        # 3. After step-by-step analysis, output one result in JSON format, with the structure: {{"{function_name}":[function1,function2,function3....]}}
        # 4. The business flows must include all involved functions without any omissions

        # """
        prompt=CorePrompt.ask_openai_for_business_flow_prompt().format(function_name=function_name)
        question=f"""

        {contract_code_without_comment}
        \n
        {prompt}

        """
        return common_ask_for_json(question)
        
    def extract_filtered_functions(self, json_string):
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
    def extract_and_concatenate_functions_content(self,function_lists, contract_info):
        """
        Extracts the content of functions based on a given function list and contract info,
        and concatenates them into a single string.
        
        :param function_lists: A list of function names.
        :param contract_info: A dictionary representing a single contract's information, including its functions.
        :return: A string that concatenates all the function contents from the function list.
        """
        concatenated_content = ""

        # Get the list of functions from the contract info
        functions = contract_info.get("functions", [])

        # Create a dictionary for quick access to functions by name
        function_dict = {str(function["name"]).split(".")[1]: function for function in functions}

        # Loop through each function name in the provided function list
        for function_name in function_lists:
            # Find the function content by name
            function_content = function_dict.get(function_name, {}).get("content")
            
            # If function content is found, append it to the concatenated_content string
            if function_content is not None:
                concatenated_content += function_content + "\n"

        return concatenated_content.strip()
    def extract_results(self,text):
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
    # Function to merge two rulesets based on sim_score
    def merge_and_sort_rulesets(self,high, medium):
        # Combine the two rulesets
        # combined_ruleset = high # only high
        combined_ruleset = high + medium
        # Sort the combined ruleset based on sim_score in descending order
        combined_ruleset.sort(key=lambda x: x['sim_score'], reverse=True)
        return combined_ruleset
    def decode_business_flow_list_from_response(self, response):
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
    def identify_contexts(self, functions_to_check):
        """
        Identify sub-calls and parent-calls for each function in functions_to_check,
        only including calls that are not in the same contract.
        Returns a dictionary with function names as keys and their sub-calls and parent-calls as values,
        including the content of the sub-calls and parent-calls.
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

                # Check if the other function is not in the same contract
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


    def get_all_business_flow(self,functions_to_check):

        """
        Extracts all business flows for a list of functions.
        :param functions_to_check: A list of function names to extract business flows for.
        :return: A dictionary containing all business flows for each contract.
        The keys of the dictionary are the contract names, and the values are dictionaries containing the business flows for each public/external function.
        整体思路
        按函数抽取业务流=>按同一个函数提取跨合约上下文并组合成完整的待扫描代码
        """
        from library.sgp.utilities.contract_extractor import group_functions_by_contract
        from library.sgp.utilities.contract_extractor import check_function_if_public_or_external
        from library.sgp.utilities.contract_extractor import check_function_if_view_or_pure

        grouped_functions = group_functions_by_contract(functions_to_check)
        contexts = self.identify_contexts(functions_to_check)
        # 遍历grouped_functions，按每个合约代码进行业务流抽取
        all_business_flow = {}
        all_business_flow_line={}
        all_business_flow_context = {}
        print("grouped contract count:",len(grouped_functions))
        
        for contract_info in grouped_functions:
            print("———————————————————————processing contract_info:",contract_info['contract_name'],"—————————————————————————")
            contract_name = contract_info['contract_name']
            functions = contract_info['functions']
            contract_code_without_comments = contract_info['contract_code_without_comment']  # Assuming this is the correct key

            # 初始化合约名字典
            all_business_flow[contract_name] = {}
            all_business_flow_line[contract_name]={}
            all_business_flow_context[contract_name] = {}

            # New logic for determining function visibility
            language_patterns = {
                '.rust': lambda f: True,  # No visibility filter for Rust
                '.python': lambda f: True,  # No visibility filter for Python
                '.move': lambda f: f['visibility'] == 'public',
                '.fr': lambda f: f['visibility'] == 'public',
                '.java': lambda f: f['visibility'] in ['public', 'protected'],
                '.cairo': lambda f: f['visibility'] == 'public',
                '.tact': lambda f: f['visibility'] == 'public',
                '.func': lambda f: f['visibility'] == 'public',
                '.go': lambda f: True
            }

            def get_file_extension(funcs):
                for func in funcs:
                    file_path = func['relative_file_path']
                    for ext in language_patterns:
                        if file_path.endswith(ext):
                            return ext
                return None

            file_ext = get_file_extension(functions)
            visibility_filter = language_patterns.get(file_ext, lambda f: True)

            all_public_external_function_names = [
                function['name'].split(".")[1] for function in functions 
                if visibility_filter(function)
            ]

            print("all_public_external_function_names count:",len(all_public_external_function_names))
            # if len(self.scan_list_for_larget_context)>0 and contract_name not in self.scan_list_for_larget_context:
            #     continue

            # With the function name list and contract_code_without_comments, we can now query GPT for business flows
            # There are 6 steps:
            # 1. Check length, skip if less than threshold
            # 2. Get business flows
            # 3. Get line information
            # 4. Get cross-contract context info and combine into complete code for scanning
            # 5. Save results to all_business_flow and all_business_flow_line
            print("-----------------asking openai for business flow-----------------")
            for public_external_function_name in all_public_external_function_names:
                
                print("***public_external_function_name***:",public_external_function_name)
                
                # 获取具体函数代码,判断长度，小于threshold则跳过
                function_code = ""
                for func in functions:
                    if func['name'].split(".")[1] == public_external_function_name:
                        function_code = func['content']
                        break
                threshold=int(os.getenv("THRESHOLD_OF_PLANNING",200))
                if len(function_code)<threshold:
                    print(f"Function code for {public_external_function_name} is too short for <{threshold}, skipping...")
                    continue
                
                #获取业务流
                if "_python" in str(contract_name) and len(all_public_external_function_names)==1:
                    key = all_public_external_function_names[0]
                    data = {key: all_public_external_function_names}
                    business_flow_list = json.dumps(data)
                else:
                    try:
                        business_flow_list = self.ask_openai_for_business_flow(public_external_function_name, contract_code_without_comments)
                    except Exception as e:
                        business_flow_list=[]
                if (not business_flow_list) or (len(business_flow_list)==0):
                    continue

                # 返回一个list，这个list中包含着多条从public_external_function_name开始的业务流函数名
                try:
                    function_lists = self.extract_filtered_functions(business_flow_list)
                    # 判断function_lists中是否包含public_external_function_name，如果包含，则去掉
                    if public_external_function_name in function_lists and len(function_lists)>1:
                        function_lists.remove(public_external_function_name)
                except Exception as e:
                    print(e)  
                print("business_flow_list:",function_lists)
                
                # 从functions_to_check中提取start_line和end_line行数
                # 然后将start_line和end_line行数对应的代码提取出来，放入all_business_flow_line
                def get_function_structure(functions, function_name):
                    for func in functions:
                        if func['name'] == function_name:
                            return func
                    return None
                line_info_list = []
                for function in function_lists:
                    if str(function)=="-1":
                        continue
                    if isinstance(function, float):
                        continue
                    if contract_name is None:
                        print("contract_name is None")
                    function_name_to_search=contract_name+"."+function
                    function_structure=get_function_structure(functions, function_name_to_search)
                    if function_structure is not None:
                        start_line=function_structure['start_line']
                        end_line=function_structure['end_line']
                        line_info_list.append((start_line, end_line))

                # 获取拼接后的业务流代码
                ask_business_flow_code = self.extract_and_concatenate_functions_content(function_lists, contract_info)
                related_functions=[]
                if os.getenv("CROSS_CONTRACT_SCAN")=="True":
                    # 获取相关函数的【跨合约】扩展代码
                    # 只要入口函数的，否则对应代码会太长，效果变差
                    extended_flow_code_text, related_functions = self.extract_related_functions_by_level([public_external_function_name], 1)

                    # 去重：移除function_lists中已有的函数
                    filtered_related_functions = []
                    for func_name, func_content in related_functions:
                        if func_name not in function_lists:
                            filtered_related_functions.append(func_content)

                    # 拼接去重后的函数内容到ask_business_flow_code
                    cross_contract_code = "\n".join(filtered_related_functions)
                    if cross_contract_code:
                        ask_business_flow_code += "\n" + cross_contract_code


                # 在 contexts 中获取扩展后的业务流内容，即本合约的上下文内容，仅用于误报确认
                # extended_flow_code = ""
                # for function in function_lists:
                #     # 获取每个函数的上下文信息
                #     context = contexts.get(contract_name + "." + function, {})
                #     # 获取父调用和子调用
                #     parent_calls = context.get("parent_calls", [])
                #     sub_calls = context.get("sub_calls", [])
                #     # 拼接所有调用的代码内容
                #     for call in parent_calls + sub_calls:
                #         extended_flow_code += call["content"] + "\n"

                # # 保存扩展后的业务流上下文
                # all_business_flow_context[contract_name][public_external_function_name] = extended_flow_code.strip()

                # 修复 新增合约state var的提取
                contract_code=contract_info['contract_code_without_comment']
                state_vars=extract_state_variables_from_code(contract_code)
                state_vars_text = '\n'.join(state_vars) if state_vars else ''
                modifiers=extract_modifiers_from_code(contract_code)
                modifiers_text = '\n'.join(modifiers) if modifiers else ''
                ask_business_flow_code += "\n" + state_vars_text + "\n" + modifiers_text

                # 将结果存储为键值对
                all_business_flow[contract_name][public_external_function_name] = ask_business_flow_code
                all_business_flow_line[contract_name][public_external_function_name] = line_info_list
        return all_business_flow,all_business_flow_line,all_business_flow_context    
        # 此时 all_business_flow 为一个字典，包含了每个合约及其对应的业务流
    
    def search_business_flow(self,all_business_flow, all_business_flow_line,all_business_flow_context, function_name, contract_name):
        """
        Search for the business flow code based on a function name and contract name.

        :param all_business_flow: The dictionary containing all business flows.
        :param function_name: The name of the function to search for.
        :param contract_name: The name of the contract where the function is located.
        :return: The business flow code if found, or a message indicating it doesn't exist.
        """
        # Check if the contract_name exists in the all_business_flow dictionary
        if contract_name in all_business_flow:
            # Check if the function_name exists within the nested dictionary for the contract
            contract_flows = all_business_flow[contract_name]
            contract_flows_line=all_business_flow_line[contract_name]
            contract_flows_context=all_business_flow_context[contract_name]
            if function_name in contract_flows:
                # Return the business flow code for the function
                return contract_flows[function_name],contract_flows_line[function_name]
            else:
                # Function name not found within the contract's business flows
                return "not found",""
        else:
            # Contract name not found in the all_business_flow dictionary
            return "not found",""
    def should_exclude_in_planning(self, relative_file_path):
        """
        判断一个文件路径是否应该在planning过程中被排除
        
        Args:
            relative_file_path: 相对文件路径
            
        Returns:
            bool: 如果应该排除返回True，否则返回False
        """
        try:
            # 读取datasets.json文件
            datasets_path = "src/dataset/agent-v1-c4/datasets.json"
            if not os.path.exists(datasets_path):
                print(f"数据集配置文件不存在: {datasets_path}")
                return False
                
            with open(datasets_path, 'r', encoding='utf-8') as f:
                datasets = json.load(f)
                
            # 在datasets中查找与project_id匹配的配置
            project_id = self.project.project_id
            if project_id not in datasets:
                return False
                
            project_config = datasets[project_id]
            
            # 检查是否开启了exclude_in_planning选项
            exclude_in_planning = project_config.get('exclude_in_planning', 'false')
            if isinstance(exclude_in_planning, str):
                exclude_in_planning = exclude_in_planning.lower() == 'true'
            if not exclude_in_planning:
                return False
                
            # 检查文件路径是否包含任何排除目录 
            # 注意这里配置是 exclude_directory (单数)
            exclude_directories = project_config.get('exclude_directory', [])
            for directory in exclude_directories:
                if directory in relative_file_path:
                    print(f"排除目录 '{directory}' 匹配到文件: {relative_file_path}")
                    return True
                    
            return False
        except Exception as e:
            print(f"检查排除设置时出错: {str(e)}")
            return False
    def do_planning(self):
        tasks = []
        print("Begin do planning...")
        switch_function_code=eval(os.environ.get('SWITCH_FUNCTION_CODE','False'))
        switch_business_code=eval(os.environ.get('SWITCH_BUSINESS_CODE','True'))
        tasks = self.taskmgr.get_task_list_by_id(self.project.project_id)
        if len(tasks) > 0:
            return 

        # 获取扫描模式
        scan_mode = os.getenv('SCAN_MODE', '')
        
        # 获取所有checklist的数量
        total_checklist_count = 0
        if scan_mode == "COMMON_PROJECT_FINE_GRAINED":
            vul_checklists = VulPromptCommon.vul_prompt_common_new()
            total_checklist_count = len(vul_checklists)
        
        # 获取基础循环次数
        base_iteration_count = int(os.environ.get('BUSINESS_FLOW_COUNT', 1))
        
        # 计算实际循环次数
        actual_iteration_count = base_iteration_count * total_checklist_count if scan_mode == "COMMON_PROJECT_FINE_GRAINED" else base_iteration_count

        # filter all "test" function
        for function in self.project.functions_to_check:
            name=function['name']
            if "test" in name:
                self.project.functions_to_check.remove(function)
        
        if switch_business_code:
            all_business_flow,all_business_flow_line,all_business_flow_context=self.get_all_business_flow(self.project.functions_to_check)                    
        
        # Process each function with optimized threshold
        for function in tqdm(self.project.functions_to_check, desc="Finding project rules"):
            
            
            name = function['name']
            content = function['content']
            contract_code = function['contract_code']
            threshold=int(os.getenv("THRESHOLD_OF_PLANNING",200))
            if len(content)<threshold:
                print(f"Function code for {name} is too short for <{threshold}, skipping...")
                continue
            # Exclude planning process for configured directories, focus on logical business contracts
            # Check if this function should be excluded
            if self.should_exclude_in_planning(function['relative_file_path']):
                print(f"Excluding function {name} in planning process based on configuration")
                continue
            contract_name = function['contract_name']
            # if len(self.scan_list_for_larget_context)>0 and contract_name not in self.scan_list_for_larget_context:
            #     continue
            task_count = 0
            print(f"————————Processing function: {name}————————")
            checklist = ""    
            if switch_business_code:
                business_flow_code,line_info_list=self.search_business_flow(all_business_flow, all_business_flow_line,all_business_flow_context, name.split(".")[1], contract_name)
                print(f"[DEBUG] 获取到的业务流代码长度: {len(business_flow_code) if business_flow_code else 0}")
                business_type_str=""
                if self.enable_checklist:
                    print(f"\n📋 为业务流程生成检查清单...")
                    # 使用业务流程代码 + 原始函数代码
                    code_for_checklist = f"{business_flow_code}\n{content}"
                    business_description,checklist = self.checklist_generator.generate_checklist(code_for_checklist)
                    # Write checklist to a CSV file
                    csv_file_path = "checklist_business_code.csv"
                    # Open the file in append mode to continuously write to it
                    with open(csv_file_path, mode='a', newline='', encoding='utf-8') as csv_file:
                        csv_writer = csv.writer(csv_file)
                        # If the file is empty, write the headers
                        if csv_file.tell() == 0:
                            csv_writer.writerow(["contract_name", "business_flow_code", "content", "business_description", "checklist"])
                        # Write data
                        csv_writer.writerow([contract_name, business_flow_code, content, business_description, checklist])

                    print(f"✅ Checklist written to {csv_file_path}")
                    print("✅ 检查清单生成完成")
                
                
                    core_prompt = CorePrompt()  # 创建实例
                    type_check_prompt = core_prompt.type_check_prompt()  # 正确调用实例方法
                        
                    try:
                        # 使用format方法而不是.format()
                        formatted_prompt = type_check_prompt.format(business_flow_code+"\n"+content)
                        type_response = common_ask_for_json(formatted_prompt)
                        print(f"[DEBUG] Claude返回的响应: {type_response}")
                        
                        cleaned_response = type_response    
                        print(f"[DEBUG] 清理后的响应: {cleaned_response}")
                        
                        type_data = json.loads(cleaned_response)
                        business_type = type_data.get('business_types', ['other'])
                        print(f"[DEBUG] 解析出的业务类型: {business_type}")
                        
                        # 防御性逻辑：确保business_type是列表类型
                        if not isinstance(business_type, list):
                            business_type = [str(business_type)]
                        
                        # 处理 other 的情况
                        if 'other' in business_type and len(business_type) > 1:
                            business_type.remove('other')
                            
                        # 确保列表不为空
                        if not business_type:
                            business_type = ['other']
                            
                        business_type_str = ','.join(str(bt) for bt in business_type)
                        print(f"[DEBUG] 最终的业务类型字符串: {business_type_str}")
                        
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] JSON解析失败: {str(e)}")
                        print(f"[ERROR] 原始响应: {type_response}")
                        business_type = ['other']
                        business_type_str = 'other'
                    except Exception as e:
                        print(f"[ERROR] 处理业务类型时发生错误: {str(e)}")
                        business_type = ['other']
                        business_type_str = 'other'

                if business_flow_code != "not found":
                    for i in range(actual_iteration_count):  # 使用新的循环次数
                        task = Project_Task(
                            project_id=self.project.project_id,
                            name=name,
                            content=content,
                            keyword=str(random.random()),
                            business_type='',
                            sub_business_type='',
                            function_type='',
                            rule='',
                            result='',
                            result_gpt4='',
                            score='',
                            category='',
                            contract_code=contract_code,
                            risklevel='',
                            similarity_with_rule='',
                            description=checklist,
                            start_line=function['start_line'],
                            end_line=function['end_line'],
                            relative_file_path=function['relative_file_path'],
                            absolute_file_path=function['absolute_file_path'],
                            recommendation=business_type_str,  # 保存转换后的字符串
                            title='',
                            business_flow_code=str(business_flow_code),
                            business_flow_lines=line_info_list,
                            business_flow_context='',
                            if_business_flow_scan=1  # Indicating scanned using business flow code
                        )
                        self.taskmgr.add_task_in_one(task)
                        task_count += 1
            
            if switch_function_code:
                if self.enable_checklist:
                    print(f"\n📋 为函数代码生成检查清单...")
                    # 仅使用函数代码
                    business_description, checklist = self.checklist_generator.generate_checklist(content)
                    # Write checklist to a CSV file
                    csv_file_path = "checklist_function_code.csv"
                    # Open the file in append mode to continuously write to it
                    with open(csv_file_path, mode='a', newline='', encoding='utf-8') as csv_file:
                        csv_writer = csv.writer(csv_file)
                        # If the file is empty, write the headers
                        if csv_file.tell() == 0:
                            csv_writer.writerow(["contract_name", "business_flow_code", "content", "business_description", "checklist"])
                        # Write data
                        csv_writer.writerow([contract_name, "", content, business_description, checklist])
                    print(f"✅ Checklist written to {csv_file_path}")
                    print("✅ 检查清单生成完成")
                for i in range(actual_iteration_count):  # 使用新的循环次数
                    task = Project_Task(
                        project_id=self.project.project_id,
                        name=name,
                        content=content,
                        keyword=str(random.random()),
                        business_type='',
                        sub_business_type='',
                        function_type='',
                        rule='',
                        result='',
                        result_gpt4='',
                        score='',
                        category='',
                        contract_code=contract_code,
                        risklevel='',
                        similarity_with_rule='',
                        description=checklist,
                        start_line=function['start_line'],
                        end_line=function['end_line'],
                        relative_file_path=function['relative_file_path'],
                        absolute_file_path=function['absolute_file_path'],
                        recommendation='',
                        title='',
                        business_flow_code='',
                        business_flow_lines='',
                        business_flow_context='',
                        if_business_flow_scan=0  # Indicating scanned using function code
                    )
                    self.taskmgr.add_task_in_one(task)
                    task_count += 1

            
        # return tasks    




    def extract_related_functions_by_level(self, function_names: List[str], level: int) -> tuple[str, List[tuple[str, str]]]:
        """
        从call_trees中提取指定函数相关的上下游函数信息并扁平化处理
        
        Args:
            function_names: 要分析的函数名列表
            level: 要分析的层级深度
            
        Returns:
            tuple: (拼接后的函数内容文本, [(函数名, 函数内容), ...])
        """
        def get_functions_from_tree(tree, current_level=0, max_level=level, collected_funcs=None, level_stats=None):
            if collected_funcs is None:
                collected_funcs = []
            if level_stats is None:
                level_stats = {}
            
            if not tree or current_level > max_level:
                return collected_funcs, level_stats
                
            if tree['function_data']:
                collected_funcs.append(tree['function_data'])
                level_stats[current_level] = level_stats.get(current_level, 0) + 1
                
            if current_level < max_level:
                for child in tree['children']:
                    get_functions_from_tree(child, current_level + 1, max_level, collected_funcs, level_stats)
                    
            return collected_funcs, level_stats

        all_related_functions = []
        statistics = {
            'total_layers': level,
            'upstream_stats': {},
            'downstream_stats': {}
        }
        
        seen_functions = set()  
        unique_functions = []   
        
        for func_name in function_names:
            for tree_data in self.project.call_trees:
                if tree_data['function'] == func_name:
                    if tree_data['upstream_tree']:
                        upstream_funcs, upstream_stats = get_functions_from_tree(tree_data['upstream_tree'])
                        all_related_functions.extend(upstream_funcs)
                        for level, count in upstream_stats.items():
                            statistics['upstream_stats'][level] = statistics['upstream_stats'].get(level, 0) + count
                            
                    if tree_data['downstream_tree']:
                        downstream_funcs, downstream_stats = get_functions_from_tree(tree_data['downstream_tree'])
                        all_related_functions.extend(downstream_funcs)
                        for level, count in downstream_stats.items():
                            statistics['downstream_stats'][level] = statistics['downstream_stats'].get(level, 0) + count
                        
                    for func in self.project.functions_to_check:
                        if func['name'].split('.')[-1] == func_name:
                            all_related_functions.append(func)
                            break
                            
                    break
        
        # 增强的去重处理，同时保存函数名和内容
        function_name_content_pairs = []
        for func in all_related_functions:
            func_identifier = f"{func['name']}_{hash(func['content'])}"
            if func_identifier not in seen_functions:
                seen_functions.add(func_identifier)
                unique_functions.append(func)
                # 保存函数名(只取最后一部分)和内容
                function_name_content_pairs.append((func['name'].split('.')[-1], func['content']))
        
        # 拼接所有函数内容
        combined_text_parts = []
        for func in unique_functions:
            state_vars = None
            for tree_data in self.project.call_trees:
                if tree_data['function'] == func['name'].split('.')[-1]:
                    state_vars = tree_data.get('state_variables', '')
                    break
            
            function_text = []
            if state_vars:
                function_text.append("// Contract State Variables:")
                function_text.append(state_vars)
                function_text.append("\n// Function Implementation:")
            function_text.append(func['content'])
            
            combined_text_parts.append('\n'.join(function_text))
        
        combined_text = '\n\n'.join(combined_text_parts)
        
        # 打印统计信息
        print(f"\nFunction Call Tree Statistics:")
        print(f"Total Layers Analyzed: {level}")
        print("\nUpstream Statistics:")
        for layer, count in statistics['upstream_stats'].items():
            print(f"Layer {layer}: {count} functions")
        print("\nDownstream Statistics:")
        for layer, count in statistics['downstream_stats'].items():
            print(f"Layer {layer}: {count} functions")
        print(f"\nTotal Unique Functions: {len(unique_functions)}")
        
        return combined_text, function_name_content_pairs
