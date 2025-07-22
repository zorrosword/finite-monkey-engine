# 业务流程分析器 - 增量式业务流程分析和Mermaid图生成
# Business Flow Analyzer - Incremental Business Flow Analysis and Mermaid Generation

import os
import sys
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# 添加项目根目录到path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from openai_api.openai import ask_claude_for_code_analysis
from .token_calculator import TokenCalculator, TokenUsage

logger = logging.getLogger(__name__)

@dataclass
class BusinessFlowStepResult:
    """业务流程分析步骤结果"""
    step_id: int
    files_analyzed: List[str]
    flow_description: str
    key_interactions: List[Dict[str, str]]
    mermaid_fragment: str
    token_usage: TokenUsage
    is_reinforcement: bool = False  # 标识是否为强化分析

@dataclass
class FolderAnalysisResult:
    """文件夹级别的分析结果"""
    folder_path: str
    folder_name: str
    files_count: int
    analysis_steps: List[BusinessFlowStepResult]
    folder_mermaid_graph: str
    folder_summary: str
    token_usage: TokenUsage

@dataclass
class CompleteBusinessFlowResult:
    """完整业务流程分析结果"""
    project_name: str
    total_files: int
    analysis_strategy: str  # "incremental" 或 "folder_based"
    
    # 增量分析结果（单一项目）
    analysis_steps: List[BusinessFlowStepResult]
    final_mermaid_graph: str
    business_summary: str
    
    # 文件夹分析结果（大项目）
    folder_analyses: Dict[str, FolderAnalysisResult]
    global_mermaid_graph: str  # 项目整体概览图
    
    total_token_usage: TokenUsage

