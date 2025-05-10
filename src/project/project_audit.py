import csv
from .project_parser import parse_project, BaseProjectFilter
import re
from library.sgp.utilities.contract_extractor import extract_state_variables_from_code, extract_state_variables_from_code_move
from concurrent.futures import ThreadPoolExecutor, as_completed

class ProjectAudit(object):
    def analyze_function_relationships(self, functions_to_check):
        # 构建函数名到函数信息的映射和调用关系字典
        func_map = {}
        relationships = {'upstream': {}, 'downstream': {}}
        
        for idx, func in enumerate(functions_to_check):
            func_name = func['name'].split('.')[-1]
            func_map[func_name] = {
                'index': idx,
                'data': func
            }
            
        # 分析每个函数的调用关系
        for func in functions_to_check:
            func_name = func['name'].split('.')[-1]
            content = func['content'].lower()
            
            if func_name not in relationships['upstream']:
                relationships['upstream'][func_name] = set()
            if func_name not in relationships['downstream']:
                relationships['downstream'][func_name] = set()
                
            # 检查其他函数是否调用了当前函数
            for other_func in functions_to_check:
                if other_func == func:
                    continue
                    
                other_name = other_func['name'].split('.')[-1]
                other_content = other_func['content'].lower()
                
                # 如果其他函数调用了当前函数
                if re.search(r'\b' + re.escape(func_name.lower()) + r'\b', other_content):
                    relationships['upstream'][func_name].add(other_name)
                    if other_name not in relationships['downstream']:
                        relationships['downstream'][other_name] = set()
                    relationships['downstream'][other_name].add(func_name)
                
                # 如果当前函数调用了其他函数
                if re.search(r'\b' + re.escape(other_name.lower()) + r'\b', content):
                    relationships['downstream'][func_name].add(other_name)
                    if other_name not in relationships['upstream']:
                        relationships['upstream'][other_name] = set()
                    relationships['upstream'][other_name].add(func_name)
        
        return relationships, func_map

    def build_call_tree(self, func_name, relationships, direction, func_map, visited=None):
        if visited is None:
            visited = set()
        
        if func_name in visited:
            return None
        
        visited.add(func_name)
        
        # 获取函数完整信息
        func_info = func_map.get(func_name, {'index': -1, 'data': None})
        
        node = {
            'name': func_name,
            'index': func_info['index'],
            'function_data': func_info['data'],  # 包含完整的函数信息
            'children': []
        }
        
        # 获取该方向上的所有直接调用
        related_funcs = relationships[direction].get(func_name, set())
        
        # 递归构建每个相关函数的调用树
        for related_func in related_funcs:
            child_tree = self.build_call_tree(related_func, relationships, direction, func_map, visited.copy())
            if child_tree:
                node['children'].append(child_tree)
        
        return node

    def print_call_tree(self, node, level=0, prefix=''):
        if not node:
            return
            
        # 打印当前节点的基本信息
        func_data = node['function_data']
        if func_data:
            print(f"{prefix}{'└─' if level > 0 else ''}{node['name']} (index: {node['index']}, "
                  f"lines: {func_data['start_line']}-{func_data['end_line']})")
        else:
            print(f"{prefix}{'└─' if level > 0 else ''}{node['name']} (index: {node['index']})")
        
        # 打印子节点
        for i, child in enumerate(node['children']):
            is_last = i == len(node['children']) - 1
            new_prefix = prefix + ('  ' if level == 0 else '│ ' if not is_last else '  ')
            self.print_call_tree(child, level + 1, new_prefix + ('└─' if is_last else '├─'))

    def __init__(self, project_id, project_path, db_engine):
        self.project_id = project_id
        self.project_path = project_path
        self.functions = []
        self.functions_to_check = []
        self.tasks = []
        self.taskkeys = set()

    def process_single_function(self, func, relationships, func_map):
        func_name = func['name'].split('.')[-1]
        upstream_tree = self.build_call_tree(func_name, relationships, 'upstream', func_map)
        downstream_tree = self.build_call_tree(func_name, relationships, 'downstream', func_map)
        state_variables = []
        if func['relative_file_path'].endswith('.move'):
            state_variables = extract_state_variables_from_code_move(func['contract_code'],func['relative_file_path'])
        if func['relative_file_path'].endswith('.sol') or func['relative_file_path'].endswith('.fr'):
            state_variables = extract_state_variables_from_code(func['contract_code'])
        state_variables_text = '\n'.join(state_variables) if state_variables else ''
        
        return {
            'function': func_name,
            'upstream_tree': upstream_tree,
            'downstream_tree': downstream_tree,
            'state_variables': state_variables_text
        }

    def parse(self, white_files, white_functions):
        parser_filter = BaseProjectFilter(white_files, white_functions)
        functions, functions_to_check = parse_project(self.project_path, parser_filter)
        self.functions = functions
        self.functions_to_check = functions_to_check
        
        # 分析函数关系
        relationships, func_map = self.analyze_function_relationships(functions_to_check)
        
        # 使用线程池处理函数分析
        call_trees = []
        from tqdm import tqdm
        with ThreadPoolExecutor(max_workers=1) as executor:
            # 创建future到函数的映射
            future_to_func = {
                executor.submit(self.process_single_function, func, relationships, func_map): func
                for func in functions_to_check
            }
            
            # 使用tqdm显示进度
            for future in tqdm(as_completed(future_to_func), total=len(functions_to_check), desc="分析函数调用关系"):
                try:
                    call_tree = future.result()
                    call_trees.append(call_tree)
                except Exception as e:
                    func = future_to_func[future]
                    tqdm.write(f"处理函数 {func['name']} 时发生错误: {str(e)}")
        
        self.call_trees = call_trees

    def get_function_names(self):
        return set([function['name'] for function in self.functions])