# 新代码总结器模块 - 增量式业务流程分析系统
# New Code Summarizer Module - Incremental Business Flow Analysis System

from typing import Dict, List, Any

# 版本信息
__version__ = "3.1.0"  # 新增强化分析和文件夹级别分析功能
__author__ = "Finite Monkey Engine Team"

# Token管理组件
from .token_calculator import (
    TokenCalculator,
    TokenUsage,
    quick_token_check,
    estimate_file_tokens,
    suggest_optimal_batching
)

# 业务流程分析组件
from .business_flow_analyzer import (
    BusinessFlowAnalyzer,
    BusinessFlowStepResult, 
    FolderAnalysisResult,
    CompleteBusinessFlowResult,
    analyze_business_flow,
    analyze_business_flow_from_path
)

# 智能业务流程分析函数 - 新增主要API
def smart_business_flow_analysis(project_path: str, 
                               project_name: str = None,
                               enable_reinforcement: bool = True,
                               file_extensions: List[str] = ['.sol', '.py', '.js', '.ts']) -> CompleteBusinessFlowResult:
    """智能业务流程分析 - 自动选择最佳策略
    
    Args:
        project_path: 项目路径
        project_name: 项目名称（可选）
        enable_reinforcement: 是否启用强化分析，提升Mermaid图质量
        file_extensions: 要分析的文件扩展名
        
    Returns:
        完整的业务流程分析结果
        
    Features:
        - 自动检测项目规模，选择增量或文件夹级别分析
        - 强化分析功能，多轮优化Mermaid图
        - 支持大型多文件夹项目的层次化分析
    """
    from pathlib import Path
    
    project_path = Path(project_path)
    if not project_name:
        project_name = project_path.name
    
    # 读取项目文件
    files_content = {}
    for ext in file_extensions:
        for file_path in project_path.glob(f"**/*{ext}"):  # 使用递归搜索
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        relative_path = str(file_path.relative_to(project_path))
                        files_content[relative_path] = content
                except Exception as e:
                    import logging
                    logging.warning(f"读取文件 {file_path} 失败: {e}")
    
    # 使用智能分析器
    analyzer = BusinessFlowAnalyzer()
    return analyzer.analyze_business_flow_smart(files_content, project_name, enable_reinforcement)

def smart_business_flow_analysis_from_content(files_content: Dict[str, str], 
                                            project_name: str,
                                            enable_reinforcement: bool = True) -> CompleteBusinessFlowResult:
    """从文件内容进行智能业务流程分析
    
    Args:
        files_content: 文件内容映射
        project_name: 项目名称
        enable_reinforcement: 是否启用强化分析
        
    Returns:
        完整的业务流程分析结果
    """
    analyzer = BusinessFlowAnalyzer()
    return analyzer.analyze_business_flow_smart(files_content, project_name, enable_reinforcement)

# 便捷的强化分析函数
def reinforced_business_flow_analysis(project_path: str, 
                                    project_name: str = None) -> CompleteBusinessFlowResult:
    """启用强化分析的业务流程分析
    
    Args:
        project_path: 项目路径
        project_name: 项目名称
        
    Returns:
        强化分析后的完整结果
    """
    return smart_business_flow_analysis(project_path, project_name, enable_reinforcement=True)

# 保留原有的快速分析功能
def quick_business_flow_analysis(project_path: str, project_name: str = None) -> CompleteBusinessFlowResult:
    """快速业务流程分析（原有API兼容）
    
    Args:
        project_path: 项目路径
        project_name: 项目名称（可选）
        
    Returns:
        完整的业务流程分析结果
    """
    return analyze_business_flow_from_path(project_path, project_name)

# 主要API导出
__all__ = [
    # Token管理组件
    "TokenCalculator",
    "TokenUsage",
    "quick_token_check",
    "estimate_file_tokens",
    "suggest_optimal_batching",
    
    # 业务流程分析组件
    "BusinessFlowAnalyzer",
    "BusinessFlowStepResult", 
    "FolderAnalysisResult",
    "CompleteBusinessFlowResult",
    "analyze_business_flow",
    "analyze_business_flow_from_path",
    
    # 新增智能分析API（推荐使用）
    "smart_business_flow_analysis",
    "smart_business_flow_analysis_from_content", 
    "reinforced_business_flow_analysis",
    
    # 兼容性API
    "quick_business_flow_analysis",
]

