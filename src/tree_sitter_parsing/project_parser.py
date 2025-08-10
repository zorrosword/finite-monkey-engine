#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tree-sitter Based Project Parser
使用tree-sitter替代ANTLR进行项目解析
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys

# 使用安装的tree-sitter包
from tree_sitter import Language, Parser, Node
import tree_sitter_solidity
import tree_sitter_rust
import tree_sitter_cpp
import tree_sitter_move
import tree_sitter_go

# 导入文档分块器
try:
    from .document_chunker import chunk_project_files
    from .chunk_config import ChunkConfigManager
except ImportError:
    # 如果相对导入失败，尝试直接导入
    from document_chunker import chunk_project_files
    from chunk_config import ChunkConfigManager

# 创建语言对象
LANGUAGES = {
    'solidity': Language(tree_sitter_solidity.language()),
    'rust': Language(tree_sitter_rust.language()),
    'cpp': Language(tree_sitter_cpp.language()),
    'move': Language(tree_sitter_move.language()),
    'go': Language(tree_sitter_go.language())
}

TREE_SITTER_AVAILABLE = True
print("✅ Tree-sitter解析器已加载，支持五种语言")


class LanguageType:
    SOLIDITY = 'solidity'
    RUST = 'rust'
    CPP = 'cpp'
    MOVE = 'move'
    GO = 'go'


class TreeSitterProjectFilter(object):
    """基于tree-sitter的项目过滤器"""
    
    def __init__(self):
        pass

    def filter_file(self, path, filename):
        """过滤文件"""
        # 检查文件后缀 - 支持五种语言：Solidity, Rust, C++, Move, Go
        valid_extensions = ('.sol', '.rs', '.move', '.c', '.cpp', '.cxx', '.cc', '.C', '.h', '.hpp', '.hxx', '.go')
        if not any(filename.endswith(ext) for ext in valid_extensions) or filename.endswith('.t.sol'):
            return True
        
        return False

    def filter_contract(self, function):
        """过滤合约函数"""
        # 支持的语言不进行筛选：rust, move, cpp
        # 检查文件扩展名或函数名特征来识别语言类型
        file_path = function.get('file_path', '')
        if file_path:
            if file_path.endswith('.rs'):  # Rust文件
                return False
            if file_path.endswith('.move'):  # Move文件
                return False
            if file_path.endswith(('.c', '.cpp', '.cxx', '.cc', '.C', '.h', '.hpp', '.hxx')):  # C++文件
                return False
        
        # 兼容旧的命名方式
        if '_rust' in function["name"]:
            return False
        if '_move' in function["name"]:
            return False
        if '_cpp' in function["name"]:
            return False
        
        # 过滤构造函数和接收函数
        if function.get('visibility') in ['constructor', 'receive', 'fallback']:
            return True
        
        return False

    def should_check_function_code_if_statevar_assign(self, function_code, contract_code):
        """检查函数代码中是否应该进行状态变量赋值检查"""
        return True

    def check_function_code_if_statevar_assign(self, function_code, contract_code):
        """检查函数代码中的状态变量赋值"""
        return self.should_check_function_code_if_statevar_assign(function_code, contract_code)


def _detect_language_from_path(file_path: Path) -> Optional[str]:
    """根据文件路径检测语言类型"""
    suffix = file_path.suffix.lower()
    
    if suffix == '.sol':
        return 'solidity'
    elif suffix == '.rs':
        return 'rust'
    elif suffix in ['.cpp', '.cc', '.cxx', '.c', '.h', '.hpp', '.hxx']:
        return 'cpp'
    elif suffix == '.move':
        return 'move'
    elif suffix == '.go':
        return 'go'
    return None


