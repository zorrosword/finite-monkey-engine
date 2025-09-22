"""
调用树工具模块

提供函数调用树相关的工具函数，包括：
- 获取下游函数内容
- 获取上游函数内容
- 深度提取下游函数
- 简化的下游内容获取
"""

from typing import List, Dict, Optional, Set


class CallTreeUtils:
    """调用树工具类"""
    
    def __init__(self, project_audit):
        """
        初始化调用树工具
        
        Args:
            project_audit: TreeSitterProjectAudit实例，包含解析后的项目数据
        """
        self.project_audit = project_audit
        self.call_trees = project_audit.call_trees
        self.functions_to_check = project_audit.functions_to_check
    
    def extract_downstream_to_deepest(self, func_name: str, visited: Set[str] = None, depth: int = 0, max_depth: int = 10) -> List[Dict]:
        """深度提取某个函数的所有下游函数到最深层
        
        Args:
            func_name: 起始函数名
            visited: 已访问的函数集合（避免循环）
            depth: 当前深度
            max_depth: 最大深度限制
            
        Returns:
            List[Dict]: 下游函数链表，包含深度信息
        """
        if visited is None:
            visited = set()
        
        if func_name in visited or depth > max_depth:
            return []
        
        visited.add(func_name)
        downstream_chain = []
        
        # 使用新的调用树格式查找当前函数的下游函数
        for call_tree in self.call_trees:
            # 使用完整的函数名匹配，适配新的 filename.function_name 格式
            if call_tree.get('function_name') == func_name:
                relationships = call_tree.get('relationships', {})
                downstream_funcs = relationships.get('downstream', {}).get(func_name, set())
                
                for downstream_func in downstream_funcs:
                    # 找到下游函数的完整信息
                    for func in self.functions_to_check:
                        if func['name'] == downstream_func:
                            downstream_info = {
                                'function': func,
                                'depth': depth + 1,
                                'parent': func_name
                            }
                            downstream_chain.append(downstream_info)
                            
                            # 递归获取更深层的下游函数
                            deeper_downstream = self.extract_downstream_to_deepest(
                                func['name'], visited.copy(), depth + 1, max_depth
                            )
                            downstream_chain.extend(deeper_downstream)
                            break
                break
        
        return downstream_chain

    def get_downstream_content_with_call_tree(self, func_name: str, max_depth: int = 5) -> str:
        """使用call tree获取函数的downstream内容（使用统一的提取逻辑）
        
        Args:
            func_name: 函数名
            max_depth: 最大深度
            
        Returns:
            str: 拼接的downstream内容
        """
        if hasattr(self.project_audit, 'call_trees') and self.project_audit.call_trees:
            try:
                from tree_sitter_parsing.advanced_call_tree_builder import AdvancedCallTreeBuilder
                builder = AdvancedCallTreeBuilder()
                # 使用统一的内容提取方法
                return builder.get_call_content_with_direction(
                    self.project_audit.call_trees, func_name, 'downstream', max_depth
                )
            except Exception as e:
                print(f"    ⚠️ 使用统一call tree提取失败: {e}，使用简化方法")
                contents = self._get_downstream_content_fallback(func_name, max_depth)
                return '\n\n'.join(contents)
        else:
            contents = self._get_downstream_content_fallback(func_name, max_depth)
            return '\n\n'.join(contents)
    
    def get_upstream_content_with_call_tree(self, func_name: str, max_depth: int = 5) -> str:
        """使用call tree获取函数的upstream内容（使用统一的提取逻辑）
        
        Args:
            func_name: 函数名
            max_depth: 最大深度
            
        Returns:
            str: 拼接的upstream内容
        """
        if hasattr(self.project_audit, 'call_trees') and self.project_audit.call_trees:
            try:
                from tree_sitter_parsing.advanced_call_tree_builder import AdvancedCallTreeBuilder
                builder = AdvancedCallTreeBuilder()
                # 使用统一的内容提取方法
                return builder.get_call_content_with_direction(
                    self.project_audit.call_trees, func_name, 'upstream', max_depth
                )
            except Exception as e:
                print(f"    ⚠️ 使用统一call tree提取upstream失败: {e}")
                return ""
        else:
            return ""
        
    def _get_downstream_content_fallback(self, func_name: str, max_depth: int) -> List[str]:
        """简化的downstream内容获取方法"""
        downstream_chain = self.extract_downstream_to_deepest(func_name)
        contents = []
        
        for item in downstream_chain:
            if item.get('depth', 0) <= max_depth:
                function = item.get('function')
                if function and function.get('content'):
                    contents.append(function['content'])
        
        return contents


# 便捷函数，用于创建CallTreeUtils实例
def create_call_tree_utils(project_audit) -> CallTreeUtils:
    """创建CallTreeUtils实例的便捷函数"""
    return CallTreeUtils(project_audit)


# 便捷函数，用于直接调用功能
def extract_downstream_to_deepest(project_audit, func_name: str, visited: Set[str] = None, depth: int = 0, max_depth: int = 10) -> List[Dict]:
    """深度提取下游函数的便捷函数"""
    utils = CallTreeUtils(project_audit)
    return utils.extract_downstream_to_deepest(func_name, visited, depth, max_depth)


def get_downstream_content_with_call_tree(project_audit, func_name: str, max_depth: int = 5) -> str:
    """获取下游内容的便捷函数"""
    utils = CallTreeUtils(project_audit)
    return utils.get_downstream_content_with_call_tree(func_name, max_depth)


def get_upstream_content_with_call_tree(project_audit, func_name: str, max_depth: int = 5) -> str:
    """获取上游内容的便捷函数"""
    utils = CallTreeUtils(project_audit)
    return utils.get_upstream_content_with_call_tree(func_name, max_depth)
