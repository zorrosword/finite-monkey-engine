import json
import os
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
    def extract_business_flows_from_mermaid(mermaid_content: str) -> List[Dict]:
        """从mermaid内容中提取业务流
        
        Args:
            mermaid_content: mermaid图的内容
            
        Returns:
            List[Dict]: 提取的业务流列表
        """
        prompt = f"""基于以上业务流程图，提取出业务流，以JSON格式输出，结构如下：
{{
"flows": [
{{
"name": "业务流1的自然语言描述",
"steps": ["文件1.函数", "文件2.函数", "文件3.函数"]
}},
{{
"name": "业务流2的自然语言描述", 
"steps": ["文件1.函数", "文件2.函数"]
}}
]
}}

请分析以下Mermaid业务流程图：

{mermaid_content}

要求：
1. 从图中识别所有完整的业务流程
2. 每个业务流应该包含一系列有序的步骤
3. 业务流之间可以有稍微的交叉，但**绝对不能**重复或高度重叠
4. 步骤格式必须是"文件名.函数名"或"合约名.函数名"，中间必须是"."
5. 确保步骤顺序反映实际的业务流程
6. 函数名应该与代码中的实际函数名匹配

请严格按照JSON格式输出，不要包含其他解释文字。"""
        
        try:
            print(f"[DEBUG] 调用AI分析Mermaid图，内容长度: {len(mermaid_content)}")
            response = common_ask_for_json(prompt)
            
            print(f"[DEBUG] AI响应长度: {len(response) if response else 0}")
            if response:
                print(f"[DEBUG] AI响应前100字符: {response[:100]}")
            else:
                print("[DEBUG] AI响应为空")
                return []
            
            # 尝试解析JSON
            flows_data = json.loads(response)
            flows = flows_data.get('flows', [])
            
            print(f"[DEBUG] 成功解析，提取到 {len(flows)} 个业务流")
            return flows
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析错误: {str(e)}")
            print(f"[DEBUG] 原始响应: {response[:500] if response else 'None'}")
            
            # 尝试手动提取JSON部分
            if response and "flows" in response:
                try:
                    # 查找JSON部分
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_content = response[json_start:json_end]
                        print(f"[DEBUG] 尝试提取JSON部分: {json_content[:100]}")
                        flows_data = json.loads(json_content)
                        flows = flows_data.get('flows', [])
                        print(f"[DEBUG] 手动提取成功，得到 {len(flows)} 个业务流")
                        return flows
                except:
                    pass
            
            return []
        except Exception as e:
            print(f"❌ 从Mermaid提取业务流失败: {str(e)}")
            print(f"[DEBUG] 异常详情: {type(e).__name__}")
            if response:
                print(f"[DEBUG] 响应内容: {response[:200]}")
            return []
    
    @staticmethod
    def clean_business_flows(flows: List[Dict]) -> List[Dict]:
        """清洗业务流数据，确保格式正确
        
        Args:
            flows: 原始业务流列表
            
        Returns:
            List[Dict]: 清洗后的业务流列表
        """
        import re
        from openai_api.openai import common_ask_for_json
        
        def clean_step(step: str) -> str:
            """清洗单个步骤，确保格式为 文件名.函数名"""
            # 移除路径，只保留文件名
            if '/' in step or '\\' in step:
                # 提取文件名部分
                parts = re.split(r'[/\\]', step)
                step = parts[-1]  # 取最后一部分作为文件名
            
            # 确保有且仅有一个点
            if '.' not in step:
                # 如果没有点，尝试智能分割
                # 例如: "myFunction" -> "unknown.myFunction"
                return f"unknown.{step}"
            elif step.count('.') > 1:
                # 如果有多个点，保留最后一个
                parts = step.split('.')
                filename = parts[0]
                funcname = '.'.join(parts[1:])
                # 移除文件扩展名
                if filename.endswith(('.sol', '.py', '.js', '.ts', '.rs', '.go', '.java', '.c', '.cpp')):
                    filename = re.sub(r'\.[^.]+$', '', filename)
                return f"{filename}.{funcname}"
            
            # 移除文件扩展名
            filename, funcname = step.split('.', 1)
            if filename.endswith(('.sol', '.py', '.js', '.ts', '.rs', '.go', '.java', '.c', '.cpp')):
                filename = re.sub(r'\.[^.]+$', '', filename)
            
            return f"{filename}.{funcname}"
        
        def validate_format(flows_data: List[Dict]) -> bool:
            """验证业务流格式是否正确"""
            pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*$')
            
            for flow in flows_data:
                if 'steps' not in flow:
                    return False
                for step in flow['steps']:
                    if not pattern.match(step):
                        return False
            return True
        
        try:
            # 初次清洗
            cleaned_flows = []
            for flow in flows:
                cleaned_flow = {
                    'name': flow.get('name', 'Unknown Flow'),
                    'steps': [clean_step(step) for step in flow.get('steps', [])]
                }
                cleaned_flows.append(cleaned_flow)
            
            # 验证格式
            max_retries = 3
            retry_count = 0
            
            while not validate_format(cleaned_flows) and retry_count < max_retries:
                retry_count += 1
                print(f"⚠️ 业务流格式验证失败，第 {retry_count} 次尝试修复...")
                
                # 使用AI进行格式修复
                repair_prompt = f"""请修复以下业务流数据的格式问题，确保每个step都严格符合"文件名.函数名"的格式：

要求：
1. 文件名和函数名之间必须用"."连接
2. 文件名不能包含路径，只能是单独的文件名（不带扩展名）
3. 文件名和函数名只能包含字母、数字和下划线，且必须以字母或下划线开头

当前数据：
{json.dumps(cleaned_flows, indent=2, ensure_ascii=False)}

请返回修复后的JSON数据，格式完全相同：
"""
                
                try:
                    response = common_ask_for_json(repair_prompt)
                    if response:
                        repaired_data = json.loads(response)
                        if isinstance(repaired_data, list):
                            cleaned_flows = repaired_data
                        elif isinstance(repaired_data, dict) and 'flows' in repaired_data:
                            cleaned_flows = repaired_data['flows']
                        else:
                            # print(f"❌ AI修复返回格式错误")
                            break
                    else:
                        print(f"❌ AI修复无响应")
                        break
                except Exception as e:
                    print(f"❌ AI修复失败: {str(e)}")
                    break
            
            # 最终验证
            if validate_format(cleaned_flows):
                print(f"✅ 业务流格式验证通过，共 {len(cleaned_flows)} 个业务流")
                return cleaned_flows
            else:
                print(f"⚠️ 返回清洗后的数据")
                # 强制最后一次格式修复
                final_cleaned = []
                for flow in cleaned_flows:
                    final_steps = []
                    for step in flow.get('steps', []):
                        # 强制格式化
                        clean_step_final = re.sub(r'[^a-zA-Z0-9_.]', '', str(step))
                        if '.' not in clean_step_final:
                            clean_step_final = f"unknown.{clean_step_final}"
                        elif clean_step_final.count('.') > 1:
                            parts = clean_step_final.split('.')
                            clean_step_final = f"{parts[0]}.{parts[-1]}"
                        final_steps.append(clean_step_final)
                    
                    final_cleaned.append({
                        'name': flow.get('name', 'Unknown Flow'),
                        'steps': final_steps
                    })
                
                return final_cleaned
                
        except Exception as e:
            print(f"❌ 清洗业务流数据失败: {str(e)}")
            return flows  # 返回原始数据
    
    @staticmethod
    def load_mermaid_files(mermaid_output_dir: str, project_id: str) -> List[str]:
        """加载项目的所有mermaid文件内容
        
        Args:
            mermaid_output_dir: mermaid文件输出目录
            project_id: 项目ID
            
        Returns:
            List[str]: 所有mermaid文件的内容列表
        """
        mermaid_contents = []
        
        if not mermaid_output_dir or not os.path.exists(mermaid_output_dir):
            print(f"❌ Mermaid输出目录不存在: {mermaid_output_dir}")
            return mermaid_contents
        
        # 查找所有.mmd文件
        for file_name in os.listdir(mermaid_output_dir):
            if file_name.endswith('.mmd') and project_id in file_name:
                file_path = os.path.join(mermaid_output_dir, file_name)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            mermaid_contents.append(content)
                            print(f"✅ 加载Mermaid文件: {file_name}")
                except Exception as e:
                    print(f"❌ 读取Mermaid文件失败 {file_name}: {str(e)}")
        
        return mermaid_contents
    
    @staticmethod
    def extract_all_business_flows_from_mermaid_files(mermaid_output_dir: str, project_id: str) -> List[Dict]:
        """从所有mermaid文件中提取业务流
        
        Args:
            mermaid_output_dir: mermaid文件输出目录 
            project_id: 项目ID
            
        Returns:
            List[Dict]: 所有提取的业务流列表
        """
        all_flows = []
        
        # 加载所有mermaid文件
        mermaid_contents = BusinessFlowUtils.load_mermaid_files(mermaid_output_dir, project_id)
        
        if not mermaid_contents:
            print("❌ 未找到有效的Mermaid文件")
            return all_flows
        
        print(f"🔍 开始从 {len(mermaid_contents)} 个Mermaid文件中提取业务流...")
        
        # 从每个mermaid文件中提取业务流
        for i, mermaid_content in enumerate(mermaid_contents, 1):
            print(f"📄 处理第 {i} 个Mermaid文件...")
            flows = BusinessFlowUtils.extract_business_flows_from_mermaid(mermaid_content)
            
            if flows:
                # 清洗业务流数据，确保格式正确
                print(f"🧹 清洗第 {i} 个文件的业务流数据...")
                cleaned_flows = BusinessFlowUtils.clean_business_flows(flows)
                all_flows.extend(cleaned_flows)
                print(f"✅ 从第 {i} 个文件提取并清洗到 {len(cleaned_flows)} 个业务流")
            else:
                print(f"⚠️ 第 {i} 个文件未提取到业务流")
        
        print(f"🎉 总共提取到 {len(all_flows)} 个业务流")
        return all_flows
    
    @staticmethod
    def match_functions_from_business_flows(business_flows: List[Dict], functions_to_check: List[Dict]) -> Dict[str, List[Dict]]:
        """根据业务流中的函数匹配functions_to_check中的具体函数
        
        Args:
            business_flows: 从mermaid提取的业务流列表
            functions_to_check: 项目中要检查的函数列表
            
        Returns:
            Dict[str, List[Dict]]: 匹配的业务流和对应的函数
        """
        matched_flows = {}
        
        # 创建函数查找索引：函数名 -> 函数对象列表
        function_name_index = {}
        contract_function_index = {}
        
        for func in functions_to_check:
            func_name = func['name']
            # 提取纯函数名（去掉合约前缀）
            if '.' in func_name:
                contract_name, pure_func_name = func_name.split('.', 1)
                
                # 按纯函数名索引
                if pure_func_name not in function_name_index:
                    function_name_index[pure_func_name] = []
                function_name_index[pure_func_name].append(func)
                
                # 按合约.函数名索引
                contract_func_key = f"{contract_name}.{pure_func_name}"
                if contract_func_key not in contract_function_index:
                    contract_function_index[contract_func_key] = []
                contract_function_index[contract_func_key].append(func)
                
                # 按完整文件路径.函数名索引
                file_name = os.path.basename(func['relative_file_path']).replace('.sol', '').replace('.py', '').replace('.js', '').replace('.ts', '')
                file_func_key = f"{file_name}.{pure_func_name}"
                if file_func_key not in contract_function_index:
                    contract_function_index[file_func_key] = []
                contract_function_index[file_func_key].append(func)
        
        print(f"🔍 开始匹配 {len(business_flows)} 个业务流中的函数...")
        
        # 处理每个业务流
        for flow in business_flows:
            flow_name = flow.get('name', 'Unknown Flow')
            steps = flow.get('steps', [])
            
            print(f"\n🔄 处理业务流: {flow_name} ({len(steps)} 个步骤)")
            
            matched_functions = []
            
            for step in steps:
                # 解析步骤：可能的格式包括 "文件.函数", "合约.函数"
                matched_func = None
                
                if '.' in step:
                    # 首先尝试精确匹配（合约.函数 或 文件.函数）
                    if step in contract_function_index:
                        candidates = contract_function_index[step]
                        if candidates:
                            matched_func = candidates[0]  # 取第一个匹配
                            print(f"  ✅ 精确匹配: {step} -> {matched_func['name']}")
                    
                    # 如果精确匹配失败，尝试只匹配函数名
                    if not matched_func:
                        _, func_name = step.split('.', 1)
                        if func_name in function_name_index:
                            candidates = function_name_index[func_name]
                            if candidates:
                                matched_func = candidates[0]  # 取第一个匹配
                                print(f"  ✅ 函数名匹配: {step} -> {matched_func['name']}")
                else:
                    # 只有函数名的情况
                    if step in function_name_index:
                        candidates = function_name_index[step]
                        if candidates:
                            matched_func = candidates[0]
                            print(f"  ✅ 纯函数名匹配: {step} -> {matched_func['name']}")
                
                if matched_func:
                    matched_functions.append(matched_func)
                else:
                    print(f"  ❌ 未找到匹配函数: {step}")
            
            if matched_functions:
                matched_flows[flow_name] = matched_functions
                print(f"✅ 业务流 '{flow_name}' 匹配到 {len(matched_functions)} 个函数")
            else:
                print(f"⚠️ 业务流 '{flow_name}' 未匹配到任何函数")
        
        print(f"\n🎉 成功匹配 {len(matched_flows)} 个业务流")
        return matched_flows
    
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