#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rust语言解析器
专门处理Rust代码的AST解析和调用图生成
"""

from typing import Dict, List, Optional, Any

from ..base_parser import BaseParser
from ..data_structures import (
    LanguageType, CallType, FunctionInfo, StructInfo, ModuleInfo
)


class RustParser(BaseParser):
    """Rust语言解析器"""
    
    def __init__(self):
        super().__init__(LanguageType.RUST)
    
    def extract_structures(self, node, lines: List[str], context: str) -> None:
        """提取Rust结构"""
        for child in node.children:
            if child.type in self.config.function_types:
                func_info = self.extract_rust_function(child, lines, context)
                if func_info:
                    self.functions[func_info.full_name] = func_info
            elif child.type in self.config.struct_types:
                struct_info = self.extract_rust_struct(child, lines, context)
                if struct_info:
                    self.structs[struct_info.full_name] = struct_info
            elif child.type in self.config.module_types:
                module_info = self.extract_rust_module(child, lines, context)
                if module_info:
                    self.modules[module_info.full_name] = module_info
            else:
                self.extract_structures(child, lines, context)
    
    def extract_rust_function(self, node, lines: List[str], file_context: str) -> Optional[FunctionInfo]:
        """提取Rust函数"""
        func_name = None
        
        # 提取函数名
        for child in node.children:
            if child.type == 'identifier':
                func_name = self.get_node_text(child, lines)
                break
        
        if not func_name:
            return None
        
        func_text = self.get_node_text(node, lines)
        
        # 提取可见性
        visibility = 'private'
        if 'pub' in func_text:
            visibility = 'public'
        
        # 提取Rust特定属性
        is_async = 'async' in func_text
        is_unsafe = 'unsafe' in func_text
        
        func_info = FunctionInfo(
            name=func_name,
            full_name=f"{file_context}::{func_name}",
            language=LanguageType.RUST,
            visibility=visibility,
            is_async=is_async,
            is_unsafe=is_unsafe,
            line_number=node.start_point.row + 1
        )
        
        # 提取函数调用
        self.extract_function_calls(node, func_info, lines)
        
        return func_info
    
    def extract_rust_struct(self, node, lines: List[str], file_context: str) -> Optional[StructInfo]:
        """提取Rust结构体"""
        struct_name = None
        
        for child in node.children:
            if child.type == 'type_identifier':
                struct_name = self.get_node_text(child, lines)
                break
        
        if not struct_name:
            return None
        
        struct_text = self.get_node_text(node, lines)
        
        # 提取derives
        derives = []
        if '#[derive(' in struct_text:
            start = struct_text.find('#[derive(') + 9
            end = struct_text.find(')]', start)
            if end > start:
                derive_content = struct_text[start:end]
                derives = [d.strip() for d in derive_content.split(',')]
        
        struct_info = StructInfo(
            name=struct_name,
            full_name=f"{file_context}::{struct_name}",
            language=LanguageType.RUST,
            derives=derives,
            line_number=node.start_point.row + 1
        )
        
        return struct_info
    
    def extract_rust_module(self, node, lines: List[str], file_context: str) -> Optional[ModuleInfo]:
        """提取Rust模块"""
        module_name = None
        
        for child in node.children:
            if child.type == 'identifier':
                module_name = self.get_node_text(child, lines)
                break
        
        if not module_name:
            return None
        
        module_info = ModuleInfo(
            name=module_name,
            full_name=f"{file_context}::{module_name}",
            language=LanguageType.RUST,
            line_number=node.start_point.row + 1
        )
        
        return module_info
    
    def resolve_function_call(self, call_node, lines: List[str]) -> Optional[str]:
        """解析Rust函数调用"""
        if call_node.type == 'call_expression':
            for child in call_node.children:
                if child.type == 'identifier':
                    return self.get_node_text(child, lines)
                elif child.type == 'field_expression':
                    # 处理方法调用，如 obj.method()
                    field_text = self.get_node_text(child, lines)
                    if '.' in field_text:
                        return field_text.split('.')[-1]
                    return field_text
                elif child.type == 'scoped_identifier':
                    # 处理路径调用，如 std::io::println!
                    return self.get_node_text(child, lines)
        elif call_node.type == 'macro_invocation':
            # 处理宏调用
            for child in call_node.children:
                if child.type == 'identifier':
                    macro_name = self.get_node_text(child, lines)
                    return f"{macro_name}!"
        
        return None
    
    def determine_call_type(self, caller_info: FunctionInfo, call: str) -> CallType:
        """确定Rust调用类型"""
        # 检查是否为异步调用
        if caller_info.is_async and '.await' in call:
            return CallType.ASYNC
        
        # 检查是否为宏调用
        if call.endswith('!'):
            return CallType.MACRO
        
        # 检查是否为trait方法调用
        if '::' in call:
            return CallType.TRAIT
        
        return CallType.DIRECT
    
    def calculate_language_features(self) -> Dict[str, int]:
        """计算Rust特定特性"""
        features = {
            'async_functions': 0,
            'unsafe_functions': 0,
            'public_functions': 0,
            'structs_with_derives': 0
        }
        
        # 统计函数特性
        for func in self.functions.values():
            if func.is_async:
                features['async_functions'] += 1
            if func.is_unsafe:
                features['unsafe_functions'] += 1
            if func.visibility == 'public':
                features['public_functions'] += 1
        
        # 统计结构体特性
        for struct in self.structs.values():
            if struct.derives:
                features['structs_with_derives'] += 1
        
        return features 