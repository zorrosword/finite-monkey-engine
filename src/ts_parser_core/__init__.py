#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tree-sitter多语言代码分析器包
支持 Solidity、Rust、C++、Move 四种语言的 AST 解析和 Call Graph 分析
"""

from .ts_parser import *

print("✅ Tree-sitter解析器已加载，支持四种语言")

__all__ = [
    'LanguageType', 'CallType',
    'FunctionInfo', 'StructInfo', 'ModuleInfo', 'CallGraphEdge',
    'LanguageConfig', 'get_language_config',
    'MultiLanguageAnalyzer'
] 