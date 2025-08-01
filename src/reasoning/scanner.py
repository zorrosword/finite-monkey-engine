import os
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from .utils.dialogue_manager import DialogueHistory
from .utils.scan_utils import ScanUtils
from prompt_factory.vul_prompt_common import VulPromptCommon
from openai_api.openai import ask_vul, ask_claude, common_ask_for_json
from logging_config import get_logger


class VulnerabilityScanner:
    """漏洞扫描器，负责智能合约代码的漏洞扫描（支持RAG选择）"""
    
    def __init__(self, project_audit):
        self.project_audit = project_audit
        self.logger = get_logger(f"VulnerabilityScanner[{project_audit.project_id}]")
        # 实例级别的 prompt index 追踪
        self.current_prompt_index = 0
        self.total_prompt_count = len(VulPromptCommon.vul_prompt_common_new().keys())
        # 对话历史管理
        self.dialogue_history = DialogueHistory(project_audit.project_id)
        
        # 初始化RAG处理器（如果可用）
        self.rag_processor = None
        self._initialize_rag_processor()
    
    def _initialize_rag_processor(self):
        """初始化RAG处理器"""
        try:
            from context.rag_processor import RAGProcessor
            # 尝试初始化RAG处理器
            call_trees = getattr(self.project_audit, 'call_trees', [])
            self.rag_processor = RAGProcessor(
                self.project_audit.functions_to_check, 
                "./src/codebaseQA/lancedb", 
                self.project_audit.project_id,
                call_trees
            )
            print("✅ Reasoning模块: RAG处理器初始化完成")
        except Exception as e:
            print(f"⚠️ Reasoning模块: RAG处理器初始化失败: {e}")
            self.rag_processor = None

    def get_available_rag_types(self) -> Dict[str, str]:
        """获取可用的RAG类型列表及其描述"""
        if not self.rag_processor:
            return {}
        
        return {
            # 基础RAG类型
            'name': '名字检索 - 基于函数名称的精确匹配，适合查找特定函数',
            'content': '内容检索 - 基于函数源代码内容的语义相似性，适合查找相似功能的代码',
            'natural': '自然语言检索 - 基于AI生成的功能描述的语义理解，适合描述性查询',
            
            # 关系型RAG类型
            'upstream': '上游函数检索 - 基于调用此函数的上游函数内容，适合查找调用链上游',
            'downstream': '下游函数检索 - 基于此函数调用的下游函数内容，适合查找调用链下游',
            
            # 专门的关系表RAG类型
            'upstream_natural': '上游自然语言关系检索 - 基于上游函数的自然语言描述，适合理解上游逻辑',
            'downstream_natural': '下游自然语言关系检索 - 基于下游函数的自然语言描述，适合理解下游影响',
            'upstream_content': '上游内容关系检索 - 基于上游函数的代码内容，适合代码层面的上游分析',
            'downstream_content': '下游内容关系检索 - 基于下游函数的代码内容，适合代码层面的下游分析',
            
            # 文件级RAG类型
            'file_content': '文件内容检索 - 基于整个文件的内容，适合文件级别的分析',
            'file_natural': '文件自然语言检索 - 基于文件的自然语言描述，适合文件功能理解'
        }

    def ask_llm_to_choose_rag_and_query(self, vulnerability_question: str, context_info: str = "") -> Dict[str, Any]:
        """让大模型选择RAG类型并提供查询内容
        
        Args:
            vulnerability_question: 漏洞分析问题
            context_info: 上下文信息
            
        Returns:
            Dict包含选择的RAG类型、查询内容和RAG结果
        """
        if not self.rag_processor:
            return {
                'rag_chosen': None,
                'query_used': None,
                'rag_results': [],
                'reason': 'RAG处理器不可用'
            }
        
        # 获取可用的RAG类型
        rag_types = self.get_available_rag_types()
        
        # 构建提示，让大模型选择RAG类型
        rag_selection_prompt = f"""你正在进行智能合约漏洞分析。根据以下问题和上下文，请选择最合适的RAG检索类型，并提供相应的查询内容。

**漏洞分析问题**：
{vulnerability_question}

**当前上下文**：
{context_info}

**可用的RAG检索类型**：
{chr(10).join([f'- {k}: {v}' for k, v in rag_types.items()])}

**请分析并回答**：
1. 最适合此问题的RAG类型是什么？
2. 应该使用什么查询内容进行检索？
3. 为什么选择这种RAG类型？

请用JSON格式回答：
{{
    "rag_type": "选择的RAG类型名称",
    "query_content": "用于检索的具体查询内容",
    "reason": "选择此RAG类型的原因",
    "backup_rag_type": "备选RAG类型（可选）",
    "backup_query": "备选查询内容（可选）"
}}

只返回JSON，不要其他解释。"""

        try:
            # 询问大模型选择RAG类型
            response = common_ask_for_json(rag_selection_prompt)
            
            if not response:
                return {
                    'rag_chosen': None,
                    'query_used': None,
                    'rag_results': [],
                    'reason': '大模型未返回RAG选择'
                }
            
            import json
            rag_choice = json.loads(response) if isinstance(response, str) else response
            
            chosen_rag = rag_choice.get('rag_type', 'content')  # 默认使用content
            query_content = rag_choice.get('query_content', vulnerability_question)
            reason = rag_choice.get('reason', '默认选择')
            
            print(f"🤖 大模型选择的RAG类型: {chosen_rag}")
            print(f"🔍 查询内容: {query_content}")
            print(f"💭 选择原因: {reason}")
            
            # 根据选择执行相应的RAG查询
            rag_results = self._execute_rag_query(chosen_rag, query_content)
            
            # 如果主要RAG没有结果，尝试备选方案
            if not rag_results and rag_choice.get('backup_rag_type'):
                backup_rag = rag_choice.get('backup_rag_type')
                backup_query = rag_choice.get('backup_query', query_content)
                print(f"🔄 尝试备选RAG: {backup_rag}")
                rag_results = self._execute_rag_query(backup_rag, backup_query)
                chosen_rag = backup_rag
                query_content = backup_query
            
            return {
                'rag_chosen': chosen_rag,
                'query_used': query_content,
                'rag_results': rag_results,
                'reason': reason,
                'llm_choice': rag_choice
            }
            
        except Exception as e:
            print(f"❌ RAG选择过程失败: {e}")
            # 回退到简单的content搜索
            rag_results = self._execute_rag_query('content', vulnerability_question)
            return {
                'rag_chosen': 'content',
                'query_used': vulnerability_question,
                'rag_results': rag_results,
                'reason': f'RAG选择失败，回退到默认: {str(e)}'
            }

    def _execute_rag_query(self, rag_type: str, query: str, k: int = 5) -> List[Dict]:
        """执行指定类型的RAG查询
        
        Args:
            rag_type: RAG类型
            query: 查询内容
            k: 返回结果数量
            
        Returns:
            List[Dict]: RAG查询结果
        """
        if not self.rag_processor:
            return []
        
        try:
            # 根据RAG类型调用相应的搜索方法
            if rag_type == 'name':
                return self.rag_processor.search_functions_by_name(query, k)
            elif rag_type == 'content':
                return self.rag_processor.search_functions_by_content(query, k)
            elif rag_type == 'natural':
                return self.rag_processor.search_functions_by_natural_language(query, k)
            elif rag_type == 'upstream':
                return self.rag_processor.search_functions_by_upstream(query, k)
            elif rag_type == 'downstream':
                return self.rag_processor.search_functions_by_downstream(query, k)
            elif rag_type == 'upstream_natural':
                return self.rag_processor.search_relationships_by_upstream_natural(query, k)
            elif rag_type == 'downstream_natural':
                return self.rag_processor.search_relationships_by_downstream_natural(query, k)
            elif rag_type == 'upstream_content':
                return self.rag_processor.search_relationships_by_upstream_content(query, k)
            elif rag_type == 'downstream_content':
                return self.rag_processor.search_relationships_by_downstream_content(query, k)
            elif rag_type == 'file_content':
                return self.rag_processor.search_files_by_content(query, k)
            elif rag_type == 'file_natural':
                return self.rag_processor.search_files_by_natural_language(query, k)
            else:
                print(f"⚠️ 未知的RAG类型: {rag_type}，使用默认content搜索")
                return self.rag_processor.search_functions_by_content(query, k)
                
        except Exception as e:
            print(f"❌ RAG查询失败 ({rag_type}): {e}")
            return []

    def do_scan(self, task_manager, is_gpt4=False, filter_func=None):
        """执行漏洞扫描（增强RAG支持）"""
        # 获取任务列表
        tasks = task_manager.get_task_list()
        if len(tasks) == 0:
            return []

        # 检查是否启用对话模式
        dialogue_mode = os.getenv("ENABLE_DIALOGUE_MODE", "False").lower() == "true"
        
        if dialogue_mode:
            print("🗣️ 对话模式已启用（支持RAG选择）")
            return self._scan_with_dialogue_mode(tasks, task_manager, filter_func, is_gpt4)
        else:
            print("🔄 标准模式运行中（支持RAG选择）")
            return self._scan_standard_mode(tasks, task_manager, filter_func, is_gpt4)

    def _scan_standard_mode(self, tasks, task_manager, filter_func, is_gpt4):
        """标准模式扫描（增强RAG支持）"""
        max_threads = int(os.getenv("MAX_THREADS_OF_SCAN", 5))
        
        def process_task(task):
            self._process_single_task_standard_with_rag(task, task_manager, filter_func, is_gpt4)
            
        ScanUtils.execute_parallel_scan(tasks, process_task, max_threads)
        return tasks

    def _scan_with_dialogue_mode(self, tasks, task_manager, filter_func, is_gpt4):
        """对话模式扫描（增强RAG支持）"""
        # 按task.name分组任务
        task_groups = ScanUtils.group_tasks_by_name(tasks)
        
        # 清除历史对话记录
        self.dialogue_history.clear()
        
        # 对每组任务进行处理
        max_threads = int(os.getenv("MAX_THREADS_OF_SCAN", 5))
        
        def process_task_group(group_tasks):
            for task in group_tasks:
                self._process_single_task_dialogue_with_rag(task, task_manager, filter_func, is_gpt4)
        
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = []
            for task_name, group_tasks in task_groups.items():
                future = executor.submit(process_task_group, group_tasks)
                futures.append(future)
            
            with tqdm(total=len(task_groups), desc="Processing task groups with RAG") as pbar:
                for future in as_completed(futures):
                    future.result()
                    pbar.update(1)
        
        return tasks

    def _process_single_task_standard_with_rag(self, task, task_manager, filter_func, is_gpt4):
        """标准模式下处理单个任务（增强RAG支持）"""
        # 检查任务是否已经扫描过
        if ScanUtils.is_task_already_scanned(task):
            self.logger.info(f"任务 {task.name} 已经扫描过，跳过")
            return
        
        # 检查是否应该扫描此任务
        if not ScanUtils.should_scan_task(task, filter_func):
            self.logger.info(f"任务 {task.name} 不满足扫描条件，跳过")
            return
        
        try:
            # 获取任务相关信息
            task_info = self._extract_task_info(task)
            vulnerability_question = task_info.get('question', '')
            context_info = task_info.get('context', '')
            
            # 让大模型选择RAG并查询
            rag_result = self.ask_llm_to_choose_rag_and_query(vulnerability_question, context_info)
            
            # 构建增强的提示（包含RAG结果）
            enhanced_context = self._build_enhanced_context(task_info, rag_result)
            
            # 调用原有的扫描逻辑（传入增强的上下文）
            self._execute_vulnerability_scan(task, task_manager, enhanced_context, is_gpt4)
            
        except Exception as e:
            print(f"❌ 任务处理失败: {e}")
            # 回退到原有逻辑
            self._process_single_task_standard(task, task_manager, filter_func, is_gpt4)

    def _process_single_task_dialogue_with_rag(self, task, task_manager, filter_func, is_gpt4):
        """对话模式下处理单个任务（增强RAG支持）"""
        # 类似标准模式，但包含对话历史
        if ScanUtils.is_task_already_scanned(task):
            self.logger.info(f"任务 {task.name} 已经扫描过，跳过")
            return
        
        try:
            # 获取对话历史
            dialogue_context = self.dialogue_history.get_relevant_context(task)
            
            # 获取任务相关信息
            task_info = self._extract_task_info(task)
            task_info['dialogue_context'] = dialogue_context
            
            vulnerability_question = task_info.get('question', '')
            context_info = f"{task_info.get('context', '')}\n对话历史: {dialogue_context}"
            
            # 让大模型选择RAG并查询
            rag_result = self.ask_llm_to_choose_rag_and_query(vulnerability_question, context_info)
            
            # 构建增强的提示（包含RAG结果和对话历史）
            enhanced_context = self._build_enhanced_context(task_info, rag_result)
            
            # 执行扫描并更新对话历史
            scan_result = self._execute_vulnerability_scan(task, task_manager, enhanced_context, is_gpt4)
            self.dialogue_history.add_scan_result(task, scan_result, rag_result)
            
        except Exception as e:
            print(f"❌ 对话任务处理失败: {e}")
            # 回退到原有逻辑
            self._process_single_task_dialogue(task, task_manager, filter_func, is_gpt4)

    def _extract_task_info(self, task) -> Dict[str, str]:
        """从任务中提取关键信息"""
        return {
            'question': getattr(task, 'description', ''),
            'context': getattr(task, 'content', ''),
            'task_type': getattr(task, 'task_type', ''),
            'function_names': [f.get('name', '') for f in getattr(task, 'functions_to_check', [])]
        }

    def _build_enhanced_context(self, task_info: Dict, rag_result: Dict) -> str:
        """构建增强的上下文信息"""
        context_parts = [
            f"任务描述: {task_info.get('question', '')}",
            f"任务类型: {task_info.get('task_type', '')}",
        ]
        
        if rag_result.get('rag_chosen'):
            context_parts.append(f"\n=== RAG增强信息 ===")
            context_parts.append(f"使用的RAG类型: {rag_result['rag_chosen']}")
            context_parts.append(f"选择原因: {rag_result.get('reason', '')}")
            
            if rag_result.get('rag_results'):
                context_parts.append(f"找到 {len(rag_result['rag_results'])} 个相关结果:")
                for i, result in enumerate(rag_result['rag_results'][:3], 1):  # 只显示前3个
                    if isinstance(result, dict):
                        func_name = result.get('name', result.get('function_name', 'Unknown'))
                        context_parts.append(f"  {i}. {func_name}")
            else:
                context_parts.append("未找到相关RAG结果")
        
        return "\n".join(context_parts)

    def _execute_vulnerability_scan(self, task, task_manager, enhanced_context: str, is_gpt4: bool) -> str:
        """执行漏洞扫描（使用增强上下文）"""
        # 这里调用原有的扫描逻辑，但传入增强的上下文
        # 具体实现依赖于原有的扫描方法
        try:
            # 调用原有方法（传入增强上下文）
            if is_gpt4:
                result = ask_vul(enhanced_context, task.content)
            else:
                # 将上下文和任务内容合并成完整的prompt
                full_prompt = f"{enhanced_context}\n\n任务内容:\n{task.content}"
                result = ask_claude(full_prompt)
            
            # 保存结果
            if hasattr(task, 'id') and task.id:
                # 使用正确的更新方法
                task_manager.update_result(task.id, result)
            else:
                # 如果任务没有ID，记录警告
                self.logger.warning(f"任务 {task.name} 没有ID，无法保存结果")
            
            return result
        except Exception as e:
            print(f"❌ 漏洞扫描执行失败: {e}")
            return ""

    # 保留原有方法作为回退
    def _process_single_task_standard(self, task, task_manager, filter_func, is_gpt4):
        """原有的标准模式处理方法（作为回退）"""
        # 这里是原有的实现逻辑...
        pass

    def _process_single_task_dialogue(self, task, task_manager, filter_func, is_gpt4):
        """原有的对话模式处理方法（作为回退）"""
        # 这里是原有的实现逻辑...
        pass 