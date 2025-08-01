#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced Call Tree Builder
使用src/tree_sitter核心功能的高级调用树构建器
替代简化的正则表达式实现，使用真正的MultiLanguageAnalyzer
"""

import os
import sys
from typing import List, Dict, Set, Tuple, Any, Optional
from tqdm import tqdm
import tempfile
from pathlib import Path

# 导入tree-sitter相关模块
from ts_parser_core import MultiLanguageAnalyzer, LanguageType
print("✅ 高级MultiLanguageAnalyzer可用")


class AdvancedCallTreeBuilder:
    """使用真正tree-sitter核心功能的高级调用树构建器"""
    
    def __init__(self):
        self.analyzer = MultiLanguageAnalyzer()
        self.temp_files = []  # 跟踪临时文件以便清理
    
    def __del__(self):
        """清理临时文件"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass
    
    def _detect_language_from_file_path(self, file_path: str) -> Optional[LanguageType]:
        """根据文件路径检测语言类型"""
        if not file_path:
            return LanguageType.SOLIDITY  # 默认
            
        suffix = Path(file_path).suffix.lower()
        if suffix == '.sol':
            return LanguageType.SOLIDITY
        elif suffix == '.rs':
            return LanguageType.RUST
        elif suffix in ['.cpp', '.cc', '.cxx', '.c', '.h', '.hpp', '.hxx']:
            return LanguageType.CPP
        elif suffix == '.move':
            return LanguageType.MOVE
        
        return LanguageType.SOLIDITY  # 默认
    
    def _find_project_root(self, file_path: str) -> Optional[str]:
        """查找项目根目录"""
        path = Path(file_path)
        current_dir = path.parent if path.is_file() else path
        
        # 向上查找，直到找到包含多个代码文件的目录或到达系统根目录
        while current_dir.parent != current_dir:  # 不是根目录
            # 检查是否包含项目标识文件
            project_indicators = [
                'package.json', 'Cargo.toml', 'Cargo.lock', 
                'pyproject.toml', 'requirements.txt', 
                '.git', '.gitignore',
                'Move.toml', 'foundry.toml', 'hardhat.config.js'
            ]
            
            for indicator in project_indicators:
                if (current_dir / indicator).exists():
                    return str(current_dir)
            
            # 检查是否包含多个代码文件（启发式判断）
            code_extensions = ['.sol', '.rs', '.cpp', '.c', '.h', '.move']
            code_files = []
            
            try:
                for ext in code_extensions:
                    code_files.extend(list(current_dir.glob(f'**/*{ext}')))
                    if len(code_files) >= 3:  # 如果有3个或更多代码文件，认为是项目根目录
                        return str(current_dir)
            except (PermissionError, OSError):
                pass
            
            current_dir = current_dir.parent
        
        # 如果找不到明确的项目根目录，返回文件所在目录
        return str(path.parent if path.is_file() else path)
    
    def _create_temp_files_from_functions(self, functions_to_check: List[Dict]) -> Dict[str, str]:
        """从函数数据创建临时文件用于分析"""
        temp_files_map = {}
        
        # 按文件路径分组函数
        files_content = {}
        for func in functions_to_check:
            file_path = func.get('file_path', 'unknown.sol')
            if file_path not in files_content:
                files_content[file_path] = []
            files_content[file_path].append(func)
        
        # 为每个文件创建临时文件
        for file_path, funcs in files_content.items():
            # 尝试读取原始文件内容
            content = ""
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except:
                    # 如果无法读取，使用函数内容拼接
                    content = self._reconstruct_file_content(funcs, file_path)
            else:
                # 重构文件内容
                content = self._reconstruct_file_content(funcs, file_path)
            
            # 创建临时文件
            suffix = Path(file_path).suffix or '.sol'
            with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as temp_f:
                temp_f.write(content)
                temp_file_path = temp_f.name
                self.temp_files.append(temp_file_path)
                temp_files_map[file_path] = temp_file_path
        
        return temp_files_map
    
    def _reconstruct_file_content(self, funcs: List[Dict], file_path: str) -> str:
        """重构文件内容"""
        language = self._detect_language_from_file_path(file_path)
        
        if language == LanguageType.SOLIDITY:
            # 为Solidity重构
            content = "pragma solidity ^0.8.0;\n\n"
            
            # 按合约分组
            contracts = {}
            for func in funcs:
                contract_name = func.get('contract_name', 'Unknown')
                if contract_name not in contracts:
                    contracts[contract_name] = []
                contracts[contract_name].append(func)
            
            # 生成合约代码
            for contract_name, contract_funcs in contracts.items():
                content += f"contract {contract_name} {{\n"
                for func in contract_funcs:
                    func_content = func.get('content', '')
                    if func_content:
                        content += f"    {func_content}\n\n"
                content += "}\n\n"
                
        elif language == LanguageType.RUST:
            # 为Rust重构
            content = "// Rust module\n\n"
            for func in funcs:
                func_content = func.get('content', '')
                if func_content:
                    content += f"{func_content}\n\n"
                    
        elif language == LanguageType.CPP:
            # 为C++重构
            content = "#include <iostream>\n\n"
            for func in funcs:
                func_content = func.get('content', '')
                if func_content:
                    content += f"{func_content}\n\n"
                    
        elif language == LanguageType.MOVE:
            # 为Move重构
            content = "module 0x1::Module {\n"
            for func in funcs:
                func_content = func.get('content', '')
                if func_content:
                    content += f"    {func_content}\n\n"
            content += "}\n"
        
        return content
    
    def analyze_function_relationships(self, functions_to_check: List[Dict]) -> Tuple[Dict, Dict]:
        """使用高级分析器分析整个项目目录的函数关系"""
        if not self.analyzer:
            print("⚠️ MultiLanguageAnalyzer不可用，使用简化分析方法")
            return self._fallback_analyze_relationships(functions_to_check)
        
        print(f"🔍 使用高级分析器分析整个项目目录的调用关系...")
        
        # 构建函数映射
        func_map = {}
        relationships = {'upstream': {}, 'downstream': {}}
        
        for idx, func in enumerate(functions_to_check):
            func_name = func['name']  # 使用完整的函数名（包括合约名）
            func_map[func_name] = {
                'index': idx,
                'data': func
            }
            relationships['upstream'][func_name] = set()
            relationships['downstream'][func_name] = set()
        
        # 分析整个项目目录 - 按语言分组分析
        project_paths = set()
        language_paths = {}
        
        # 从functions_to_check中提取项目路径和语言信息
        for func in functions_to_check:
            file_path = func.get('absolute_file_path', '')
            if file_path and os.path.exists(file_path):
                # 获取项目根目录（向上找到包含多个代码文件的目录）
                project_root = self._find_project_root(file_path)
                if project_root:
                    language = self._detect_language_from_file_path(file_path)
                    if language not in language_paths:
                        language_paths[language] = set()
                    language_paths[language].add(project_root)
        
        # 对每种语言的项目目录进行分析
        total_call_graph = []
        for language, paths in language_paths.items():
            for project_path in paths:
                try:
                    print(f"  📁 分析 {language.value} 项目目录: {project_path}")
                    
                    # 使用MultiLanguageAnalyzer分析整个目录
                    self.analyzer.analyze_directory(project_path, language)
                    
                    # 获取完整的调用图
                    call_graph = self.analyzer.get_call_graph(language)
                    functions = self.analyzer.get_functions(language)
                    
                    total_call_graph.extend(call_graph)
                    
                    print(f"  ✅ 发现 {len(call_graph)} 个调用关系，{len(functions)} 个函数")
                    
                except Exception as e:
                    print(f"  ⚠️ 分析目录 {project_path} 失败: {e}")
                    continue
        
        # 处理所有调用关系
        processed_relations = 0
        for edge in total_call_graph:
            caller_name = edge.caller.split('.')[-1] if '.' in edge.caller else edge.caller
            callee_name = edge.callee.split('.')[-1] if '.' in edge.callee else edge.callee
            
            # 只处理我们关心的函数
            if caller_name in func_map and callee_name in func_map:
                relationships['downstream'][caller_name].add(callee_name)
                relationships['upstream'][callee_name].add(caller_name)
                processed_relations += 1
        
        print(f"✅ 项目目录调用关系分析完成: 处理了 {processed_relations} 个相关调用关系")
        return relationships, func_map
    
    def _fallback_analyze_relationships(self, functions_to_check: List[Dict]) -> Tuple[Dict, Dict]:
        """简化的备选分析方法（与原实现相同）"""
        func_map = {}
        relationships = {'upstream': {}, 'downstream': {}}
        
        for idx, func in enumerate(functions_to_check):
            func_name = func['name']  # 使用完整的函数名（包括合约名）
            func_map[func_name] = {'index': idx, 'data': func}
            relationships['upstream'][func_name] = set()
            relationships['downstream'][func_name] = set()
        
        # 使用函数中的calls信息和启发式搜索
        for func in functions_to_check:
            func_name = func['name']  # 使用完整的函数名（包括合约名）
            
            if 'calls' in func and func['calls']:
                for called_func in func['calls']:
                    # 对于called_func，也使用完整名称来查找
                    clean_called_func = called_func if called_func in func_map else None
                    # 如果直接查找失败，尝试只用函数名部分匹配
                    if not clean_called_func:
                        func_name_only = called_func.split('.')[-1] if '.' in called_func else called_func
                        for full_name in func_map.keys():
                            if full_name.split('.')[-1] == func_name_only:
                                clean_called_func = full_name
                                break
                    
                    if clean_called_func and clean_called_func in func_map:
                        relationships['downstream'][func_name].add(clean_called_func)
                        relationships['upstream'][clean_called_func].add(func_name)
        
        return relationships, func_map
    
    def build_call_tree(self, func_name: str, relationships: Dict, direction: str, func_map: Dict, visited: Set = None) -> Dict:
        """构建完整的调用树（无深度限制，只进行循环检测）"""
        if visited is None:
            visited = set()
        
        # 循环检测 - 在当前调用路径中检测循环
        if func_name in visited:
            return {
                'name': func_name,
                'index': func_map.get(func_name, {'index': -1})['index'],
                'function_data': func_map.get(func_name, {'data': None})['data'],
                'children': [],
                'circular_reference': True  # 标记循环引用
            }
        
        visited.add(func_name)
        
        func_info = func_map.get(func_name, {'index': -1, 'data': None})
        
        node = {
            'name': func_name,
            'index': func_info['index'],
            'function_data': func_info['data'],
            'children': []
        }
        
        related_funcs = relationships[direction].get(func_name, set())
        
        for related_func in related_funcs:
            # 为每个分支创建独立的visited副本，允许合理的重复遍历
            # 这样同一个函数可以在不同的调用路径中出现
            child_tree = self.build_call_tree(
                related_func, 
                relationships, 
                direction, 
                func_map, 
                visited.copy()
            )
            if child_tree:
                node['children'].append(child_tree)
        
        return node
    
    def extract_call_tree_with_depth(self, call_tree: Dict, max_depth: int, current_depth: int = 0) -> Dict:
        """从完整的调用树中提取指定深度的子树（查询时使用）"""
        if current_depth >= max_depth:
            return {
                'name': call_tree['name'],
                'index': call_tree['index'],
                'function_data': call_tree['function_data'],
                'children': [],
                'truncated': True,  # 标记被截断
                'max_depth_reached': True,
                'depth': current_depth
            }
        
        # 如果是循环引用节点，直接返回
        if call_tree.get('circular_reference'):
            result = call_tree.copy()
            result['depth'] = current_depth
            return result
        
        # 复制当前节点
        result = {
            'name': call_tree['name'],
            'index': call_tree['index'],
            'function_data': call_tree['function_data'],
            'children': [],
            'depth': current_depth
        }
        
        # 如果有循环引用标记，保留它
        if call_tree.get('circular_reference'):
            result['circular_reference'] = True
        
        # 递归处理子节点
        for child in call_tree.get('children', []):
            child_with_depth = self.extract_call_tree_with_depth(child, max_depth, current_depth + 1)
            result['children'].append(child_with_depth)
        
        return result
    
    def build_call_trees(self, functions_to_check: List[Dict], max_workers: int = 1) -> List[Dict]:
        """
        构建调用树（主要入口，与原接口兼容）
        使用高级分析器提供更准确的结果
        """
        if not functions_to_check:
            return []
        
        print(f"🌳 开始使用高级分析器为 {len(functions_to_check)} 个函数构建调用树...")
        
        # 使用高级分析器分析函数关系
        relationships, func_map = self.analyze_function_relationships(functions_to_check)
        
        call_trees = []
        
        print("🌲 构建完整的调用树（无深度限制）...")
        
        # 为每个函数构建完整的调用树
        for func in tqdm(functions_to_check, desc="构建完整调用树"):
            func_name = func['name']  # 使用完整的函数名（包括合约名）
            
            # 构建完整的上游和下游调用树
            upstream_tree = self.build_call_tree(func_name, relationships, 'upstream', func_map)
            downstream_tree = self.build_call_tree(func_name, relationships, 'downstream', func_map)
            
            call_tree_info = {
                'function': func,
                'function_name': func_name,
                'upstream': upstream_tree,
                'downstream': downstream_tree,
                'upstream_count': len(relationships['upstream'].get(func_name, [])),
                'downstream_count': len(relationships['downstream'].get(func_name, [])),
                'relationships': relationships,
                'analyzer_type': 'advanced'
            }
            
            call_trees.append(call_tree_info)
        
        print(f"✅ 完整调用树构建完成，共构建 {len(call_trees)} 个调用树")
        return call_trees
    
    def get_call_tree_with_depth_limit(self, call_trees: List[Dict], func_name: str, direction: str, max_depth: int = 5) -> Dict:
        """获取指定深度限制的调用树（查询方法）
        
        Args:
            call_trees: 完整的调用树列表
            func_name: 函数名
            direction: 'upstream' 或 'downstream'
            max_depth: 最大深度限制
            
        Returns:
            指定深度的调用树
        """
        # 查找对应的函数调用树
        target_call_tree = None
        for call_tree_info in call_trees:
            if call_tree_info['function_name'] == func_name:
                target_call_tree = call_tree_info
                break
        
        if not target_call_tree:
            return None
        
        # 获取完整的调用树
        full_tree = target_call_tree[direction]
        
        if not full_tree:
            return None
        
        # 应用深度限制
        limited_tree = self.extract_call_tree_with_depth(full_tree, max_depth)
        
        return {
            'function': target_call_tree['function'],
            'function_name': func_name,
            'direction': direction,
            'max_depth': max_depth,
            'tree': limited_tree,
            'total_count': target_call_tree[f'{direction}_count'],
            'analyzer_type': target_call_tree['analyzer_type']
        }
    
    def get_full_call_graph_summary(self, call_trees: List[Dict]) -> Dict:
        """获取完整调用图的统计摘要
        
        Args:
            call_trees: 完整的调用树列表
            
        Returns:
            调用图统计信息
        """
        summary = {
            'total_functions': len(call_trees),
            'functions': [],
            'call_relationships': {
                'upstream_total': 0,
                'downstream_total': 0
            },
            'circular_references': [],
            'isolated_functions': []
        }
        
        for call_tree_info in call_trees:
            func_name = call_tree_info['function_name']
            upstream_count = call_tree_info['upstream_count']
            downstream_count = call_tree_info['downstream_count']
            
            func_summary = {
                'name': func_name,
                'upstream_count': upstream_count,
                'downstream_count': downstream_count,
                'has_circular_upstream': self._has_circular_reference(call_tree_info['upstream']),
                'has_circular_downstream': self._has_circular_reference(call_tree_info['downstream'])
            }
            
            summary['functions'].append(func_summary)
            summary['call_relationships']['upstream_total'] += upstream_count
            summary['call_relationships']['downstream_total'] += downstream_count
            
            # 检查循环引用
            if func_summary['has_circular_upstream'] or func_summary['has_circular_downstream']:
                summary['circular_references'].append(func_name)
            
            # 检查孤立函数
            if upstream_count == 0 and downstream_count == 0:
                summary['isolated_functions'].append(func_name)
        
        return summary
    
    def _has_circular_reference(self, tree: Dict) -> bool:
        """递归检查调用树中是否有循环引用"""
        if not tree:
            return False
        
        if tree.get('circular_reference'):
            return True
        
        for child in tree.get('children', []):
            if self._has_circular_reference(child):
                return True
        
        return False
    
    def get_dependency_graph(self, target_function: str, functions_to_check: List[Dict], max_depth: int = 3) -> Dict:
        """
        获取函数依赖图（参考dependency_demo.py的功能）
        提供更详细的依赖分析
        """
        if not self.analyzer:
            print("⚠️ MultiLanguageAnalyzer不可用，高级依赖分析不可用")
            return {'upstream_functions': {}, 'downstream_functions': {}}
        
        # 创建临时文件并分析
        temp_files_map = self._create_temp_files_from_functions(functions_to_check)
        
        dependency_result = {'upstream_functions': {}, 'downstream_functions': {}}
        
        for original_path, temp_path in temp_files_map.items():
            language = self._detect_language_from_file_path(original_path)
            
            try:
                self.analyzer.analyze_file(temp_path, language)
                
                # 获取目标函数的完整名称
                functions = self.analyzer.get_functions(language)
                target_full_name = None
                
                for full_name, func_info in functions.items():
                    if func_info.name == target_function or target_function in full_name:
                        target_full_name = full_name
                        break
                
                if target_full_name:
                    # 使用MultiLanguageAnalyzer的依赖分析功能
                    dependency_graph = self.analyzer.get_function_dependency_graph(
                        target_full_name, language, max_depth
                    )
                    
                    # 合并结果
                    dependency_result['upstream_functions'].update(dependency_graph['upstream_functions'])
                    dependency_result['downstream_functions'].update(dependency_graph['downstream_functions'])
                    
                    print(f"✅ 找到函数 {target_function} 的依赖关系")
                    break
                    
            except Exception as e:
                print(f"⚠️ 依赖分析失败: {e}")
                continue
        
        return dependency_result