def _extract_functions_from_node(node: Node, source_code: bytes, language: str, file_path: str) -> List[Dict]:
    """从AST节点中提取函数信息"""
    functions = []
    
    def traverse_node(node, contract_name=""):
        if node.type == 'function_definition' and language == 'solidity':
            # Solidity函数定义
            func_info = _parse_solidity_function(node, source_code, contract_name, file_path)
            if func_info:
                functions.append(func_info)
        
        elif node.type == 'function_item' and language == 'rust':
            # Rust函数定义
            func_info = _parse_rust_function(node, source_code, file_path)
            if func_info:
                functions.append(func_info)
        
        elif node.type == 'function_definition' and language == 'cpp':
            # C++函数定义
            func_info = _parse_cpp_function(node, source_code, file_path)
            if func_info:
                functions.append(func_info)
        
        elif node.type == 'function_definition' and language == 'move':
            # Move函数定义
            func_info = _parse_move_function(node, source_code, file_path)
            if func_info:
                functions.append(func_info)
        
        elif node.type == 'function_declaration' and language == 'go':
            # Go函数定义
            func_info = _parse_go_function(node, source_code, file_path)
            if func_info:
                functions.append(func_info)
        
        elif node.type == 'contract_declaration' and language == 'solidity':
            # Solidity合约声明
            contract_name = _get_node_text(node.child_by_field_name('name'), source_code)
        
        # 递归遍历子节点
        for child in node.children:
            traverse_node(child, contract_name)
    
    traverse_node(node)
    return functions


def _get_node_text(node: Node, source_code: bytes) -> str:
    """获取节点对应的源代码文本"""
    if node is None:
        return ""
    return source_code[node.start_byte:node.end_byte].decode('utf-8')


def _extract_function_calls(node: Node, source_code: bytes) -> List[str]:
    """从函数节点中提取函数调用"""
    calls = []
    
    def traverse_for_calls(node):
        if node.type == 'call_expression':
            # 获取被调用的函数名
            called_func = _get_function_call_name(node, source_code)
            if called_func:
                calls.append(called_func)
        
        # 递归遍历子节点
        for child in node.children:
            traverse_for_calls(child)
    
    traverse_for_calls(node)
    return calls


def _get_function_call_name(call_node: Node, source_code: bytes) -> Optional[str]:
    """从call_expression节点中提取被调用的函数名"""
    try:
        # 遍历call_expression的子节点查找函数名
        for child in call_node.children:
            # Rust: scoped_identifier (如 instructions::borrow)
            if child.type == 'scoped_identifier':
                scoped_text = _get_node_text(child, source_code).strip()
                # 将 Rust 模块调用转换为我们的命名格式
                # instructions::withdraw -> withdraw.withdraw
                if '::' in scoped_text:
                    parts = scoped_text.split('::')
                    if len(parts) >= 2:
                        module_name = parts[-2]  # instructions
                        func_name = parts[-1]    # withdraw
                        # 对于 instructions 模块，函数名就是文件名
                        if module_name == 'instructions':
                            return f"{func_name}.{func_name}"
                        else:
                            return f"{module_name}.{func_name}"
                return scoped_text  # 保留原始名称作为备选
            # Rust: identifier (如 simple_function_call)
            elif child.type == 'identifier':
                return _get_node_text(child, source_code).strip()
            # Rust: field_expression (如 obj.method)
            elif child.type == 'field_expression':
                field_text = _get_node_text(child, source_code).strip()
                return field_text
            # Solidity: expression
            elif child.type == 'expression':
                # 在expression中查找实际的函数名
                for expr_child in child.children:
                    if expr_child.type == 'identifier':
                        # 简单函数调用，如: functionName()
                        return _get_node_text(expr_child, source_code).strip()
                    elif expr_child.type == 'member_expression':
                        # 成员函数调用，如: obj.method()
                        member_text = _get_node_text(expr_child, source_code).strip()
                        if '.' in member_text:
                            return member_text.split('.')[-1]  # 返回方法名
                        return member_text
            # Solidity: member_expression（作为备选方案）
            elif child.type == 'member_expression':
                member_text = _get_node_text(child, source_code).strip()
                if '.' in member_text:
                    return member_text.split('.')[-1]
                return member_text
        return None
    except Exception:
        return None


