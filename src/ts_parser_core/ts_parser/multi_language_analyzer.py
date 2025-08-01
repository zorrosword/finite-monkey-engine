#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多语言统一分析器
协调各种语言解析器，提供统一的接口
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
from datetime import datetime

from .data_structures import (
    LanguageType, CallType, FunctionInfo, StructInfo, 
    ModuleInfo, CallGraphEdge, AnalysisStats
)
from .language_configs import get_language_by_extension
from .parsers import SolidityParser, RustParser, CppParser, MoveParser


class MultiLanguageAnalyzer:
    """多语言代码分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.parsers = {
            LanguageType.SOLIDITY: SolidityParser(),
            LanguageType.RUST: RustParser(),
            LanguageType.CPP: CppParser(),
            LanguageType.MOVE: MoveParser(),
        }
        
        print("✅ 使用高级调用树构建器（基于真正的tree-sitter）")
        
        # 当前活跃的解析器
        self._current_parser = None
    
    def analyze_code(self, code: str, language: LanguageType, filename: str = "unknown") -> None:
        """分析代码字符串"""
        parser = self.parsers[language]
        parser.parse_code(code, filename)
        self._current_parser = parser
    
    def analyze_file(self, file_path: str, language: Optional[LanguageType] = None) -> None:
        """分析单个文件"""
        file_path = Path(file_path)
        
        # 自动检测语言类型
        if language is None:
            try:
                language = get_language_by_extension(file_path.suffix)
            except ValueError:
                print(f"无法识别文件类型: {file_path}")
                return
        
        parser = self.parsers[language]
        parser.parse_file(str(file_path))
        self._current_parser = parser
    
    def analyze_directory(self, directory_path: str, language: LanguageType) -> None:
        """分析目录中的所有文件"""
        parser = self.parsers[language]
        parser.parse_directory(directory_path)
        self._current_parser = parser
    
    def get_modules(self, language: Optional[LanguageType] = None) -> Dict[str, ModuleInfo]:
        """获取模块信息"""
        if language:
            return self.parsers[language].get_modules()
        elif self._current_parser:
            return self._current_parser.get_modules()
        return {}
    
    def get_functions(self, language: Optional[LanguageType] = None) -> Dict[str, FunctionInfo]:
        """获取函数信息"""
        if language:
            return self.parsers[language].get_functions()
        elif self._current_parser:
            return self._current_parser.get_functions()
        return {}
    
    def get_structs(self, language: Optional[LanguageType] = None) -> Dict[str, StructInfo]:
        """获取结构体信息"""
        if language:
            return self.parsers[language].get_structs()
        elif self._current_parser:
            return self._current_parser.get_structs()
        return {}
    
    def get_call_graph(self, language: Optional[LanguageType] = None) -> List[CallGraphEdge]:
        """获取调用图"""
        if language:
            return self.parsers[language].get_call_graph()
        elif self._current_parser:
            return self._current_parser.get_call_graph()
        return []
    
    def get_statistics(self, language: Optional[LanguageType] = None) -> AnalysisStats:
        """获取统计信息"""
        if language:
            return self.parsers[language].get_statistics()
        elif self._current_parser:
            return self._current_parser.get_statistics()
        return AnalysisStats(language=LanguageType.SOLIDITY)  # 默认值
    
    def get_language_specific_features(self, language: Optional[LanguageType] = None) -> Dict[str, int]:
        """获取语言特定特性"""
        if language:
            return self.parsers[language].calculate_language_features()
        elif self._current_parser:
            return self._current_parser.calculate_language_features()
        return {}
    
    def get_function_by_name(self, name: str, language: Optional[LanguageType] = None) -> Optional[FunctionInfo]:
        """根据名称获取函数信息"""
        if language:
            return self.parsers[language].get_function_by_name(name)
        elif self._current_parser:
            return self._current_parser.get_function_by_name(name)
        return None
    
    def get_callers(self, function_name: str, language: Optional[LanguageType] = None) -> List[str]:
        """获取调用指定函数的函数列表"""
        if language:
            return self.parsers[language].get_callers(function_name)
        elif self._current_parser:
            return self._current_parser.get_callers(function_name)
        return []
    
    def get_callees(self, function_name: str, language: Optional[LanguageType] = None) -> List[str]:
        """获取指定函数调用的函数列表"""
        if language:
            return self.parsers[language].get_callees(function_name)
        elif self._current_parser:
            return self._current_parser.get_callees(function_name)
        return []

    def get_recursive_upstream_functions(self, function_name: str, language: Optional[LanguageType] = None, 
                                       max_depth: int = 15) -> Dict[str, int]:
        """获取递归上游函数（调用该函数的所有函数，递归获取）
        
        Args:
            function_name: 目标函数名
            language: 语言类型
            max_depth: 最大递归深度，防止无限递归
            
        Returns:
            Dict[str, int]: 函数名 -> 调用深度的映射
        """
        upstream_funcs = {}
        visited = set()
        
        def _get_upstream_recursive(func_name: str, depth: int):
            if depth > max_depth or func_name in visited:
                return
            
            visited.add(func_name)
            callers = self.get_callers(func_name, language)
            
            for caller in callers:
                if caller not in upstream_funcs or upstream_funcs[caller] > depth:
                    upstream_funcs[caller] = depth
                    _get_upstream_recursive(caller, depth + 1)
        
        _get_upstream_recursive(function_name, 1)
        return upstream_funcs

    def get_recursive_downstream_functions(self, function_name: str, language: Optional[LanguageType] = None, 
                                         max_depth: int = 15) -> Dict[str, int]:
        """获取递归下游函数（该函数调用的所有函数，递归获取）
        
        Args:
            function_name: 目标函数名
            language: 语言类型
            max_depth: 最大递归深度，防止无限递归
            
        Returns:
            Dict[str, int]: 函数名 -> 调用深度的映射
        """
        downstream_funcs = {}
        visited = set()
        
        def _get_downstream_recursive(func_name: str, depth: int):
            if depth > max_depth or func_name in visited:
                return
            
            visited.add(func_name)
            callees = self.get_callees(func_name, language)
            
            for callee in callees:
                if callee not in downstream_funcs or downstream_funcs[callee] > depth:
                    downstream_funcs[callee] = depth
                    _get_downstream_recursive(callee, depth + 1)
        
        _get_downstream_recursive(function_name, 1)
        return downstream_funcs

    def get_function_dependency_graph(self, function_name: str, language: Optional[LanguageType] = None, 
                                    max_depth: int = 15) -> Dict[str, Any]:
        """获取函数的完整依赖图（上游+下游+自身）
        
        Args:
            function_name: 目标函数名
            language: 语言类型
            max_depth: 最大递归深度
            
        Returns:
            Dict包含:
            - target_function: 目标函数信息
            - upstream_functions: 上游函数 {name: depth}
            - downstream_functions: 下游函数 {name: depth}
            - total_dependencies: 总依赖数量
        """
        # 获取目标函数信息
        target_func = self.get_function_by_name(function_name, language)
        if not target_func:
            return {
                'target_function': None,
                'upstream_functions': {},
                'downstream_functions': {},
                'total_dependencies': 0,
                'error': f'Function "{function_name}" not found'
            }
        
        # 获取上游和下游函数
        upstream = self.get_recursive_upstream_functions(function_name, language, max_depth)
        downstream = self.get_recursive_downstream_functions(function_name, language, max_depth)
        
        return {
            'target_function': target_func,
            'upstream_functions': upstream,
            'downstream_functions': downstream,
            'total_dependencies': len(upstream) + len(downstream),
            'analysis_depth': max_depth
        }

    def print_dependency_graph(self, function_name: str, language: Optional[LanguageType] = None, 
                             max_depth: int = 15) -> None:
        """打印函数的依赖图
        
        Args:
            function_name: 目标函数名
            language: 语言类型
            max_depth: 最大递归深度
        """
        dependency_graph = self.get_function_dependency_graph(function_name, language, max_depth)
        
        if 'error' in dependency_graph:
            print(f"❌ 错误: {dependency_graph['error']}")
            return
        
        target_func = dependency_graph['target_function']
        upstream = dependency_graph['upstream_functions']
        downstream = dependency_graph['downstream_functions']
        
        print(f"\n🎯 函数依赖图分析")
        print("=" * 60)
        print(f"🔧 目标函数: {target_func.name}")
        print(f"📄 完整名称: {target_func.full_name}")
        print(f"🔧 语言: {target_func.language.value.upper()}")
        print(f"📍 位置: 第{target_func.line_number}行")
        print(f"👁️  可见性: {target_func.visibility}")
        
        # 显示语言特定属性
        attrs = []
        if hasattr(target_func, 'is_async') and target_func.is_async:
            attrs.append('async')
        if hasattr(target_func, 'is_unsafe') and target_func.is_unsafe:
            attrs.append('unsafe')
        if hasattr(target_func, 'is_payable') and target_func.is_payable:
            attrs.append('payable')
        if hasattr(target_func, 'is_view') and target_func.is_view:
            attrs.append('view')
        if hasattr(target_func, 'is_pure') and target_func.is_pure:
            attrs.append('pure')
        if hasattr(target_func, 'is_virtual') and target_func.is_virtual:
            attrs.append('virtual')
        if hasattr(target_func, 'is_entry') and target_func.is_entry:
            attrs.append('entry')
        
        if attrs:
            print(f"🏷️  属性: {', '.join(attrs)}")
        
        print(f"\n📊 依赖统计:")
        print(f"  ⬆️  上游函数: {len(upstream)} 个")
        print(f"  ⬇️  下游函数: {len(downstream)} 个")
        print(f"  📈 总依赖: {dependency_graph['total_dependencies']} 个")
        print(f"  🔍 分析深度: {dependency_graph['analysis_depth']} 层")
        
        # 打印上游函数（调用目标函数的函数）
        if upstream:
            print(f"\n⬆️  上游函数 (调用 {target_func.name} 的函数):")
            upstream_by_depth = {}
            for func, depth in upstream.items():
                if depth not in upstream_by_depth:
                    upstream_by_depth[depth] = []
                upstream_by_depth[depth].append(func)
            
            for depth in sorted(upstream_by_depth.keys()):
                indent = "  " + "  " * (depth - 1)
                for func in upstream_by_depth[depth]:
                    func_info = self.get_function_by_name(func, language)
                    if func_info:
                        print(f"{indent}🔧 {func} (第{func_info.line_number}行, {func_info.visibility})")
                    else:
                        print(f"{indent}🔧 {func}")
        
        # 打印目标函数
        print(f"\n🎯 目标函数:")
        print(f"  🔧 {target_func.name} (第{target_func.line_number}行, {target_func.visibility})")
        
        # 打印下游函数（目标函数调用的函数）
        if downstream:
            print(f"\n⬇️  下游函数 ({target_func.name} 调用的函数):")
            downstream_by_depth = {}
            for func, depth in downstream.items():
                if depth not in downstream_by_depth:
                    downstream_by_depth[depth] = []
                downstream_by_depth[depth].append(func)
            
            for depth in sorted(downstream_by_depth.keys()):
                indent = "  " + "  " * (depth - 1)
                for func in downstream_by_depth[depth]:
                    func_info = self.get_function_by_name(func, language)
                    if func_info:
                        print(f"{indent}🔧 {func} (第{func_info.line_number}行, {func_info.visibility})")
                    else:
                        print(f"{indent}🔧 {func}")
        
        # 打印调用关系图
        print(f"\n🔗 调用关系图:")
        print("```")
        
        # 构建完整的调用图
        all_funcs = set([target_func.full_name]) | set(upstream.keys()) | set(downstream.keys())
        call_graph = self.get_call_graph(language)
        
        # 过滤相关的调用关系
        relevant_edges = []
        for edge in call_graph:
            if edge.caller in all_funcs and edge.callee in all_funcs:
                relevant_edges.append(edge)
        
        # 按调用者分组
        caller_groups = {}
        for edge in relevant_edges:
            caller = edge.caller
            if caller not in caller_groups:
                caller_groups[caller] = []
            caller_groups[caller].append(edge)
        
        # 打印调用关系
        for caller, edges in caller_groups.items():
            # 标记目标函数
            marker = "🎯 " if caller == target_func.full_name else "   "
            print(f"{marker}{caller}")
            for edge in edges:
                call_type = f" ({edge.call_type.value})" if edge.call_type.value != 'direct' else ""
                target_marker = "🎯 " if edge.callee == target_func.full_name else "   "
                print(f"  └─→ {target_marker}{edge.callee}{call_type}")
        
        print("```")
        
        # 总结
        print(f"\n✅ 依赖图分析完成!")
        if not upstream and not downstream:
            print("  📝 该函数没有依赖关系")
        elif not upstream:
            print("  📝 该函数是调用链的起始点（无上游函数）")
        elif not downstream:
            print("  📝 该函数是调用链的终点（无下游函数）")
        else:
            print(f"  📝 该函数处于调用链中间，连接了{len(upstream)}个上游和{len(downstream)}个下游函数")
    
    def get_most_called_functions(self, language: Optional[LanguageType] = None, top_n: int = 10) -> List[tuple]:
        """获取被调用最多的函数"""
        call_graph = self.get_call_graph(language)
        call_counts = {}
        
        for edge in call_graph:
            call_counts[edge.callee] = call_counts.get(edge.callee, 0) + 1
        
        return sorted(call_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    def get_most_calling_functions(self, language: Optional[LanguageType] = None, top_n: int = 10) -> List[tuple]:
        """获取调用其他函数最多的函数"""
        call_graph = self.get_call_graph(language)
        call_counts = {}
        
        for edge in call_graph:
            call_counts[edge.caller] = call_counts.get(edge.caller, 0) + 1
        
        return sorted(call_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    def get_all_supported_languages(self) -> List[LanguageType]:
        """获取所有支持的语言"""
        return list(self.parsers.keys())
    
    def clear_all_results(self) -> None:
        """清理所有解析结果"""
        for parser in self.parsers.values():
            parser.clear_results()
        self._current_parser = None
    
    def compare_languages(self, languages: List[LanguageType] = None) -> Dict[str, Any]:
        """比较不同语言的解析结果"""
        if languages is None:
            languages = list(self.parsers.keys())
        
        comparison = {
            'languages': {},
            'summary': {
                'total_modules': 0,
                'total_functions': 0,
                'total_structs': 0,
                'total_call_relationships': 0,
            }
        }
        
        for language in languages:
            stats = self.get_statistics(language)
            comparison['languages'][language.value] = stats.to_dict()
            
            # 累加到总计
            comparison['summary']['total_modules'] += stats.modules_count
            comparison['summary']['total_functions'] += stats.functions_count
            comparison['summary']['total_structs'] += stats.structs_count
            comparison['summary']['total_call_relationships'] += stats.call_relationships
        
        return comparison

    def visualize_dependency_graph(self, function_name: str, language: Optional[LanguageType] = None, 
                                  max_depth: int = 15, save_path: Optional[str] = None, 
                                  show_plot: bool = True) -> Optional[str]:
        """生成函数依赖图的可视化图表
        
        Args:
            function_name: 目标函数名
            language: 语言类型
            max_depth: 最大递归深度
            save_path: 保存路径（可选）
            show_plot: 是否显示图表
            
        Returns:
            保存的文件路径（如果保存了）
        """
        try:
            # 获取依赖图数据
            dependency_graph = self.get_function_dependency_graph(function_name, language, max_depth)
            
            if 'error' in dependency_graph:
                print(f"❌ 无法生成可视化: {dependency_graph['error']}")
                return None
            
            target_func = dependency_graph['target_function']
            upstream = dependency_graph['upstream_functions']
            downstream = dependency_graph['downstream_functions']
            
            # 创建有向图
            G = nx.DiGraph()
            
            # 节点颜色和大小映射
            node_colors = {}
            node_sizes = {}
            node_labels = {}
            
            # 添加目标函数节点（中心节点）
            target_node = target_func.name
            G.add_node(target_node)
            node_colors[target_node] = '#FF6B6B'  # 红色 - 目标函数
            node_sizes[target_node] = 2000
            node_labels[target_node] = f"TARGET: {target_func.name}\n({target_func.visibility})"
            
            # 定义深度颜色 - 扩展到更多层级
            upstream_colors = [
                '#4ECDC4', '#45B7D1', '#6C5CE7', '#A29BFE', '#FD79A8',  # 前5层
                '#74B9FF', '#0984E3', '#6F42C1', '#E83E8C', '#DC3545',  # 6-10层  
                '#FD7E14', '#FFC107', '#28A745', '#17A2B8', '#6F6F6F'   # 11-15层
            ]  # 青紫色系 - 上游
            downstream_colors = [
                '#00B894', '#00CEC9', '#74B9FF', '#0984E3', '#6C5CE7',  # 前5层
                '#28A745', '#20C997', '#17A2B8', '#6F42C1', '#E83E8C',  # 6-10层
                '#DC3545', '#FD7E14', '#FFC107', '#6F6F6F', '#495057'   # 11-15层  
            ]  # 蓝绿色系 - 下游
            
            # 添加上游函数节点
            for func, depth in upstream.items():
                short_name = func.split('.')[-1] if '.' in func else func
                G.add_node(func)
                color_idx = min(depth - 1, len(upstream_colors) - 1)
                node_colors[func] = upstream_colors[color_idx]
                node_sizes[func] = max(800, 1500 - depth * 150)
                node_labels[func] = f"UP: {short_name}\n(depth{depth})"
                
                # 添加边 - 上游函数指向目标函数
                G.add_edge(func, target_node)
            
            # 添加下游函数节点
            for func, depth in downstream.items():
                short_name = func.split('.')[-1] if '.' in func else func
                G.add_node(func)
                color_idx = min(depth - 1, len(downstream_colors) - 1)
                node_colors[func] = downstream_colors[color_idx]
                node_sizes[func] = max(800, 1500 - depth * 150)
                node_labels[func] = f"DOWN: {short_name}\n(depth{depth})"
                
                # 添加边 - 目标函数指向下游函数
                G.add_edge(target_node, func)
            
            # 同时添加下游函数之间的调用关系
            call_graph = self.get_call_graph(language)
            all_funcs = set([target_func.full_name]) | set(upstream.keys()) | set(downstream.keys())
            
            for edge in call_graph:
                if edge.caller in all_funcs and edge.callee in all_funcs:
                    # 只添加不是直接连接到目标函数的边
                    if edge.caller != target_func.full_name and edge.callee != target_func.full_name:
                        if edge.caller in G.nodes() and edge.callee in G.nodes():
                            G.add_edge(edge.caller, edge.callee)
            
            # 创建图形
            plt.figure(figsize=(16, 12))
            plt.clf()
            
            # 设置字体以支持中文和emoji（如果可能）
            try:
                plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False
            except:
                pass
            
            # 使用层次化布局
            pos = self._calculate_hierarchical_layout(G, target_node, upstream, downstream)
            
            # 绘制边
            nx.draw_networkx_edges(G, pos, edge_color='#BDC3C7', arrows=True, 
                                 arrowsize=15, arrowstyle='->', alpha=0.6, width=1.5)
            
            # 绘制节点
            colors = [node_colors[node] for node in G.nodes()]
            sizes = [node_sizes[node] for node in G.nodes()]
            
            nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=sizes, 
                                 alpha=0.9, edgecolors='white', linewidths=2)
            
            # 绘制标签
            labels = {node: node_labels.get(node, node) for node in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, font_size=9, font_weight='bold')
            
            # 添加标题和图例
            language_name = target_func.language.value.upper()
            plt.title(f'Function Dependency Graph - {target_func.name} ({language_name})\n'
                     f'Total Dependencies: {len(upstream) + len(downstream)} | '
                     f'Upstream: {len(upstream)} | Downstream: {len(downstream)}',
                     fontsize=16, fontweight='bold', pad=20)
            
            # 创建图例
            legend_elements = [
                mpatches.Patch(color='#FF6B6B', label='Target Function'),
                mpatches.Patch(color='#4ECDC4', label='Upstream Functions'),
                mpatches.Patch(color='#00B894', label='Downstream Functions'),
            ]
            
            plt.legend(handles=legend_elements, loc='upper right', fontsize=12, 
                      bbox_to_anchor=(1, 1), frameon=True, shadow=True)
            
            # 设置图形属性
            plt.axis('off')
            plt.tight_layout()
            
            # 保存或显示图表
            saved_path = None
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
                saved_path = save_path
                print(f"📊 依赖图已保存到: {save_path}")
            
            if show_plot:
                plt.show()
            else:
                plt.close()
            
            return saved_path
            
        except Exception as e:
            print(f"❌ 生成可视化失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _calculate_hierarchical_layout(self, G, target_node: str, upstream: Dict[str, int], 
                                     downstream: Dict[str, int]) -> Dict[str, tuple]:
        """计算层次化布局"""
        pos = {}
        
        # 目标函数在中心
        pos[target_node] = (0, 0)
        
        # 上游函数布局（上方）
        if upstream:
            upstream_by_depth = {}
            for func, depth in upstream.items():
                if depth not in upstream_by_depth:
                    upstream_by_depth[depth] = []
                upstream_by_depth[depth].append(func)
            
            for depth, funcs in upstream_by_depth.items():
                y = depth * 2  # 上方
                for i, func in enumerate(funcs):
                    x = (i - len(funcs) / 2 + 0.5) * 3
                    pos[func] = (x, y)
        
        # 下游函数布局（下方）
        if downstream:
            downstream_by_depth = {}
            for func, depth in downstream.items():
                if depth not in downstream_by_depth:
                    downstream_by_depth[depth] = []
                downstream_by_depth[depth].append(func)
            
            for depth, funcs in downstream_by_depth.items():
                y = -depth * 2  # 下方
                for i, func in enumerate(funcs):
                    x = (i - len(funcs) / 2 + 0.5) * 3
                    pos[func] = (x, y)
        
        return pos

    def save_dependency_graph_image(self, function_name: str, language: Optional[LanguageType] = None, 
                                   max_depth: int = 15, output_dir: str = "dependency_graphs") -> Optional[str]:
        """保存函数依赖图到图片文件
        
        Args:
            function_name: 目标函数名
            language: 语言类型
            max_depth: 最大递归深度
            output_dir: 输出目录
            
        Returns:
            保存的文件路径
        """
        try:
            # 创建输出目录
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            lang_name = language.value if language else "unknown"
            safe_func_name = function_name.replace('.', '_').replace('::', '_').replace('/', '_')
            filename = f"dependency_{safe_func_name}_{lang_name}_{timestamp}.png"
            full_path = output_path / filename
            
            # 生成可视化图表
            saved_path = self.visualize_dependency_graph(
                function_name, language, max_depth, 
                save_path=str(full_path), show_plot=False
            )
            
            return saved_path
            
        except Exception as e:
            print(f"❌ 保存依赖图失败: {e}")
            return None

    def generate_dependency_mermaid(self, function_name: str, language: Optional[LanguageType] = None, 
                                   max_depth: int = 15) -> str:
        """生成Mermaid格式的依赖图
        
        Args:
            function_name: 目标函数名
            language: 语言类型
            max_depth: 最大递归深度
            
        Returns:
            Mermaid格式的图表字符串
        """
        try:
            dependency_graph = self.get_function_dependency_graph(function_name, language, max_depth)
            
            if 'error' in dependency_graph:
                return f"ERROR: {dependency_graph['error']}"
            
            target_func = dependency_graph['target_function']
            upstream = dependency_graph['upstream_functions']
            downstream = dependency_graph['downstream_functions']
            
            mermaid_lines = ['graph TD']
            
            # 节点定义
            target_id = "TARGET"
            target_display = target_func.name.replace('.', '_')
            mermaid_lines.append(f'    {target_id}[🎯 {target_display}]')
            mermaid_lines.append(f'    {target_id} --> {target_id}')
            
            # 上游函数
            upstream_ids = {}
            for i, (func, depth) in enumerate(upstream.items()):
                func_id = f"UP_{i}"
                func_display = func.split('.')[-1] if '.' in func else func
                upstream_ids[func] = func_id
                mermaid_lines.append(f'    {func_id}[⬆️ {func_display}<br/>深度{depth}]')
                mermaid_lines.append(f'    {func_id} --> {target_id}')
            
            # 下游函数
            downstream_ids = {}
            for i, (func, depth) in enumerate(downstream.items()):
                func_id = f"DOWN_{i}"
                func_display = func.split('.')[-1] if '.' in func else func
                downstream_ids[func] = func_id
                mermaid_lines.append(f'    {func_id}[⬇️ {func_display}<br/>深度{depth}]')
                mermaid_lines.append(f'    {target_id} --> {func_id}')
            
            # 样式定义
            mermaid_lines.extend([
                '',
                '    classDef target fill:#ff6b6b,stroke:#d63447,stroke-width:3px',
                '    classDef upstream fill:#4ecdc4,stroke:#00b894,stroke-width:2px',
                '    classDef downstream fill:#00b894,stroke:#00a085,stroke-width:2px',
                '',
                f'    class {target_id} target',
            ])
            
            if upstream_ids:
                upstream_id_list = ','.join(upstream_ids.values())
                mermaid_lines.append(f'    class {upstream_id_list} upstream')
            
            if downstream_ids:
                downstream_id_list = ','.join(downstream_ids.values())
                mermaid_lines.append(f'    class {downstream_id_list} downstream')
            
            return '\n'.join(mermaid_lines)
            
        except Exception as e:
            return f"ERROR: 生成Mermaid图表失败: {e}" 