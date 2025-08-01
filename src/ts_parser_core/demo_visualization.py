#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
递归依赖图可视化功能演示
展示所有可视化选项和功能
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """运行命令并显示描述"""
    print(f"\n🚀 {description}")
    print(f"📝 命令: {cmd}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
        if result.returncode == 0:
            print(f"✅ {description} 完成")
        else:
            print(f"❌ {description} 失败")
    except Exception as e:
        print(f"❌ 运行失败: {e}")

def main():
    """主演示函数"""
    print("🎨 递归依赖图可视化功能完整演示")
    print("=" * 60)
    print("🎯 本演示将展示所有可视化功能和输出格式")
    print("📊 支持Solidity、Rust、C++、Move四种语言")
    print("🎮 包含PNG图片、Mermaid图表等多种输出")
    
    # 确保在正确的目录
    demo_dir = Path(__file__).parent
    os.chdir(demo_dir)
    
    # 激活虚拟环境的命令前缀
    venv_prefix = "source .venv/bin/activate && " if Path(".venv").exists() else ""
    
    # 创建输出目录
    output_dir = "visualization_demo"
    Path(output_dir).mkdir(exist_ok=True)
    
    print(f"\n📁 输出目录: {output_dir}/")
    
    # 演示1: Solidity函数可视化
    run_command(
        f"{venv_prefix}python3 dependency_demo.py contracts/Token.sol _transfer --save-image --mermaid --output-dir {output_dir}",
        "演示1: Solidity _transfer函数依赖图可视化"
    )
    
    # 演示2: Rust函数可视化  
    run_command(
        f"{venv_prefix}python3 dependency_demo.py rust_examples/ distance_from_origin --save-image --mermaid --output-dir {output_dir}",
        "演示2: Rust distance_from_origin函数依赖图可视化"
    )
    
    # 演示3: 复杂函数的深度分析
    run_command(
        f"{venv_prefix}python3 dependency_demo.py contracts/Token.sol transferFrom --save-image --mermaid --depth 3 --output-dir {output_dir}",
        "演示3: Solidity transferFrom函数深度依赖分析"
    )
    
    # 检查生成的文件
    print(f"\n📊 检查生成的文件:")
    print("-" * 60)
    
    png_files = list(Path(output_dir).glob("*.png"))
    mmd_files = list(Path(".").glob("dependency_*.mmd"))
    
    print(f"📄 生成的PNG图片文件 ({len(png_files)} 个):")
    for png_file in png_files:
        size = png_file.stat().st_size / 1024  # KB
        print(f"  📊 {png_file.name} (大小: {size:.1f} KB)")
    
    print(f"\n📄 生成的Mermaid文件 ({len(mmd_files)} 个):")
    for mmd_file in mmd_files:
        with open(mmd_file, 'r', encoding='utf-8') as f:
            lines = len(f.readlines())
        print(f"  🧜‍♀️ {mmd_file.name} (行数: {lines})")
    
    # 显示使用说明
    print(f"\n💡 使用生成的文件:")
    print("-" * 60)
    print("📊 PNG图片文件:")
    print("  - 可以直接在图片查看器中打开")
    print("  - 适合插入到文档、报告、PPT中")
    print("  - 高分辨率，适合打印")
    
    print("\n🧜‍♀️ Mermaid图表文件:")
    print("  - 访问 https://mermaid.live/ 查看交互式图表")
    print("  - 可以嵌入到Markdown文档中")
    print("  - 支持在GitHub、GitLab等平台直接显示")
    print("  - 可以进一步编辑和自定义样式")
    
    print(f"\n🎯 功能总结:")
    print("-" * 60)
    print("✅ 递归上游函数分析: 找出调用目标函数的所有函数")
    print("✅ 递归下游函数分析: 找出目标函数调用的所有函数") 
    print("✅ 智能层次化布局: 上游在上方，下游在下方，目标居中")
    print("✅ 美观色彩编码: 红色目标，青色上游，绿色下游")
    print("✅ 深度可视化: 不同递归深度用颜色和大小区分")
    print("✅ 多格式输出: PNG图片、Mermaid图表、交互式显示")
    print("✅ 全语言支持: Solidity、Rust、C++、Move")
    print("✅ 智能文件命名: 包含函数名、语言、时间戳")
    print("✅ 可配置选项: 深度控制、输出目录、显示选项")
    
    print(f"\n🚀 快速使用命令:")
    print("-" * 60)
    print("# 基础分析")
    print("python3 dependency_demo.py contracts/Token.sol _transfer")
    print("\n# 生成可视化")
    print("python3 dependency_demo.py contracts/Token.sol _transfer --save-image --mermaid")
    print("\n# 深度分析")
    print("python3 dependency_demo.py contracts/Token.sol transferFrom --depth 3 --save-image")
    print("\n# 自定义目录")
    print("python3 dependency_demo.py rust_examples/ distance_from_origin --save-image --output-dir graphs/")
    
    print(f"\n🎉 可视化功能演示完成!")
    print(f"📁 查看生成的文件: ls -la {output_dir}/ && ls -la dependency_*.mmd")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc() 