def _parse_solidity_function(node: Node, source_code: bytes, contract_name: str, file_path: str) -> Optional[Dict]:
    """解析Solidity函数"""
    try:
        name_node = node.child_by_field_name('name')
        if not name_node:
            return None
        
        func_name = _get_node_text(name_node, source_code)
        func_content = _get_node_text(node, source_code)
        
        # 提取可见性
        visibility = 'public'  # 默认
        for child in node.children:
            if child.type == 'visibility':
                # 在visibility节点的children中查找具体的可见性关键字
                for vis_child in child.children:
                    if vis_child.type in ['public', 'private', 'internal', 'external']:
                        visibility = vis_child.type
                        break
                break
        
        # 提取修饰符和参数
        modifiers = []
        parameters = []
        return_type = ''
        
        for child in node.children:
            if child.type == 'modifier_invocation':
                # 解析修饰符
                modifier_name = _get_node_text(child, source_code).strip()
                if modifier_name:
                    modifiers.append(modifier_name)
            elif child.type == 'parameter':
                # 解析参数
                param_text = _get_node_text(child, source_code).strip()
                if param_text:
                    parameters.append(param_text)
            elif child.type == 'return_type_definition':
                # 解析返回类型
                return_type = _get_node_text(child, source_code).strip().replace('returns', '').strip().strip('(').strip(')')
        
        # 提取函数调用
        function_calls = _extract_function_calls(node, source_code)
        
        return {
            'name': f"{contract_name}.{func_name}" if contract_name else func_name,
            'contract_name': contract_name,
            'content': func_content,
            'signature': func_content.split('{')[0].strip() if '{' in func_content else func_content,
            'visibility': visibility,
            'modifiers': modifiers,
            'parameters': parameters,
            'return_type': return_type,
            'calls': function_calls,
            'line_number': node.start_point[0] + 1,
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
            'file_path': file_path,
            'relative_file_path': os.path.relpath(file_path) if file_path else '',
            'absolute_file_path': os.path.abspath(file_path) if file_path else '',
            'type': 'FunctionDefinition'
        }
    except Exception as e:
        print(f"解析Solidity函数失败: {e}")
        return None


def _parse_rust_function(node: Node, source_code: bytes, file_path: str) -> Optional[Dict]:
    """解析Rust函数"""
    try:
        name_node = node.child_by_field_name('name')
        if not name_node:
            return None
        
        func_name = _get_node_text(name_node, source_code)
        func_content = _get_node_text(node, source_code)
        
        # 从文件路径提取文件名（不包含扩展名）
        import os
        file_name = os.path.splitext(os.path.basename(file_path))[0] if file_path else 'unknown'
        
        # 提取可见性修饰符
        visibility = 'private'  # Rust默认为私有
        modifiers = []
        parameters = []
        return_type = ''
        
        for child in node.children:
            if child.type == 'visibility_modifier':
                # Rust可见性：pub, pub(crate), pub(super), pub(in path)
                vis_text = _get_node_text(child, source_code).strip()
                if vis_text.startswith('pub'):
                    visibility = 'public'
                    if '(' in vis_text:  # pub(crate), pub(super) etc.
                        modifiers.append(vis_text)
            elif child.type == 'parameters':
                # 解析参数列表
                param_text = _get_node_text(child, source_code).strip().strip('(').strip(')')
                if param_text:
                    # 简单分割参数（可以进一步优化）
                    params = [p.strip() for p in param_text.split(',') if p.strip()]
                    parameters.extend(params)
            elif child.type in ['type', 'primitive_type', 'generic_type']:
                # 可能是返回类型
                return_type = _get_node_text(child, source_code).strip()
        
        # 检查是否有返回类型箭头
        if '->' in func_content:
            return_part = func_content.split('->')[1].split('{')[0].strip() if '{' in func_content else func_content.split('->')[1].strip()
            if return_part:
                return_type = return_part
        
        # 提取函数调用
        function_calls = _extract_function_calls(node, source_code)
        
        return {
            'name': f"{file_name}.{func_name}",  # 修改为 文件名.函数名 格式
            'contract_name': file_name,  # 修改为文件名
            'content': func_content,
            'signature': func_content.split('{')[0].strip() if '{' in func_content else func_content,
            'visibility': visibility,
            'modifiers': modifiers,
            'parameters': parameters,
            'return_type': return_type,
            'calls': function_calls,
            'line_number': node.start_point[0] + 1,
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
            'file_path': file_path,
            'relative_file_path': os.path.relpath(file_path) if file_path else '',
            'absolute_file_path': os.path.abspath(file_path) if file_path else '',
            'type': 'FunctionDefinition'
        }
    except Exception as e:
        print(f"解析Rust函数失败: {e}")
        return None