def print_usage():
    """打印使用说明"""
    
    usage_text = """
🚀 FiniteMonkey 智能业务流程分析器 v3.1
=============================================

🎯 主要功能：
   ✨ 智能分析策略 - 自动选择增量或文件夹级别分析
   ✨ 强化分析 - 多轮优化，提升Mermaid图质量和细节
   ✨ 文件夹级别分析 - 支持大型多文件夹项目
   ✨ Token智能管理 - 优化API成本
   ✨ 多种文件格式支持 - Solidity, Python, JavaScript等

📖 推荐用法（新版智能API）：

from code_summarizer import smart_business_flow_analysis

# 智能分析（推荐）- 自动选择最佳策略
result = smart_business_flow_analysis(
    project_path='path/to/project', 
    project_name='ProjectName',
    enable_reinforcement=True  # 启用强化分析
)

# 查看分析结果
print(f"分析策略: {result.analysis_strategy}")  # "incremental" 或 "folder_based"
print(f"总Token使用: {result.total_token_usage.total_tokens:,}")
print(f"置信度: {result.overall_confidence:.2f}")

if result.analysis_strategy == "folder_based":
    # 文件夹级别分析结果
    print(f"全局架构图: {result.global_mermaid_graph}")
    for folder_path, folder_result in result.folder_analyses.items():
        print(f"文件夹 {folder_path}: {folder_result.folder_mermaid_graph}")
else:
    # 增量分析结果
    print(f"项目流程图: {result.final_mermaid_graph}")

🔧 高级用法：

from code_summarizer import BusinessFlowAnalyzer

analyzer = BusinessFlowAnalyzer()
result = analyzer.analyze_business_flow_smart(
    files_content, 
    project_name,
    enable_reinforcement=True
)

# 查看强化分析步骤
for step in result.analysis_steps:
    if step.is_reinforcement:
        print(f"强化步骤 {step.step_id}: {step.files_analyzed}")

💡 新特性：
   • 🤖 智能策略选择 - 小项目用增量，大项目用文件夹级别
   • 🔄 强化分析 - 多轮优化提升Mermaid图质量
   • 📁 文件夹级别分析 - 支持复杂项目结构
   • 📊 层次化结果 - 项目级 + 文件夹级双重视图
   • 🎯 防御性逻辑 - 通过prompt强化避免信息丢失

📊 适用场景：
   • 小型项目（<30文件）→ 增量分析 + 强化分析
   • 大型项目（≥30文件）→ 文件夹级别分析 + 全局概览
   • 复杂项目（多文件夹）→ 层次化分析 + 强化分析

📚 支持的文件类型：
   • Solidity (.sol)     • Python (.py)
   • JavaScript (.js)    • TypeScript (.ts)
   • Rust (.rs)         • Move (.move)
   • Cairo (.cairo)     • 更多...

🎯 最佳实践：
   • 使用 smart_business_flow_analysis() 获得最佳体验
   • 对重要项目启用 enable_reinforcement=True
   • 大项目关注 result.folder_analyses 的详细结果
   • 查看 result.analysis_strategy 了解使用的分析策略

更多信息请查看 README.md
"""
    
    print(usage_text)

# 模块信息
def get_module_info():
    """获取模块信息"""
    return {
        "name": "code_summarizer",
        "version": __version__,
        "description": "智能业务流程分析器",
        "new_features": [
            "智能分析策略选择",
            "强化分析和多轮优化",
            "文件夹级别分析",
            "层次化结果输出",
            "防御性逻辑设计"
        ],
        "recommended_api": "smart_business_flow_analysis",
        "components": [
            "BusinessFlowAnalyzer",
            "TokenCalculator",
        ]
    }

if __name__ == "__main__":
    print_usage() 