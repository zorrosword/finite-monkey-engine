#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
C++语言解析器
专门处理C++代码的AST解析和调用图生成
"""

from typing import Dict, List, Optional, Any

from ..base_parser import BaseParser
from ..data_structures import (
    LanguageType, CallType, FunctionInfo, StructInfo, ModuleInfo
)


class CppParser(BaseParser):
    """C++语言解析器"""
    
    def __init__(self):
        super().__init__(LanguageType.CPP)
    
    def extract_structures(self, node, lines: List[str], context: str) -> None:
        """提取C++结构"""
        for child in node.children:
            if child.type in self.config.function_types:
                func_info = self.extract_cpp_function(child, lines, context)
                if func_info:
                    self.functions[func_info.full_name] = func_info
            elif child.type in self.config.struct_types:
                struct_info = self.extract_cpp_struct(child, lines, context)
                if struct_info:
                    self.structs[struct_info.full_name] = struct_info
            elif child.type in self.config.module_types:
                module_info = self.extract_cpp_namespace(child, lines, context)
                if module_info:
                    self.modules[module_info.full_name] = module_info
                
                # 无论命名空间提取是否成功，都要递归处理其子节点
                self.extract_structures(child, lines, context)
            elif child.type == "declaration_list":
                # 处理声明列表（如命名空间内的声明）
                self.extract_structures(child, lines, context)
            else:
                # 递归处理其他节点
                self.extract_structures(child, lines, context)
    
    def extract_cpp_function(self, node, lines: List[str], file_context: str) -> Optional[FunctionInfo]:
        """提取C++函数"""
        func_name = None
        
        # 查找函数声明器
        declarator = self.find_function_declarator(node)
        if declarator:
            # 尝试多种方式获取函数名
            func_name = self.extract_function_name_from_declarator(declarator, lines)
        
        if not func_name:
            return None
        
        func_text = self.get_node_text(node, lines)
        
        # 提取可见性
        visibility = self.extract_cpp_visibility(node, lines)
        
        # 提取C++特定属性
        is_virtual = 'virtual' in func_text
        is_override = 'override' in func_text
        is_pure_virtual = '= 0' in func_text
        
        func_info = FunctionInfo(
            name=func_name,
            full_name=f"{file_context}::{func_name}",
            language=LanguageType.CPP,
            visibility=visibility,
            is_virtual=is_virtual,
            is_override=is_override,
            is_pure_virtual=is_pure_virtual,
            line_number=node.start_point.row + 1
        )
        
        # 提取函数调用
        self.extract_function_calls(node, func_info, lines)
        
        return func_info
    
    def find_function_declarator(self, node):
        """查找函数声明器"""
        for child in node.children:
            if child.type == 'function_declarator':
                return child
        return node
    
    def extract_function_name_from_declarator(self, declarator, lines: List[str]) -> Optional[str]:
        """从函数声明器中提取函数名"""
        # 方法1: 查找identifier
        for child in declarator.children:
            if child.type == 'identifier':
                return self.get_node_text(child, lines)
        
        # 方法2: 查找qualified_identifier
        for child in declarator.children:
            if child.type == 'qualified_identifier':
                # 获取限定标识符的最后一个部分作为函数名
                parts = []
                self.collect_identifier_parts(child, parts, lines)
                if parts:
                    return parts[-1]  # 返回最后一个部分作为函数名
        
        # 方法3: 查找field_identifier
        for child in declarator.children:
            if child.type == 'field_identifier':
                return self.get_node_text(child, lines)
        
        return None
    
    def collect_identifier_parts(self, node, parts: List[str], lines: List[str]) -> None:
        """收集标识符的各个部分"""
        for child in node.children:
            if child.type == 'identifier':
                parts.append(self.get_node_text(child, lines))
            elif child.type == 'qualified_identifier':
                self.collect_identifier_parts(child, parts, lines)
    
    def extract_cpp_visibility(self, node, lines: List[str]) -> str:
        """提取C++可见性"""
        # 简化实现，实际需要分析类上下文
        return 'public'
    
    def extract_cpp_struct(self, node, lines: List[str], file_context: str) -> Optional[StructInfo]:
        """提取C++类/结构体"""
        struct_name = None
        
        for child in node.children:
            if child.type == 'type_identifier':
                struct_name = self.get_node_text(child, lines)
                break
        
        if not struct_name:
            return None
        
        # 提取基类
        base_classes = self.extract_base_classes(node, lines)
        
        struct_info = StructInfo(
            name=struct_name,
            full_name=f"{file_context}::{struct_name}",
            language=LanguageType.CPP,
            base_classes=base_classes,
            line_number=node.start_point.row + 1
        )
        
        return struct_info
    
    def extract_base_classes(self, class_node, lines: List[str]) -> List[str]:
        """提取基类"""
        base_classes = []
        
        for child in class_node.children:
            if child.type == 'base_class_clause':
                for grandchild in child.children:
                    if grandchild.type == 'type_identifier':
                        base_name = self.get_node_text(grandchild, lines)
                        base_classes.append(base_name)
        
        return base_classes
    
    def extract_cpp_namespace(self, node, lines: List[str], file_context: str) -> Optional[ModuleInfo]:
        """提取C++命名空间"""
        namespace_name = None
        
        for child in node.children:
            if child.type == 'identifier':
                namespace_name = self.get_node_text(child, lines)
                break
        
        if not namespace_name:
            return None
        
        module_info = ModuleInfo(
            name=namespace_name,
            full_name=f"{file_context}::{namespace_name}",
            language=LanguageType.CPP,
            namespace_type='namespace',
            line_number=node.start_point.row + 1
        )
        
        return module_info
    
    def calculate_language_features(self) -> Dict[str, int]:
        """计算C++特定特性"""
        features = {
            'virtual_functions': 0,
            'override_functions': 0,
            'pure_virtual_functions': 0,
            'classes_with_inheritance': 0
        }
        
        # 统计函数特性
        for func in self.functions.values():
            if func.is_virtual:
                features['virtual_functions'] += 1
            if func.is_override:
                features['override_functions'] += 1
            if func.is_pure_virtual:
                features['pure_virtual_functions'] += 1
        
        # 统计类继承
        for struct in self.structs.values():
            if struct.base_classes:
                features['classes_with_inheritance'] += 1
        
        return features 