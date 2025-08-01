#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多语言代码分析器 Demo
使用模块化分析器分析指定路径的代码文件或目录

使用方法:
    python demo.py <文件路径或目录路径>
    python demo.py contracts/Token.sol
    python demo.py rust_examples/
    python demo.py --help
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from analyzers import MultiLanguageAnalyzer, LanguageType


def save_call_graph_to_file(analyzer: MultiLanguageAnalyzer, language: LanguageType, output_path: Path):
    """保存call graph到JSON文件"""
    try:
        # 获取分析结果
        modules = analyzer.get_modules(language)
        functions = analyzer.get_functions(language)
        structs = analyzer.get_structs(language)
        call_graph = analyzer.get_call_graph(language)
        features = analyzer.get_language_specific_features(language)
        stats = analyzer.get_statistics(language)
        
        # 转换为可序列化的格式
        result_data = {
            'language': language.value,
            'analysis_time': str(datetime.now()),
            'statistics': {
                'modules_count': len(modules),
                'functions_count': len(functions),
                'structs_count': len(structs),
                'call_relationships': len(call_graph)
            },
            'language_features': features,
            'modules': {
                name: {
                    'name': module.name,
                    'full_name': module.full_name,
                    'line_number': module.line_number,
                    'functions_count': len(module.functions),
                    'structs_count': len(module.structs),
                    'inheritance': getattr(module, 'inheritance', []),
                    'address': getattr(module, 'address', None),
                    'is_library': getattr(module, 'is_library', False),
                    'namespace_type': getattr(module, 'namespace_type', None)
                } for name, module in modules.items()
            },
            'functions': {
                name: {
                    'name': func.name,
                    'full_name': func.full_name,
                    'visibility': func.visibility,
                    'line_number': func.line_number,
                    'calls': func.calls,
                    'language_specific': {
                        'is_async': func.is_async,
                        'is_unsafe': func.is_unsafe,
                        'is_payable': func.is_payable,
                        'is_view': func.is_view,
                        'is_pure': func.is_pure,
                        'is_virtual': func.is_virtual,
                        'is_override': func.is_override,
                        'is_entry': func.is_entry,
                        'is_native': func.is_native,
                        'modifiers': func.modifiers,
                        'acquires': func.acquires
                    }
                } for name, func in functions.items()
            },
            'structs': {
                name: {
                    'name': struct.name,
                    'full_name': struct.full_name,
                    'line_number': struct.line_number,
                    'base_classes': struct.base_classes,
                    'abilities': struct.abilities,
                    'derives': struct.derives,
                    'is_interface': struct.is_interface,
                    'is_abstract': struct.is_abstract
                } for name, struct in structs.items()
            },
            'call_graph': {
                'edges': [
                    {
                        'caller': edge.caller,
                        'callee': edge.callee,
                        'call_type': edge.call_type.value if edge.call_type else 'direct',
                        'language': edge.language.value if edge.language else None
                    } for edge in call_graph
                ],
                'most_called_functions': analyzer.get_most_called_functions(language, top_n=10),
                'most_calling_functions': analyzer.get_most_calling_functions(language, top_n=10)
            }
        }
        
        # 保存到文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        print(f"📁 Call graph已保存到: {output_path}")
        print(f"📊 保存内容: {len(call_graph)}个调用关系, {len(functions)}个函数")
        
    except Exception as e:
        print(f"❌ 保存失败: {e}")


