from typing import List, Dict, Tuple


class FunctionUtils:
    """函数处理相关的工具函数"""
    
    @staticmethod
    def extract_related_functions_by_level(
        project, 
        function_names: List[str], 
        level: int
    ) -> Tuple[str, List[Tuple[str, str]]]:
        """
        从call_trees中提取指定函数相关的上下游函数信息并扁平化处理
        
        Args:
            project: 项目对象
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
            for tree_data in project.call_trees:
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
                        
                    for func in project.functions_to_check:
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
            for tree_data in project.call_trees:
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