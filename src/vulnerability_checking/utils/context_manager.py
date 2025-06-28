import os
import json
import re
from typing import List, Dict

from prompt_factory.core_prompt import CorePrompt
from openai_api.openai import common_get_embedding, ask_claude, ask_grok3_deepsearch


class ContextManager:
    """上下文管理器，负责获取和管理分析所需的额外上下文信息"""
    
    def __init__(self, project_audit, lancedb, lance_table_name):
        self.project_audit = project_audit
        self.lancedb = lancedb
        self.lance_table_name = lance_table_name
    
    def get_related_functions(self, query: str, k: int = 3) -> List[Dict]:
        """通过语义搜索获取相关函数"""
        query_embedding = common_get_embedding(query)
        table = self.lancedb.open_table(self.lance_table_name)
        return table.search(query_embedding).limit(k).to_list()
    
    def extract_required_info(self, claude_response: str) -> List[str]:
        """从Claude的响应中提取需要进一步调查的信息"""
        prompt = CorePrompt.extract_required_info_prompt()
        
        extraction_result = ask_claude(prompt.format(response=claude_response))
        if not extraction_result or extraction_result.isspace():
            return []
        
        # 如果响应包含否定短语，返回空列表
        if any(phrase in extraction_result.lower() for phrase in ["no need", "not needed", "no additional", "no more"]):
            return []
        
        return [extraction_result]
    
    def get_additional_context(self, query_contents: List[str]) -> str:
        """获取额外的上下文信息"""
        if not query_contents:
            print("❌ 没有查询内容，无法获取额外上下文")
            return ""
        
        print(f"🔍 正在查询 {len(query_contents)} 条相关信息...")
        related_functions = []
        for query in query_contents:
            results = self.get_related_functions(query, k=10)
            if results:
                print(f"✅ 找到 {len(results)} 个相关函数")
                related_functions.extend(results)
            else:
                print("⚠️ 未找到相关函数")
        
        if related_functions:
            function_names = [func['name'].split('.')[-1] for func in related_functions]
            print(f"📑 正在提取 {len(function_names)} 个函数的上下文...")
            return self.extract_related_functions_by_level(function_names, 3)
        
        print("❌ 未找到任何相关函数")
        return ""
    
    def extract_related_functions_by_level(self, function_names: List[str], level: int) -> str:
        """
        从call_trees中提取指定函数相关的上下游函数信息并扁平化处理
        
        Args:
            function_names: 要分析的函数名列表
            level: 要分析的层级深度
            
        Returns:
            str: 所有相关函数内容的拼接文本
        """
        def get_functions_from_tree(tree, current_level=0, max_level=level, collected_funcs=None, level_stats=None):
            """递归获取树中指定层级内的所有函数信息"""
            if collected_funcs is None:
                collected_funcs = []
            if level_stats is None:
                level_stats = {}
                
            if not tree or current_level > max_level:
                return collected_funcs, level_stats
                    
            # 添加当前节点的函数信息
            if tree['function_data']:
                collected_funcs.append(tree['function_data'])
                # 更新层级统计
                level_stats[current_level] = level_stats.get(current_level, 0) + 1
                    
            # 递归处理子节点
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
        
        # 使用集合进行更严格的去重
        seen_functions = set()  # 存储函数的唯一标识符
        unique_functions = []   # 存储去重后的函数
        
        # 遍历每个指定的函数名
        for func_name in function_names:
            # 在call_trees中查找对应的树
            for tree_data in self.project_audit.call_trees:
                if tree_data['function'] == func_name:
                    # 处理上游调用树
                    if tree_data['upstream_tree']:
                        upstream_funcs, upstream_stats = get_functions_from_tree(tree_data['upstream_tree'])
                        all_related_functions.extend(upstream_funcs)
                        # 合并上游统计信息
                        for level, count in upstream_stats.items():
                            statistics['upstream_stats'][level] = (
                                statistics['upstream_stats'].get(level, 0) + count
                            )
                            
                    # 处理下游调用树
                    if tree_data['downstream_tree']:
                        downstream_funcs, downstream_stats = get_functions_from_tree(tree_data['downstream_tree'])
                        all_related_functions.extend(downstream_funcs)
                        # 合并下游统计信息
                        for level, count in downstream_stats.items():
                            statistics['downstream_stats'][level] = (
                                statistics['downstream_stats'].get(level, 0) + count
                            )
                        
                    # 添加原始函数本身
                    for func in self.project_audit.functions_to_check:
                        if func['name'].split('.')[-1] == func_name:
                            all_related_functions.append(func)
                            break
                                
                    break
        
        # 增强的去重处理
        for func in all_related_functions:
            # 创建一个更精确的唯一标识符，包含函数名和内容的hash
            func_identifier = f"{func['name']}_{hash(func['content'])}"
            if func_identifier not in seen_functions:
                seen_functions.add(func_identifier)
                unique_functions.append(func)
        
        # 拼接所有函数内容，包括状态变量
        combined_text_parts = []
        for func in unique_functions:
            # 查找对应的状态变量
            state_vars = None
            for tree_data in self.project_audit.call_trees:
                if tree_data['function'] == func['name'].split('.')[-1]:
                    state_vars = tree_data.get('state_variables', '')
                    break
            
            # 构建函数文本，包含状态变量
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
        
        return combined_text
    
    def get_additional_internet_info(self, required_info: List[str]) -> str:
        """判断是否需要联网搜索并获取网络信息
        
        Args:
            required_info: 需要进一步调查的信息列表
            
        Returns:
            str: 搜索获取的相关信息
        """
        # 检查环境变量是否允许网络搜索
        if os.getenv("ENABLE_INTERNET_SEARCH", "False").lower() != "true":
            print("❌ 网络搜索已禁用")
            return ""
        
        if not required_info:
            print("❌ 没有查询内容，无法进行网络搜索")
            return ""
        
        # 构建判断是否需要联网搜索的提示词
        judge_prompt = CorePrompt.judge_prompt()
        
        # 将所有required_info合并成一个查询文本
        combined_query = "\n".join(required_info)
        
        # 获取判断结果
        judge_response = ask_claude(judge_prompt.format(combined_query))
        print("\n🔍 网络搜索需求分析:")
        print(judge_response)
        
        try:
            # 尝试提取JSON部分 - 只匹配第一个完整的JSON对象
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', judge_response)
            if json_match:
                json_str = json_match.group(0)
                # 清理可能的额外字符
                json_str = json_str.strip()
                judge_result = json.loads(json_str)
            else:
                raise json.JSONDecodeError("No JSON found in response", judge_response, 0)
                
            if judge_result.get("needs_search", "no").lower() == "yes":
                print(f"\n🌐 需要网络搜索: {judge_result.get('reason', '')}")
                
                # 使用 grok 进行深度搜索
                search_results = ask_grok3_deepsearch(combined_query)
                if search_results:
                    print(f"\n✅ 获取到网络搜索结果 (长度: {len(search_results)} 字符)")
                    return search_results
                else:
                    print("\n⚠️ 网络搜索未返回有效结果")
                    return ""
            else:
                print(f"\n📝 无需网络搜索: {judge_result.get('reason', '')}")
                return ""
            
        except json.JSONDecodeError:
            print("\n⚠️ JSON 解析错误 - 跳过网络搜索")
            return "" 