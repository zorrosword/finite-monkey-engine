#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tree-sitter Based Call Tree Builder
使用真正的tree-sitter核心功能替代简化的正则表达式实现

注意：现在使用AdvancedCallTreeBuilder作为主要实现
原有的简化实现保留作为备选方案
"""

import re
import os
import sys
from typing import List, Dict, Set, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# 添加路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 尝试导入高级实现
try:
    from .advanced_call_tree_builder import AdvancedCallTreeBuilder
    ADVANCED_BUILDER_AVAILABLE = True
    print("✅ 使用高级调用树构建器")
except ImportError:
    try:
        # 尝试直接导入
        sys.path.insert(0, os.path.dirname(__file__))
        from advanced_call_tree_builder import AdvancedCallTreeBuilder
        ADVANCED_BUILDER_AVAILABLE = True
        print("✅ 使用高级调用树构建器")
    except ImportError:
        ADVANCED_BUILDER_AVAILABLE = False
        print("⚠️ 高级调用树构建器不可用，使用简化实现")


class SimplifiedCallTreeBuilder:
    """简化的调用树构造器（备选实现，使用正则表达式）"""
    
    def __init__(self):
        pass
    
    def analyze_function_relationships(self, functions_to_check: List[Dict]) -> Tuple[Dict, Dict]:
        """
        分析函数之间的调用关系
        使用更精确的tree-sitter分析替代原有的正则表达式匹配
        """
        # 构建函数名到函数信息的映射和调用关系字典
        func_map = {}
        relationships = {'upstream': {}, 'downstream': {}}
        
        # 构建函数映射
        for idx, func in enumerate(functions_to_check):
            func_name = func['name']  # 使用完整的函数名（包括合约名）
            func_map[func_name] = {
                'index': idx,
                'data': func
            }
        
        print(f"🔍 分析 {len(functions_to_check)} 个函数的调用关系...")
        
        # 分析每个函数的调用关系
        for func in tqdm(functions_to_check, desc="分析函数调用关系"):
            func_name = func['name']  # 使用完整的函数名（包括合约名）
            content = func.get('content', '').lower()
            
            if func_name not in relationships['upstream']:
                relationships['upstream'][func_name] = set()
            if func_name not in relationships['downstream']:
                relationships['downstream'][func_name] = set()
            
            # 使用现有的calls信息（来自tree-sitter分析）
            if 'calls' in func and func['calls']:
                for called_func in func['calls']:
                    # 清理函数名
                    clean_called_func = called_func.split('.')[-1] if '.' in called_func else called_func
                    
                    # 检查被调用的函数是否在我们的函数列表中
                    if clean_called_func in func_map:
                        relationships['downstream'][func_name].add(clean_called_func)
                        if clean_called_func not in relationships['upstream']:
                            relationships['upstream'][clean_called_func] = set()
                        relationships['upstream'][clean_called_func].add(func_name)
            
            # 额外的启发式搜索（作为备选方案）
            for other_func in functions_to_check:
                if other_func == func:
                    continue
                    
                other_name = other_func['name']  # 使用完整的函数名（包括合约名） 
                other_content = other_func.get('content', '').lower()
                
                # 检查其他函数是否调用了当前函数
                if self._is_function_called_in_content(func_name, other_content):
                    relationships['upstream'][func_name].add(other_name)
                    if other_name not in relationships['downstream']:
                        relationships['downstream'][other_name] = set()
                    relationships['downstream'][other_name].add(func_name)
                
                # 检查当前函数是否调用了其他函数
                if self._is_function_called_in_content(other_name, content):
                    relationships['downstream'][func_name].add(other_name)
                    if other_name not in relationships['upstream']:
                        relationships['upstream'][other_name] = set()
                    relationships['upstream'][other_name].add(func_name)
        
        print(f"✅ 调用关系分析完成")
        return relationships, func_map
    
    def _is_function_called_in_content(self, func_name: str, content: str) -> bool:
        """更精确的函数调用检测"""
        # 多种模式匹配
        patterns = [
            rf'\b{re.escape(func_name.lower())}\s*\(',  # 直接调用
            rf'\.{re.escape(func_name.lower())}\s*\(',  # 成员调用
            rf'{re.escape(func_name.lower())}\s*\(',    # 简单调用
        ]
        
        return any(re.search(pattern, content) for pattern in patterns)
    
    def build_call_tree(self, func_name: str, relationships: Dict, direction: str, func_map: Dict, visited: Set = None) -> Dict:
        """构建调用树"""
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
    
    def build_call_trees(self, functions_to_check: List[Dict], max_workers: int = 1) -> List[Dict]:
        """
        为所有函数构建调用树
        返回格式与原始CallTreeBuilder兼容
        """
        if not functions_to_check:
            return []
        
        print(f"🌳 开始为 {len(functions_to_check)} 个函数构建调用树...")
        
        # 分析函数关系
        relationships, func_map = self.analyze_function_relationships(functions_to_check)
        
        call_trees = []
        
        # 为每个函数构建上游和下游调用树
        for func in tqdm(functions_to_check, desc="构建调用树"):
            func_name = func['name']  # 使用完整的函数名（包括合约名）
            
            # 构建上游调用树（调用此函数的函数）
            upstream_tree = self.build_call_tree(func_name, relationships, 'upstream', func_map)
            
            # 构建下游调用树（此函数调用的函数）
            downstream_tree = self.build_call_tree(func_name, relationships, 'downstream', func_map)
            
            call_tree_info = {
                'function': func,
                'function_name': func_name,
                'upstream': upstream_tree,
                'downstream': downstream_tree,
                'upstream_count': len(relationships['upstream'].get(func_name, [])),
                'downstream_count': len(relationships['downstream'].get(func_name, [])),
                'relationships': relationships  # 保存关系数据供后续使用
            }
            
            call_trees.append(call_tree_info)
        
        print(f"✅ 调用树构建完成，共构建 {len(call_trees)} 个调用树")
        return call_trees
    
    def print_call_tree(self, node: Dict, level: int = 0, prefix: str = ''):
        """打印调用树"""
        if not node:
            return
            
        # 打印当前节点的基本信息
        func_data = node.get('function_data')
        if func_data:
            visibility = func_data.get('visibility', 'unknown')
            contract = func_data.get('contract_name', 'unknown')
            line_num = func_data.get('line_number', 'unknown')
            
            print(f"{prefix}{'└─' if level > 0 else ''}{node['name']} "
                  f"(index: {node['index']}, {visibility}, {contract}:{line_num})")
        else:
            print(f"{prefix}{'└─' if level > 0 else ''}{node['name']} (index: {node['index']})")
        
        # 递归打印子节点
        children = node.get('children', [])
        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            child_prefix = prefix + ('    ' if level > 0 else '')
            if not is_last:
                child_prefix += '├─'
            else:
                child_prefix += '└─'
            
            self.print_call_tree(child, level + 1, child_prefix)
    
    def get_call_tree_statistics(self, call_trees: List[Dict]) -> Dict:
        """获取调用树统计信息"""
        stats = {
            'total_functions': len(call_trees),
            'functions_with_upstream': 0,
            'functions_with_downstream': 0,
            'max_upstream_count': 0,
            'max_downstream_count': 0,
            'isolated_functions': 0
        }
        
        for tree in call_trees:
            upstream_count = tree.get('upstream_count', 0)
            downstream_count = tree.get('downstream_count', 0)
            
            if upstream_count > 0:
                stats['functions_with_upstream'] += 1
                stats['max_upstream_count'] = max(stats['max_upstream_count'], upstream_count)
            
            if downstream_count > 0:
                stats['functions_with_downstream'] += 1
                stats['max_downstream_count'] = max(stats['max_downstream_count'], downstream_count)
            
            if upstream_count == 0 and downstream_count == 0:
                stats['isolated_functions'] += 1
        
        return stats
    
    def find_entry_points(self, call_trees: List[Dict]) -> List[Dict]:
        """查找入口点函数（没有上游调用的函数）"""
        entry_points = []
        for tree in call_trees:
            if tree.get('upstream_count', 0) == 0:
                entry_points.append(tree['function'])
        return entry_points
    
    def find_leaf_functions(self, call_trees: List[Dict]) -> List[Dict]:
        """查找叶子函数（没有下游调用的函数）"""
        leaf_functions = []
        for tree in call_trees:
            if tree.get('downstream_count', 0) == 0:
                leaf_functions.append(tree['function'])
        return leaf_functions


class TreeSitterCallTreeBuilder:
    """
    智能调用树构建器适配器
    优先使用高级实现（真正的tree-sitter），备选简化实现
    """
    
    def __init__(self):
        if ADVANCED_BUILDER_AVAILABLE:
            self.builder = AdvancedCallTreeBuilder()
            self.builder_type = "advanced"
        else:
            self.builder = SimplifiedCallTreeBuilder()
            self.builder_type = "simplified"
    
    def build_call_trees(self, functions_to_check: List[Dict], max_workers: int = 1) -> List[Dict]:
        """构建调用树（主要接口）"""
        return self.builder.build_call_trees(functions_to_check, max_workers)
    
    def analyze_function_relationships(self, functions_to_check: List[Dict]) -> Tuple[Dict, Dict]:
        """分析函数关系"""
        return self.builder.analyze_function_relationships(functions_to_check)
    
    def build_call_tree(self, func_name: str, relationships: Dict, direction: str, func_map: Dict, visited: Set = None) -> Dict:
        """构建单个调用树"""
        return self.builder.build_call_tree(func_name, relationships, direction, func_map, visited)
    
    def get_call_tree_statistics(self, call_trees: List[Dict]) -> Dict:
        """获取调用树统计信息"""
        if hasattr(self.builder, 'get_call_tree_statistics'):
            return self.builder.get_call_tree_statistics(call_trees)
        else:
            # 简化实现的备选统计
            return self._basic_statistics(call_trees)
    
    def _basic_statistics(self, call_trees: List[Dict]) -> Dict:
        """基础统计信息"""
        stats = {
            'total_functions': len(call_trees),
            'functions_with_upstream': 0,
            'functions_with_downstream': 0,
            'max_upstream_count': 0,
            'max_downstream_count': 0,
            'isolated_functions': 0
        }
        
        for tree in call_trees:
            upstream_count = tree.get('upstream_count', 0)
            downstream_count = tree.get('downstream_count', 0)
            
            if upstream_count > 0:
                stats['functions_with_upstream'] += 1
                stats['max_upstream_count'] = max(stats['max_upstream_count'], upstream_count)
            
            if downstream_count > 0:
                stats['functions_with_downstream'] += 1
                stats['max_downstream_count'] = max(stats['max_downstream_count'], downstream_count)
            
            if upstream_count == 0 and downstream_count == 0:
                stats['isolated_functions'] += 1
        
        return stats
    
    def get_dependency_graph(self, target_function: str, functions_to_check: List[Dict], max_depth: int = 3) -> Dict:
        """获取函数依赖图（高级功能）"""
        if hasattr(self.builder, 'get_dependency_graph'):
            return self.builder.get_dependency_graph(target_function, functions_to_check, max_depth)
        else:
            print("⚠️ 依赖图分析需要高级实现")
            return {'upstream_functions': {}, 'downstream_functions': {}}
    
    def get_builder_info(self) -> Dict:
        """获取构建器信息"""
        return {
            'type': self.builder_type,
            'advanced_available': ADVANCED_BUILDER_AVAILABLE,
            'features': {
                'basic_call_trees': True,
                'dependency_graph': hasattr(self.builder, 'get_dependency_graph'),
                'visualization': hasattr(self.builder, 'visualize_dependency_graph'),
                'mermaid_export': hasattr(self.builder, 'generate_dependency_mermaid')
            }
        }


# 向后兼容的别名
CallTreeBuilder = TreeSitterCallTreeBuilder


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
    
    print("🧪 测试智能调用树构建器...")
    
    builder = TreeSitterCallTreeBuilder()
    builder_info = builder.get_builder_info()
    
    print(f"📊 构建器信息:")
    print(f"  类型: {builder_info['type']}")
    print(f"  高级功能可用: {builder_info['advanced_available']}")
    print(f"  支持的功能: {builder_info['features']}")
    
    call_trees = builder.build_call_trees(test_functions)
    
    print(f"\n✅ 构建了 {len(call_trees)} 个调用树")
    for tree in call_trees:
        print(f"\n📊 函数: {tree['function_name']}")
        print(f"  上游调用数: {tree['upstream_count']}")
        print(f"  下游调用数: {tree['downstream_count']}")
        
        if 'analyzer_type' in tree:
            print(f"  分析器类型: {tree['analyzer_type']}")
    
    # 测试依赖图功能
    if builder_info['features']['dependency_graph']:
        print(f"\n🔍 测试依赖图分析...")
        dep_graph = builder.get_dependency_graph('transfer', test_functions)
        print(f"  上游函数: {list(dep_graph['upstream_functions'].keys())}")
        print(f"  下游函数: {list(dep_graph['downstream_functions'].keys())}")
    
    print("\n🎉 测试完成") 