def _parse_cpp_function(node: Node, source_code: bytes, file_path: str) -> Optional[Dict]:
    """解析C++函数"""
    try:
        declarator = node.child_by_field_name('declarator')
        if not declarator:
            return None
        
        # 提取函数名（从 declarator 中提取）
        func_name = ''
        if declarator.type == 'function_declarator':
            name_node = declarator.child_by_field_name('declarator')
            if name_node:
                func_name = _get_node_text(name_node, source_code).strip()
        else:
            func_name = _get_node_text(declarator, source_code).strip()
        
        # 如果仍然没有名称，尝试其他方法
        if not func_name or '(' in func_name:
            func_name = func_name.split('(')[0].strip() if '(' in func_name else func_name
        
        func_content = _get_node_text(node, source_code)
        
        # 提取返回类型、可见性和修饰符
        visibility = 'public'  # C++默认公有（在class中可能不同）
        modifiers = []
        parameters = []
        return_type = ''
        
        # 提取返回类型
        type_node = node.child_by_field_name('type')
        if type_node:
            return_type = _get_node_text(type_node, source_code).strip()
        
        # 提取参数
        if declarator.type == 'function_declarator':
            params_node = declarator.child_by_field_name('parameters')
            if params_node:
                param_text = _get_node_text(params_node, source_code).strip().strip('(').strip(')')
                if param_text and param_text != 'void':
                    # 简单分割参数
                    params = [p.strip() for p in param_text.split(',') if p.strip() and p.strip() != 'void']
                    parameters.extend(params)
        
        # 检查修饰符（static, const, virtual, override 等）
        for child in node.children:
            if child.type in ['storage_class_specifier', 'type_qualifier']:
                modifier_text = _get_node_text(child, source_code).strip()
                if modifier_text in ['static', 'const', 'virtual', 'override', 'final', 'inline']:
                    modifiers.append(modifier_text)
        
        # 检查声明中的const修饰符
        if 'const' in func_content and func_content.count('const') > len([m for m in modifiers if m == 'const']):
            if 'const' not in modifiers:
                modifiers.append('const')
        
        # 提取函数调用
        function_calls = _extract_function_calls(node, source_code)
        
        return {
            'name': f"_cpp.{func_name}",
            'contract_name': 'CppModule',
            'content': func_content,
            'signature': func_content.split('{')[0].strip() if '{' in func_content else func_content,
            'visibility': visibility,
            'modifiers': modifiers,
            'parameters': parameters,
            'return_type': return_type,
            'calls': function_calls,
            'line_number': node.start_point[0] + 1,
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
            'file_path': file_path,
            'relative_file_path': os.path.relpath(file_path) if file_path else '',
            'absolute_file_path': os.path.abspath(file_path) if file_path else '',
            'type': 'FunctionDefinition'
        }
    except Exception as e:
        print(f"解析C++函数失败: {e}")
        return None