# 向后兼容的别名
TreeSitterCallTreeBuilder = AdvancedCallTreeBuilder


if __name__ == '__main__':
    # 测试代码
    test_functions = [
        {
            'name': 'TestContract.transfer',
            'content': 'function transfer(address to, uint256 amount) public { _transfer(msg.sender, to, amount); }',
            'calls': ['_transfer'],
            'contract_name': 'TestContract',
            'visibility': 'public',
            'line_number': 10,
            'file_path': 'test_contract.sol'
        },
        {
            'name': 'TestContract._transfer',
            'content': 'function _transfer(address from, address to, uint256 amount) internal { emit Transfer(from, to, amount); }',
            'calls': ['emit'],
            'contract_name': 'TestContract',
            'visibility': 'internal',
            'line_number': 15,
            'file_path': 'test_contract.sol'
        }
    ]
    
    print("🧪 测试高级调用树构建器...")
    
    builder = AdvancedCallTreeBuilder()
    call_trees = builder.build_call_trees(test_functions)
    
    print(f"\n✅ 构建了 {len(call_trees)} 个调用树")
    for tree in call_trees:
        print(f"\n📊 函数: {tree['function_name']}")
        print(f"  上游调用数: {tree['upstream_count']}")
        print(f"  下游调用数: {tree['downstream_count']}")
        print(f"  分析器类型: {tree['analyzer_type']}")
    
    print("\n🎉 测试完成") 