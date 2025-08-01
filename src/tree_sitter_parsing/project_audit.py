#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tree-sitter Based Project Audit
使用tree-sitter替代ANTLR进行项目审计
"""

import csv
import re
import os
import sys
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from .project_parser import parse_project, TreeSitterProjectFilter
from .call_tree_builder import TreeSitterCallTreeBuilder

# 导入call_graph相关模块
from ts_parser_core import MultiLanguageAnalyzer, LanguageType
from ts_parser_core.ts_parser.data_structures import CallGraphEdge

# 导入日志系统
try:
    from logging_config import get_logger, log_step, log_success, log_warning, log_data_info
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False


class TreeSitterProjectAudit(object):
    """基于tree-sitter的项目审计器"""
    
    def __init__(self, project_id, project_path, db_engine=None):
        self.project_id = project_id
        self.project_path = project_path
        self.db_engine = db_engine  # 可选的数据库引擎
        self.functions = []
        self.functions_to_check = []
        self.tasks = []
        self.taskkeys = set()
        self.call_tree_builder = TreeSitterCallTreeBuilder()
        self.call_trees = []
        
        # 初始化call_graph相关属性
        self.call_graphs = []  # 存储所有语言的call_graph
        self.analyzer = MultiLanguageAnalyzer()
        
        # 初始化日志
        if LOGGING_AVAILABLE:
            self.logger = get_logger(f"ProjectAudit[{project_id}]")
            self.logger.info(f"初始化项目审计器: {project_id}")
            self.logger.info(f"项目路径: {project_path}")
        else:
            self.logger = None

    def print_call_tree(self, node, level=0, prefix=''):
        """打印调用树（代理到CallTreeBuilder）"""
        self.call_tree_builder.print_call_tree(node, level, prefix)

    def parse(self):
        """
        解析项目文件并构建调用树
        """
        if self.logger:
            log_step(self.logger, "创建项目过滤器")
        
        parser_filter = TreeSitterProjectFilter()
        
        if self.logger:
            log_step(self.logger, "开始解析项目文件")
        
        functions, functions_to_check = parse_project(self.project_path, parser_filter)
        self.functions = functions
        self.functions_to_check = functions_to_check
        
        if self.logger:
            log_success(self.logger, "项目文件解析完成")
            log_data_info(self.logger, "总函数数", len(self.functions))
            log_data_info(self.logger, "待检查函数数", len(self.functions_to_check))
        
        # 检查 huge_project 开关，如果为 true 则跳过 call tree 构建
        huge_project = eval(os.environ.get('HUGE_PROJECT', 'False'))
        
        if self.logger:
            self.logger.info(f"HUGE_PROJECT设置: {huge_project}")
        
        if huge_project:
            if self.logger:
                log_warning(self.logger, "检测到 HUGE_PROJECT=True，跳过调用树和调用图构建")
            else:
                print("🚀 检测到 HUGE_PROJECT=True，跳过 call tree 和 call graph 构建")
            self.call_trees = []  # 设置为空列表，避免后续访问出错
            self.call_graphs = []  # 设置为空列表，避免后续访问出错
        else:
            # 使用TreeSitterCallTreeBuilder构建调用树
            if self.logger:
                log_step(self.logger, "开始构建调用树")
            else:
                print("🌳 开始构建调用树...")
                
            self.call_trees = self.call_tree_builder.build_call_trees(functions_to_check, max_workers=1)
            
            if self.logger:
                log_success(self.logger, "调用树构建完成")
                log_data_info(self.logger, "构建的调用树", len(self.call_trees))
            else:
                print(f"✅ 调用树构建完成，共构建 {len(self.call_trees)} 个调用树")
            
            # 构建 call graph
            self._build_call_graphs()

    def get_function_names(self):
        """获取所有函数名称"""
        return set([function['name'] for function in self.functions])
    
    def get_functions_by_contract(self, contract_name):
        """根据合约名获取函数列表"""
        return [func for func in self.functions if func.get('contract_name') == contract_name]
    
    def get_function_by_name(self, function_name):
        """根据函数名获取函数信息"""
        for func in self.functions:
            if func['name'] == function_name:
                return func
        return None
    
    def export_to_csv(self, output_path):
        """导出分析结果到CSV"""
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['name', 'contract', 'visibility', 'line_number', 'file_path', 'modifiers', 'calls_count']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for func in self.functions_to_check:
                writer.writerow({
                    'name': func.get('name', ''),
                    'contract': func.get('contract_name', ''),
                    'visibility': func.get('visibility', ''),
                    'line_number': func.get('line_number', ''),
                    'file_path': func.get('file_path', ''),
                    'modifiers': ', '.join(func.get('modifiers', [])),
                    'calls_count': len(func.get('calls', []))
                })
    
    def _build_call_graphs(self):
        """构建 call graphs（内部方法）"""
        if not self.analyzer:
            if self.logger:
                log_warning(self.logger, "MultiLanguageAnalyzer 不可用，跳过 call graph 构建")
            else:
                print("⚠️ MultiLanguageAnalyzer 不可用，跳过 call graph 构建")
            self.call_graphs = []
            return
        
        if self.logger:
            log_step(self.logger, "开始构建 call graph")
        else:
            print("🔗 开始构建 call graph...")
        
        try:
            # 根据项目路径和函数信息构建 call graph
            language_paths = self._detect_project_languages()
            
            total_call_graphs = []
            
            for language, paths in language_paths.items():
                for project_path in paths:
                    try:
                        if self.logger:
                            self.logger.info(f"分析 {language.value} 项目目录: {project_path}")
                        else:
                            print(f"  📁 分析 {language.value} 项目目录: {project_path}")
                        
                        # 使用MultiLanguageAnalyzer分析整个目录
                        self.analyzer.analyze_directory(project_path, language)
                        
                        # 获取调用图
                        call_graph = self.analyzer.get_call_graph(language)
                        
                        if call_graph:
                            total_call_graphs.extend(call_graph)
                            
                        if self.logger:
                            self.logger.info(f"发现 {len(call_graph)} 个调用关系")
                        else:
                            print(f"  ✅ 发现 {len(call_graph)} 个调用关系")
                            
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"分析目录 {project_path} 失败: {e}")
                        else:
                            print(f"  ⚠️ 分析目录 {project_path} 失败: {e}")
                        continue
            
            self.call_graphs = total_call_graphs
            
            if self.logger:
                log_success(self.logger, "Call graph 构建完成")
                log_data_info(self.logger, "构建的调用关系", len(self.call_graphs))
            else:
                print(f"✅ Call graph 构建完成，共发现 {len(self.call_graphs)} 个调用关系")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Call graph 构建失败: {e}")
            else:
                print(f"❌ Call graph 构建失败: {e}")
            self.call_graphs = []
    
    def _detect_project_languages(self):
        """检测项目中的语言类型"""
        from pathlib import Path
        language_paths = {}
        
        project_path = Path(self.project_path)
        
        # 检测 Solidity 文件
        sol_files = list(project_path.rglob('*.sol'))
        if sol_files:
            language_paths[LanguageType.SOLIDITY] = [str(project_path)]
        
        # 检测 Rust 文件
        rs_files = list(project_path.rglob('*.rs'))
        if rs_files:
            language_paths[LanguageType.RUST] = [str(project_path)]
        
        # 检测 C++ 文件
        cpp_files = list(project_path.rglob('*.cpp')) + list(project_path.rglob('*.cc')) + list(project_path.rglob('*.cxx'))
        if cpp_files:
            language_paths[LanguageType.CPP] = [str(project_path)]
        
        # 检测 Move 文件
        move_files = list(project_path.rglob('*.move'))
        if move_files:
            language_paths[LanguageType.MOVE] = [str(project_path)]
        
        return language_paths
    
    def get_call_graphs(self):
        """获取 call graphs"""
        return self.call_graphs.copy() if self.call_graphs else []
    
    def print_call_graph(self, limit=50):
        """打印 call graph 信息"""
        if not self.call_graphs:
            print("📊 没有 call graph 数据")
            return
        
        print(f"📊 Call Graph 总览 (共 {len(self.call_graphs)} 个调用关系):")
        print("=" * 80)
        
        displayed = 0
        for edge in self.call_graphs:
            if displayed >= limit:
                print(f"... 还有 {len(self.call_graphs) - limit} 个调用关系")
                break
                
            caller_short = edge.caller.split('.')[-1] if '.' in edge.caller else edge.caller
            callee_short = edge.callee.split('.')[-1] if '.' in edge.callee else edge.callee
            
            print(f"➡️  {caller_short} -> {callee_short} [{edge.call_type.value}] ({edge.language.value})")
            displayed += 1
        
        print("=" * 80)
    
    def get_call_graph_statistics(self):
        """获取 call graph 统计信息"""
        if not self.call_graphs:
            return {"total_edges": 0, "languages": {}, "call_types": {}}
        
        stats = {
            "total_edges": len(self.call_graphs),
            "languages": {},
            "call_types": {},
            "unique_functions": set()
        }
        
        for edge in self.call_graphs:
            # 统计语言
            lang = edge.language.value
            stats["languages"][lang] = stats["languages"].get(lang, 0) + 1
            
            # 统计调用类型
            call_type = edge.call_type.value
            stats["call_types"][call_type] = stats["call_types"].get(call_type, 0) + 1
            
            # 统计独特函数
            stats["unique_functions"].add(edge.caller)
            stats["unique_functions"].add(edge.callee)
        
        stats["unique_functions_count"] = len(stats["unique_functions"])
        del stats["unique_functions"]  # 移除set，不需要返回
        
        return stats


if __name__ == '__main__':
    # 简单测试
    print("🧪 测试TreeSitterProjectAudit...")
    
    # 创建临时测试目录
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, 'test.sol')
        with open(test_file, 'w') as f:
            f.write("""
pragma solidity ^0.8.0;

contract TestContract {
    function testFunction() public pure returns (uint256) {
        return 42;
    }
}
""")
        
        audit = TreeSitterProjectAudit("test", temp_dir)
        audit.parse()
        
        print(f"✅ 解析完成，找到 {len(audit.functions)} 个函数")
        print(f"✅ 需要检查 {len(audit.functions_to_check)} 个函数")
        print(f"✅ 构建了 {len(audit.call_trees)} 个调用树")
        print(f"✅ 构建了 {len(audit.call_graphs)} 个调用关系")
        
        # 测试 call graph 相关功能
        call_graph_stats = audit.get_call_graph_statistics()
        print(f"📊 Call Graph 统计: {call_graph_stats}")
        
        if audit.call_graphs:
            print("🔗 Call Graph 样例:")
            audit.print_call_graph(limit=5)
        
    print("✅ TreeSitterProjectAudit测试完成") 