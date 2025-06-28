"""
漏洞扫描模块

此模块负责智能合约的漏洞扫描功能，包括：
- 代码扫描
- 对话模式扫描
- 扫描结果处理
"""

from .scanner import VulnerabilityScanner
from .utils.dialogue_manager import DialogueHistory

__all__ = ['VulnerabilityScanner', 'DialogueHistory'] 