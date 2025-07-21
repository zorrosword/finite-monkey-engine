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
    confidence_score: float
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
    confidence_score: float

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
    overall_confidence: float

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
        self.LARGE_PROJECT_THRESHOLD = 30  # 超过30个文件认为是大项目
        self.MAX_FILES_PER_FOLDER = 15     # 每个文件夹最多分析15个文件
        
        logger.info(f"初始化业务流程分析器，模型: {model}")
    
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
        logger.info(f"开始智能业务流程分析: {project_name} ({len(files_content)} 个文件)")
        
        # 判断使用哪种分析策略
        if len(files_content) <= self.LARGE_PROJECT_THRESHOLD and not self._has_complex_folder_structure(files_content):
            # 小型项目：使用增量分析
            logger.info("检测到小型项目，使用增量分析策略")
            return self._analyze_with_incremental_strategy(files_content, project_name, enable_reinforcement)
        else:
            # 大型项目：使用文件夹级别分析
            logger.info("检测到大型项目，使用文件夹级别分析策略")
            return self._analyze_with_folder_strategy(files_content, project_name, enable_reinforcement)
    
    def _has_complex_folder_structure(self, files_content: Dict[str, str]) -> bool:
        """检测是否有复杂的文件夹结构"""
        folder_set = set()
        for file_path in files_content.keys():
            # 获取文件夹路径
            folder = str(Path(file_path).parent)
            if folder != '.':
                folder_set.add(folder)
        
        # 如果有3个以上不同的文件夹，认为结构复杂
        return len(folder_set) >= 3
    
    def _analyze_with_incremental_strategy(self, 
                                         files_content: Dict[str, str],
                                         project_name: str,
                                         enable_reinforcement: bool) -> CompleteBusinessFlowResult:
        """使用增量分析策略"""
        
        # 执行原有的增量分析
        incremental_result = self.analyze_business_flow_incremental(files_content, project_name)
        
        # 如果启用强化分析，进行多轮强化
        if enable_reinforcement:
            logger.info("开始强化分析，提升Mermaid图质量")
            reinforced_result = self._perform_reinforcement_analysis(
                files_content, project_name, incremental_result)
            
            # 合并强化分析结果
            incremental_result.analysis_steps.extend(reinforced_result.analysis_steps)
            incremental_result.final_mermaid_graph = reinforced_result.final_mermaid_graph
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
            total_token_usage=incremental_result.total_token_usage,
            overall_confidence=incremental_result.overall_confidence
        )
    
    def _analyze_with_folder_strategy(self, 
                                    files_content: Dict[str, str],
                                    project_name: str,
                                    enable_reinforcement: bool) -> CompleteBusinessFlowResult:
        """使用文件夹级别分析策略"""
        
        # 按文件夹分组文件
        folder_groups = self._group_files_by_folder(files_content)
        
        # 分析每个文件夹
        folder_analyses = {}
        all_steps = []
        total_token_usage = TokenUsage(0, 0, 0, True, 200000, "")
        
        for folder_path, folder_files in folder_groups.items():
            logger.info(f"分析文件夹: {folder_path} ({len(folder_files)} 个文件)")
            
            # 分析单个文件夹
            folder_result = self._analyze_single_folder(
                folder_files, folder_path, project_name, enable_reinforcement)
            
            folder_analyses[folder_path] = folder_result
            all_steps.extend(folder_result.analysis_steps)
            total_token_usage = self._merge_token_usage(total_token_usage, folder_result.token_usage)
        
        # 生成全局概览图
        global_mermaid = self._generate_global_overview_mermaid(folder_analyses, project_name)
        
        # 计算整体置信度
        overall_confidence = sum(folder.confidence_score for folder in folder_analyses.values()) / len(folder_analyses) if folder_analyses else 0.0
        
        return CompleteBusinessFlowResult(
            project_name=project_name,
            total_files=len(files_content),
            analysis_strategy="folder_based",
            analysis_steps=all_steps,
            final_mermaid_graph="",  # 文件夹模式下主要看各文件夹的图
            business_summary=f"{project_name}项目文件夹级别分析完成，共分析{len(folder_analyses)}个文件夹",
            folder_analyses=folder_analyses,
            global_mermaid_graph=global_mermaid,
            total_token_usage=total_token_usage,
            overall_confidence=overall_confidence
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
    
    def _analyze_single_folder(self, 
                             folder_files: Dict[str, str],
                             folder_path: str,
                             project_name: str,
                             enable_reinforcement: bool) -> FolderAnalysisResult:
        """分析单个文件夹"""
        
        folder_name = Path(folder_path).name if folder_path != 'root' else 'root'
        
        # 如果文件夹文件太多，需要进一步分批
        if len(folder_files) > self.MAX_FILES_PER_FOLDER:
            logger.warning(f"文件夹 {folder_path} 文件数过多({len(folder_files)})，将进行分批处理")
            # 这里可以进一步细分，暂时简化处理
        
        # 对文件夹进行增量分析
        temp_analyzer = BusinessFlowAnalyzer(self.model)
        folder_incremental_result = temp_analyzer.analyze_business_flow_incremental(
            folder_files, f"{project_name}_{folder_name}")
        
        # 如果启用强化分析
        if enable_reinforcement:
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
            token_usage=folder_incremental_result.total_token_usage,
            confidence_score=folder_incremental_result.overall_confidence
        )
    
    def _perform_reinforcement_analysis(self, 
                                      files_content: Dict[str, str],
                                      project_name: str,
                                      base_result: 'CompleteBusinessFlowResult') -> 'CompleteBusinessFlowResult':
        """执行强化分析，提升Mermaid图的详细程度"""
        
        logger.info("开始强化分析，增强Mermaid图细节")
        
        # 获取当前最佳的mermaid图
        current_mermaid = base_result.final_mermaid_graph
        
        # 第一轮：选择最重要的文件进行强化分析
        important_files = self._select_files_for_reinforcement(files_content, base_result.analysis_steps)
        
        reinforcement_steps = []
        
        for file_path, content in important_files.items():
            logger.info(f"强化分析文件: {file_path}")
            
            # 执行强化分析
            reinforced_step = self._analyze_file_for_reinforcement(
                file_path, content, current_mermaid, project_name, len(reinforcement_steps) + 1)
            
            reinforcement_steps.append(reinforced_step)
            
            # 更新当前mermaid图
            current_mermaid = reinforced_step.mermaid_fragment
        
        # 🆕 第二轮：专门补充被遗漏的getter/setter函数
        logger.info("开始第二轮强化：专门查找被遗漏的getter/setter函数")
        getter_setter_step = self._analyze_missing_getter_setter_functions(
            files_content, current_mermaid, project_name, len(reinforcement_steps) + 1)
        
        if getter_setter_step:
            reinforcement_steps.append(getter_setter_step)
            current_mermaid = getter_setter_step.mermaid_fragment
        
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
            total_token_usage=reinforcement_token_usage,
            overall_confidence=0.9  # 强化分析通常有更高置信度
        )
    
    def _analyze_missing_getter_setter_functions(self, 
                                               files_content: Dict[str, str],
                                               current_mermaid: str,
                                               project_name: str,
                                               step_id: int) -> Optional[BusinessFlowStepResult]:
        """专门分析可能被遗漏的getter/setter函数"""
        
        logger.info("分析可能被遗漏的getter/setter函数")
        
        # 提取所有文件中的getter/setter函数
        all_getter_setter_functions = self._extract_getter_setter_functions(files_content)
        
        if not all_getter_setter_functions:
            logger.info("未发现明显的getter/setter函数")
            return None
        
        # 检查哪些函数可能被遗漏了
        missing_functions = []
        for func_info in all_getter_setter_functions:
            if func_info['name'] not in current_mermaid:
                missing_functions.append(func_info)
        
        if not missing_functions:
            logger.info("所有getter/setter函数都已覆盖")
            return None
        
        logger.info(f"发现 {len(missing_functions)} 个可能被遗漏的getter/setter函数")
        
        # 构建专门的getter/setter强化prompt
        prompt = self._build_getter_setter_reinforcement_prompt(
            missing_functions, current_mermaid, project_name)
        
        # 计算token使用量
        token_usage = self.token_calculator.calculate_prompt_tokens(prompt, self.model)
        
        # 调用Claude进行分析
        analysis_result = ask_claude_for_code_analysis(prompt)
        
        # 解析结果
        flow_description, interactions, enhanced_mermaid, confidence = \
            self._parse_reinforcement_result(analysis_result)
        
        return BusinessFlowStepResult(
            step_id=step_id,
            files_analyzed=[info['file_path'] for info in missing_functions],
            flow_description=f"Getter/Setter函数补充分析: {flow_description}",
            key_interactions=interactions,
            mermaid_fragment=enhanced_mermaid,
            token_usage=token_usage,
            confidence_score=confidence,
            is_reinforcement=True
        )
    
    def _extract_getter_setter_functions(self, files_content: Dict[str, str]) -> List[Dict[str, str]]:
        """提取文件中的getter/setter函数"""
        
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
                                
                                getter_setter_functions.append({
                                    'name': func_name,
                                    'type': 'getter',
                                    'file_path': file_path,
                                    'line_number': i + 1,
                                    'content': line.strip()
                                })
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
                                
                                getter_setter_functions.append({
                                    'name': func_name,
                                    'type': 'setter',
                                    'file_path': file_path,
                                    'line_number': i + 1,
                                    'content': line.strip()
                                })
                        except:
                            continue
        
        logger.info(f"提取到 {len(getter_setter_functions)} 个getter/setter函数")
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

