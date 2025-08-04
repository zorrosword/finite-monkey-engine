#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基础解析器模块
定义了通用的AST解析逻辑和接口
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

from tree_sitter import Language, Parser
import tree_sitter_solidity as ts_solidity
import tree_sitter_rust as ts_rust
import tree_sitter_cpp as ts_cpp
import tree_sitter_move as ts_move

from .data_structures import (
    LanguageType, CallType, FunctionInfo, StructInfo, 
    ModuleInfo, CallGraphEdge, AnalysisStats
)
from .language_configs import get_language_config, LanguageConfig


class BaseParser(ABC):
    """基础解析器抽象类"""
    
    def __init__(self, language: LanguageType):
        self.language = language
        self.config = get_language_config(language)
        self.parser = self._initialize_parser()
        
        # 解析结果存储
        self.modules: Dict[str, ModuleInfo] = {}
        self.functions: Dict[str, FunctionInfo] = {}
        self.structs: Dict[str, StructInfo] = {}
        self.call_graph: List[CallGraphEdge] = []
    
    def _initialize_parser(self) -> Parser:
        """初始化Tree-sitter解析器"""
        parser = Parser()
        
        # 根据语言类型设置对应的解析器
        if self.language == LanguageType.SOLIDITY:
            language = Language(ts_solidity.language())
        elif self.language == LanguageType.RUST:
            language = Language(ts_rust.language())
        elif self.language == LanguageType.CPP:
            language = Language(ts_cpp.language())
        elif self.language == LanguageType.MOVE:
            language = Language(ts_move.language())
        else:
            raise ValueError(f"Unsupported language: {self.language}")
        
        # 使用正确的API设置语言
        parser.language = language
        return parser
    
    def parse_code(self, code: str, filename: str = "unknown") -> None:
        """解析代码字符串"""
        if not code.strip():
            return
        
        # 不要清理之前的结果，让结果累积
        # self.clear_results()
        
        try:
            # 解析AST
            tree = self.parser.parse(bytes(code, "utf8"))
            lines = code.split('\n')
            
            # 提取语言特定的结构
            self.extract_structures(tree.root_node, lines, filename)
            
            # 生成调用图
            self.generate_call_graph()
            
        except Exception as e:
            print(f"解析代码时出错 ({filename}): {e}")
    
    def parse_file(self, file_path: str) -> None:
        """解析文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            self.parse_code(code, file_path)
        except Exception as e:
            print(f"读取文件时出错 ({file_path}): {e}")
    
    def parse_directory(self, directory_path: str) -> None:
        """解析目录中的所有文件"""
        directory = Path(directory_path)
        if not directory.exists():
            print(f"目录不存在: {directory_path}")
            return
        
        # 不要清理之前的结果，让结果累积
        # self.clear_results()
        
        # 遍历所有相关文件
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix in self.config.file_extensions:
                self.parse_file(str(file_path))
    
    def clear_results(self) -> None:
        """清理解析结果"""
        self.modules.clear()
        self.functions.clear()
        self.structs.clear()
        self.call_graph.clear()
    
    @abstractmethod
    def extract_structures(self, node, lines: List[str], context: str) -> None:
        """提取语言特定的结构（抽象方法）"""
        pass
    
    def get_node_text(self, node, lines: List[str]) -> str:
        """获取节点对应的源代码文本"""
        start_row, start_col = node.start_point
        end_row, end_col = node.end_point
        
        if start_row == end_row:
            return lines[start_row][start_col:end_col]
        
        result = lines[start_row][start_col:]
        for row in range(start_row + 1, end_row):
            result += '\n' + lines[row]
        result += '\n' + lines[end_row][:end_col]
        
        return result
    
    def extract_function_calls(self, node, func_info: FunctionInfo, lines: List[str]) -> None:
        """提取函数调用关系"""
        for child in node.children:
            if child.type in self.config.call_expression_types:
                call_name = self.resolve_function_call(child, lines)
                if call_name and call_name not in func_info.calls:
                    func_info.calls.append(call_name)
            
            # 递归处理子节点
            self.extract_function_calls(child, func_info, lines)
    
    def resolve_function_call(self, call_node, lines: List[str]) -> Optional[str]:
        """解析函数调用名称"""
        # 通用实现，子类可以重写
        for child in call_node.children:
            if child.type == 'identifier':
                return self.get_node_text(child, lines)
            elif child.type == 'field_expression' or child.type == 'member_expression':
                # 处理成员调用，如 obj.method()
                return self.get_node_text(child, lines)
        
        return None
    
    def generate_call_graph(self) -> None:
        """生成调用图"""
        self.call_graph.clear()
        
        for func_name, func_info in self.functions.items():
            for call in func_info.calls:
                # 解析被调用函数的完整名称
                callee_full_name = self.resolve_callee_name(call, func_info)
                
                # 创建调用边
                edge = CallGraphEdge(
                    caller=func_name,
                    callee=callee_full_name,
                    call_type=self.determine_call_type(func_info, call),
                    language=self.language
                )
                
                self.call_graph.append(edge)
    
    def resolve_callee_name(self, call: str, caller_info: FunctionInfo) -> str:
        """解析被调用函数的完整名称"""
        # 基础实现，子类可以重写
        if call in self.functions:
            return call
        
        # 尝试在同一模块中查找
        caller_parts = caller_info.full_name.split(self.config.separator)
        if len(caller_parts) > 1:
            module_prefix = self.config.separator.join(caller_parts[:-1])
            potential_name = f"{module_prefix}{self.config.separator}{call}"
            if potential_name in self.functions:
                return potential_name
        
        return call
    
    def determine_call_type(self, caller_info: FunctionInfo, call: str) -> CallType:
        """确定调用类型"""
        # 基础实现，子类可以重写
        return CallType.DIRECT
    
    def get_statistics(self) -> AnalysisStats:
        """获取统计信息"""
        stats = AnalysisStats(language=self.language)
        stats.modules_count = len(self.modules)
        stats.functions_count = len(self.functions)
        stats.structs_count = len(self.structs)
        stats.call_relationships = len(self.call_graph)
        
        # 计算语言特定特性
        stats.language_specific_features = self.calculate_language_features()
        
        return stats
    
    @abstractmethod
    def calculate_language_features(self) -> Dict[str, int]:
        """计算语言特定特性（抽象方法）"""
        pass
    
    def get_modules(self) -> Dict[str, ModuleInfo]:
        """获取所有模块"""
        return self.modules.copy()
    
    def get_functions(self) -> Dict[str, FunctionInfo]:
        """获取所有函数"""
        return self.functions.copy()
    
    def get_structs(self) -> Dict[str, StructInfo]:
        """获取所有结构体"""
        return self.structs.copy()
    
    def get_call_graph(self) -> List[CallGraphEdge]:
        """获取调用图"""
        return self.call_graph.copy()
    
    def get_function_by_name(self, name: str) -> Optional[FunctionInfo]:
        """根据名称获取函数信息"""
        return self.functions.get(name)
    
    def get_callers(self, function_name: str) -> List[str]:
        """获取调用指定函数的函数列表"""
        callers = []
        for edge in self.call_graph:
            if edge.callee == function_name:
                callers.append(edge.caller)
        return callers
    
    def get_callees(self, function_name: str) -> List[str]:
        """获取指定函数调用的函数列表"""
        callees = []
        for edge in self.call_graph:
            if edge.caller == function_name:
                callees.append(edge.callee)
        return callees 