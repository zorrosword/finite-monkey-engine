import pandas as pd
from tqdm import tqdm
import json
from openai_api.openai import ask_claude, ask_deepseek, ask_o3_mini_json, common_ask_for_json,ask_claude_37
import concurrent.futures
from threading import Lock
from prompt_factory.core_prompt import CorePrompt

class ResProcessor:
    def __init__(self, df):
        self.df = df
        self.lock = Lock()
        self.grouping_workers = 4  # 归集处理的线程数
        self.merging_workers = 3   # 合并处理的线程数

    def process(self):
        self.df['flow_code_len'] = self.df['相对路径'].str.len()
        grouped = list(self.df.groupby('相对路径'))
        
        # 第一步：完成所有组的归集
        all_grouped_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_group = {executor.submit(self._collect_group, flow_code, group): flow_code 
                             for flow_code, group in grouped}
            
            with tqdm(total=len(grouped), desc="漏洞归集") as pbar:
                for future in concurrent.futures.as_completed(future_to_group):
                    result = future.result()
                    with self.lock:
                        all_grouped_results.append(result)
                        pbar.update(1)
        
        print("\nDebug - All vulnerability grouping completed, now starting description merging...")
        
        # 第二步：处理所有已归集的组的描述合并
        processed_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_merge = {executor.submit(self._process_merge_result, result): result 
                             for result in all_grouped_results}
            
            with tqdm(total=len(all_grouped_results), desc="合并描述") as pbar:
                for future in concurrent.futures.as_completed(future_to_merge):
                    result = future.result()
                    with self.lock:
                        if isinstance(result, list):
                            processed_results.extend(result)
                        else:
                            processed_results.append(result)
                        pbar.update(1)
        
        new_df = pd.DataFrame(processed_results)
        
        if 'flow_code_len' in new_df.columns:
            new_df = new_df.drop('flow_code_len', axis=1)
            
        original_columns = [col for col in self.df.columns if col != 'flow_code_len']
        new_df = new_df[original_columns]
        
        return new_df

    def _collect_group(self, flow_code, group):
        """仅执行归集操作"""
        if len(group) <= 1:
            return {'group': group.iloc[0], 'valid_groups': None}
        
        base_info = group.iloc[0].copy()
        id_list = [str(id_) for id_ in group['ID'].tolist()]
        
        try:
            valid_groups = self._collect_all_groups(group, base_info, id_list)
            return {
                'group': group,
                'base_info': base_info,
                'valid_groups': valid_groups,
                'id_list': id_list
            }
        except Exception as e:
            print(f"\nDebug - Error in collect_group: {str(e)}")
            return {
                'group': group,
                'base_info': base_info,
                'valid_groups': None,
                'id_list': id_list
            }

    def _process_merge_result(self, collect_result):
        """处理归集结果的描述合并"""
        if collect_result['valid_groups'] is None:
            if isinstance(collect_result['group'], pd.Series):
                return self._process_single_vulnerability(collect_result['group'])
            return self._create_fallback_result(
                self._get_vuln_descriptions(collect_result['group']),
                collect_result['id_list'],
                collect_result['base_info'],
                collect_result['group']
            )
        
        return self._merge_all_descriptions(
            collect_result['valid_groups'],
            collect_result['group'],
            collect_result['base_info']
        )

    def _process_single_vulnerability(self, row):