**🎯 专项任务 - 补充Getter/Setter函数:**
1. **保留所有现有内容** - 绝对不能删除任何participant或交互
2. **补充所有遗漏的Getter函数** - 每个Getter函数都必须添加到图中
3. **补充所有遗漏的Setter函数** - 每个Setter函数都必须添加到图中
4. **使用正确的交互格式** - 确保函数名、参数和返回值准确
5. **保持原始合约名** - 使用具体的合约名，不能使用通用名称

**补充要求:**
- **Getter函数格式**: `User->>ContractName: functionName(parameters) returns returnType`
- **Setter函数格式**: `Admin->>ContractName: functionName(parameters)`
- **状态查询格式**: `System->>ContractName: isFunction(parameters) returns bool`
- **权限函数格式**: `Admin->>AccessControl: grantRole(bytes32 role, address account)`

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

## 置信度评估
[给出0-1之间的置信度分数，评估Getter/Setter函数补充的完整性]

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
        
        # 基于分析步骤的置信度选择文件
        low_confidence_files = set()
        
        for step in analysis_steps:
            if step.confidence_score < 0.7:  # 置信度较低的步骤
                low_confidence_files.update(step.files_analyzed)
        
        # 选择最多5个文件进行强化
        selected_files = {}
        count = 0
        
        for file_path in low_confidence_files:
            if count >= 5:  # 限制强化分析的文件数量
                break
            if file_path in files_content:
                selected_files[file_path] = files_content[file_path]
                count += 1
        
        # 如果没有低置信度文件，选择最重要的文件
        if not selected_files:
            prioritized_files = self._prioritize_files_for_flow_analysis(files_content)
            for file_path, content in prioritized_files[:3]:  # 选择前3个重要文件
                selected_files[file_path] = content
        
        logger.info(f"选择了 {len(selected_files)} 个文件进行强化分析")
        return selected_files
    
    def _analyze_file_for_reinforcement(self, 
                                      file_path: str,
                                      file_content: str,
                                      current_mermaid: str,
                                      project_name: str,
                                      step_id: int) -> BusinessFlowStepResult:
        """对单个文件进行强化分析"""
        
        # 构建强化分析prompt
        prompt = self._build_reinforcement_prompt(file_path, file_content, current_mermaid, project_name)
        
        # 计算token使用量
        token_usage = self.token_calculator.calculate_prompt_tokens(prompt, self.model)
        
        # 调用Claude进行强化分析
        analysis_result = ask_claude_for_code_analysis(prompt)
        
        # 解析强化分析结果
        flow_description, interactions, enhanced_mermaid, confidence = \
            self._parse_reinforcement_result(analysis_result)
        
        return BusinessFlowStepResult(
            step_id=step_id,
            files_analyzed=[file_path],
            flow_description=flow_description,
            key_interactions=interactions,
            mermaid_fragment=enhanced_mermaid,
            token_usage=token_usage,
            confidence_score=confidence,
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

**🔍 强化任务 - 100%函数覆盖:**
1. **保留所有现有内容** - 绝对不能删除任何participant或交互
2. **全函数覆盖分析** - 识别 {file_path} 中的**每一个函数**，包括：
   - ✅ **Public/External函数** - 所有对外暴露的函数
   - ✅ **Getter函数** - 所有获取状态变量的函数（如 getValue, getBalance, isActive）
   - ✅ **Setter函数** - 所有设置状态变量的函数（如 setValue, setOwner, setConfig）
   - ✅ **View/Pure函数** - 所有查询类函数，无论多简单
   - ✅ **构造函数** - constructor函数
   - ✅ **事件触发** - 所有emit语句
   - ✅ **修饰符函数** - 重要的modifier应用
   - ✅ **内部函数** - 重要的internal函数调用
3. **补充遗漏交互** - 特别关注简单的getter/setter函数，它们经常被忽略
4. **增加具体细节** - 为每个函数调用添加具体参数和返回值信息
5. **优化交互描述** - **必须使用原始的合约名和函数名**

**🚨 特别强调 - 不能遗漏的函数类型:**
- **简单getter函数**: 如 `getOwner()`, `balanceOf(address)`, `totalSupply()`
- **简单setter函数**: 如 `setOwner(address)`, `pause()`, `unpause()`
- **状态查询函数**: 如 `isOwner(address)`, `isPaused()`, `exists(uint256)`
- **配置函数**: 如 `setConfig()`, `updateParam()`, `setThreshold()`
- **权限函数**: 如 `grantRole()`, `revokeRole()`, `hasRole()`

**关键格式要求 - 必须严格遵守:**
- **合约名**: 使用 {file_path} 中的原始合约名，不能使用通用名称
- **函数名**: 使用代码中的准确函数名，包含完整的函数签名
- **参数类型**: 包含准确的参数类型 (如: address, uint256, string, bool)
- **返回值**: 明确标注函数返回值类型和含义
- **修饰符**: 包含重要的访问控制修饰符检查

**强化重点 (使用原始名称，覆盖所有函数):**
- Getter示例: `User->>TokenContract: balanceOf(address owner) returns uint256`
- Setter示例: `Owner->>TokenContract: setOwner(address newOwner)`
- 状态查询: `System->>AccessControl: hasRole(bytes32 role, address account) returns bool`
- 配置函数: `Admin->>Config: setThreshold(uint256 newThreshold)`
- 事件触发: `TokenContract->>System: emit Transfer(address from, address to, uint256 amount)`
- 权限检查: `TokenContract->>AccessControl: requireRole(msg.sender, "MINTER_ROLE") returns bool`

**输出格式:**
## 强化分析描述
[详细描述对 {file_path} 的**全函数覆盖分析**，列出所有发现的函数，包括被遗漏的getter/setter函数]

## 强化后的完整业务流程图
```mermaid
sequenceDiagram
    [保留所有原有participant和交互]
    [新增 {file_path} 的**所有函数**交互，包括getter/setter]
    [确保每个函数调用都有明确的参数类型和返回值]
    [示例: User->>ERC20Token: balanceOf(address owner) returns uint256]
    [示例: Owner->>ERC20Token: setOwner(address newOwner)]
    [示例: Admin->>Contract: pause() modifiers: onlyOwner]
```

## 强化质量评估
[给出0-1之间的置信度分数，评估是否成功覆盖了所有函数]

**🔥 关键要求:**
- **绝对不能遗漏任何函数** - 包括最简单的getter/setter
- 绝对保持原有图表的完整性
- **绝对不能使用通用名称如 "Contract", "Token", "System"，必须使用具体的合约名**
- 专注**100%覆盖** {file_path} 中的所有函数
- 特别关注之前可能被忽略的简单函数
"""
        
        return prompt
    
    def _parse_reinforcement_result(self, analysis_result: str) -> Tuple[str, List[Dict], str, float]:
        """解析强化分析结果"""
        
        flow_description = ""
        interactions = []
        enhanced_mermaid = ""
        confidence = 0.9  # 强化分析默认更高置信度
        
        try:
            # 提取强化分析描述
            if "## 强化分析描述" in analysis_result:
                desc_start = analysis_result.find("## 强化分析描述") + len("## 强化分析描述")
                desc_end = analysis_result.find("##", desc_start + 1)
                if desc_end != -1:
                    flow_description = analysis_result[desc_start:desc_end].strip()
                else:
                    mermaid_pos = analysis_result.find("```mermaid", desc_start)
                    if mermaid_pos != -1:
                        flow_description = analysis_result[desc_start:mermaid_pos].strip()
            
            # 提取强化后的Mermaid图
            mermaid_start = analysis_result.find("```mermaid")
            if mermaid_start != -1:
                mermaid_start += len("```mermaid")
                mermaid_end = analysis_result.find("```", mermaid_start)
                if mermaid_end != -1:
                    enhanced_mermaid = analysis_result[mermaid_start:mermaid_end].strip()
            
            # 提取置信度
            if "强化质量评估" in analysis_result or "置信度" in analysis_result:
                confidence_section = analysis_result[analysis_result.find("强化质量评估"):]
                import re
                confidence_match = re.search(r'(\d*\.?\d+)', confidence_section)
                if confidence_match:
                    confidence = float(confidence_match.group(1))
                    if confidence > 1:
                        confidence = confidence / 100
            
            # 简化交互关系处理
            interactions = [{"type": "reinforcement", "description": f"强化分析结果，mermaid长度: {len(enhanced_mermaid)}"}]
            
        except Exception as e:
            logger.warning(f"解析强化分析结果时出错: {e}")
        
        return flow_description, interactions, enhanced_mermaid, confidence
    
    def _generate_global_overview_mermaid(self, 
                                        folder_analyses: Dict[str, FolderAnalysisResult],
                                        project_name: str) -> str:
        """生成全局概览Mermaid图"""
        
        if not folder_analyses:
            return ""
        
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

**关键格式要求:**
- **模块命名**: 使用实际的文件夹名称 (如: Asset, Plan, GMEvent, Comptroller)
- **功能描述**: 基于folder_summary提供具体的功能描述
- **避免通用名称**: 不使用 "Module", "Component" 等通用术语

**输出格式:**
```mermaid
flowchart TD
    [创建清晰的项目架构概览图，使用具体的文件夹名称]
    [显示各文件夹/模块的关系，如: Asset, Plan, GMEvent, Comptroller]
    [使用适当的样式和分组，但保持具体的命名]
    [示例: Asset["Asset Management"] --> Plan["Plan Management"]]
```

请生成简洁但信息丰富的全局架构图，使用具体的模块名称而非通用术语。
"""
        
        try:
            analysis_result = ask_claude_for_code_analysis(prompt)
            
            # 提取Mermaid图
            mermaid_start = analysis_result.find("```mermaid")
            if mermaid_start != -1:
                mermaid_start += len("```mermaid")
                mermaid_end = analysis_result.find("```", mermaid_start)
                if mermaid_end != -1:
                    return analysis_result[mermaid_start:mermaid_end].strip()
            
        except Exception as e:
            logger.warning(f"生成全局概览图失败: {e}")
        
        # 备用简单图
        return f"""flowchart TD
    A[{project_name}]
    {chr(10).join([f"A --> {folder_result.folder_name}[{folder_result.folder_name}]" for folder_result in folder_analyses.values()])}
"""
    
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
        logger.info(f"开始真正的增量式业务流程分析: {project_name} ({len(files_content)} 个文件)")
        
        # 重置分析历史
        self.analysis_history = []
        
        # 第一步：按优先级排序文件
        sorted_files = self._prioritize_files_for_flow_analysis(files_content)
        
        # 第二步：真正的增量分析 - 累积构建mermaid图
        cumulative_mermaid = ""  # 累积的mermaid图
        
        for step_id, (file_path, content) in enumerate(sorted_files, 1):
            logger.info(f"增量分析步骤 {step_id}: {file_path}")
            
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
        file_priorities = []
        
        for file_path, content in files_content.items():
            priority = self._calculate_business_flow_priority(file_path, content)
            file_priorities.append((priority, file_path, content))
        
        # 按优先级降序排序
        file_priorities.sort(key=lambda x: x[0], reverse=True)
        
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
        logger.info(f"单文件增量分析: {file_path}")
        
        # 构建增量分析prompt
        prompt = self._build_true_incremental_prompt(
            file_path, file_content, existing_mermaid, step_id, project_name)
        
        # 计算token使用量
        token_usage = self.token_calculator.calculate_prompt_tokens(prompt, self.model)
        
        # 调用Claude进行增量分析
        analysis_result = ask_claude_for_code_analysis(prompt)
        
        # 解析分析结果，获取扩展后的完整mermaid图
        flow_description, interactions, extended_mermaid, confidence = \
            self._parse_incremental_result(analysis_result)
        
        return BusinessFlowStepResult(
            step_id=step_id,
            files_analyzed=[file_path],  # 只包含当前文件
            flow_description=flow_description,
            key_interactions=interactions,
            mermaid_fragment=extended_mermaid,  # 这是累积的完整图
            token_usage=token_usage,
            confidence_score=confidence
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
1. **全函数覆盖分析** - 分析 {file_path} 中的**每一个函数**，包括：
   - ✅ **Public/External函数** - 所有对外暴露的函数
   - ✅ **Getter函数** - 所有获取状态变量的函数（如 getValue, getBalance, isActive）
   - ✅ **Setter函数** - 所有设置状态变量的函数（如 setValue, setOwner, setConfig）
   - ✅ **View/Pure函数** - 所有查询类函数，无论多简单
   - ✅ **构造函数** - constructor函数
   - ✅ **事件触发** - 所有emit语句
   - ✅ **修饰符函数** - 重要的modifier应用
   - ✅ **内部函数** - 重要的internal函数调用
2. **创建完整的Mermaid序列图** - **必须使用原始的合约名和函数名**
3. **确保图表结构清晰** - 为后续文件扩展做好准备，但不能遗漏任何函数

**🚨 特别强调 - 不能遗漏的函数类型:**
- **简单getter函数**: 如 `getOwner()`, `balanceOf(address)`, `totalSupply()`
- **简单setter函数**: 如 `setOwner(address)`, `pause()`, `unpause()`
- **状态查询函数**: 如 `isOwner(address)`, `isPaused()`, `exists(uint256)`
- **配置函数**: 如 `setConfig()`, `updateParam()`, `setThreshold()`
- **权限函数**: 如 `grantRole()`, `revokeRole()`, `hasRole()`

**关键格式要求 - 必须严格遵守:**
- **合约名**: 使用文件中的原始合约名 (如: ERC20AssetGateway, PlanFactory, GMEvent)
- **函数名**: 使用代码中的准确函数名 (如: constructor, transfer, approve, confirmJoin)
- **参数**: 包含函数的真实参数名和类型 (如: address _user, uint256 _amount)
- **返回值**: 明确标注函数返回值类型和含义
- **修饰符**: 包含重要的修饰符检查 (如: onlyOwner, requireRole)

**函数覆盖示例:**
- Getter函数: `User->>TokenContract: balanceOf(address owner) returns uint256`
- Setter函数: `Owner->>TokenContract: setOwner(address newOwner)`
- 状态查询: `System->>AccessControl: hasRole(bytes32 role, address account) returns bool`
- 构造函数: `User->>TokenContract: constructor(address tokenAddress, address registry)`
- 配置函数: `Admin->>Config: setThreshold(uint256 newThreshold)`

**输出格式:**
## 业务流程描述
[详细描述 {file_path} 的**所有函数**业务逻辑，包括getter/setter函数，使用原始合约名和函数名]

## 完整Mermaid图
```mermaid
sequenceDiagram
    [创建详细的序列图，严格使用原始合约名和函数名]
    [**必须包含文件中的所有函数**，包括简单的getter/setter]
    [格式示例: User->>ERC20Token: balanceOf(address owner) returns uint256]
    [格式示例: Owner->>ERC20Token: setOwner(address newOwner)]
    [格式示例: Admin->>Contract: pause() modifiers: onlyOwner]
    [格式示例: User->>TokenContract: constructor(address tokenAddress, address registry)]
```

## 置信度评估
[给出0-1之间的置信度分数，评估是否成功覆盖了所有函数]

**🔥 重要提醒:**
- **绝对不能遗漏任何函数** - 包括最简单的getter/setter
- 绝对不能使用通用名称如 "Contract", "Token"，必须使用具体的合约名
- 函数名必须与源代码完全一致
- 参数名要尽可能使用源代码中的原始参数名
- 特别关注可能被忽略的简单查询和设置函数
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
1. **绝对保留**已有Mermaid图中的所有内容，一个交互都不能丢失
2. **全函数覆盖分析** - 分析新文件 {file_path} 中的**每一个函数**，包括：
   - ✅ **Public/External函数** - 所有对外暴露的函数
   - ✅ **Getter函数** - 所有获取状态变量的函数（如 getValue, getBalance, isActive）
   - ✅ **Setter函数** - 所有设置状态变量的函数（如 setValue, setOwner, setConfig）
   - ✅ **View/Pure函数** - 所有查询类函数，无论多简单
   - ✅ **构造函数** - constructor函数
   - ✅ **事件触发** - 所有emit语句
   - ✅ **修饰符函数** - 重要的modifier应用
   - ✅ **内部函数** - 重要的internal函数调用
3. **将新文件的所有函数业务流程扩展到已有图中**
4. **必须使用原始的合约名和函数名**，确保新增的交互包含具体的函数名和参数
5. **保持图表的逻辑顺序和清晰结构**

**🚨 特别强调 - 不能遗漏的函数类型:**
- **简单getter函数**: 如 `getOwner()`, `balanceOf(address)`, `totalSupply()`
- **简单setter函数**: 如 `setOwner(address)`, `pause()`, `unpause()`
- **状态查询函数**: 如 `isOwner(address)`, `isPaused()`, `exists(uint256)`
- **配置函数**: 如 `setConfig()`, `updateParam()`, `setThreshold()`
- **权限函数**: 如 `grantRole()`, `revokeRole()`, `hasRole()`

**关键格式要求 - 必须严格遵守:**
- **合约名**: 使用 {file_path} 中的原始合约名 (如: SurplusPool, Plan, GMEventAbstract)
- **函数名**: 使用代码中的准确函数名 (如: deposit, withdraw, confirmJoin, approve)
- **参数**: 包含函数的真实参数名和类型 (如: uint256 epoch, address _payer, uint256 amount)
- **返回值**: 明确标注函数返回值类型和含义
- **事件**: 包含emit语句 (如: emit Deposited(epoch, amount))

**函数覆盖示例:**
- Getter函数: `User->>NewContract: balanceOf(address owner) returns uint256`
- Setter函数: `Owner->>NewContract: setOwner(address newOwner)`
- 状态查询: `System->>NewContract: hasRole(bytes32 role, address account) returns bool`
- 配置函数: `Admin->>NewContract: setThreshold(uint256 newThreshold)`
- 事件触发: `NewContract->>System: emit Transfer(address from, address to, uint256 amount)`

**输出格式:**
## 业务流程描述
[详细描述 {file_path} 的**所有函数**如何融入现有业务流程，包括getter/setter函数，使用原始合约名和函数名]

## 扩展后的完整Mermaid图
```mermaid
sequenceDiagram
    [包含所有原有内容 + 新增的 {file_path} 的**所有函数**交互]
    [确保所有原有的交互都完整保留]
    [**必须包含新文件中的所有函数**，包括简单的getter/setter]
    [示例: User->>NewContract: balanceOf(address owner) returns uint256]
    [示例: Owner->>NewContract: setOwner(address newOwner)]
    [示例: Admin->>NewContract: pause() modifiers: onlyOwner]
    [示例: NewContract->>System: emit Transfer(address from, address to, uint256 amount)]
```

## 置信度评估
[给出0-1之间的置信度分数，评估是否成功覆盖了新文件中的所有函数]

**🔥 重要提醒:** 
- **绝对不能遗漏新文件中的任何函数** - 包括最简单的getter/setter
- 必须保留原有Mermaid图的所有participant和交互
- 只能新增，绝对不能删除或修改原有内容
- **绝对不能使用通用名称如 "Contract", "Token"，必须使用具体的合约名**
- 函数名必须与源代码完全一致
- 确保扩展后的图表逻辑连贯、结构清晰
- 特别关注之前可能被忽略的简单查询和设置函数
"""
        
        return prompt
    
    def _parse_incremental_result(self, analysis_result: str) -> Tuple[str, List[Dict], str, float]:
        """解析增量分析结果，提取扩展后的完整mermaid图"""
        
        flow_description = ""
        interactions = []
        extended_mermaid = ""
        confidence = 0.8  # 默认置信度
        
        try:
            # 提取业务流程描述
            if "## 业务流程描述" in analysis_result:
                desc_start = analysis_result.find("## 业务流程描述") + len("## 业务流程描述")
                desc_end = analysis_result.find("##", desc_start + 1)  # 找下一个##标题
                if desc_end != -1:
                    flow_description = analysis_result[desc_start:desc_end].strip()
                else:
                    # 如果没有找到下一个##，就到mermaid开始位置
                    mermaid_pos = analysis_result.find("```mermaid", desc_start)
                    if mermaid_pos != -1:
                        flow_description = analysis_result[desc_start:mermaid_pos].strip()
            
            # 提取扩展后的完整Mermaid图
            mermaid_start = analysis_result.find("```mermaid")
            if mermaid_start != -1:
                mermaid_start += len("```mermaid")
                mermaid_end = analysis_result.find("```", mermaid_start)
                if mermaid_end != -1:
                    extended_mermaid = analysis_result[mermaid_start:mermaid_end].strip()
            
            # 提取置信度
            if "置信度" in analysis_result or "confidence" in analysis_result.lower():
                # 寻找置信度部分
                confidence_keywords = ["置信度", "confidence"]
                for keyword in confidence_keywords:
                    if keyword in analysis_result.lower():
                        confidence_section = analysis_result[analysis_result.lower().find(keyword):]
                        # 尝试找到数字
                        import re
                        confidence_match = re.search(r'(\d*\.?\d+)', confidence_section)
                        if confidence_match:
                            confidence = float(confidence_match.group(1))
                            if confidence > 1:  # 如果是百分比形式
                                confidence = confidence / 100
                            break
            
            # 简化交互关系处理
            interactions = [{"type": "incremental", "description": f"从增量分析结果解析，mermaid长度: {len(extended_mermaid)}"}]
            
        except Exception as e:
            logger.warning(f"解析增量分析结果时出错: {e}")
        
        return flow_description, interactions, extended_mermaid, confidence
    
    def _finalize_cumulative_mermaid(self, 
                                    project_name: str,
                                    files_content: Dict[str, str],
                                    step_results: List[BusinessFlowStepResult],
                                    cumulative_mermaid: str) -> CompleteBusinessFlowResult:
        """优化最终的累积mermaid图"""
        
        logger.info("优化最终的累积mermaid图")
        
        # 构建最终优化prompt
        final_prompt = self._build_final_optimization_prompt(project_name, cumulative_mermaid)
        
        # 计算token使用量
        token_usage = self.token_calculator.calculate_prompt_tokens(final_prompt, self.model)
        
        # 调用Claude进行最终优化
        final_analysis = ask_claude_for_code_analysis(final_prompt)
        
        # 提取优化后的Mermaid图和业务总结
        final_mermaid = self._extract_final_mermaid(final_analysis)
        business_summary = self._extract_business_summary(final_analysis)
        
        # 如果优化失败，使用累积的mermaid图
        if not final_mermaid or len(final_mermaid) < len(cumulative_mermaid) * 0.8:
            logger.warning("优化后的图表可能不完整，使用累积图")
            final_mermaid = cumulative_mermaid
        
        # 计算总体置信度
        overall_confidence = sum(step.confidence_score for step in step_results) / len(step_results) if step_results else 0.0
        
        # 计算总token使用量
        total_token_usage = self._calculate_total_token_usage(step_results, token_usage)
        
        return CompleteBusinessFlowResult(
            project_name=project_name,
            total_files=len(files_content),
            analysis_strategy="incremental",
            analysis_steps=step_results,
            final_mermaid_graph=final_mermaid,
            business_summary=business_summary if business_summary else f"{project_name}项目业务流程分析完成",
            folder_analyses={},
            global_mermaid_graph=final_mermaid,
            total_token_usage=total_token_usage,
            overall_confidence=overall_confidence
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

**🎯 优化任务 - 保持100%函数覆盖:**
1. **保留所有现有内容** - 绝对不能删除任何participant或交互，包括所有getter/setter函数
2. **验证函数覆盖完整性** - 确保包含了所有类型的函数：
   - ✅ Public/External函数
   - ✅ Getter函数（如 getValue, getBalance, isActive）
   - ✅ Setter函数（如 setValue, setOwner, setConfig）
   - ✅ View/Pure函数
   - ✅ 构造函数
   - ✅ 事件触发
   - ✅ 修饰符检查
3. **优化交互的逻辑顺序**，确保业务流程的时序合理
4. **添加适当的注释和分组**（使用 %% 注释和 Note）
5. **保持所有原始合约名和函数名** - 确保所有函数名和参数都准确无误
6. **检查并修正可能的语法错误**

**🚨 特别关注 - 确保这些函数没有被遗漏:**
- **简单getter函数**: 如 `getOwner()`, `balanceOf(address)`, `totalSupply()`
- **简单setter函数**: 如 `setOwner(address)`, `pause()`, `unpause()`
- **状态查询函数**: 如 `isOwner(address)`, `isPaused()`, `exists(uint256)`
- **配置函数**: 如 `setConfig()`, `updateParam()`, `setThreshold()`
- **权限函数**: 如 `grantRole()`, `revokeRole()`, `hasRole()`

**关键格式要求:**
- **绝对不能修改合约名** - 保持所有原始合约名 (如: ERC20AssetGateway, PlanFactory, GMEvent)
- **绝对不能修改函数名** - 保持所有原始函数名和参数
- **不能使用通用名称** - 禁止将具体合约名改为 "Contract", "Token" 等通用名称
- **不能删除任何函数交互** - 特别是简单的getter/setter函数

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
- 如果发现通用名称，必须保持原有的具体合约名
- 特别关注简单函数，确保它们没有在优化过程中被遗漏
"""
        
        return prompt
    
    def _extract_final_mermaid(self, analysis_result: str) -> str:
        """从最终分析结果中提取Mermaid图"""
        
        try:
            mermaid_start = analysis_result.find("```mermaid")
            if mermaid_start != -1:
                mermaid_start += len("```mermaid")
                mermaid_end = analysis_result.find("```", mermaid_start)
                if mermaid_end != -1:
                    return analysis_result[mermaid_start:mermaid_end].strip()
        except Exception as e:
            logger.warning(f"提取Mermaid图失败: {e}")
        
        return ""
    
    def _extract_business_summary(self, analysis_result: str) -> str:
        """从分析结果中提取业务总结"""
        
        try:
            if "## 业务流程总结" in analysis_result:
                summary_start = analysis_result.find("## 业务流程总结") + len("## 业务流程总结")
                summary_end = analysis_result.find("## 完整业务流程图", summary_start)
                if summary_end == -1:
                    summary_end = analysis_result.find("```mermaid", summary_start)
                if summary_end != -1:
                    return analysis_result[summary_start:summary_end].strip()
        except Exception as e:
            logger.warning(f"提取业务总结失败: {e}")
        
        return "无法提取业务总结"
    

    
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
    analyzer = BusinessFlowAnalyzer(model)
    return analyzer.analyze_business_flow_incremental(files_content, project_name)

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
    
    # 读取项目文件
    files_content = {}
    for ext in file_extensions:
        for file_path in project_path.glob(f"*{ext}"):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        relative_path = str(file_path.relative_to(project_path))
                        files_content[relative_path] = content
                except Exception as e:
                    logger.warning(f"读取文件 {file_path} 失败: {e}")
    
    return analyze_business_flow(files_content, project_name, model) 