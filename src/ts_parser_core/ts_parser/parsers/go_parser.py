#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Go语言解析器
专门处理Go代码的AST解析和调用图生成
"""

from typing import Dict, List, Optional, Any

from ..base_parser import BaseParser
from ..data_structures import (
    LanguageType, CallType, FunctionInfo, StructInfo, ModuleInfo
)


class GoParser(BaseParser):
    """Go语言解析器"""
    
    def __init__(self):
        super().__init__(LanguageType.GO)
    
    def extract_structures(self, node, lines: List[str], context: str) -> None:
        """提取Go结构"""
        for child in node.children:
            if child.type in self.config.function_types:
                func_info = self.extract_go_function(child, lines, context)
                if func_info:
                    self.functions[func_info.full_name] = func_info
            elif child.type in self.config.struct_types:
                struct_info = self.extract_go_struct(child, lines, context)
                if struct_info:
                    self.structs[struct_info.full_name] = struct_info
            elif child.type in self.config.module_types:
                module_info = self.extract_go_package(child, lines, context)
                if module_info:
                    self.modules[module_info.full_name] = module_info
            else:
                self.extract_structures(child, lines, context)
    
    def extract_go_function(self, node, lines: List[str], file_context: str) -> Optional[FunctionInfo]:
        """提取Go函数"""
        func_name = None
        
        # 提取函数名
        for child in node.children:
            if child.type == 'identifier':
                func_name = self.get_node_text(child, lines)
                break
        
        if not func_name:
            return None
        
        # 创建函数完整名称
        full_name = f"{file_context}.{func_name}" if file_context else func_name
        
        # 创建函数信息对象
        func_info = FunctionInfo(
            name=func_name,
            full_name=full_name,
            language=LanguageType.GO,
            line_number=node.start_point[0] + 1
        )
        
        # 确定可见性 (Go中大写开头表示public)
        if func_name and func_name[0].isupper():
            func_info.visibility = "public"
        else:
            func_info.visibility = "private"
        
        # 提取参数和返回类型
        self.extract_go_function_signature(node, lines, func_info)
        
        # 提取函数调用
        self.extract_function_calls(node, lines, func_info)
        
        return func_info
    
    def extract_go_function_signature(self, node, lines: List[str], func_info: FunctionInfo) -> None:
        """提取Go函数签名"""
        for child in node.children:
            if child.type == 'parameter_list':
                # 提取参数
                for param_child in child.children:
                    if param_child.type == 'parameter_declaration':
                        param_text = self.get_node_text(param_child, lines)
                        if param_text:
                            func_info.parameters.append(param_text)
            elif child.type == 'type_identifier' and not func_info.return_type:
                # 简单返回类型
                func_info.return_type = self.get_node_text(child, lines)
            elif child.type == 'type_spec':
                # 复杂返回类型
                func_info.return_type = self.get_node_text(child, lines)
    
    def extract_go_struct(self, node, lines: List[str], file_context: str) -> Optional[StructInfo]:
        """提取Go结构体"""
        struct_name = None
        
        # Go的type_declaration包含多种类型，需要找到struct
        for child in node.children:
            if child.type == 'type_spec':
                for spec_child in child.children:
                    if spec_child.type == 'type_identifier':
                        struct_name = self.get_node_text(spec_child, lines)
                    elif spec_child.type == 'struct_type':
                        # 这是一个结构体声明
                        if struct_name:
                            full_name = f"{file_context}.{struct_name}" if file_context else struct_name
                            
                            struct_info = StructInfo(
                                name=struct_name,
                                full_name=full_name,
                                language=LanguageType.GO,
                                line_number=node.start_point[0] + 1
                            )
                            
                            # 提取字段
                            self.extract_go_struct_fields(spec_child, lines, struct_info)
                            
                            return struct_info
        
        return None
    
    def extract_go_struct_fields(self, struct_node, lines: List[str], struct_info: StructInfo) -> None:
        """提取Go结构体字段"""
        for child in struct_node.children:
            if child.type == 'field_declaration_list':
                for field_child in child.children:
                    if field_child.type == 'field_declaration':
                        field_text = self.get_node_text(field_child, lines)
                        if field_text:
                            struct_info.fields.append(field_text)
    
    def extract_go_package(self, node, lines: List[str], file_context: str) -> Optional[ModuleInfo]:
        """提取Go包信息"""
        package_name = None
        
        for child in node.children:
            if child.type == 'package_identifier':
                package_name = self.get_node_text(child, lines)
                break
        
        if not package_name:
            return None
        
        module_info = ModuleInfo(
            name=package_name,
            full_name=package_name,
            language=LanguageType.GO,
            line_number=node.start_point[0] + 1
        )
        
        return module_info
    
    def extract_function_calls(self, node, lines: List[str], func_info: FunctionInfo) -> None:
        """提取Go函数调用"""
        for child in node.children:
            call = self.extract_call_from_node(child, lines)
            if call and call not in func_info.calls:
                func_info.calls.append(call)
            # 递归处理子节点
            self.extract_function_calls(child, lines, func_info)
    
    def extract_call_from_node(self, node, lines: List[str]) -> Optional[str]:
        """从节点提取调用信息"""
        if node.type in self.config.call_expression_types:
            return self.extract_go_call(node, lines)
        return None
    
    def extract_go_call(self, call_node, lines: List[str]) -> Optional[str]:
        """提取Go函数调用"""
        function_name = None
        
        for child in call_node.children:
            if child.type == 'identifier':
                function_name = self.get_node_text(child, lines)
                break
            elif child.type == 'selector_expression':
                # 处理 package.Function() 或 obj.Method() 调用
                selector_text = self.get_node_text(child, lines)
                if selector_text:
                    return selector_text
        
        return function_name
    
    def determine_call_type(self, caller_info: FunctionInfo, call: str) -> CallType:
        """确定Go调用类型"""
        # 检查是否为go routine调用
        if call.startswith('go '):
            return CallType.ASYNC
        
        # 检查是否为方法调用
        if '.' in call:
            return CallType.VIRTUAL
        
        return CallType.DIRECT
    
    def calculate_language_features(self) -> Dict[str, int]:
        """计算Go特定特性"""
        features = {
            'public_functions': 0,
            'private_functions': 0,
            'public_structs': 0,
            'private_structs': 0,
            'method_calls': 0
        }
        
        # 统计函数特性
        for func in self.functions.values():
            if func.visibility == 'public':
                features['public_functions'] += 1
            else:
                features['private_functions'] += 1
            
            # 统计方法调用
            for call in func.calls:
                if '.' in call:
                    features['method_calls'] += 1
        
        # 统计结构体特性
        for struct in self.structs.values():
            if struct.name and struct.name[0].isupper():
                features['public_structs'] += 1
            else:
                features['private_structs'] += 1
        
        return features