def load_call_graph_from_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """从JSON文件加载call graph"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📁 已从文件加载call graph: {file_path}")
        print(f"📊 加载内容: {data['statistics']['call_relationships']}个调用关系")
        return data
        
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return None


def display_loaded_call_graph(data: Dict[str, Any]):
    """显示从文件加载的call graph"""
    print(f"\n🚀 Call Graph 分析结果")
    print("=" * 60)
    print(f"🔧 语言: {data['language'].upper()}")
    print(f"⏰ 分析时间: {data['analysis_time']}")
    
    # 显示统计信息
    stats = data['statistics']
    print(f"\n📊 统计信息:")
    print(f"  📁 模块数: {stats['modules_count']}")
    print(f"  🔧 函数数: {stats['functions_count']}")
    print(f"  📦 结构体数: {stats['structs_count']}")
    print(f"  🔗 调用关系: {stats['call_relationships']}")
    
    # 显示语言特定特性
    if data['language_features']:
        print(f"\n🎯 {data['language'].upper()}特定特性:")
        for feature, count in data['language_features'].items():
            if count > 0:
                print(f"  {feature}: {count}")
    
    # 显示最常被调用的函数
    call_graph = data['call_graph']
    if call_graph['most_called_functions']:
        print(f"\n🏆 最常被调用的函数:")
        for func_name, count in call_graph['most_called_functions']:
            print(f"  {func_name}: {count} 次")
    
    # 显示调用关系最多的函数
    if call_graph['most_calling_functions']:
        print(f"\n📞 调用最多函数的函数:")
        for func_name, count in call_graph['most_calling_functions']:
            print(f"  {func_name}: 调用 {count} 个函数")
    
    # 显示调用关系网络
    edges = call_graph['edges']
    if edges:
        print(f"\n🔗 调用关系网络 (前20个):")
        for i, edge in enumerate(edges[:20]):
            call_type = f"[{edge['call_type']}]"
            print(f"  {edge['caller']} --{call_type}--> {edge['callee']}")
        
        if len(edges) > 20:
            print(f"  ... 还有 {len(edges) - 20} 个调用关系")


def generate_call_graph_visualization(data: Dict[str, Any], output_path: Path):
    """生成call graph的文本可视化"""
    try:
        lines = []
        lines.append(f"# Call Graph Visualization - {data['language'].upper()}")
        lines.append(f"# Generated at: {data['analysis_time']}")
        lines.append("")
        
        # 统计信息
        lines.append("## Statistics")
        stats = data['statistics']
        lines.append(f"- Modules: {stats['modules_count']}")
        lines.append(f"- Functions: {stats['functions_count']}")
        lines.append(f"- Structs: {stats['structs_count']}")
        lines.append(f"- Call Relationships: {stats['call_relationships']}")
        lines.append("")
        
        # 最活跃函数
        call_graph = data['call_graph']
        if call_graph['most_called_functions']:
            lines.append("## Most Called Functions")
            for func_name, count in call_graph['most_called_functions']:
                lines.append(f"- {func_name}: {count} calls")
            lines.append("")
        
        # 调用关系图
        lines.append("## Call Graph")
        lines.append("```")
        edges = call_graph['edges']
        
        # 按调用者分组
        caller_groups = {}
        for edge in edges:
            caller = edge['caller']
            if caller not in caller_groups:
                caller_groups[caller] = []
            caller_groups[caller].append(edge)
        
        for caller, caller_edges in caller_groups.items():
            lines.append(f"{caller}")
            for edge in caller_edges:
                call_type = edge['call_type'] if edge['call_type'] != 'direct' else ''
                type_suffix = f" ({call_type})" if call_type else ""
                lines.append(f"  └─→ {edge['callee']}{type_suffix}")
            lines.append("")
        
        lines.append("```")
        
        # 函数详情
        if data['functions']:
            lines.append("## Function Details")
            for name, func in data['functions'].items():
                lang_attrs = []
                lang_specific = func['language_specific']
                
                if lang_specific['is_async']:
                    lang_attrs.append("async")
                if lang_specific['is_unsafe']:
                    lang_attrs.append("unsafe")
                if lang_specific['is_payable']:
                    lang_attrs.append("payable")
                if lang_specific['is_view']:
                    lang_attrs.append("view")
                if lang_specific['is_pure']:
                    lang_attrs.append("pure")
                if lang_specific['is_virtual']:
                    lang_attrs.append("virtual")
                if lang_specific['is_entry']:
                    lang_attrs.append("entry")
                
                attrs_str = f" [{', '.join(lang_attrs)}]" if lang_attrs else ""
                lines.append(f"- **{func['name']}** (line {func['line_number']}, {func['visibility']}){attrs_str}")
                
                if func['calls']:
                    lines.append(f"  - Calls: {', '.join(func['calls'])}")
                
                if lang_specific['modifiers']:
                    lines.append(f"  - Modifiers: {', '.join(lang_specific['modifiers'])}")
                
                if lang_specific['acquires']:
                    lines.append(f"  - Acquires: {', '.join(lang_specific['acquires'])}")
        
        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"📄 Call graph可视化已保存到: {output_path}")
        
    except Exception as e:
        print(f"❌ 生成可视化失败: {e}")


def detect_language_from_path(path: Path) -> Optional[LanguageType]:
    """根据文件路径自动检测语言类型"""
    if path.is_file():
        # 单文件检测
        suffix = path.suffix.lower()
        if suffix == '.sol':
            return LanguageType.SOLIDITY
        elif suffix == '.rs':
            return LanguageType.RUST
        elif suffix in ['.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx']:
            return LanguageType.CPP
        elif suffix == '.move':
            return LanguageType.MOVE
    else:
        # 目录检测 - 根据目录名称推测
        dir_name = path.name.lower()
        if 'contract' in dir_name or 'solidity' in dir_name:
            return LanguageType.SOLIDITY
        elif 'rust' in dir_name:
            return LanguageType.RUST
        elif 'cpp' in dir_name or 'c++' in dir_name:
            return LanguageType.CPP
        elif 'move' in dir_name:
            return LanguageType.MOVE
    
    return None


def analyze_single_file(analyzer: MultiLanguageAnalyzer, file_path: Path, language: LanguageType, save_output: bool = False):
    """分析单个文件"""
    print(f"📄 分析文件: {file_path}")
    print(f"🔧 语言类型: {language.value.upper()}")
    print("-" * 50)
    
    try:
        # 分析文件
        analyzer.analyze_file(str(file_path), language)
        
        # 获取分析结果
        modules = analyzer.get_modules(language)
        functions = analyzer.get_functions(language)
        structs = analyzer.get_structs(language)
        call_graph = analyzer.get_call_graph(language)
        features = analyzer.get_language_specific_features(language)
        stats = analyzer.get_statistics(language)
        
        # 显示统计信息
        print(f"📊 解析统计:")
        print(f"  📁 模块数: {len(modules)}")
        print(f"  🔧 函数数: {len(functions)}")
        print(f"  📦 结构体数: {len(structs)}")
        print(f"  🔗 调用关系: {len(call_graph)}")
        
        # 显示语言特定特性
        if features:
            print(f"\n🎯 {language.value.upper()}特定特性:")
            for feature, count in features.items():
                if count > 0:
                    print(f"  {feature}: {count}")
        
        # 显示模块详情
        if modules:
            print(f"\n📁 模块详情:")
            for name, module in modules.items():
                print(f"  📄 {module.name} (第{module.line_number}行)")
                if module.functions:
                    print(f"    🔧 包含函数: {len(module.functions)}个")
                if module.structs:
                    print(f"    📦 包含结构体: {len(module.structs)}个")
                if hasattr(module, 'inheritance') and module.inheritance:
                    print(f"    🔗 继承: {', '.join(module.inheritance)}")
                if hasattr(module, 'address') and module.address:
                    print(f"    📮 地址: {module.address}")
        
        # 显示函数详情
        if functions:
            print(f"\n🔧 函数详情:")
            for name, func in functions.items():
                func_details = [f"第{func.line_number}行", func.visibility]
                
                # 添加语言特定属性
                if func.is_async:
                    func_details.append("async")
                if func.is_unsafe:
                    func_details.append("unsafe")
                if func.is_payable:
                    func_details.append("payable")
                if func.is_view:
                    func_details.append("view")
                if func.is_pure:
                    func_details.append("pure")
                if func.is_virtual:
                    func_details.append("virtual")
                if func.is_override:
                    func_details.append("override")
                if func.is_entry:
                    func_details.append("entry")
                if func.is_native:
                    func_details.append("native")
                
                print(f"  🔧 {func.name}: {', '.join(func_details)}")
                
                if func.modifiers:
                    print(f"    🛡️  修饰符: {', '.join(func.modifiers)}")
                if func.acquires:
                    print(f"    📥 获取资源: {', '.join(func.acquires)}")
                if func.calls:
                    print(f"    ➡️  调用函数: {', '.join(func.calls)}")
        
        # 显示结构体详情
        if structs:
            print(f"\n📦 结构体详情:")
            for name, struct in structs.items():
                struct_details = [f"第{struct.line_number}行"]
                
                if struct.base_classes:
                    struct_details.append(f"继承: {', '.join(struct.base_classes)}")
                if struct.abilities:
                    struct_details.append(f"abilities: {', '.join(struct.abilities)}")
                if struct.derives:
                    struct_details.append(f"derives: {', '.join(struct.derives)}")
                
                print(f"  📦 {struct.name}: {', '.join(struct_details)}")
        
        # 显示调用图
        if call_graph:
            print(f"\n🔗 调用关系图:")
            
            # 按调用次数统计
            most_called = analyzer.get_most_called_functions(language, top_n=5)
            if most_called:
                print(f"  🏆 最常被调用:")
                for func_name, count in most_called:
                    print(f"    {func_name}: {count} 次")
            
            # 显示部分调用关系
            print(f"  🔗 调用关系 (前10个):")
            for i, edge in enumerate(call_graph[:10]):
                call_type_desc = f"[{edge.call_type.value}]" if edge.call_type else "[direct]"
                print(f"    {edge.caller} --{call_type_desc}--> {edge.callee}")
            
            if len(call_graph) > 10:
                print(f"    ... 还有 {len(call_graph) - 10} 个调用关系")
        
        print(f"\n✅ 文件分析完成!")
        
        # 保存call graph到文件
        if save_output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = file_path.stem
            
            # JSON格式保存
            json_path = Path(f"callgraph_{base_name}_{language.value}_{timestamp}.json")
            save_call_graph_to_file(analyzer, language, json_path)
            
            # Markdown可视化保存
            md_path = Path(f"callgraph_{base_name}_{language.value}_{timestamp}.md")
            data = load_call_graph_from_file(json_path)
            if data:
                generate_call_graph_visualization(data, md_path)
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()


def analyze_directory(analyzer: MultiLanguageAnalyzer, dir_path: Path, language: LanguageType, save_output: bool = False):
    """分析目录"""
    print(f"📁 分析目录: {dir_path}")
    print(f"🔧 语言类型: {language.value.upper()}")
    print("-" * 50)
    
    try:
        # 分析目录
        analyzer.analyze_directory(str(dir_path), language)
        
        # 获取统计信息
        stats = analyzer.get_statistics(language)
        features = analyzer.get_language_specific_features(language)
        
        # 显示总体统计
        print(f"📊 目录分析统计:")
        print(f"  📁 模块数: {stats.modules_count}")
        print(f"  🔧 函数数: {stats.functions_count}")
        print(f"  📦 结构体数: {stats.structs_count}")
        print(f"  🔗 调用关系: {stats.call_relationships}")
        
        # 显示语言特定特性
        if features:
            print(f"\n🎯 {language.value.upper()}特性统计:")
            for feature, count in features.items():
                if count > 0:
                    print(f"  {feature}: {count}")
        
        # 获取和显示文件列表
        files = list(dir_path.rglob(f"*{analyzer.parsers[language].config.file_extensions[0]}"))
        if files:
            print(f"\n📄 已分析文件:")
            for file_path in files:
                rel_path = file_path.relative_to(dir_path)
                print(f"  📄 {rel_path}")
        
        # 显示最活跃的函数
        most_called = analyzer.get_most_called_functions(language, top_n=5)
        if most_called:
            print(f"\n🏆 最常被调用的函数:")
            for func_name, count in most_called:
                print(f"  {func_name}: {count} 次")
        
        most_calling = analyzer.get_most_calling_functions(language, top_n=5)
        if most_calling:
            print(f"\n📞 调用最多函数的函数:")
            for func_name, count in most_calling:
                print(f"  {func_name}: 调用 {count} 个函数")
        
        print(f"\n✅ 目录分析完成!")
        
        # 保存call graph到文件
        if save_output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dir_name = dir_path.name
            
            # JSON格式保存
            json_path = Path(f"callgraph_{dir_name}_{language.value}_{timestamp}.json")
            save_call_graph_to_file(analyzer, language, json_path)
            
            # Markdown可视化保存
            md_path = Path(f"callgraph_{dir_name}_{language.value}_{timestamp}.md")
            data = load_call_graph_from_file(json_path)
            if data:
                generate_call_graph_visualization(data, md_path)
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="多语言代码分析器 Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python demo.py contracts/Token.sol          # 分析单个Solidity文件
  python demo.py rust_examples/ --save        # 分析Rust目录并保存call graph
  python demo.py move_examples/basic_move.move # 分析Move文件
  python demo.py cpp_examples/ --lang cpp     # 强制指定语言类型
  python demo.py --load callgraph.json        # 从文件加载call graph
  python demo.py --visualize callgraph.json   # 生成call graph可视化
        """
    )
    
    parser.add_argument('path', nargs='?', help='要分析的文件或目录路径')
    parser.add_argument('--lang', choices=['solidity', 'rust', 'cpp', 'move'], 
                       help='强制指定语言类型（可选，默认自动检测）')
    parser.add_argument('--save', '-s', action='store_true',
                       help='保存call graph到JSON和Markdown文件')
    parser.add_argument('--load', '-l', type=str,
                       help='从JSON文件加载并显示call graph')
    parser.add_argument('--visualize', type=str,
                       help='从JSON文件生成Markdown可视化')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='显示详细信息')
    
    args = parser.parse_args()
    
    # 处理加载call graph的情况
    if args.load:
        load_path = Path(args.load)
        if not load_path.exists():
            print(f"❌ 错误: JSON文件 '{args.load}' 不存在")
            sys.exit(1)
        
        data = load_call_graph_from_file(load_path)
        if data:
            display_loaded_call_graph(data)
        return
    
    # 处理生成可视化的情况
    if args.visualize:
        load_path = Path(args.visualize)
        if not load_path.exists():
            print(f"❌ 错误: JSON文件 '{args.visualize}' 不存在")
            sys.exit(1)
        
        data = load_call_graph_from_file(load_path)
        if data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"visualization_{data['language']}_{timestamp}.md")
            generate_call_graph_visualization(data, output_path)
        return
    
    # 检验路径 (只有在不是load/visualize模式时才需要)
    if not args.path:
        print("❌ 错误: 需要提供分析路径，或使用 --load/--visualize 参数")
        parser.print_help()
        sys.exit(1)
    
    path = Path(args.path)
    if not path.exists():
        print(f"❌ 错误: 路径 '{args.path}' 不存在")
        sys.exit(1)
    
    # 确定语言类型
    if args.lang:
        language = LanguageType(args.lang)
        print(f"🔧 使用指定语言: {language.value.upper()}")
    else:
        language = detect_language_from_path(path)
        if language is None:
            print(f"❌ 错误: 无法自动检测语言类型，请使用 --lang 参数指定")
            print("支持的语言: solidity, rust, cpp, move")
            sys.exit(1)
        print(f"🔍 自动检测语言: {language.value.upper()}")
    
    print(f"\n🚀 多语言代码分析器 Demo")
    print("=" * 60)
    
    # 创建分析器
    analyzer = MultiLanguageAnalyzer()
    
    # 根据路径类型进行分析
    if path.is_file():
        analyze_single_file(analyzer, path, language, save_output=args.save)
    else:
        analyze_directory(analyzer, path, language, save_output=args.save)
    
    print("\n" + "=" * 60)
    print("🎉 Demo 运行完成!")
    print("\n📖 更多功能:")
    print("  - 使用 --save 参数保存call graph到JSON和Markdown文件")
    print("  - 使用 --load 参数从JSON文件加载call graph")
    print("  - 使用 --visualize 参数生成call graph可视化")
    print("  - 使用 --lang 参数强制指定语言类型")
    print("  - 支持分析单个文件或整个目录")
    print("  - 自动生成调用图和语言特性统计")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("🚀 多语言代码分析器 Demo")
        print("=" * 40)
        print("使用方法: python demo.py <文件路径或目录路径>")
        print("")
        print("📁 可用的示例目录:")
        example_dirs = ['contracts', 'rust_examples', 'cpp_examples', 'move_examples']
        for dir_name in example_dirs:
            if Path(dir_name).exists():
                print(f"  📁 {dir_name}/")
        
        print("\n📄 示例命令:")
        print("  python demo.py contracts/Token.sol")
        print("  python demo.py rust_examples/ --save")
        print("  python demo.py --load callgraph.json")
        print("  python demo.py --help")
        
        sys.exit(0)
    
    main() 