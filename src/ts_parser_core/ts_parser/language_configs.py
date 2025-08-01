#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语言配置模块
定义了各种编程语言的解析配置和特定规则
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set
from .data_structures import LanguageType


@dataclass
class LanguageConfig:
    """语言配置类"""
    language: LanguageType
    file_extensions: List[str]
    separator: str  # 命名空间分隔符
    
    # AST节点类型配置
    module_types: List[str]
    function_types: List[str]
    struct_types: List[str]
    class_types: List[str] = field(default_factory=list)
    interface_types: List[str] = field(default_factory=list)
    enum_types: List[str] = field(default_factory=list)
    
    # 可见性关键字
    visibility_keywords: Set[str] = field(default_factory=set)
    
    # 语言特定关键字
    special_keywords: Set[str] = field(default_factory=set)
    
    # 调用表达式类型
    call_expression_types: List[str] = field(default_factory=list)
    
    # 注释符号
    line_comment: str = "//"
    block_comment_start: str = "/*"
    block_comment_end: str = "*/"


# Solidity配置
SOLIDITY_CONFIG = LanguageConfig(
    language=LanguageType.SOLIDITY,
    file_extensions=['.sol'],
    separator='.',
    module_types=['contract_declaration', 'library_declaration', 'interface_declaration'],
    function_types=['function_definition', 'constructor_definition', 'modifier_definition'],
    struct_types=['struct_definition'],
    class_types=['contract_declaration'],
    interface_types=['interface_declaration'],
    enum_types=['enum_definition'],
    visibility_keywords={'public', 'private', 'internal', 'external'},
    special_keywords={'payable', 'view', 'pure', 'override', 'virtual', 'constant'},
    call_expression_types=['call_expression'],
    line_comment='//',
    block_comment_start='/*',
    block_comment_end='*/'
)


# Rust配置
RUST_CONFIG = LanguageConfig(
    language=LanguageType.RUST,
    file_extensions=['.rs'],
    separator='::',
    module_types=['mod_item'],
    function_types=['function_item'],
    struct_types=['struct_item'],
    class_types=[],  # Rust没有类
    interface_types=['trait_item'],
    enum_types=['enum_item'],
    visibility_keywords={'pub', 'crate'},
    special_keywords={'async', 'unsafe', 'const', 'static', 'extern', 'fn', 'impl'},
    call_expression_types=['call_expression', 'method_call_expression', 'macro_invocation'],
    line_comment='//',
    block_comment_start='/*',
    block_comment_end='*/'
)


# C++配置
CPP_CONFIG = LanguageConfig(
    language=LanguageType.CPP,
    file_extensions=['.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx'],
    separator='::',
    module_types=['namespace_definition'],
    function_types=['function_definition', 'function_declarator'],
    struct_types=['struct_specifier', 'class_specifier'],
    class_types=['class_specifier'],
    interface_types=[],  # C++没有专门的接口
    enum_types=['enum_specifier'],
    visibility_keywords={'public', 'private', 'protected'},
    special_keywords={'virtual', 'override', 'const', 'static', 'extern', 'inline', 'explicit'},
    call_expression_types=['call_expression', 'subscript_expression'],
    line_comment='//',
    block_comment_start='/*',
    block_comment_end='*/'
)


# Move配置
MOVE_CONFIG = LanguageConfig(
    language=LanguageType.MOVE,
    file_extensions=['.move'],
    separator='::',
    module_types=['module'],
    function_types=['function_decl'],
    struct_types=['struct_decl'],
    class_types=[],  # Move没有类
    interface_types=[],  # Move没有接口
    enum_types=[],  # Move没有enum
    visibility_keywords={'public', 'entry'},
    special_keywords={'native', 'acquires', 'has', 'key', 'store', 'copy', 'drop'},
    call_expression_types=['call_expression', 'pack_expression'],
    line_comment='//',
    block_comment_start='/*',
    block_comment_end='*/'
)


# 配置映射
LANGUAGE_CONFIGS: Dict[LanguageType, LanguageConfig] = {
    LanguageType.SOLIDITY: SOLIDITY_CONFIG,
    LanguageType.RUST: RUST_CONFIG,
    LanguageType.CPP: CPP_CONFIG,
    LanguageType.MOVE: MOVE_CONFIG,
}


def get_language_config(language: LanguageType) -> LanguageConfig:
    """获取指定语言的配置"""
    return LANGUAGE_CONFIGS[language]


def get_language_by_extension(file_extension: str) -> LanguageType:
    """根据文件扩展名确定语言类型"""
    for language, config in LANGUAGE_CONFIGS.items():
        if file_extension.lower() in config.file_extensions:
            return language
    raise ValueError(f"Unsupported file extension: {file_extension}")


def is_visibility_keyword(language: LanguageType, keyword: str) -> bool:
    """检查是否为可见性关键字"""
    config = get_language_config(language)
    return keyword in config.visibility_keywords


def is_special_keyword(language: LanguageType, keyword: str) -> bool:
    """检查是否为语言特定关键字"""
    config = get_language_config(language)
    return keyword in config.special_keywords 