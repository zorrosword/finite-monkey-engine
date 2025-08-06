#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据结构模块
定义了多语言分析器使用的所有数据结构和枚举类型
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class LanguageType(Enum):
    """支持的编程语言类型"""
    SOLIDITY = "solidity"
    RUST = "rust"
    CPP = "cpp"
    MOVE = "move"
    GO = "go"


class CallType(Enum):
    """调用类型"""
    DIRECT = "direct"              # 直接函数调用
    VIRTUAL = "virtual"            # 虚函数调用 (C++)
    ASYNC = "async"                # 异步调用 (Rust)
    EXTERNAL = "external"          # 外部合约调用 (Solidity)
    ENTRY = "entry"                # 入口函数调用 (Move)
    TRAIT = "trait"                # Trait方法调用 (Rust)
    MACRO = "macro"                # 宏调用 (Rust)
    CONSTRUCTOR = "constructor"    # 构造函数调用
    MODIFIER = "modifier"          # 修饰符调用 (Solidity)


@dataclass
class FunctionInfo:
    """增强的函数信息"""
    name: str
    full_name: str
    language: LanguageType
    
    # 通用属性
    visibility: str = "private"
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    calls: List[str] = field(default_factory=list)
    line_number: int = 0
    
    # 语言特定属性
    is_async: bool = False          # Rust
    is_unsafe: bool = False         # Rust
    is_virtual: bool = False        # C++
    is_pure_virtual: bool = False   # C++
    is_override: bool = False       # C++
    is_entry: bool = False          # Move
    is_native: bool = False         # Move
    is_payable: bool = False        # Solidity
    is_view: bool = False           # Solidity
    is_pure: bool = False           # Solidity
    
    # 高级属性
    modifiers: List[str] = field(default_factory=list)      # Solidity修饰符
    acquires: List[str] = field(default_factory=list)       # Move acquires
    generic_params: List[str] = field(default_factory=list) # 泛型参数
    
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StructInfo:
    """增强的结构体/类信息"""
    name: str
    full_name: str
    language: LanguageType
    
    # 通用属性
    fields: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    line_number: int = 0
    
    # 语言特定属性
    base_classes: List[str] = field(default_factory=list)   # C++基类
    abilities: List[str] = field(default_factory=list)      # Move abilities
    is_interface: bool = False                               # Solidity接口
    is_abstract: bool = False                                # C++抽象类
    is_template: bool = False                                # C++模板
    derives: List[str] = field(default_factory=list)        # Rust derives
    
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleInfo:
    """增强的模块信息"""
    name: str
    full_name: str
    language: LanguageType
    
    # 内容
    functions: List[FunctionInfo] = field(default_factory=list)
    structs: List[StructInfo] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    line_number: int = 0
    
    # 语言特定属性
    inheritance: List[str] = field(default_factory=list)    # Solidity contracts
    address: Optional[str] = None                            # Move modules
    is_library: bool = False                                 # Solidity
    namespace_type: Optional[str] = None                     # C++ namespaces
    
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CallGraphEdge:
    """调用图边信息"""
    caller: str
    callee: str
    call_type: CallType = CallType.DIRECT
    language: Optional[LanguageType] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisStats:
    """分析统计信息"""
    language: LanguageType
    modules_count: int = 0
    functions_count: int = 0
    structs_count: int = 0
    call_relationships: int = 0
    language_specific_features: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'language': self.language.value,
            'modules_count': self.modules_count,
            'functions_count': self.functions_count,
            'structs_count': self.structs_count,
            'call_relationships': self.call_relationships,
            'language_specific_features': self.language_specific_features
        } 