#         translate_prompt = f"""请对以下漏洞描述翻译，用中文输出，请不要包含任何特殊字符或格式符号：
# 原漏洞描述：
# {row['漏洞结果']}
# """
        translate_prompt = CorePrompt.translate_prompt().format(vul_res=row['漏洞结果'])
        
        translated_description = ask_claude(translate_prompt)
        # 清理特殊字符
        translated_description = self._clean_text_for_excel(translated_description)
        
        return {
            '漏洞结果': translated_description,
            'ID': row['ID'],
            '项目名称': row['项目名称'],
            '合同编号': row['合同编号'],
            'UUID': row['UUID'],
            '函数名称': row['函数名称'],
            '函数代码': row['函数代码'],
            '开始行': row['开始行'],
            '结束行': row['结束行'],
            '相对路径': row['相对路径'],
            '绝对路径': row['绝对路径'],
            '业务流程代码': row['业务流程代码'],
            '业务流程行': row['业务流程行'],
            '业务流程上下文': row['业务流程上下文'],
            '确认结果': row['确认结果'],
            '确认细节': row['确认细节']
        }

    def _clean_text_for_excel(self, text):
        """清理文本中的特殊字符，确保Excel兼容性"""
        if pd.isna(text):
            return ''
        
        # 移除或替换可能导致Excel问题的字符
        text = str(text).strip()
        # 替换常见的特殊字符
        replacements = {
            '\r': ' ',
            '\n': ' ',
            '\t': ' ',
            '\f': ' ',
            '\v': ' ',
            '\0': '',
            '\x00': '',
            '\u0000': '',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # 移除其他不可见字符
        text = ''.join(char for char in text if ord(char) >= 32 or char == ' ')
        
        return text

    def _merge_vulnerabilities(self, group):
        base_info = group.iloc[0].copy()
        id_list = [str(id_) for id_ in group['ID'].tolist()]
        
        print(f"\nDebug - Processing group with {len(id_list)} vulnerabilities")
        
        try:
            # 第一步：完成所有归集
            valid_groups = self._collect_all_groups(group, base_info, id_list)
            if not valid_groups:
                return self._create_fallback_result(self._get_vuln_descriptions(group), id_list, base_info, group)
            
            # 打印归集结果
            print("\nDebug - All grouping completed. Grouping results:")
            for i, group_ids in enumerate(valid_groups, 1):
                print(f"Group {i}: IDs = {group_ids}")
            
            # 第二步：对所有已归集的组进行描述合并
            return self._merge_all_descriptions(valid_groups, group, base_info)
            
        except Exception as e:
            print(f"\nDebug - Error in merge_vulnerabilities: {str(e)}")
            return self._create_fallback_result(self._get_vuln_descriptions(group), id_list, base_info, group)

    def _get_vuln_descriptions(self, group):
        """获取漏洞描述列表"""
        return "\n".join([
            f"ID:{str(row['ID'])}\n漏洞内容：{row['漏洞结果']}" 
            for _, row in group.iterrows()
        ])

    def _collect_all_groups(self, group, base_info, id_list):
        """收集所有归集组"""
        vuln_descriptions = self._get_vuln_descriptions(group)
#         group_prompt = f"""将以下漏洞进行归集分组，用中文输出，必须严格遵循以下要求：
# 1. 被归集的多个漏洞必须发生在同一个函数中
# 2. 可能存在一个函数有多种漏洞，这种情况下依然把它们归集到一起
# 3. 必须按照如下JSON格式输出，可能有多组ID：
# {{
#     "groups": [
#         {{
#             "grouped_ids": [ID1, ID2...]
#         }},
#         {{
#             "grouped_ids": [ID3, ID4...]
#         }}
#     ]
# }}

# 以下是需要归集的漏洞列表：
# {vuln_descriptions}
# """
        group_prompt = CorePrompt.group_prompt().format(vuln_descriptions=vuln_descriptions)
        print("\nDebug - Starting grouping process...")
        grouped_result = self._process_grouping(group_prompt)
        grouped_data = json.loads(grouped_result)
        
        if not isinstance(grouped_data, dict) or 'groups' not in grouped_data:
            if 'grouped_ids' in grouped_data:
                grouped_data = {'groups': [{'grouped_ids': grouped_data['grouped_ids']}]}
            else:
                raise ValueError("Missing 'groups' field in JSON")
        
        # 验证并收集所有有效的分组
        valid_groups = []
        for group_info in grouped_data['groups']:
            if not isinstance(group_info, dict) or 'grouped_ids' not in group_info:
                continue
            
            actual_ids = [str(id_) for id_ in group_info['grouped_ids'] if str(id_) in id_list]
            if actual_ids:
                valid_groups.append(actual_ids)
        
        # 对分组进行去重，保留最大集
        print("\nDebug - Original groups before deduplication:")
        for i, group_ids in enumerate(valid_groups, 1):
            print(f"Group {i}: IDs = {group_ids}")
            
        deduplicated_groups = self._deduplicate_groups(valid_groups)
        
        print("\nDebug - Groups after deduplication:")
        for i, group_ids in enumerate(deduplicated_groups, 1):
            print(f"Group {i}: IDs = {group_ids}")
            
        return deduplicated_groups

    def _deduplicate_groups(self, groups):
        """去重分组，保留包含相同元素的最大集合"""
        if not groups:
            return []
            
        # 将列表转换为集合，方便处理
        groups_sets = [set(group) for group in groups]
        
        # 按集合大小降序排序
        groups_sets.sort(key=len, reverse=True)
        
        # 存储最终的去重结果
        final_groups = []
        used_elements = set()
        
        for group_set in groups_sets:
            # 如果当前组与已使用的元素没有交集，则保留该组
            if not group_set.intersection(used_elements):
                final_groups.append(sorted(list(group_set), key=lambda x: int(x)))  # 转回有序列表
                used_elements.update(group_set)
        
        return final_groups

    def _merge_all_descriptions(self, valid_groups, group, base_info):
        """合并所有已归集组的描述"""
        print("\nDebug - Starting description merging process...")
        all_results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.merging_workers) as executor:
            future_to_ids = {
                executor.submit(self._merge_vulnerability_descriptions, group, actual_ids): actual_ids 
                for actual_ids in valid_groups
            }
            
            for future in concurrent.futures.as_completed(future_to_ids):
                actual_ids = future_to_ids[future]
                try:
                    merged_description = future.result()
                    result = {
                        '漏洞结果': merged_description,
                        'ID': ",".join(actual_ids),
                        '项目名称': base_info['项目名称'],
                        '合同编号': base_info['合同编号'],
                        'UUID': base_info['UUID'],
                        '函数名称': base_info['函数名称'],
                        '函数代码': base_info['函数代码'],
                        '开始行': min(group['开始行']),
                        '结束行': max(group['结束行']),
                        '相对路径': base_info['相对路径'],
                        '绝对路径': base_info['绝对路径'],
                        '业务流程代码': base_info['业务流程代码'],
                        '业务流程行': base_info['业务流程行'],
                        '业务流程上下文': base_info['业务流程上下文'],
                        '确认结果': base_info['确认结果'],
                        '确认细节': base_info['确认细节']
                    }
                    print(f"\nDebug - Merged description for IDs {actual_ids}")
                    all_results.append(result)
                except Exception as e:
                    print(f"\nDebug - Error merging description for IDs {actual_ids}: {str(e)}")
        
        return all_results[0] if len(all_results) == 1 else all_results

    def _retry_ask_model(self, prompt, max_retries=3, is_grouping=True):
        """重试机制封装"""
        for attempt in range(max_retries):
            try:
                print(f"\nDebug - Attempt {attempt + 1} of {max_retries}")
                # 根据操作类型选择不同的模型和处理方式
                if is_grouping:
                    response = common_ask_for_json(prompt)
                    # 只在归集时验证JSON
                    json_result = self._extract_json_from_text(response)
                    return json_result
                else:
                    # 合并描述时直接返回文本结果
                    return ask_claude_37(prompt)
            except Exception as e:
                print(f"Debug - Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:  # 最后一次尝试
                    raise
                continue

    def _process_grouping(self, group_prompt, max_retries=3):
        """使用多线程处理归集过程"""
        def _grouping_task():
            return self._retry_ask_model(group_prompt, is_grouping=True)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.grouping_workers) as executor:
            futures = [executor.submit(_grouping_task) for _ in range(max_retries)]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    return result
                except Exception as e:
                    print(f"Debug - Grouping attempt failed: {str(e)}")
                    continue
            
        raise ValueError("All grouping attempts failed")

    def _process_merging(self, grouped_data, group, id_list, base_info):
        """使用多线程处理合并描述过程"""
        all_results = []
        merge_tasks = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.merging_workers) as executor:
            for i, group_info in enumerate(grouped_data['groups']):
                if not isinstance(group_info, dict) or 'grouped_ids' not in group_info:
                    continue
                
                actual_ids = [str(id_) for id_ in group_info['grouped_ids'] if str(id_) in id_list]
                if not actual_ids:
                    continue
                
                merge_tasks.append(executor.submit(
                    self._process_single_merge,
                    group,
                    actual_ids,
                    base_info
                ))
            
            for future in concurrent.futures.as_completed(merge_tasks):
                try:
                    result = future.result()
                    if result:
                        with self.lock:
                            all_results.append(result)
                except Exception as e:
                    print(f"Debug - Merge task failed: {str(e)}")
        
        return all_results

    def _process_single_merge(self, group, actual_ids, base_info):
        """处理单个合并任务"""
        try:
            merged_description = self._merge_vulnerability_descriptions(group, actual_ids)
            return {
                '漏洞结果': merged_description,
                'ID': ",".join(actual_ids),
                '项目名称': base_info['项目名称'],
                '合同编号': base_info['合同编号'],
                'UUID': base_info['UUID'],
                '函数名称': base_info['函数名称'],
                '函数代码': base_info['函数代码'],
                '开始行': min(group['开始行']),
                '结束行': max(group['结束行']),
                '相对路径': base_info['相对路径'],
                '绝对路径': base_info['绝对路径'],
                '业务流程代码': base_info['业务流程代码'],
                '业务流程行': base_info['业务流程行'],
                '业务流程上下文': base_info['业务流程上下文'],
                '确认结果': base_info['确认结果'],
                '确认细节': base_info['确认细节']
            }
        except Exception as e:
            print(f"Debug - Error in single merge process: {str(e)}")
            return None

    def _create_fallback_result(self, vuln_descriptions, id_list, base_info, group):
        """创建回退结果"""
        return {
            '漏洞结果': f"合并失败，原始漏洞列表：\n{vuln_descriptions}",
            'ID': ",".join(id_list),
            '项目名称': base_info['项目名称'],
            '合同编号': base_info['合同编号'],
            'UUID': base_info['UUID'],
            '函数名称': base_info['函数名称'],
            '函数代码': base_info['函数代码'],
            '开始行': min(group['开始行']),
            '结束行': max(group['结束行']),
            '相对路径': base_info['相对路径'],
            '绝对路径': base_info['绝对路径'],
            '业务流程代码': base_info['业务流程代码'],
            '业务流程行': base_info['业务流程行'],
            '业务流程上下文': base_info['业务流程上下文'],
            '确认结果': base_info['确认结果'],
            '确认细节': base_info['确认细节']
        }

    def _extract_json_from_text(self, text):
        """从文本中提取JSON字符串，增加防御性编程措施"""
        print("\nDebug - Starting JSON extraction")
        print(f"Debug - Input text length: {len(text)}")
        
        try:
            # 首先尝试直接解析整个文本
            try:
                json.loads(text)
                return text
            except json.JSONDecodeError:
                pass
            
            # 查找JSON代码块标记
            json_markers = ['```json', '`json', '{']
            start_pos = -1
            
            for marker in json_markers:
                pos = text.find(marker)
                if pos != -1:
                    start_pos = pos + len(marker)
                    if marker != '{':
                        # 如果找到代码块标记，继续寻找实际的JSON开始位置
                        json_start = text.find('{', start_pos)
                        if json_start != -1:
                            start_pos = json_start
                    break
            
            if start_pos == -1:
                raise ValueError("No JSON object found in text")
            
            # 从找到的位置开始寻找匹配的大括号
            bracket_count = 0
            in_string = False
            escape_char = False
            end_pos = -1
            
            for i in range(start_pos, len(text)):
                char = text[i]
                
                if escape_char:
                    escape_char = False
                    continue
                    
                if char == '\\':
                    escape_char = True
                    continue
                    
                if char == '"' and not escape_char:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '{':
                        bracket_count += 1
                    elif char == '}':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_pos = i + 1
                            break
            
            if end_pos == -1 or bracket_count != 0:
                raise ValueError("No valid JSON object found (unmatched brackets)")
            
            # 提取JSON部分
            json_str = text[start_pos:end_pos].strip()
            
            # 验证是否为有效的JSON
            parsed_json = json.loads(json_str)
            
            # 验证JSON结构
            if not isinstance(parsed_json, dict) or 'groups' not in parsed_json:
                if 'grouped_ids' in parsed_json:
                    # 如果直接返回了grouped_ids，自动包装成正确的格式
                    return json.dumps({'groups': [{'grouped_ids': parsed_json['grouped_ids']}]})
                raise ValueError("Invalid JSON structure: missing required fields")
            
            return json_str
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Debug - Error extracting JSON: {str(e)}")
            print(f"Debug - Original text: {text}")
            raise ValueError(f"Failed to extract valid JSON: {str(e)}")

    def _merge_vulnerability_descriptions(self, group, merged_ids):
        """合并指定ID组的漏洞描述"""
        relevant_vulns = group[group['ID'].astype(str).isin(merged_ids)]
        vuln_details = "\n".join([
            f"ID:{str(row['ID'])}\n漏洞内容：{row['漏洞结果']}\n业务流程代码：{row['业务流程代码']}\n业务流程上下文：{row['业务流程上下文']}"
            for _, row in relevant_vulns.iterrows()
        ])
        
