#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Solidity语言解析器
专门处理Solidity智能合约的AST解析和调用图生成
"""

from typing import Dict, List, Optional, Any

from ..base_parser import BaseParser
from ..data_structures import (
    LanguageType, CallType, FunctionInfo, StructInfo, ModuleInfo
)


class SolidityParser(BaseParser):
    """Solidity语言解析器"""
    
    def __init__(self):
        super().__init__(LanguageType.SOLIDITY)
    
    def extract_structures(self, node, lines: List[str], context: str) -> None:
        """提取Solidity结构"""
        for child in node.children:
            if child.type in self.config.module_types:
                module_info = self.extract_solidity_module(child, lines, context)
                if module_info:
                    self.modules[module_info.full_name] = module_info
            else:
                self.extract_structures(child, lines, context)
    
    def extract_solidity_module(self, node, lines: List[str], file_context: str) -> Optional[ModuleInfo]:
        """提取Solidity合约/库/接口"""
        module_name = None
        module_type = node.type
        
        # 提取名称
        for child in node.children:
            if child.type == 'identifier':
                module_name = self.get_node_text(child, lines)
                break
        
        if not module_name:
            return None
        
        module_info = ModuleInfo(
            name=module_name,
            full_name=f"{file_context}.{module_name}",
            language=LanguageType.SOLIDITY,
            line_number=node.start_point.row + 1,
            is_library=(module_type == 'library_definition')
        )
        
        # 提取继承关系
        self.extract_inheritance(node, module_info, lines)
        
        # 提取模块内容
        for child in node.children:
            if child.type == 'contract_body' or child.type == 'library_body' or child.type == 'interface_body':
                self.extract_module_body(child, module_info, lines)
        
        return module_info
    
    def extract_inheritance(self, contract_node, module_info: ModuleInfo, lines: List[str]) -> None:
        """提取继承关系"""
        for child in contract_node.children:
            if child.type == 'inheritance_specifier':
                for grandchild in child.children:
                    if grandchild.type == 'identifier' or grandchild.type == 'user_defined_type_name':
                        base_name = self.get_node_text(grandchild, lines)
                        module_info.inheritance.append(base_name)
    
    def extract_module_body(self, body_node, module_info: ModuleInfo, lines: List[str]) -> None:
        """提取模块体内容"""
        for child in body_node.children:
            if child.type in self.config.function_types:
                func_info = self.extract_solidity_function(child, lines, module_info.full_name)
                if func_info:
                    module_info.functions.append(func_info)
                    self.functions[func_info.full_name] = func_info
            elif child.type in self.config.struct_types:
                struct_info = self.extract_solidity_struct(child, lines, module_info.full_name)
                if struct_info:
                    module_info.structs.append(struct_info)
                    self.structs[struct_info.full_name] = struct_info
    
    def extract_solidity_function(self, node, lines: List[str], module_context: str) -> Optional[FunctionInfo]:
        """提取Solidity函数"""
        func_name = None
        
        # 提取函数名
        for child in node.children:
            if child.type == 'identifier':
                func_name = self.get_node_text(child, lines)
                break
        
        if not func_name:
            if node.type == 'constructor_definition':
                func_name = 'constructor'
            else:
                return None
        
        func_text = self.get_node_text(node, lines)
        
        # 提取可见性
        visibility = self.extract_visibility(node, lines)
        
        # 提取Solidity特定属性
        is_payable = 'payable' in func_text
        is_view = 'view' in func_text
        is_pure = 'pure' in func_text
        
        # 提取修饰符
        modifiers = self.extract_modifiers(node, lines)
        
        func_info = FunctionInfo(
            name=func_name,
            full_name=f"{module_context}.{func_name}",
            language=LanguageType.SOLIDITY,
            visibility=visibility,
            is_payable=is_payable,
            is_view=is_view,
            is_pure=is_pure,
            modifiers=modifiers,
            line_number=node.start_point.row + 1
        )
        
        # 提取函数调用
        self.extract_function_calls(node, func_info, lines)
        
        return func_info
    
    def extract_visibility(self, node, lines: List[str]) -> str:
        """提取可见性"""
        func_text = self.get_node_text(node, lines)
        
        for visibility in ['external', 'public', 'internal', 'private']:
            if visibility in func_text:
                return visibility
        
        return 'internal'  # Solidity默认可见性
    
    def extract_modifiers(self, node, lines: List[str]) -> List[str]:
        """提取函数修饰符"""
        modifiers = []
        
        for child in node.children:
            if child.type == 'modifier_invocation':
                for grandchild in child.children:
                    if grandchild.type == 'identifier':
                        modifier_name = self.get_node_text(grandchild, lines)
                        modifiers.append(modifier_name)
        
        return modifiers
    
    def extract_solidity_struct(self, node, lines: List[str], module_context: str) -> Optional[StructInfo]:
        """提取Solidity结构体"""
        struct_name = None
        
        for child in node.children:
            if child.type == 'identifier':
                struct_name = self.get_node_text(child, lines)
                break
        
        if not struct_name:
            return None
        
        struct_info = StructInfo(
            name=struct_name,
            full_name=f"{module_context}.{struct_name}",
            language=LanguageType.SOLIDITY,
            line_number=node.start_point.row + 1
        )
        
        # 提取字段
        for child in node.children:
            if child.type == 'struct_member':
                field_name = self.extract_struct_field_name(child, lines)
                if field_name:
                    struct_info.fields.append(field_name)
        
        return struct_info
    
    def extract_struct_field_name(self, member_node, lines: List[str]) -> Optional[str]:
        """提取结构体字段名"""
        for child in member_node.children:
            if child.type == 'identifier':
                return self.get_node_text(child, lines)
        return None
    
    def resolve_function_call(self, call_node, lines: List[str]) -> Optional[str]:
        """解析Solidity函数调用"""
        if call_node.type == 'call_expression':
            # 查找被调用的函数名 - 通常是第一个expression子节点
            for child in call_node.children:
                if child.type == 'expression':
                    # 在expression节点中查找identifier或member_expression
                    for grandchild in child.children:
                        if grandchild.type == 'identifier':
                            return self.get_node_text(grandchild, lines)
                        elif grandchild.type == 'member_expression':
                            # 处理成员调用，如 obj.method()
                            member_text = self.get_node_text(grandchild, lines)
                            if '.' in member_text:
                                return member_text.split('.')[-1]  # 返回方法名
                            return member_text
                # 也处理直接的identifier（兼容性）
                elif child.type == 'identifier':
                    return self.get_node_text(child, lines)
                elif child.type == 'member_expression':
                    # 处理成员调用，如 obj.method()
                    member_text = self.get_node_text(child, lines)
                    if '.' in member_text:
                        return member_text.split('.')[-1]  # 返回方法名
                    return member_text
        
        return None
    
    def determine_call_type(self, caller_info: FunctionInfo, call: str) -> CallType:
        """确定Solidity调用类型"""
        # 检查是否为修饰符调用
        if call in caller_info.modifiers:
            return CallType.MODIFIER
        
        # 检查是否为外部调用（通过地址或合约实例）
        if '(' in call or '.' in call:
            return CallType.EXTERNAL
        
        return CallType.DIRECT
    
    def calculate_language_features(self) -> Dict[str, int]:
        """计算Solidity特定特性"""
        features = {
            'contracts': 0,
            'libraries': 0,
            'interfaces': 0,
            'payable_functions': 0,
            'view_functions': 0,
            'pure_functions': 0,
            'functions_with_modifiers': 0
        }
        
        # 统计模块类型
        for module in self.modules.values():
            if module.is_library:
                features['libraries'] += 1
            else:
                features['contracts'] += 1
        
        # 统计函数特性
        for func in self.functions.values():
            if func.is_payable:
                features['payable_functions'] += 1
            if func.is_view:
                features['view_functions'] += 1
            if func.is_pure:
                features['pure_functions'] += 1
            if func.modifiers:
                features['functions_with_modifiers'] += 1
        
        return features 