def _parse_move_function(node: Node, source_code: bytes, file_path: str) -> Optional[Dict]:
    """解析Move函数"""
    try:
        name_node = node.child_by_field_name('name')
        if not name_node:
            return None
        
        func_name = _get_node_text(name_node, source_code)
        func_content = _get_node_text(node, source_code)
        
        # 提取可见性、修饰符、参数和返回类型
        visibility = 'private'  # Move默认为私有
        modifiers = []
        parameters = []
        return_type = ''
        
        for child in node.children:
            if child.type == 'visibility':
                # Move可见性：public, public(script), public(friend)
                vis_text = _get_node_text(child, source_code).strip()
                if vis_text.startswith('public'):
                    visibility = 'public'
                    if '(' in vis_text:  # public(script), public(friend)
                        modifiers.append(vis_text)
            elif child.type == 'ability':
                # Move特有的 ability
                ability_text = _get_node_text(child, source_code).strip()
                modifiers.append(ability_text)
            elif child.type == 'parameters':
                # 解析参数列表
                param_text = _get_node_text(child, source_code).strip().strip('(').strip(')')
                if param_text:
                    # 简单分割参数
                    params = [p.strip() for p in param_text.split(',') if p.strip()]
                    parameters.extend(params)
            elif child.type in ['type', 'primitive_type', 'struct_type']:
                # 可能是返回类型
                return_type = _get_node_text(child, source_code).strip()
        
        # 检查是否有返回类型冒号
        if ':' in func_content and '{' in func_content:
            # 尝试提取 : 和 { 之间的返回类型
            try:
                colon_part = func_content.split(':')[1].split('{')[0].strip()
                if colon_part and not return_type:
                    return_type = colon_part
            except:
                pass
        
        # 检查native修饰符
        if 'native' in func_content:
            modifiers.append('native')
        
        # 提取函数调用
        function_calls = _extract_function_calls(node, source_code)
        
        return {
            'name': f"_move.{func_name}",
            'contract_name': 'MoveModule',
            'content': func_content,
            'signature': func_content.split('{')[0].strip() if '{' in func_content else func_content,
            'visibility': visibility,
            'modifiers': modifiers,
            'parameters': parameters,
            'return_type': return_type,
            'calls': function_calls,
            'line_number': node.start_point[0] + 1,
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
            'file_path': file_path,
            'relative_file_path': os.path.relpath(file_path) if file_path else '',
            'absolute_file_path': os.path.abspath(file_path) if file_path else '',
            'type': 'FunctionDefinition'
        }
    except Exception as e:
        print(f"解析Move函数失败: {e}")
        return None


def _parse_go_function(node: Node, source_code: bytes, file_path: str) -> Optional[Dict]:
    """解析Go函数"""
    try:
        name_node = node.child_by_field_name('name')
        if not name_node:
            return None
        
        func_name = _get_node_text(name_node, source_code)
        func_content = _get_node_text(node, source_code)
        
        # 提取可见性、修饰符、参数和返回类型
        visibility = 'private'  # Go默认为私有
        modifiers = []
        parameters = []
        return_type = ''
        
        # Go语言的可见性是基于首字母大小写
        if func_name and func_name[0].isupper():
            visibility = 'public'
        
        # 遍历子节点提取参数和返回类型
        for child in node.children:
            if child.type == 'parameter_list':
                # 解析参数列表
                param_text = _get_node_text(child, source_code).strip().strip('(').strip(')')
                if param_text:
                    # 简单分割参数
                    params = [p.strip() for p in param_text.split(',') if p.strip()]
                    parameters.extend(params)
            elif child.type in ['type_identifier', 'pointer_type', 'slice_type', 'array_type']:
                # 可能是返回类型
                return_type = _get_node_text(child, source_code).strip()
        
        # 检查是否为方法（receiver）
        receiver_node = node.child_by_field_name('receiver')
        if receiver_node:
            receiver_text = _get_node_text(receiver_node, source_code).strip()
            modifiers.append(f"method:{receiver_text}")
        
        # 提取函数调用
        function_calls = _extract_function_calls(node, source_code)
        
        return {
            'name': f"_go.{func_name}",
            'contract_name': 'GoPackage',
            'content': func_content,
            'signature': func_content.split('{')[0].strip() if '{' in func_content else func_content,
            'visibility': visibility,
            'modifiers': modifiers,
            'parameters': parameters,
            'return_type': return_type,
            'calls': function_calls,
            'line_number': node.start_point[0] + 1,
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
            'file_path': file_path,
            'relative_file_path': os.path.relpath(file_path) if file_path else '',
            'absolute_file_path': os.path.abspath(file_path) if file_path else '',
            'type': 'FunctionDefinition'
        }
    except Exception as e:
        print(f"解析Go函数失败: {e}")
        return None