#         merge_desc_prompt = f"""请将以上同一函数中的多个漏洞描述合并成一段完整的描述，要求：
# 1. 合并后的描述要完整概括所有漏洞的所有细节，如果存在多个漏洞，一定要在一段话内分开描述，分点描述，详细描述
# 2. 保持描述的准确性和完整性，同时保持逻辑易理解，不要晦涩难懂
# 3. 描述中必须附带有代码或代码段辅助解释，代码或代码段必须和描述互有交错，其最终目的是为了保证描述易懂,不要给出大段代码段
# 4. 每个漏洞的描述必须清晰，完整，不能遗漏任何关键点或代码或代码段或变量
# 5. 不要包含任何特殊字符或格式符号
# 6. 用中文输出，用markdown格式

# 以下是需要合并的漏洞描述：
# {vuln_details}
# """
        merge_desc_prompt = CorePrompt.merge_desc_prompt().format(vuln_details=vuln_details)
        
        try:
            # 直接使用模型返回的文本结果
            merged_description = ask_deepseek(merge_desc_prompt)
            # 清理特殊字符
            return self._clean_text_for_excel(merged_description)
            
        except Exception as e:
            print(f"Debug - Error in merge descriptions: {str(e)}")
            return self._clean_text_for_excel(f"合并描述失败，原始漏洞描述：\n{vuln_details}")

    def _clean_text(self, text):
        if pd.isna(text):
            return ''
        return str(text).strip()