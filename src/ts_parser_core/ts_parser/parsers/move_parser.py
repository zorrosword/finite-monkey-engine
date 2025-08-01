#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Move语言解析器
专门处理Move代码的AST解析和调用图生成
"""

from typing import Dict, List, Optional, Any

from ..base_parser import BaseParser
from ..data_structures import (
    LanguageType, CallType, FunctionInfo, StructInfo, ModuleInfo
)


class MoveParser(BaseParser):
    """Move语言解析器"""
    
    def __init__(self):
        super().__init__(LanguageType.MOVE)
    
    def extract_structures(self, node, lines: List[str], context: str) -> None:
        """提取Move结构"""
        for child in node.children:
            if child.type in self.config.module_types:
                module_info = self.extract_move_module(child, lines, context)
                if module_info:
                    self.modules[module_info.full_name] = module_info
            else:
                self.extract_structures(child, lines, context)
    
    def extract_move_module(self, node, lines: List[str], file_context: str) -> Optional[ModuleInfo]:
        """提取Move模块"""
        module_name = None
        address = None
        
        # 提取模块名和地址
        for child in node.children:
            if child.type == 'identifier':
                module_name = self.get_node_text(child, lines)
            elif child.type == 'numerical_addr':
                address = self.get_node_text(child, lines)
        
        if not module_name:
            return None
        
        module_info = ModuleInfo(
            name=module_name,
            full_name=f"{file_context}::{address}::{module_name}" if address else f"{file_context}::{module_name}",
            language=LanguageType.MOVE,
            address=address,
            line_number=node.start_point.row + 1
        )
        
        # 提取模块内容
        for child in node.children:
            if child.type == 'declaration':
                self.extract_move_declaration(child, lines, module_info)
        
        return module_info
    
    def extract_move_declaration(self, node, lines: List[str], module_info: ModuleInfo) -> None:
        """提取Move声明"""
        for child in node.children:
            if child.type in self.config.function_types:
                func_info = self.extract_move_function(child, lines, module_info.full_name)
                if func_info:
                    module_info.functions.append(func_info)
                    self.functions[func_info.full_name] = func_info
            elif child.type in self.config.struct_types:
                struct_info = self.extract_move_struct(child, lines, module_info.full_name)
                if struct_info:
                    module_info.structs.append(struct_info)
                    self.structs[struct_info.full_name] = struct_info
    
    def extract_move_function(self, node, lines: List[str], module_context: str) -> Optional[FunctionInfo]:
        """提取Move函数"""
        func_name = None
        
        for child in node.children:
            if child.type == 'identifier':
                func_name = self.get_node_text(child, lines)
                break
        
        if not func_name:
            return None
        
        func_text = self.get_node_text(node, lines)
        
        # 检查修饰符
        is_public = 'public' in func_text
        is_entry = 'entry' in func_text
        is_native = 'native' in func_text
        
        # 提取acquires
        acquires = []
        if 'acquires' in func_text:
            # 简单提取逻辑
            parts = func_text.split('acquires')
            if len(parts) > 1:
                acquire_part = parts[1].split('{')[0].strip()
                if acquire_part:
                    acquires = [part.strip() for part in acquire_part.split(',')]
        
        visibility = 'entry' if is_entry else ('public' if is_public else 'private')
        
        func_info = FunctionInfo(
            name=func_name,
            full_name=f"{module_context}::{func_name}",
            language=LanguageType.MOVE,
            visibility=visibility,
            is_entry=is_entry,
            is_native=is_native,
            acquires=acquires,
            line_number=node.start_point.row + 1
        )
        
        # 提取函数调用
        self.extract_function_calls(node, func_info, lines)
        
        return func_info
    
    def extract_move_struct(self, node, lines: List[str], module_context: str) -> Optional[StructInfo]:
        """提取Move结构体"""
        struct_name = None
        
        for child in node.children:
            if child.type == 'identifier':
                struct_name = self.get_node_text(child, lines)
                break
        
        if not struct_name:
            return None
        
        struct_text = self.get_node_text(node, lines)
        
        # 提取abilities
        abilities = []
        if 'has key' in struct_text:
            abilities.append('key')
        if 'has store' in struct_text:
            abilities.append('store')
        if 'has copy' in struct_text:
            abilities.append('copy')
        if 'has drop' in struct_text:
            abilities.append('drop')
        
        struct_info = StructInfo(
            name=struct_name,
            full_name=f"{module_context}::{struct_name}",
            language=LanguageType.MOVE,
            abilities=abilities,
            line_number=node.start_point.row + 1
        )
        
        return struct_info
    
    def determine_call_type(self, caller_info: FunctionInfo, call: str) -> CallType:
        """确定Move调用类型"""
        # 检查是否为entry函数调用
        if caller_info.is_entry:
            return CallType.ENTRY
        
        return CallType.DIRECT
    
    def calculate_language_features(self) -> Dict[str, int]:
        """计算Move特定特性"""
        features = {
            'entry_functions': 0,
            'native_functions': 0,
            'functions_with_acquires': 0,
            'structs_with_abilities': 0
        }
        
        # 统计函数特性
        for func in self.functions.values():
            if func.is_entry:
                features['entry_functions'] += 1
            if func.is_native:
                features['native_functions'] += 1
            if func.acquires:
                features['functions_with_acquires'] += 1
        
        # 统计结构体特性
        for struct in self.structs.values():
            if struct.abilities:
                features['structs_with_abilities'] += 1
        
        return features 