class BusinessFlowAnalyzer:
    """业务流程分析器 - 增量式分析和流程图生成"""
    
    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        """初始化业务流程分析器
        
        Args:
            model: 使用的AI模型名称
        """
        self.model = model
        self.token_calculator = TokenCalculator()
        self.analysis_history: List[BusinessFlowStepResult] = []
        
        # 文件夹分析配置
        self.LARGE_PROJECT_THRESHOLD = 20  # 降低阈值，超过20个文件认为是大项目
        self.MAX_FILES_PER_FOLDER = 10     # 每个文件夹最多分析10个文件
        
        logger.info(f"🚀 初始化业务流程分析器，模型: {model}")
        logger.info(f"📊 Mermaid图生成日志已启用")

    def _log_mermaid_generation_start(self, context: str, file_info: str = ""):
        """记录Mermaid生成开始日志"""
        logger.info(f"🎨 开始生成Mermaid图: {context}")
        if file_info:
            logger.info(f"📁 处理文件: {file_info}")

    def _log_mermaid_generation_result(self, mermaid_content: str, context: str = "", 
                                     step_id: int = 0):
        """记录Mermaid生成结果日志"""
        if not mermaid_content:
            logger.warning(f"⚠️  Mermaid图生成失败或为空: {context}")
            return
        
        # 简单统计Mermaid图信息
        lines = mermaid_content.split('\n')
        total_lines = len(lines)
        interaction_lines = [line for line in lines if '->>' in line or '-->' in line]
        
        logger.info(f"✅ Mermaid图生成成功: {context}")
        logger.info(f"📏 图表规模 - 总行数: {total_lines}, 交互: {len(interaction_lines)}")
        
        if step_id > 0:
            logger.info(f"🔄 分析步骤: {step_id}")

    def _log_mermaid_optimization(self, original_length: int, optimized_length: int, context: str):
        """记录Mermaid优化过程日志"""
        if optimized_length == 0:
            logger.warning(f"❌ Mermaid图优化失败: {context}")
            return
        
        change_percent = ((optimized_length - original_length) / original_length * 100) if original_length > 0 else 0
        
        if abs(change_percent) > 5:
            direction = "扩展" if change_percent > 0 else "精简"
            logger.info(f"📈 Mermaid图{direction}: {context} ({change_percent:+.1f}%, {original_length}→{optimized_length}字符)")
        else:
            logger.info(f"🔧 Mermaid图优化完成: {context} ({original_length}→{optimized_length}字符)")

    def _log_folder_merge(self, folder_count: int, total_diagrams: int, context: str):
        """记录文件夹图表合并过程日志"""
        logger.info(f"🔀 合并多文件夹图表: {context}")
        logger.info(f"📊 合并统计 - 文件夹数: {folder_count}, 图表数: {total_diagrams}")

    def analyze_business_flow_smart(self, 
                                  files_content: Dict[str, str],
                                  project_name: str,
                                  enable_reinforcement: bool = True) -> CompleteBusinessFlowResult:
        """智能业务流程分析 - 自动选择增量或文件夹级别分析
        
        Args:
            files_content: 文件内容映射
            project_name: 项目名称
            enable_reinforcement: 是否启用强化分析
            
        Returns:
            完整的业务流程分析结果
        """
        logger.info(f"🎯 开始智能业务流程分析: {project_name} ({len(files_content)} 个文件)")
        
        # 判断使用哪种分析策略
        if len(files_content) <= self.LARGE_PROJECT_THRESHOLD and not self._has_complex_folder_structure(files_content):
            # 小型项目：使用增量分析
            logger.info("🔍 检测到小型项目，使用增量分析策略")
            return self._analyze_with_incremental_strategy(files_content, project_name, enable_reinforcement)
        else:
            # 大型项目：使用文件夹级别分析
            logger.info("🏢 检测到大型项目，使用文件夹级别分析策略")
            return self._analyze_with_folder_strategy(files_content, project_name, enable_reinforcement)
    
    def _has_complex_folder_structure(self, files_content: Dict[str, str]) -> bool:
        """检测是否有复杂的文件夹结构"""
        folder_set = set()
        for file_path in files_content.keys():
            # 获取文件夹路径
            folder = str(Path(file_path).parent)
            if folder != '.':
                folder_set.add(folder)
        
        # 如果有2个以上不同的文件夹，认为结构复杂，使用文件夹模式
        is_complex = len(folder_set) >= 2
        logger.info(f"📂 文件夹结构检测 - 发现 {len(folder_set)} 个文件夹，{'使用文件夹模式' if is_complex else '使用单一模式'}")
        return is_complex
    
    def _analyze_with_incremental_strategy(self, 
                                         files_content: Dict[str, str],
                                         project_name: str,
                                         enable_reinforcement: bool) -> CompleteBusinessFlowResult:
        """使用增量分析策略"""
        
        # 执行原有的增量分析
        incremental_result = self.analyze_business_flow_incremental(files_content, project_name)
        
        # 如果启用强化分析，进行多轮强化
        if enable_reinforcement:
            logger.info("💪 开始强化分析，提升Mermaid图质量")
            reinforced_result = self._perform_reinforcement_analysis(
                files_content, project_name, incremental_result)
            
            # 合并强化分析结果
            incremental_result.analysis_steps.extend(reinforced_result.analysis_steps)
            
            # 记录强化前后的对比
            original_length = len(incremental_result.final_mermaid_graph)
            incremental_result.final_mermaid_graph = reinforced_result.final_mermaid_graph
            final_length = len(incremental_result.final_mermaid_graph)
            
            self._log_mermaid_optimization(original_length, final_length, "强化分析")
            
            incremental_result.total_token_usage = self._merge_token_usage(
                incremental_result.total_token_usage, reinforced_result.total_token_usage)
        
        # 转换为统一格式
        return CompleteBusinessFlowResult(
            project_name=project_name,
            total_files=len(files_content),
            analysis_strategy="incremental",
            analysis_steps=incremental_result.analysis_steps,
            final_mermaid_graph=incremental_result.final_mermaid_graph,
            business_summary=incremental_result.business_summary,
            folder_analyses={},
            global_mermaid_graph=incremental_result.final_mermaid_graph,
            total_token_usage=incremental_result.total_token_usage
        )
    
    def _analyze_with_folder_strategy(self, 
                                    files_content: Dict[str, str],
                                    project_name: str,
                                    enable_reinforcement: bool) -> CompleteBusinessFlowResult:
        """使用文件夹级别分析策略"""
        
        # 按文件夹分组文件
        folder_groups = self._group_files_by_folder(files_content)
        logger.info(f"📂 项目分组完成 - 共 {len(folder_groups)} 个文件夹")
        
        # 分析每个文件夹
        folder_analyses = {}
        all_steps = []
        total_token_usage = TokenUsage(0, 0, 0, True, 200000, "")
        
        for folder_path, folder_files in folder_groups.items():
            logger.info(f"📂 分析文件夹: {folder_path} ({len(folder_files)} 个文件)")
            
            # 分析单个文件夹 - 使用增量分析
            folder_result = self._analyze_single_folder_incremental(
                folder_files, folder_path, project_name, enable_reinforcement)
            
            folder_analyses[folder_path] = folder_result
            all_steps.extend(folder_result.analysis_steps)
            total_token_usage = self._merge_token_usage(total_token_usage, folder_result.token_usage)
            
            # 记录文件夹分析结果
            self._log_mermaid_generation_result(
                folder_result.folder_mermaid_graph, 
                f"文件夹{folder_path}分析"
            )
        
        # 生成全局概览图 - 合并多个文件夹的diagram
        logger.info("🌐 合并多文件夹diagram生成全局业务流")
        global_mermaid = self._merge_folder_diagrams(folder_analyses, project_name)
        
        # 记录合并结果
        self._log_folder_merge(len(folder_analyses), sum(len(f.analysis_steps) for f in folder_analyses.values()), "全局业务流合并")
        
        return CompleteBusinessFlowResult(
            project_name=project_name,
            total_files=len(files_content),
            analysis_strategy="folder_based",
            analysis_steps=all_steps,
            final_mermaid_graph="",  # 文件夹模式下主要看各文件夹的图和全局图
            business_summary=f"{project_name}项目文件夹级别分析完成，共分析{len(folder_analyses)}个文件夹",
            folder_analyses=folder_analyses,
            global_mermaid_graph=global_mermaid,
            total_token_usage=total_token_usage
        )
    
    def _group_files_by_folder(self, files_content: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """按文件夹分组文件"""
        folder_groups = {}
        
        for file_path, content in files_content.items():
            folder = str(Path(file_path).parent)
            if folder == '.':
                folder = 'root'
            
            if folder not in folder_groups:
                folder_groups[folder] = {}
            
            folder_groups[folder][file_path] = content
        
        return folder_groups
    
    def _analyze_single_folder_incremental(self, 
                                         folder_files: Dict[str, str],
                                         folder_path: str,
                                         project_name: str,
                                         enable_reinforcement: bool) -> FolderAnalysisResult:
        """使用增量分析策略分析单个文件夹"""
        
        folder_name = Path(folder_path).name if folder_path != 'root' else 'root'
        
        # 如果文件夹文件太多，进行分批处理
        if len(folder_files) > self.MAX_FILES_PER_FOLDER:
            logger.warning(f"⚠️  文件夹 {folder_path} 文件数过多({len(folder_files)})，将只处理前{self.MAX_FILES_PER_FOLDER}个文件")
            # 按优先级选择前N个文件
            prioritized_files = self._prioritize_files_for_flow_analysis(folder_files)
            folder_files = dict(prioritized_files[:self.MAX_FILES_PER_FOLDER])
        
        # 对文件夹内文件进行增量分析
        logger.info(f"🔄 文件夹 {folder_path} 开始增量分析")
        temp_analyzer = BusinessFlowAnalyzer(self.model)
        folder_incremental_result = temp_analyzer.analyze_business_flow_incremental(
            folder_files, f"{project_name}_{folder_name}")
        
        # 如果启用强化分析
        if enable_reinforcement and len(folder_files) <= 5:  # 只有小文件夹才强化
            logger.info(f"💪 文件夹 {folder_path} 开始强化分析")
            reinforced_result = self._perform_reinforcement_analysis(
                folder_files, f"{project_name}_{folder_name}", folder_incremental_result)
            
            folder_incremental_result.analysis_steps.extend(reinforced_result.analysis_steps)
            folder_incremental_result.final_mermaid_graph = reinforced_result.final_mermaid_graph
        
        return FolderAnalysisResult(
            folder_path=folder_path,
            folder_name=folder_name,
            files_count=len(folder_files),
            analysis_steps=folder_incremental_result.analysis_steps,
            folder_mermaid_graph=folder_incremental_result.final_mermaid_graph,
            folder_summary=folder_incremental_result.business_summary,
            token_usage=folder_incremental_result.total_token_usage
        )
    
    def _perform_reinforcement_analysis(self, 
                                      files_content: Dict[str, str],
                                      project_name: str,
                                      base_result: 'CompleteBusinessFlowResult') -> 'CompleteBusinessFlowResult':
        """执行强化分析，提升Mermaid图的详细程度"""
        
        logger.info("💪 开始强化分析，增强Mermaid图细节")
        
        # 获取当前最佳的mermaid图
        current_mermaid = base_result.final_mermaid_graph
        original_length = len(current_mermaid)
        
        # 第一轮：选择最重要的文件进行强化分析
        important_files = self._select_files_for_reinforcement(files_content, base_result.analysis_steps)
        
        reinforcement_steps = []
        
        for file_path, content in important_files.items():
            logger.info(f"🔧 强化分析文件: {file_path}")
            
            # 执行强化分析
            reinforced_step = self._analyze_file_for_reinforcement(
                file_path, content, current_mermaid, project_name, len(reinforcement_steps) + 1)
            
            reinforcement_steps.append(reinforced_step)
            
            # 记录强化步骤结果
            self._log_mermaid_generation_result(
                reinforced_step.mermaid_fragment, 
                f"强化分析-{file_path}", 
                reinforced_step.step_id
            )
            
            # 更新当前mermaid图
            prev_length = len(current_mermaid)
            current_mermaid = reinforced_step.mermaid_fragment
            current_length = len(current_mermaid)
            
            self._log_mermaid_optimization(prev_length, current_length, f"强化步骤{reinforced_step.step_id}")
        
        # 🆕 第二轮：专门补充被遗漏的getter/setter函数
        logger.info("🔍 开始第二轮强化：专门查找被遗漏的getter/setter函数")
        getter_setter_step = self._analyze_missing_getter_setter_functions(
            files_content, current_mermaid, project_name, len(reinforcement_steps) + 1)
        
        if getter_setter_step:
            reinforcement_steps.append(getter_setter_step)
            
            # 记录getter/setter补充结果
            prev_length = len(current_mermaid)
            current_mermaid = getter_setter_step.mermaid_fragment
            current_length = len(current_mermaid)
            
            self._log_mermaid_generation_result(
                current_mermaid, 
                "Getter/Setter补充分析", 
                getter_setter_step.step_id
            )
            
            self._log_mermaid_optimization(prev_length, current_length, "Getter/Setter补充")
        
        # 记录总体强化效果
        final_length = len(current_mermaid)
        improvement_percent = ((final_length - original_length) / original_length * 100) if original_length > 0 else 0
        logger.info(f"🎉 强化分析完成 - 图表改进了 {improvement_percent:+.1f}% ({original_length}→{final_length}字符)")
        
        # 计算强化分析的token使用量
        reinforcement_token_usage = self._calculate_total_token_usage(
            reinforcement_steps, TokenUsage(0, 0, 0, True, 200000, ""))
        
        return CompleteBusinessFlowResult(
            project_name=f"{project_name}_reinforced",
            total_files=len(important_files),
            analysis_strategy="reinforcement",
            analysis_steps=reinforcement_steps,
            final_mermaid_graph=current_mermaid,
            business_summary=f"{project_name}强化分析完成",
            folder_analyses={},
            global_mermaid_graph=current_mermaid,
            total_token_usage=reinforcement_token_usage
        )
    
    def _analyze_missing_getter_setter_functions(self, 
                                               files_content: Dict[str, str],
                                               current_mermaid: str,
                                               project_name: str,
                                               step_id: int) -> Optional[BusinessFlowStepResult]:
        """专门分析可能被遗漏的getter/setter函数"""
        
        logger.info("🔍 分析可能被遗漏的getter/setter函数")
        
        # 提取所有文件中的getter/setter函数
        all_getter_setter_functions = self._extract_getter_setter_functions(files_content)
        
        if not all_getter_setter_functions:
            logger.info("❌ 未发现明显的getter/setter函数")
            return None
        
        # 检查哪些函数可能被遗漏了
        missing_functions = []
        for func_info in all_getter_setter_functions:
            if func_info['name'] not in current_mermaid:
                missing_functions.append(func_info)
        
        if not missing_functions:
            logger.info("✅ 所有getter/setter函数都已覆盖")
            return None
        
        logger.info(f"🎯 发现 {len(missing_functions)} 个可能被遗漏的getter/setter函数")
        
        # 构建专门的getter/setter强化prompt
        prompt = self._build_getter_setter_reinforcement_prompt(
            missing_functions, current_mermaid, project_name)
        
        # 计算token使用量
        token_usage = self.token_calculator.calculate_prompt_tokens(prompt, self.model)
        
        # 调用Claude进行分析
        logger.info("📤 发送Getter/Setter补充分析请求")
        analysis_result = ask_claude_for_code_analysis(prompt)
        
        # 解析结果
        flow_description, interactions, enhanced_mermaid = \
            self._parse_reinforcement_result(analysis_result)
        
        return BusinessFlowStepResult(
            step_id=step_id,
            files_analyzed=[info['file_path'] for info in missing_functions],
            flow_description=f"Getter/Setter函数补充分析: {flow_description}",
            key_interactions=interactions,
            mermaid_fragment=enhanced_mermaid,
            token_usage=token_usage,
            is_reinforcement=True
        )
    
    def _extract_getter_setter_functions(self, files_content: Dict[str, str]) -> List[Dict[str, str]]:
        """提取文件中的getter/setter函数"""
        
        logger.info(f"🔍 开始从 {len(files_content)} 个文件中提取getter/setter函数")
        
        getter_setter_functions = []
        
        # 常见的getter/setter函数模式
        getter_patterns = [
            'function get', 'function is', 'function has', 'function owner', 'function name',
            'function symbol', 'function decimals', 'function totalSupply', 'function balanceOf',
            'function allowance', 'function paused', 'function threshold'
        ]
        
        setter_patterns = [
            'function set', 'function pause', 'function unpause', 'function grant', 'function revoke',
            'function renounce', 'function approve'
        ]
        
        view_patterns = ['view returns', 'pure returns']
        
        for file_path, content in files_content.items():
            file_functions = []
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                line_stripped = line.strip().lower()
                
                # 检查getter函数
                if any(pattern in line_stripped for pattern in getter_patterns) or \
                   any(pattern in line_stripped for pattern in view_patterns):
                    
                    # 提取函数名
                    if 'function ' in line_stripped:
                        try:
                            func_start = line_stripped.find('function ') + 9
                            func_end = line_stripped.find('(', func_start)
                            if func_end != -1:
                                func_name = line_stripped[func_start:func_end].strip()
                                
                                function_info = {
                                    'name': func_name,
                                    'type': 'getter',
                                    'file_path': file_path,
                                    'line_number': i + 1,
                                    'content': line.strip()
                                }
                                getter_setter_functions.append(function_info)
                                file_functions.append(func_name)
                        except:
                            continue
                
                # 检查setter函数
                elif any(pattern in line_stripped for pattern in setter_patterns):
                    
                    if 'function ' in line_stripped:
                        try:
                            func_start = line_stripped.find('function ') + 9
                            func_end = line_stripped.find('(', func_start)
                            if func_end != -1:
                                func_name = line_stripped[func_start:func_end].strip()
                                
                                function_info = {
                                    'name': func_name,
                                    'type': 'setter',
                                    'file_path': file_path,
                                    'line_number': i + 1,
                                    'content': line.strip()
                                }
                                getter_setter_functions.append(function_info)
                                file_functions.append(func_name)
                        except:
                            continue
            
            if file_functions:
                logger.info(f"📁 {file_path}: 发现 {len(file_functions)} 个getter/setter函数: {', '.join(file_functions[:5])}{'...' if len(file_functions) > 5 else ''}")
        
        # 按类型统计
        getters = [f for f in getter_setter_functions if f['type'] == 'getter']
        setters = [f for f in getter_setter_functions if f['type'] == 'setter']
        
        logger.info(f"✅ 提取完成 - 总计: {len(getter_setter_functions)} 个函数 (Getter: {len(getters)}, Setter: {len(setters)})")
        
        return getter_setter_functions
    
    def _build_getter_setter_reinforcement_prompt(self, 
                                                 missing_functions: List[Dict[str, str]],
                                                 current_mermaid: str,
                                                 project_name: str) -> str:
        """构建专门的getter/setter函数强化prompt"""
        
        # 按类型分组函数
        getters = [f for f in missing_functions if f['type'] == 'getter']
        setters = [f for f in missing_functions if f['type'] == 'setter']
        
        functions_summary = f"发现 {len(getters)} 个Getter函数和 {len(setters)} 个Setter函数可能被遗漏"
        
        # 列出遗漏的函数
        missing_list = "**被遗漏的Getter函数:**\n"
        for func in getters:
            missing_list += f"- {func['name']}() 在 {func['file_path']}\n"
        
        missing_list += "\n**被遗漏的Setter函数:**\n"
        for func in setters:
            missing_list += f"- {func['name']}() 在 {func['file_path']}\n"
        
        # 截断current_mermaid以控制prompt长度
        if len(current_mermaid) > 3000:
            mermaid_preview = current_mermaid[:3000] + "\n... (图表内容较长，仅显示前部分)"
        else:
            mermaid_preview = current_mermaid
        
        prompt = f"""
你是 {project_name} 项目的资深架构师，发现业务流程图中**遗漏了重要的Getter/Setter函数**。

**当前业务流程图:**
```mermaid
{mermaid_preview}
```

**🔍 发现的问题:**
{functions_summary}

{missing_list}

**🎯 专项任务要求:**
1. **必须保持sequenceDiagram格式** - 确保输出以 `sequenceDiagram` 开头
2. **保留所有现有内容** - 绝对不能删除任何participant或交互
3. **补充所有遗漏的Getter函数** - 每个Getter函数都必须添加到图中
4. **补充所有遗漏的Setter函数** - 每个Setter函数都必须添加到图中
5. **使用正确的交互格式** - 确保函数名、参数和返回值准确
6. **保持原始合约名** - 使用具体的合约名，不能使用通用名称

**输出格式:**
## 补充分析描述
[描述补充了哪些被遗漏的Getter/Setter函数，以及它们的作用]

## 补充后的完整业务流程图
```mermaid
sequenceDiagram
    [保留所有原有participant和交互]
    [新增所有被遗漏的Getter函数交互]
    [新增所有被遗漏的Setter函数交互]
    [确保每个函数都有正确的参数和返回值]
```



**🔥 关键要求:**
- **必须补充所有列出的遗漏函数** - 一个都不能少
- 绝对保持原有图表的完整性
- 使用具体的合约名，不能使用通用名称
- 确保函数签名和参数准确无误
"""
        
        return prompt
    
    def _select_files_for_reinforcement(self, 
                                      files_content: Dict[str, str],
                                      analysis_steps: List[BusinessFlowStepResult]) -> Dict[str, str]:
        """选择需要强化分析的重要文件"""
        
        logger.info("🎯 选择文件进行强化分析")
        
        # 选择最重要的文件进行强化
        selected_files = {}
        
        # 选择最重要的文件
        logger.info("📋 选择最重要的文件进行强化")
        prioritized_files = self._prioritize_files_for_flow_analysis(files_content)
        for file_path, content in prioritized_files[:3]:  # 选择前3个重要文件
            selected_files[file_path] = content
        
        logger.info(f"✅ 已选择 {len(selected_files)} 个文件进行强化分析: {list(selected_files.keys())}")
        return selected_files
    
    def _analyze_file_for_reinforcement(self, 
                                      file_path: str,
                                      file_content: str,
                                      current_mermaid: str,
                                      project_name: str,
                                      step_id: int) -> BusinessFlowStepResult:
        """对单个文件进行强化分析"""
        
        self._log_mermaid_generation_start(f"强化分析-文件{step_id}", file_path)
        
        # 构建强化分析prompt
        prompt = self._build_reinforcement_prompt(file_path, file_content, current_mermaid, project_name)
        
        # 计算token使用量
        token_usage = self.token_calculator.calculate_prompt_tokens(prompt, self.model)
        
        # 调用Claude进行强化分析
        logger.info(f"📤 发送强化分析请求 - 文件: {file_path}")
        analysis_result = ask_claude_for_code_analysis(prompt)
        
        # 解析强化分析结果
        flow_description, interactions, enhanced_mermaid = \
            self._parse_reinforcement_result(analysis_result)
        
        # 记录强化分析结果
        self._log_mermaid_generation_result(
            enhanced_mermaid, 
            f"强化分析-{file_path}",
            step_id
        )
        
        return BusinessFlowStepResult(
            step_id=step_id,
            files_analyzed=[file_path],
            flow_description=flow_description,
            key_interactions=interactions,
            mermaid_fragment=enhanced_mermaid,
            token_usage=token_usage,
            is_reinforcement=True
        )
    
    def _build_reinforcement_prompt(self, 
                                  file_path: str,
                                  file_content: str,
                                  current_mermaid: str,
                                  project_name: str) -> str:
        """构建强化分析prompt"""
        
        # 智能截断文件内容
        truncated_content = file_content[:6000] + ("\n... (内容已截断)" if len(file_content) > 6000 else "")
        
        # 智能截断当前mermaid图
        if len(current_mermaid) > 4000:
            mermaid_preview = current_mermaid[:4000] + "\n... (mermaid图内容较长，仅显示前部分)"
        else:
            mermaid_preview = current_mermaid
        
        prompt = f"""
你是 {project_name} 项目的资深架构师，现在需要对业务流程图进行**强化分析**，**必须覆盖所有函数，不能遗漏任何一个**。

**强化目标文件: {file_path}**

**文件详细内容:**
{truncated_content}

**当前业务流程图:**
```mermaid
{mermaid_preview}
```

**🔍 强化任务要求:**
1. **必须保持sequenceDiagram格式** - 确保输出以 `sequenceDiagram` 开头
2. **保留所有现有内容** - 绝对不能删除任何participant或交互
3. **全函数覆盖分析** - 识别 {file_path} 中的**每一个函数**，包括：
   - ✅ **Public/External函数** - 所有对外暴露的函数
   - ✅ **Getter函数** - 所有获取状态变量的函数（如 getValue, getBalance, isActive）
   - ✅ **Setter函数** - 所有设置状态变量的函数（如 setValue, setOwner, setConfig）
   - ✅ **View/Pure函数** - 所有查询类函数，无论多简单
   - ✅ **构造函数** - constructor函数
   - ✅ **事件触发** - 所有emit语句
4. **补充遗漏交互** - 特别关注简单的getter/setter函数，它们经常被忽略
5. **增加具体细节** - 为每个函数调用添加具体参数和返回值信息
6. **优化交互描述** - **必须使用原始的合约名和函数名**

**关键格式要求:**
- **合约名**: 使用 {file_path} 中的原始合约名，不能使用通用名称
- **函数名**: 使用代码中的准确函数名，包含完整的函数签名
- **参数类型**: 包含准确的参数类型 (如: address, uint256, string, bool)
- **返回值**: 明确标注函数返回值类型和含义

**输出格式:**
## 强化分析描述
[详细描述对 {file_path} 的**全函数覆盖分析**，列出所有发现的函数，包括被遗漏的getter/setter函数]

## 强化后的完整业务流程图
```mermaid
sequenceDiagram
    [保留所有原有participant和交互]
    [新增 {file_path} 的**所有函数**交互，包括getter/setter]
    [确保每个函数调用都有明确的参数类型和返回值]
```



**🔥 关键要求:**
- **绝对不能遗漏任何函数** - 包括最简单的getter/setter
- 绝对保持原有图表的完整性
- **绝对不能使用通用名称如 "Contract", "Token", "System"，必须使用具体的合约名**
- 专注**100%覆盖** {file_path} 中的所有函数
"""
        
        return prompt
    
    def _parse_reinforcement_result(self, analysis_result: str) -> Tuple[str, List[Dict], str]:
        """解析强化分析结果，直接使用完整结果"""
        
        logger.info("🔍 直接使用AI强化分析的完整结果")
        
        # 简单处理：直接使用完整的分析结果
        flow_description = "AI强化分析结果"
        interactions = [{"type": "reinforcement", "description": "直接使用AI完整结果"}]
        
        # 直接使用分析结果作为mermaid图内容
        enhanced_mermaid = analysis_result
        
        logger.info(f"✅ 使用强化完整结果，长度: {len(enhanced_mermaid)}字符")
        
        return flow_description, interactions, enhanced_mermaid
    
    def _parse_incremental_result(self, analysis_result: str) -> Tuple[str, List[Dict], str]:
        """解析增量分析结果，直接使用完整结果"""
        
        logger.info("🔍 直接使用AI生成的完整结果")
        
        # 简单处理：直接使用完整的分析结果作为描述
        flow_description = "AI生成的业务流程分析"
        interactions = [{"type": "incremental", "description": "直接使用AI完整结果"}]
        
        # 直接使用分析结果作为mermaid图内容
        extended_mermaid = analysis_result
        
        logger.info(f"✅ 使用完整结果，长度: {len(extended_mermaid)}字符")
        
        return flow_description, interactions, extended_mermaid
    
    def _generate_global_overview_mermaid(self, 
                                        folder_analyses: Dict[str, FolderAnalysisResult],
                                        project_name: str) -> str:
        """生成全局概览Mermaid图，直接使用AI完整结果"""
        
        if not folder_analyses:
            logger.warning("⚠️  没有文件夹分析结果，无法生成全局概览图")
            return ""
        
        self._log_mermaid_generation_start("全局概览图生成", f"{len(folder_analyses)}个文件夹")
        
        # 构建全局概览prompt
        prompt = f"""
请为 {project_name} 项目生成全局架构概览图，基于各文件夹的分析结果。

**项目文件夹结构:**
"""
        
        for folder_path, folder_result in folder_analyses.items():
            prompt += f"""
- **{folder_path}/** ({folder_result.files_count} 个文件)
  概述: {folder_result.folder_summary[:200]}...
"""
        
        prompt += f"""

**任务要求:**
1. 创建项目级别的高层架构图
2. 展示各文件夹/模块之间的关系
3. 突出主要的数据流和控制流
4. 使用清晰的模块化设计
5. **使用具体的模块名称** - 基于文件夹名称使用准确的描述

请生成简洁但信息丰富的全局架构图，使用具体的模块名称而非通用术语。
"""
        
        try:
            logger.info("📤 发送全局概览图生成请求")
            analysis_result = ask_claude_for_code_analysis(prompt)
            
            # 直接使用AI生成的完整结果
            if analysis_result:
                logger.info(f"✅ 直接使用AI概览结果，长度: {len(analysis_result)}字符")
                self._log_mermaid_generation_result(analysis_result, "全局概览图")
                return analysis_result
            else:
                logger.warning("⚠️  AI返回空结果")
                
        except Exception as e:
            logger.warning(f"❌ 生成全局概览图失败: {e}")
        
        # 备用简单描述
        backup_description = f"{project_name} 项目架构概览\n\n包含以下模块:\n"
        for folder_path, folder_result in folder_analyses.items():
            backup_description += f"- {folder_result.folder_name}: {folder_result.files_count}个文件\n"
        
        logger.info("🔄 使用备用简单概览")
        self._log_mermaid_generation_result(backup_description, "备用全局概览图")
        
        return backup_description
    
    def _merge_token_usage(self, usage1: TokenUsage, usage2: TokenUsage) -> TokenUsage:
        """合并两个token使用量"""
        return TokenUsage(
            input_tokens=usage1.input_tokens + usage2.input_tokens,
            estimated_output_tokens=usage1.estimated_output_tokens + usage2.estimated_output_tokens,
            total_tokens=usage1.total_tokens + usage2.total_tokens,
            is_within_limit=usage1.is_within_limit and usage2.is_within_limit,
            model_limit=usage1.model_limit,
            recommendation=f"合并使用量: {usage1.total_tokens + usage2.total_tokens:,} tokens"
        )
    
    def analyze_business_flow_incremental(self, 
                                        files_content: Dict[str, str],
                                        project_name: str) -> CompleteBusinessFlowResult:
        """真正的增量式业务流程分析 - 基于mmd文件逐步构建
        
        Args:
            files_content: 文件内容映射
            project_name: 项目名称
            
        Returns:
            完整的业务流程分析结果
        """
        logger.info(f"🚀 开始真正的增量式业务流程分析: {project_name} ({len(files_content)} 个文件)")
        
        # 重置分析历史
        self.analysis_history = []
        
        # 第一步：按优先级排序文件
        sorted_files = self._prioritize_files_for_flow_analysis(files_content)
        
        # 第二步：真正的增量分析 - 累积构建mermaid图
        cumulative_mermaid = ""  # 累积的mermaid图
        
        for step_id, (file_path, content) in enumerate(sorted_files, 1):
            logger.info(f"🔄 增量分析步骤 {step_id}: {file_path}")
            
            # 进行单文件增量分析
            step_result = self._analyze_single_file_incremental(
                step_id, file_path, content, cumulative_mermaid, project_name)
            
            self.analysis_history.append(step_result)
            
            # 更新累积的mermaid图
            cumulative_mermaid = step_result.mermaid_fragment
            
            logger.info(f"步骤 {step_id} 完成，累积mermaid图长度: {len(cumulative_mermaid)}")
        
        # 第三步：最终优化累积的mermaid图
        final_result = self._finalize_cumulative_mermaid(
            project_name, files_content, self.analysis_history, cumulative_mermaid)
        
        logger.info(f"增量式业务流程分析完成，共 {len(self.analysis_history)} 个步骤")
        return final_result
    
    def _prioritize_files_for_flow_analysis(self, 
                                          files_content: Dict[str, str]) -> List[Tuple[str, str]]:
        """为业务流程分析排序文件优先级
        
        Args:
            files_content: 文件内容映射
            
        Returns:
            按优先级排序的文件列表
        """
        logger.info(f"📊 开始为 {len(files_content)} 个文件计算优先级")
        
        file_priorities = []
        
        for file_path, content in files_content.items():
            priority = self._calculate_business_flow_priority(file_path, content)
            file_priorities.append((priority, file_path, content))
        
        # 按优先级降序排序
        file_priorities.sort(key=lambda x: x[0], reverse=True)
        
        # 记录优先级排序结果
        logger.info("📋 文件优先级排序完成，前5个高优先级文件:")
        for i, (priority, file_path, _) in enumerate(file_priorities[:5]):
            logger.info(f"  {i+1}. {file_path} (优先级: {priority})")
        
        if len(file_priorities) > 5:
            logger.info(f"  ... 以及其他 {len(file_priorities) - 5} 个文件")
        
        # 返回文件路径和内容的元组列表
        return [(file_path, content) for _, file_path, content in file_priorities]
    
    def _calculate_business_flow_priority(self, file_path: str, content: str) -> int:
        """计算文件在业务流程分析中的优先级"""
        priority = 0
        file_name = file_path.lower()
        
        # 工厂模式文件（最高优先级）
        if any(keyword in file_name for keyword in ['factory', 'manager', 'controller']):
            priority += 1000
        
        # 核心业务合约
        if any(keyword in file_name for keyword in ['claim', 'deposit', 'withdraw', 'transfer']):
            priority += 800
        
        # 访问控制文件
        if any(keyword in file_name for keyword in ['access', 'auth', 'permission', 'role']):
            priority += 600
        
        # 基础功能文件
        if any(keyword in file_name for keyword in ['base', 'closable', 'pausable']):
            priority += 400
        
        # 接口文件
        if file_name.startswith('i') and file_name.endswith('.sol'):
            priority += 200
        
        # 基于内容复杂度
        function_count = content.count('function ')
        event_count = content.count('event ')
        modifier_count = content.count('modifier ')
        
        priority += function_count * 10
        priority += event_count * 5
        priority += modifier_count * 8
        
        # 基于文件大小
        if len(content) > 10000:
            priority += 100
        elif len(content) > 5000:
            priority += 50
        
        return priority
    
    def _analyze_single_file_incremental(self, 
                                        step_id: int,
                                        file_path: str,
                                        file_content: str,
                                        existing_mermaid: str,
                                        project_name: str) -> BusinessFlowStepResult:
        """真正的单文件增量分析
        
        Args:
            step_id: 步骤ID
            file_path: 当前分析的文件路径
            file_content: 当前文件内容
            existing_mermaid: 已有的累积mermaid图
            project_name: 项目名称
            
        Returns:
            步骤分析结果，包含扩展后的mermaid图
        """
        self._log_mermaid_generation_start(f"步骤{step_id}增量分析", file_path)
        
        # 构建增量分析prompt
        prompt = self._build_true_incremental_prompt(
            file_path, file_content, existing_mermaid, step_id, project_name)
        
        # 计算token使用量
        token_usage = self.token_calculator.calculate_prompt_tokens(prompt, self.model)
        
        # 调用Claude进行增量分析
        logger.info(f"📤 发送增量分析请求 - 文件: {file_path}, 步骤: {step_id}")
        analysis_result = ask_claude_for_code_analysis(prompt)
        
        # 解析分析结果，获取扩展后的完整mermaid图
        flow_description, interactions, extended_mermaid = \
            self._parse_incremental_result(analysis_result)
        
        # 记录分析结果
        self._log_mermaid_generation_result(
            extended_mermaid, 
            f"步骤{step_id}增量分析-{file_path}",
            step_id
        )
        
        return BusinessFlowStepResult(
            step_id=step_id,
            files_analyzed=[file_path],  # 只包含当前文件
            flow_description=flow_description,
            key_interactions=interactions,
            mermaid_fragment=extended_mermaid,  # 这是累积的完整图
            token_usage=token_usage
        )
    
    def _build_true_incremental_prompt(self, 
                                      file_path: str,
                                      file_content: str,
                                      existing_mermaid: str,
                                      step_id: int,
                                      project_name: str) -> str:
        """构建真正的增量分析prompt - 基于已有mermaid图扩展"""
        
        if step_id == 1:
            # 第一个文件，创建初始mermaid图 - 限制文件内容长度
            truncated_content = file_content[:8000] + ("\n... (内容已截断)" if len(file_content) > 8000 else "")
            
            prompt = f"""
请为 {project_name} 项目分析第一个文件并创建初始的业务流程图，**必须覆盖文件中的所有函数**。

**当前分析文件: {file_path}**

**文件内容:**
{truncated_content}

**🎯 任务要求 - 100%函数覆盖:**
1. **必须生成sequenceDiagram格式** - 以 `sequenceDiagram` 开头
2. **全函数覆盖分析** - 分析 {file_path} 中的**每一个函数**，包括：
   - ✅ **Public/External函数** - 所有对外暴露的函数
   - ✅ **Getter函数** - 所有获取状态变量的函数（如 getValue, getBalance, isActive）
   - ✅ **Setter函数** - 所有设置状态变量的函数（如 setValue, setOwner, setConfig）
   - ✅ **View/Pure函数** - 所有查询类函数，无论多简单
   - ✅ **构造函数** - constructor函数
   - ✅ **事件触发** - 所有emit语句
   - ✅ **修饰符函数** - 重要的modifier应用
3. **创建完整的Mermaid序列图** - **必须使用原始的合约名和函数名**
4. **确保图表结构清晰** - 为后续文件扩展做好准备，但不能遗漏任何函数

**关键格式要求 - 必须严格遵守:**
- **合约名**: 使用文件中的原始合约名 (如: ERC20AssetGateway, PlanFactory, GMEvent)
- **函数名**: 使用代码中的准确函数名 (如: constructor, transfer, approve, confirmJoin)
- **参数**: 包含函数的真实参数名和类型 (如: address _user, uint256 _amount)
- **返回值**: 明确标注函数返回值类型和含义
- **修饰符**: 包含重要的修饰符检查 (如: onlyOwner, requireRole)

**输出格式:**
## 业务流程描述
[详细描述 {file_path} 的**所有函数**业务逻辑，使用原始合约名和函数名]

## 完整Mermaid图
```mermaid
sequenceDiagram
    [创建详细的序列图，严格使用原始合约名和函数名]
    [**必须包含文件中的所有函数**，包括简单的getter/setter]
    [格式示例: User->>ERC20Token: balanceOf(address owner) returns uint256]
    [格式示例: Owner->>ERC20Token: setOwner(address newOwner)]
```


"""
        else:
            # 后续文件，基于已有mermaid图扩展 - 智能控制内容长度
            truncated_content = file_content[:5000] + ("\n... (内容已截断)" if len(file_content) > 5000 else "")
            
            # 如果existing_mermaid太长，也需要适当截断提示
            if len(existing_mermaid) > 3000:
                mermaid_preview = existing_mermaid[:3000] + "\n... (已有图表内容较长，仅显示前部分)"
            else:
                mermaid_preview = existing_mermaid
            
            prompt = f"""
请为 {project_name} 项目扩展业务流程图，添加新文件 {file_path} 的**所有函数**业务逻辑。

**当前要添加的文件: {file_path}**

**新文件内容:**
{truncated_content}

**已有的业务流程图:**
```mermaid
{mermaid_preview}
```

**🎯 关键任务要求 - 100%函数覆盖:**
1. **必须保持sequenceDiagram格式** - 确保输出以 `sequenceDiagram` 开头
2. **绝对保留**已有Mermaid图中的所有内容，一个交互都不能丢失
3. **全函数覆盖分析** - 分析新文件 {file_path} 中的**每一个函数**
4. **将新文件的所有函数业务流程扩展到已有图中**
5. **必须使用原始的合约名和函数名**，确保新增的交互包含具体的函数名和参数
6. **保持图表的逻辑顺序和清晰结构**

**输出格式:**
## 业务流程描述
[详细描述 {file_path} 的**所有函数**如何融入现有业务流程，使用原始合约名和函数名]

## 扩展后的完整Mermaid图
```mermaid
sequenceDiagram
    [包含所有原有内容 + 新增的 {file_path} 的**所有函数**交互]
    [确保所有原有的交互都完整保留]
    [**必须包含新文件中的所有函数**，包括简单的getter/setter]
```


"""
        
        return prompt
    
    def _finalize_cumulative_mermaid(self, 
                                    project_name: str,
                                    files_content: Dict[str, str],
                                    step_results: List[BusinessFlowStepResult],
                                    cumulative_mermaid: str) -> CompleteBusinessFlowResult:
        """优化最终的累积mermaid图，直接使用AI生成的完整结果"""
        
        logger.info("🔧 优化最终的累积mermaid图")
        self._log_mermaid_generation_start("最终优化", f"累积图长度: {len(cumulative_mermaid)}字符")
        
        # 构建最终优化prompt
        final_prompt = self._build_final_optimization_prompt(project_name, cumulative_mermaid)
        
        # 计算token使用量
        token_usage = self.token_calculator.calculate_prompt_tokens(final_prompt, self.model)
        logger.info(f"📊 最终优化Token使用预估: {token_usage.total_tokens:,}")
        
        # 调用Claude进行最终优化
        logger.info("📤 发送最终优化请求")
        final_analysis = ask_claude_for_code_analysis(final_prompt)
        
        # 直接使用AI生成的完整结果
        original_length = len(cumulative_mermaid)
        
        if final_analysis and len(final_analysis) > 100:  # 基本的长度检查
            final_mermaid = final_analysis
            business_summary = final_analysis  # 直接使用完整结果作为总结
            final_length = len(final_mermaid)
            logger.info(f"✅ 直接使用AI优化结果，长度: {final_length}字符")
        else:
            # 如果AI返回结果太短或为空，使用原始累积图
            logger.warning("⚠️  AI返回结果太短或为空，使用原始累积图")
            final_mermaid = cumulative_mermaid
            business_summary = f"{project_name}项目业务流程分析完成"
            final_length = len(final_mermaid)
        
        # 记录最终优化效果
        self._log_mermaid_optimization(original_length, final_length, "最终优化")
        self._log_mermaid_generation_result(final_mermaid, "项目最终分析")
        
        # 计算总token使用量
        total_token_usage = self._calculate_total_token_usage(step_results, token_usage)
        
        # 记录最终统计
        logger.info(f"🎉 项目 {project_name} 分析完成!")
        logger.info(f"📈 最终统计 - 文件数: {len(files_content)}, 分析步骤: {len(step_results)}")
        logger.info(f"💰 总Token消耗: {total_token_usage.total_tokens:,}")
        logger.info(f"📏 最终Mermaid图长度: {len(final_mermaid):,}字符")
        
        return CompleteBusinessFlowResult(
            project_name=project_name,
            total_files=len(files_content),
            analysis_strategy="incremental",
            analysis_steps=step_results,
            final_mermaid_graph=final_mermaid,
            business_summary=business_summary,
            folder_analyses={},
            global_mermaid_graph=final_mermaid,
            total_token_usage=total_token_usage
        )
    
    def _build_final_optimization_prompt(self, 
                                        project_name: str,
                                        cumulative_mermaid: str) -> str:
        """构建最终优化prompt - 优化累积的mermaid图"""
        
        newline = '\n'  # 定义换行符变量，避免f-string中的反斜杠问题
        
        prompt = f"""
请优化 {project_name} 项目的完整业务流程图，**确保覆盖所有函数，包括getter/setter**，同时保持图表清晰、逻辑连贯。

**当前的完整业务流程图:**
```mermaid
{cumulative_mermaid}
```

**🎯 优化任务要求:**
1. **必须保持sequenceDiagram格式** - 确保输出以 `sequenceDiagram` 开头
2. **保留所有现有内容** - 绝对不能删除任何participant或交互，包括所有getter/setter函数
3. **验证函数覆盖完整性** - 确保包含了所有类型的函数
4. **优化交互的逻辑顺序**，确保业务流程的时序合理
5. **添加适当的注释和分组**（使用 %% 注释和 Note）
6. **保持所有原始合约名和函数名** - 确保所有函数名和参数都准确无误
7. **检查并修正可能的语法错误**

**输出格式:**
## 业务流程总结
[简要总结 {project_name} 项目的核心业务流程，**包括所有函数类型**，使用原始合约名和函数名]

## 优化后的完整业务流程图
```mermaid
{cumulative_mermaid.split(newline)[0] if cumulative_mermaid else 'sequenceDiagram'}
    [保留所有原有participant和交互，包括所有原始合约名和函数名]
    [**确保包含所有函数，包括简单的getter/setter**]
    [优化顺序和结构，添加适当注释]
    [确保语法正确，逻辑清晰，但绝不修改合约名和函数名]
```

**🔥 重要提醒:**
- **绝对不能删除任何函数交互** - 包括最简单的getter/setter函数
- 只能优化结构和顺序，不能删除任何现有内容
- **绝对不能修改任何合约名、函数名或参数名**
- 确保所有原有的交互都完整保留，包括原始的命名
- 优化应该让图表更清晰，而不是更简化
"""
        
        return prompt
    
    def _extract_final_mermaid(self, analysis_result: str) -> str:
        """直接使用AI生成的完整结果"""
        
        logger.info("🔍 直接使用最终AI生成的完整结果")
        logger.info(f"✅ 使用完整结果，长度: {len(analysis_result)}字符")
        
        return analysis_result
    
    def _extract_business_summary(self, analysis_result: str) -> str:
        """直接使用AI生成的完整结果作为业务总结"""
        
        logger.info("🔍 直接使用AI生成的完整结果作为业务总结")
        logger.info(f"✅ 使用完整结果作为总结，长度: {len(analysis_result)}字符")
        
        return analysis_result
    

    
    def _calculate_total_token_usage(self, 
                                   step_results: List[BusinessFlowStepResult],
                                   final_usage: TokenUsage) -> TokenUsage:
        """计算总的token使用量"""
        
        total_input = sum(step.token_usage.input_tokens for step in step_results) + final_usage.input_tokens
        total_output = sum(step.token_usage.estimated_output_tokens for step in step_results) + final_usage.estimated_output_tokens
        total_tokens = total_input + total_output
        
        return TokenUsage(
            input_tokens=total_input,
            estimated_output_tokens=total_output,
            total_tokens=total_tokens,
            is_within_limit=True,  # 总计不检查限制
            model_limit=final_usage.model_limit,
            recommendation=f"总计使用 {total_tokens:,} tokens"
        )
    
    def _merge_folder_diagrams(self, 
                             folder_analyses: Dict[str, FolderAnalysisResult],
                             project_name: str) -> str:
        """合并多个文件夹的diagram生成全局业务流图，直接使用AI完整结果"""
        
        if not folder_analyses:
            logger.warning("⚠️  没有文件夹分析结果，无法生成全局图")
            return ""
        
        self._log_mermaid_generation_start("多文件夹diagram合并", f"{len(folder_analyses)}个文件夹")
        
        # 收集所有文件夹的diagram内容
        folder_diagrams = {}
        for folder_path, folder_result in folder_analyses.items():
            if folder_result.folder_mermaid_graph:
                folder_diagrams[folder_path] = {
                    'diagram': folder_result.folder_mermaid_graph,
                    'summary': folder_result.folder_summary,
                    'files_count': folder_result.files_count
                }
        
        if not folder_diagrams:
            logger.warning("⚠️  所有文件夹都没有生成有效的diagram")
            return ""
        
        # 构建合并prompt
        prompt = self._build_folder_merge_prompt(folder_diagrams, project_name)
        
        try:
            logger.info("📤 发送多文件夹diagram合并请求")
            analysis_result = ask_claude_for_code_analysis(prompt)
            
            # 直接使用AI生成的完整结果
            if analysis_result:
                logger.info(f"✅ 直接使用AI合并结果，长度: {len(analysis_result)}字符")
                self._log_mermaid_generation_result(analysis_result, "多文件夹合并结果")
                return analysis_result
            else:
                logger.warning("⚠️  AI返回空结果，使用简化合并策略")
                return self._simple_merge_diagrams(folder_diagrams, project_name)
            
        except Exception as e:
            logger.warning(f"❌ 多文件夹diagram合并失败: {e}")
            return self._simple_merge_diagrams(folder_diagrams, project_name)

    def _build_folder_merge_prompt(self, 
                                 folder_diagrams: Dict[str, Dict],
                                 project_name: str) -> str:
        """构建文件夹diagram合并prompt"""
        
        diagrams_content = ""
        for folder_path, folder_data in folder_diagrams.items():
            diagrams_content += f"""
**文件夹: {folder_path}** ({folder_data['files_count']} 个文件)
功能概述: {folder_data['summary'][:200]}...

```mermaid
{folder_data['diagram']}
```

---
"""
        
        prompt = f"""
请将 {project_name} 项目的多个文件夹业务流程图合并成一个完整的项目级业务流程图。

**各文件夹的业务流程图:**
{diagrams_content}

**合并任务要求:**
1. **生成sequenceDiagram格式** - 必须以 `sequenceDiagram` 开头
2. **保留核心业务流程** - 提取各文件夹的主要业务逻辑和交互
3. **建立跨文件夹连接** - 识别文件夹间的调用关系和数据流
4. **使用具体名称** - 保持原始合约名和函数名，避免通用名称
5. **简化重复交互** - 合并相似的交互，突出核心流程
6. **保持逻辑清晰** - 确保合并后的流程图逻辑连贯

**输出格式:**
## 项目整体业务流程说明
[简要说明合并后的整体业务流程]

## 合并后的完整业务流程图
```mermaid
sequenceDiagram
    [生成完整的项目级业务流程图]
    [包含各文件夹的核心交互]
    [建立跨文件夹的业务连接]
    [使用具体的合约名和函数名]
```

请确保生成的是一个统一、连贯的项目级业务流程图。
"""
        
        return prompt

    def _simple_merge_diagrams(self, 
                             folder_diagrams: Dict[str, Dict],
                             project_name: str) -> str:
        """简单合并多个diagram的备用方法，直接文本拼接"""
        
        logger.info("🔄 使用简化策略直接拼接多个diagram")
        
        # 简单的文本拼接
        merged_content = f"{project_name} 项目整体业务流程 (简化合并)\n\n"
        
        for folder_path, folder_data in folder_diagrams.items():
            folder_name = Path(folder_path).name
            merged_content += f"=== {folder_name} 文件夹业务流程 ===\n"
            merged_content += f"文件数: {folder_data['files_count']}\n"
            merged_content += f"功能: {folder_data['summary'][:100]}...\n"
            merged_content += f"详细流程:\n{folder_data['diagram']}\n\n"
        
        logger.info(f"✅ 简化拼接完成，总长度: {len(merged_content)}字符")
        self._log_mermaid_generation_result(merged_content, "简化合并结果")
        
        return merged_content

# 便捷函数
def analyze_business_flow(files_content: Dict[str, str], 
                         project_name: str,
                         model: str = "claude-3-5-sonnet-20241022") -> CompleteBusinessFlowResult:
    """便捷的业务流程分析函数
    
    Args:
        files_content: 文件内容映射
        project_name: 项目名称
        model: 使用的AI模型
        
    Returns:
        完整的业务流程分析结果
    """
    logger.info(f"🚀 启动便捷业务流程分析: {project_name}")
    logger.info(f"📋 分析参数 - 文件数: {len(files_content)}, 模型: {model}")
    
    analyzer = BusinessFlowAnalyzer(model)
    result = analyzer.analyze_business_flow_incremental(files_content, project_name)
    
    logger.info(f"🎉 便捷分析完成 - 项目: {project_name}, 最终图表长度: {len(result.final_mermaid_graph)}字符")
    
    return result

def analyze_business_flow_from_path(project_path: str, 
                                  project_name: str = None,
                                  file_extensions: List[str] = ['.sol', '.py', '.js', '.ts'],
                                  model: str = "claude-3-5-sonnet-20241022") -> CompleteBusinessFlowResult:
    """从项目路径分析业务流程
    
    Args:
        project_path: 项目路径
        project_name: 项目名称
        file_extensions: 要分析的文件扩展名
        model: 使用的AI模型
        
    Returns:
        完整的业务流程分析结果
    """
    from pathlib import Path
    
    project_path = Path(project_path)
    if not project_name:
        project_name = project_path.name
    
    logger.info(f"🚀 启动路径业务流程分析: {project_name}")
    logger.info(f"📂 项目路径: {project_path}")
    logger.info(f"🔍 文件扩展名: {file_extensions}")
    logger.info(f"🤖 使用模型: {model}")
    
    # 读取项目文件
    files_content = {}
    total_files_found = 0
    
    for ext in file_extensions:
        ext_files = list(project_path.glob(f"*{ext}"))
        total_files_found += len(ext_files)
        logger.info(f"📄 发现 {len(ext_files)} 个 {ext} 文件")
        
        for file_path in ext_files:
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        relative_path = str(file_path.relative_to(project_path))
                        files_content[relative_path] = content
                        logger.info(f"✅ 成功读取文件: {relative_path} ({len(content):,} 字符)")
                except Exception as e:
                    logger.warning(f"❌ 读取文件 {file_path} 失败: {e}")
    
    logger.info(f"📊 文件读取完成 - 总计发现: {total_files_found} 个文件, 成功读取: {len(files_content)} 个文件")
    
    if not files_content:
        logger.warning("⚠️  没有找到可分析的文件，请检查路径和文件扩展名")
        # 返回空结果
        return CompleteBusinessFlowResult(
            project_name=project_name,
            total_files=0,
            analysis_strategy="path_based",
            analysis_steps=[],
            final_mermaid_graph="",
            business_summary="未找到可分析的文件",
            folder_analyses={},
            global_mermaid_graph="",
            total_token_usage=TokenUsage(0, 0, 0, True, 200000, "无文件可分析")
        )
    
    result = analyze_business_flow(files_content, project_name, model)
    
    logger.info(f"🎉 路径分析完成 - 项目: {project_name}")
    logger.info(f"📈 分析统计 - 处理文件: {len(files_content)}, 分析步骤: {len(result.analysis_steps)}")
    logger.info(f"💰 Token消耗: {result.total_token_usage.total_tokens:,}")
    logger.info(f"📏 最终图表: {len(result.final_mermaid_graph):,} 字符")
    
    return result