def parse_project(project_path, project_filter=None):
    """
    使用tree-sitter解析项目
    保持与原始parse_project函数相同的接口，并添加文档分块功能
    """
    if project_filter is None:
        project_filter = TreeSitterProjectFilter([], [])

    ignore_folders = set()
    if os.environ.get('IGNORE_FOLDERS'):
        ignore_folders = set(os.environ.get('IGNORE_FOLDERS').split(','))
    ignore_folders.add('.git')

    all_results = []
    all_file_paths = []  # 收集所有文件路径用于分块

    # 遍历项目目录
    for dirpath, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in ignore_folders]
        for file in files:
            file_path = os.path.join(dirpath, file)
            
            # 收集所有文件路径（不分后缀名）用于分块
            all_file_paths.append(file_path)
            
            # 应用文件过滤（仅用于函数解析）
            to_scan = not project_filter.filter_file(dirpath, file)
            print("parsing file: ", file_path, " " if to_scan else "[skipped]")

            if to_scan:
                # 检测语言类型
                language = _detect_language_from_path(Path(file))
                if language:
                    try:
                        # 使用tree-sitter分析文件
                        with open(file_path, 'rb') as f:
                            source_code = f.read()
                        
                        parser = Parser()
                        parser.language = LANGUAGES[language]  # 修正API调用
                        
                        tree = parser.parse(source_code)
                        functions = _extract_functions_from_node(tree.root_node, source_code, language, file_path)
                        
                        all_results.extend(functions)
                        
                        if functions:
                            print(f"  -> 解析到 {len(functions)} 个函数")
                                
                    except Exception as e:
                        print(f"⚠️  解析文件失败 {file_path}: {e}")
                        continue

    # 过滤函数
    functions = [result for result in all_results if result['type'] == 'FunctionDefinition']
    
    # 应用函数过滤
    functions_to_check = []
    for function in functions:
        if not project_filter.filter_contract(function):
            functions_to_check.append(function)

    print(f"📊 解析完成: 总函数 {len(functions)} 个，待检查 {len(functions_to_check)} 个")
    
    # 对项目中的所有文件进行分块（不分后缀名）
    print("🧩 开始对项目文件进行分块...")
    
    # 获取分块配置 - 项目解析默认使用代码项目配置
    config = ChunkConfigManager.get_config('code_project')
    print(f"📋 使用配置: code_project")
    
    # 处理文件分块
    chunks = chunk_project_files(all_file_paths, config=config)
    
    print(f"✅ 分块完成: 共生成 {len(chunks)} 个文档块")
    
    # 输出分块统计信息
    if chunks:
        chunk_stats = {}
        for chunk in chunks:
            ext = chunk.metadata.get('file_extension', 'unknown') if hasattr(chunk, 'metadata') else 'unknown'
            chunk_stats[ext] = chunk_stats.get(ext, 0) + 1
        
        print("📊 分块统计:")
        for ext, count in sorted(chunk_stats.items()):
            ext_display = ext if ext else '[无扩展名]'
            print(f"  - {ext_display}: {count} 个块")
    
    return functions, functions_to_check, chunks


if __name__ == "__main__":
    # 简单测试
    print("🧪 测试Tree-sitter项目解析器...")
    
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试文件
        test_file = os.path.join(temp_dir, 'test.sol')
        with open(test_file, 'w') as f:
            f.write("""
pragma solidity ^0.8.0;

contract TestContract {
    uint256 public balance;
    
    function deposit() public payable {
        balance += msg.value;
    }
    
    function withdraw(uint256 amount) public {
        require(balance >= amount, "Insufficient balance");
        balance -= amount;
        payable(msg.sender).transfer(amount);
    }
}
""")
        
        # 测试解析
        functions, functions_to_check = parse_project(temp_dir)
        print(f"✅ 找到 {len(functions)} 个函数，{len(functions_to_check)} 个需要检查")
        
        if functions_to_check:
            for func in functions_to_check:
                print(f"  - {func['name']} ({func['visibility']})")
        
    print("✅ 测试完成")