#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
函数依赖图分析 Demo
测试递归上游和下游函数分析功能

使用方法:
    python dependency_demo.py <文件路径> <函数名>
    python dependency_demo.py contracts/Token.sol transfer
    python dependency_demo.py rust_examples/ distance_from_origin
    python dependency_demo.py --help
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from analyzers import MultiLanguageAnalyzer, LanguageType


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


def analyze_function_dependencies(analyzer: MultiLanguageAnalyzer, path: Path, function_name: str, 
                                language: LanguageType, max_depth: int = 10, visualize: bool = False,
                                save_image: bool = False, mermaid: bool = False, output_dir: str = "dependency_graphs"):
    """分析函数依赖关系"""
    print(f"🚀 函数依赖图分析 Demo")
    print("=" * 60)
    print(f"📄 分析路径: {path}")
    print(f"🔧 目标函数: {function_name}")
    print(f"🔧 语言类型: {language.value.upper()}")
    print(f"🔍 分析深度: {max_depth} 层")
    print("-" * 60)

    try:
        # 分析代码
        if path.is_file():
            analyzer.analyze_file(str(path), language)
        else:
            analyzer.analyze_directory(str(path), language)

        # 获取所有函数列表
        functions = analyzer.get_functions(language)
        
        print(f"\n📋 可用函数列表 ({len(functions)} 个):")
        for i, (func_name, func_info) in enumerate(functions.items(), 1):
            if i <= 10:  # 只显示前10个
                print(f"  {i:2d}. {func_info.name} ({func_info.visibility})")
            elif i == 11:
                print(f"  ... 还有 {len(functions) - 10} 个函数")

        # 查找目标函数 - 支持模糊匹配
        target_function_full_name = None
        matching_functions = []
        
        for func_full_name, func_info in functions.items():
            if func_info.name == function_name:
                target_function_full_name = func_full_name
                break
            elif function_name.lower() in func_info.name.lower():
                matching_functions.append((func_full_name, func_info))

        # 如果没有找到精确匹配，尝试模糊匹配
        if not target_function_full_name and matching_functions:
            if len(matching_functions) == 1:
                target_function_full_name = matching_functions[0][0]
                print(f"\n🔍 使用模糊匹配找到函数: {matching_functions[0][1].name}")
            else:
                print(f"\n❓ 找到多个匹配的函数:")
                for i, (full_name, func_info) in enumerate(matching_functions, 1):
                    print(f"  {i}. {func_info.name} ({func_info.visibility})")
                target_function_full_name = matching_functions[0][0]
                print(f"\n🎯 使用第一个匹配: {matching_functions[0][1].name}")

        if not target_function_full_name:
            print(f"\n❌ 错误: 未找到函数 '{function_name}'")
            print("💡 请检查函数名是否正确，或尝试上述列表中的函数名")
            return

        # 进行依赖图分析
        print(f"\n🔬 开始分析函数依赖关系...")
        analyzer.print_dependency_graph(target_function_full_name, language, max_depth)

        # 额外显示一些统计信息
        dependency_graph = analyzer.get_function_dependency_graph(target_function_full_name, language, max_depth)
        
        upstream = dependency_graph['upstream_functions']
        downstream = dependency_graph['downstream_functions']

        print(f"\n📈 详细统计:")
        if upstream:
            print(f"  ⬆️  上游函数列表:")
            for func, depth in sorted(upstream.items(), key=lambda x: x[1]):
                print(f"    └─ 深度{depth}: {func}")

        if downstream:
            print(f"  ⬇️  下游函数列表:")
            for func, depth in sorted(downstream.items(), key=lambda x: x[1]):
                print(f"    └─ 深度{depth}: {func}")

        # 分析函数复杂度
        complexity_score = len(upstream) + len(downstream) * 2  # 下游权重更高
        if complexity_score == 0:
            complexity = "🟢 简单"
        elif complexity_score <= 5:
            complexity = "🟡 中等"
        elif complexity_score <= 10:
            complexity = "🟠 复杂"
        else:
            complexity = "🔴 高度复杂"

        print(f"\n🎯 函数复杂度评估:")
        print(f"  📊 复杂度分数: {complexity_score}")
        print(f"  🎨 复杂度等级: {complexity}")
        
        if complexity_score > 5:
            print(f"  💡 建议: 考虑重构以降低函数依赖复杂度")

        print(f"\n✅ 依赖图分析完成!")
        
        # 可视化功能
        if visualize or save_image or mermaid:
            print(f"\n🎨 生成可视化图表...")
            
            # 生成可视化图表
            if visualize:
                print("📊 显示交互式图表...")
                analyzer.visualize_dependency_graph(
                    target_function_full_name, language, max_depth, 
                    save_path=None, show_plot=True
                )
            
            # 保存图片
            if save_image:
                print("💾 保存依赖图到图片文件...")
                saved_path = analyzer.save_dependency_graph_image(
                    target_function_full_name, language, max_depth, output_dir
                )
                if saved_path:
                    print(f"📁 图片已保存到: {saved_path}")
            
            # 生成Mermaid图表
            if mermaid:
                print("🧜‍♀️ 生成Mermaid图表...")
                mermaid_code = analyzer.generate_dependency_mermaid(
                    target_function_full_name, language, max_depth
                )
                
                # 保存Mermaid代码到文件
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_func_name = function_name.replace('.', '_').replace('::', '_')
                mermaid_filename = f"dependency_{safe_func_name}_{language.value}_{timestamp}.mmd"
                
                with open(mermaid_filename, 'w', encoding='utf-8') as f:
                    f.write(mermaid_code)
                
                print(f"📁 Mermaid图表已保存到: {mermaid_filename}")
                print("🔗 你可以在Mermaid编辑器中查看: https://mermaid.live/")
                
                # 如果设置了verbose，也打印到控制台
                if True:  # 总是显示Mermaid代码
                    print(f"\n🧜‍♀️ Mermaid图表代码:")
                    print("```mermaid")
                    print(mermaid_code)
                    print("```")

    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="函数依赖图分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python dependency_demo.py contracts/Token.sol transfer      # 分析Token合约的transfer函数
  python dependency_demo.py rust_examples/ distance_from_origin  # 分析Rust函数
  python dependency_demo.py move_examples/ init_coin --depth 3   # 限制分析深度
  python dependency_demo.py contracts/DEX.sol swap --lang solidity  # 强制指定语言
  python dependency_demo.py contracts/Token.sol _transfer --visualize  # 显示可视化图表
  python dependency_demo.py contracts/Token.sol _transfer --save-image  # 保存为图片
  python dependency_demo.py contracts/Token.sol _transfer --mermaid     # 生成Mermaid图表
        """
    )

    parser.add_argument('path', help='要分析的文件或目录路径')
    parser.add_argument('function_name', help='要分析的函数名')
    parser.add_argument('--lang', choices=['solidity', 'rust', 'cpp', 'move'], 
                       help='强制指定语言类型（可选，默认自动检测）')
    parser.add_argument('--depth', '-d', type=int, default=10,
                       help='最大递归深度（默认10层）')
    parser.add_argument('--visualize', action='store_true',
                       help='生成可视化图表')
    parser.add_argument('--save-image', action='store_true',
                       help='保存依赖图为图片文件')
    parser.add_argument('--mermaid', action='store_true',
                       help='生成Mermaid格式的图表')
    parser.add_argument('--output-dir', default='dependency_graphs',
                       help='图片输出目录（默认dependency_graphs）')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='显示详细信息')

    args = parser.parse_args()

    # 检验路径
    path = Path(args.path)
    if not path.exists():
        print(f"❌ 错误: 路径 '{args.path}' 不存在")
        sys.exit(1)

    # 确定语言类型
    if args.lang:
        language_map = {
            'solidity': LanguageType.SOLIDITY,
            'rust': LanguageType.RUST,
            'cpp': LanguageType.CPP,
            'move': LanguageType.MOVE
        }
        language = language_map[args.lang]
        print(f"🔧 强制指定语言: {language.value.upper()}")
    else:
        language = detect_language_from_path(path)
        if not language:
            print(f"❌ 错误: 无法检测语言类型，请使用 --lang 参数指定")
            print("💡 支持的语言: solidity, rust, cpp, move")
            sys.exit(1)
        print(f"🔍 自动检测语言: {language.value.upper()}")

    # 创建分析器
    analyzer = MultiLanguageAnalyzer()

    # 分析函数依赖
    analyze_function_dependencies(analyzer, path, args.function_name, language, args.depth,
                                 args.visualize, args.save_image, args.mermaid, args.output_dir)

    print("\n" + "=" * 60)
    print("🎉 依赖分析 Demo 运行完成!")
    print("\n📖 更多功能:")
    print("  - 使用 --depth 参数控制递归深度")
    print("  - 使用 --lang 参数强制指定语言类型")
    print("  - 使用 --visualize 参数显示交互式图表")
    print("  - 使用 --save-image 参数保存依赖图为图片")
    print("  - 使用 --mermaid 参数生成Mermaid格式图表")
    print("  - 支持模糊匹配函数名")
    print("  - 自动评估函数复杂度")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，退出程序")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        print("\n📄 示例命令:")
        print("  python dependency_demo.py contracts/Token.sol transfer")
        print("  python dependency_demo.py rust_examples/ distance_from_origin")
        print("  python dependency_demo.py --help") 