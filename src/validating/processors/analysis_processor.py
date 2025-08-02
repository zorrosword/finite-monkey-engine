import os
import time
import json
from datetime import datetime
from typing import List, Tuple, Dict, Any

from dao.entity import Project_Task

from ..utils.check_utils import CheckUtils
from prompt_factory.prompt_assembler import PromptAssembler
from openai_api.openai import ask_claude, common_ask_confirmation, common_ask_for_json


class AnalysisProcessor:
    """Analysis processor responsible for executing specific vulnerability analysis logic (支持RAG选择)"""
    
    def __init__(self, context_data: Dict[str, Any]):
        """
        初始化分析处理器
        
        Args:
            context_data: 包含项目数据的字典，包括functions, functions_to_check等
        """
        self.context_data = context_data
        self.functions = context_data.get('functions', [])
        self.functions_to_check = context_data.get('functions_to_check', [])
        self.call_trees = context_data.get('call_trees', [])
        self.project_id = context_data.get('project_id', '')
        self.project_path = context_data.get('project_path', '')
        
        # 初始化RAG处理器（如果可用）
        self.rag_processor = None
        self._initialize_rag_processor()
    
    def _initialize_rag_processor(self):
        """初始化RAG处理器"""
        try:
            from context.rag_processor import RAGProcessor
            # 尝试初始化RAG处理器
            self.rag_processor = RAGProcessor(
                self.functions_to_check, 
                "./src/codebaseQA/lancedb", 
                self.project_id
            )
            print("✅ Validating模块: RAG处理器初始化完成")
        except Exception as e:
            print(f"⚠️ Validating模块: RAG处理器初始化失败: {e}")
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

    def ask_llm_to_choose_rag_for_validation(self, vulnerability_report: str, validation_question: str, context_info: str = "") -> Dict[str, Any]:
        """让大模型选择RAG类型进行漏洞验证
        
        Args:
            vulnerability_report: 漏洞报告内容
            validation_question: 验证问题
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
        rag_selection_prompt = f"""你正在进行智能合约漏洞验证。需要根据漏洞报告和验证问题，选择最合适的RAG检索类型来获取相关信息进行验证。

**漏洞报告**：
{vulnerability_report}

**验证问题**：
{validation_question}

**当前上下文**：
{context_info}

**可用的RAG检索类型**：
{chr(10).join([f'- {k}: {v}' for k, v in rag_types.items()])}

**请分析：**
1. 要验证这个漏洞，最需要什么类型的相关信息？
2. 应该选择哪种RAG类型来获取这些信息？
3. 应该使用什么查询内容进行检索？

**选择建议**：
- 如果需要验证函数调用关系，选择upstream/downstream相关的RAG
- 如果需要查找相似的漏洞模式，选择content或natural RAG
- 如果需要理解业务逻辑，选择natural相关的RAG
- 如果需要验证特定函数行为，选择name或content RAG

请用JSON格式回答：
{{
    "rag_type": "选择的RAG类型名称",
    "query_content": "用于检索的具体查询内容",
    "reason": "选择此RAG类型的详细原因",
    "validation_focus": "验证的重点是什么",
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
            
            rag_choice = json.loads(response) if isinstance(response, str) else response
            
            chosen_rag = rag_choice.get('rag_type', 'content')  # 默认使用content
            query_content = rag_choice.get('query_content', validation_question)
            reason = rag_choice.get('reason', '默认选择')
            validation_focus = rag_choice.get('validation_focus', '常规验证')
            
            print(f"🤖 验证阶段大模型选择的RAG类型: {chosen_rag}")
            print(f"🔍 验证查询内容: {query_content}")
            print(f"🎯 验证重点: {validation_focus}")
            print(f"💭 选择原因: {reason}")
            
            # 根据选择执行相应的RAG查询
            rag_results = self._execute_rag_query(chosen_rag, query_content)
            
            # 如果主要RAG没有结果，尝试备选方案
            if not rag_results and rag_choice.get('backup_rag_type'):
                backup_rag = rag_choice.get('backup_rag_type')
                backup_query = rag_choice.get('backup_query', query_content)
                print(f"🔄 验证阶段尝试备选RAG: {backup_rag}")
                rag_results = self._execute_rag_query(backup_rag, backup_query)
                chosen_rag = backup_rag
                query_content = backup_query
            
            return {
                'rag_chosen': chosen_rag,
                'query_used': query_content,
                'rag_results': rag_results,
                'reason': reason,
                'validation_focus': validation_focus,
                'llm_choice': rag_choice
            }
            
        except Exception as e:
            print(f"❌ 验证RAG选择过程失败: {e}")
            # 回退到简单的content搜索
            rag_results = self._execute_rag_query('content', validation_question)
            return {
                'rag_chosen': 'content',
                'query_used': validation_question,
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

    def extract_required_info(self, response_text: str) -> List[str]:
        """提取需要进一步分析的信息（增强RAG支持）"""
        # 首先尝试使用大模型提取关键信息
        try:
            extract_prompt = f"""从以下漏洞分析报告中提取需要进一步验证或分析的关键信息点：

{response_text}

请提取：
1. 需要验证的函数调用关系
2. 需要确认的代码逻辑
3. 需要查找的相关函数或合约
4. 需要分析的业务流程
5. 其他需要进一步分析的要点

请用JSON格式返回：
{{
    "required_info": [
        "信息点1的具体描述",
        "信息点2的具体描述"
    ],
    "analysis_type": "需要的分析类型（如函数关系分析、逻辑验证等）",
    "priority": "high/medium/low"
}}

只返回JSON，不要其他解释。"""

            response = common_ask_for_json(extract_prompt)
            if response:
                extracted = json.loads(response) if isinstance(response, str) else response
                return extracted.get('required_info', [])
        except Exception as e:
            print(f"⚠️ AI信息提取失败，使用简化方法: {e}")
        
        # 回退到简化的实现
        required_info = []
        keywords = ['需要进一步', '更多信息', '需要查看', '需要确认', '缺少信息', '验证', '分析']
        
        for keyword in keywords:
            if keyword in response_text:
                sentences = response_text.split('。')
                for sentence in sentences:
                    if keyword in sentence:
                        required_info.append(sentence.strip())
                        break
        
        return required_info

    def get_additional_context_with_rag(self, required_info: List[str], original_report: str = "") -> str:
        """使用RAG获取额外的上下文信息
        
        Args:
            required_info: 需要的信息列表
            original_report: 原始报告内容
            
        Returns:
            str: 增强的上下文信息
        """
        if not required_info:
            return "未找到需要进一步分析的信息"
        
        enhanced_context_parts = []
        
        for i, info in enumerate(required_info, 1):
            try:
                print(f"🔍 处理信息点 {i}: {info[:50]}...")
                
                # 为每个信息点让大模型选择RAG类型
                validation_question = f"需要验证或分析：{info}"
                rag_result = self.ask_llm_to_choose_rag_for_validation(original_report, validation_question, info)
                
                enhanced_context_parts.append(f"\n=== 信息点 {i} ===")
                enhanced_context_parts.append(f"需要分析: {info}")
                
                if rag_result.get('rag_chosen'):
                    enhanced_context_parts.append(f"使用RAG类型: {rag_result['rag_chosen']}")
                    enhanced_context_parts.append(f"验证重点: {rag_result.get('validation_focus', '常规验证')}")
                    
                    if rag_result.get('rag_results'):
                        enhanced_context_parts.append(f"找到 {len(rag_result['rag_results'])} 个相关结果:")
                        for j, result in enumerate(rag_result['rag_results'][:2], 1):  # 只显示前2个
                            if isinstance(result, dict):
                                func_name = result.get('name', result.get('function_name', 'Unknown'))
                                content_preview = result.get('content', '')[:100] if result.get('content') else ''
                                enhanced_context_parts.append(f"  {j}. {func_name}: {content_preview}...")
                    else:
                        enhanced_context_parts.append("  未找到直接相关的代码")
                else:
                    enhanced_context_parts.append("  RAG查询不可用，使用传统分析")
                    # 使用传统方法查找相关函数
                    traditional_context = self._get_traditional_context(info)
                    if traditional_context:
                        enhanced_context_parts.append(f"  传统分析结果: {traditional_context}")
                
            except Exception as e:
                print(f"❌ 处理信息点 {i} 失败: {e}")
                enhanced_context_parts.append(f"  处理失败: {str(e)}")
        
        return '\n'.join(enhanced_context_parts)

    def _get_traditional_context(self, info: str) -> str:
        """传统方法获取上下文（作为RAG的备选）"""
        context_parts = []
        info_lower = info.lower()
        
        # 在functions中查找相关信息
        for func in self.functions_to_check:
            func_content = func.get('content', '').lower()
            func_name = func.get('name', '')
            
            # 简单的关键词匹配
            if any(keyword in func_content for keyword in info_lower.split()):
                context_parts.append(f"相关函数: {func_name}")
                if len(context_parts) >= 3:  # 限制结果数量
                    break
        
        return '; '.join(context_parts) if context_parts else "未找到相关函数"

    def get_additional_internet_info(self, required_info: List[str]) -> str:
        """获取网络信息（简化实现）"""
        if required_info:
            return f"网络搜索结果：找到{len(required_info)}个相关信息点（简化实现）"
        return ""

    def get_additional_context(self, required_info: List[str]) -> str:
        """获取额外上下文（向后兼容方法）"""
        return self.get_additional_context_with_rag(required_info)

    def process_task_analysis(self, task:Project_Task,task_manager):
        """Agent化的三轮漏洞检测流程"""
        import json
        from datetime import datetime
        
        start_time = time.time()
        logs = []
        
        print(f"\n🚀 启动Agent化漏洞检测流程 - 任务: {task.name}")
        logs.append(f"开始时间: {datetime.utcnow().isoformat()}")
        
        # 获取规则和业务流代码
        vulnerability_result = task.result
        business_flow_code = task.business_flow_code or task.content
        
        logs.append(f"规则类型: {task.rule_key}")
        logs.append(f"代码长度: {len(business_flow_code)} 字符")
        
        # 执行三轮独立检测
        round_results = []
        
        for round_num in range(1, 4):  # 三轮检测
            print(f"\n--- 第 {round_num} 轮独立检测 ---")
            logs.append(f"开始第 {round_num} 轮检测")
            
            try:
                round_result = self._execute_single_detection_round(
                    vulnerability_result, business_flow_code, task, round_num, logs
                )
                round_results.append(round_result)
                logs.append(f"第 {round_num} 轮结果: {round_result}")
                
            except Exception as e:
                print(f"❌ 第 {round_num} 轮检测失败: {e}")
                logs.append(f"第 {round_num} 轮失败: {str(e)}")
                round_results.append("not_sure")
        
        # 汇总三轮结果
        final_short_result, final_detailed_result = self._aggregate_round_results(round_results, logs)
        
        # 计算处理时间
        end_time = time.time()
        process_time = round(end_time - start_time, 2)
        
        logs.append(f"最终简短结果: {final_short_result}")
        logs.append(f"处理耗时: {process_time}秒")
        logs.append(f"结束时间: {datetime.utcnow().isoformat()}")
        
        print(f"\n🎯 最终结果: {final_short_result}")
        print(f"⏱️ 总耗时: {process_time}秒")
        
        # 保存结果
        task.set_result(final_detailed_result)
        task.set_short_result(final_short_result)
        
        # 保存完整日志到scan_record
        scan_data = {
            'logs': logs,
            'round_results': round_results,
            'process_time': process_time,
            'timestamp': datetime.utcnow().isoformat(),
            'rounds_count': 3
        }
        task.scan_record = json.dumps(scan_data, ensure_ascii=False)
        
        # 更新数据库
        task_manager.save_task(task)
        
        return final_short_result

    def _build_confirmation_prompt(self, task, comprehensive_analysis: str, round_num: int, max_rounds: int) -> str:
        """构建确认提示（包含RAG增强信息）"""
        base_prompt = PromptAssembler.confirmation_analysis_prompt(
            task.content, comprehensive_analysis
        )
        
        # Add round-specific instructions
        round_instruction = f"""
这是第 {round_num}/{max_rounds} 轮确认分析。

上述分析中包含了基于RAG检索的增强上下文信息，请特别注意：
1. RAG检索到的相关函数和代码片段
2. 上游/下游函数调用关系信息
3. 相似功能或漏洞模式的代码

请基于这些增强信息进行更准确的漏洞确认。
"""
        
        return base_prompt + round_instruction
    
    def _perform_initial_analysis(self, code_to_be_tested: str, result: str, analysis_collection: List) -> Tuple:
        """Execute initial analysis"""
        print("\n=== First Round Analysis Start ===")
        print("📝 Analyzing potential vulnerabilities...")
        prompt = PromptAssembler.assemble_vul_check_prompt(code_to_be_tested, result)
        
        initial_response = common_ask_confirmation(prompt)
        if not initial_response or initial_response == "":
            print(f"❌ Error: Empty response received")
            return "not sure", "Empty response"
        
        print("\n📊 Initial Analysis Result Length:")
        print("-" * 80)
        print(len(initial_response))
        print("-" * 80)

        # Collect initial analysis results
        analysis_collection.extend([
            "=== Initial Analysis Results ===",
            initial_response
        ])

        # Process initial response
        initial_result_status = CheckUtils.process_round_response(initial_response)
        analysis_collection.extend([
            "=== Initial Analysis Status ===",
            initial_result_status
        ])

        # Extract required information
        required_info = self.context_data.get("extract_required_info")(initial_response)
        if required_info:
            analysis_collection.append("=== Information Requiring Further Analysis ===")
            analysis_collection.extend(required_info)

        if CheckUtils.should_skip_early(initial_result_status):
            print("\n🛑 Initial analysis shows clear 'no vulnerability' - stopping further analysis")
            return "no", "Analysis stopped after initial round due to clear 'no vulnerability' result"
        
        return None, None  # Continue with multi-round confirmation
    


    def _execute_single_detection_round(self, vulnerability_result, business_flow_code, task, round_num, logs):
        """执行单轮检测流程"""
        from openai_api.openai import (ask_agent_initial_analysis, ask_agent_json_extraction, 
                                       ask_agent_info_query, ask_agent_info_extraction,
                                       ask_agent_final_analysis, ask_agent_final_extraction)
        from prompt_factory.vul_check_prompt import VulCheckPrompt
        
        logs.append(f"第 {round_num} 轮: 开始初步确认")
        
        # 第一步：使用prompt factory生成完整的初步分析prompt
        initial_prompt = VulCheckPrompt.vul_check_prompt_agent_initial_complete(
            vulnerability_result, business_flow_code
        )

        try:
            # 使用专门的初始分析模型获取自然语言响应
            natural_response = ask_agent_initial_analysis(initial_prompt)
            if not natural_response:
                logs.append(f"第 {round_num} 轮: 初始分析模型无响应")
                return "not_sure"
            
            logs.append(f"第 {round_num} 轮: 初始分析自然语言响应长度={len(natural_response)}")
            
            # 使用prompt factory生成JSON提取prompt
            json_extraction_prompt = VulCheckPrompt.vul_check_prompt_agent_json_extraction(
                natural_response
            )

            initial_response = ask_agent_json_extraction(json_extraction_prompt)
            if not initial_response:
                logs.append(f"第 {round_num} 轮: JSON提取失败")
                return "not_sure"
            
            initial_result = json.loads(initial_response) if isinstance(initial_response, str) else initial_response
            assessment = initial_result.get('initial_assessment', 'not_sure')
            additional_info = initial_result.get('additional_info_needed', '')
            
            logs.append(f"第 {round_num} 轮: 初步评估={assessment}")
            logs.append(f"第 {round_num} 轮: 自然语言分析={natural_response[:200]}...")
            
            print(f"  📊 初步评估: {assessment}")
            
            # 如果是明确的yes或no，直接返回
            if assessment in ['yes', 'no']:
                logs.append(f"第 {round_num} 轮: 明确结果，直接返回")
                return assessment
            
            # 如果需要更多信息，直接获取所有类型的信息
            if assessment == 'need_more_info' and additional_info:
                print(f"  🔍 需要更多信息: {additional_info}")
                logs.append(f"第 {round_num} 轮: 需要更多信息: {additional_info}")
                
                try:
                    # 直接获取所有类型的RAG信息
                    print(f"  🔍 同时获取所有类型的RAG信息...")
                    all_additional_info = self._get_all_additional_info(
                        additional_info, task, logs, round_num
                    )
                    
                    # 格式化为字符串
                    additional_context = self._format_all_additional_info(all_additional_info)
                    
                    logs.append(f"第 {round_num} 轮: 获取所有RAG信息完成")
                    print(f"  ✅ 获取信息完成: Functions={len(all_additional_info['function_info'])}, Upstream/Downstream={len(all_additional_info['upstream_downstream_info'])}, Chunks={len(all_additional_info['chunk_info'])}")
                    # Files={len(all_additional_info['file_info'])}, - 已注释
                        
                    # 使用prompt factory生成最终分析prompt
                    final_analysis_prompt = VulCheckPrompt.vul_check_prompt_agent_final_analysis(
                        vulnerability_result, business_flow_code, assessment, additional_info, additional_context
                    )
                    
                    # 使用专门的最终分析模型进行最终分析
                    final_natural_response = ask_agent_final_analysis(final_analysis_prompt)
                    if final_natural_response:
                        # 使用prompt factory生成最终结果提取prompt
                        final_extraction_prompt = VulCheckPrompt.vul_check_prompt_agent_final_extraction(
                            final_natural_response
                        )

                        final_response = ask_agent_final_extraction(final_extraction_prompt)
                        if final_response:
                            final_result = json.loads(final_response) if isinstance(final_response, str) else final_response
                            final_assessment = final_result.get('final_result', 'not_sure')
                            
                            logs.append(f"第 {round_num} 轮: 最终结果={final_assessment}")
                            logs.append(f"第 {round_num} 轮: 最终分析={final_natural_response[:200]}...")
                            
                            print(f"  🎯 最终判断: {final_assessment}")
                            return final_assessment
                        
                except Exception as e:
                    logs.append(f"第 {round_num} 轮: 信息获取阶段失败: {str(e)}")
                    print(f"  ❌ 信息获取失败: {e}")
            
            # 如果以上都失败，返回初步评估结果
            return assessment if assessment in ['yes', 'no'] else 'not_sure'
            
        except Exception as e:
            logs.append(f"第 {round_num} 轮: 检测失败: {str(e)}")
            print(f"  ❌ 检测失败: {e}")
            return "not_sure"

    def _get_additional_info_by_type(self, info_type, specific_query, task, logs, round_num):
        """根据信息类型获取额外信息"""
        try:
            if info_type == 'function':
                # 使用RAG搜索函数信息
                if self.rag_processor:
                    # 先尝试按名称搜索
                    name_results = self.rag_processor.search_functions_by_name(specific_query, 3)
                    # 再尝试按内容搜索
                    content_results = self.rag_processor.search_functions_by_content(specific_query, 3)
                    
                    context_parts = []
                    if name_results:
                        context_parts.append("=== 按名称搜索的函数 ===")
                        for result in name_results[:2]:
                            func_name = result.get('name', 'Unknown')
                            func_content = result.get('content', '')[:200]
                            context_parts.append(f"函数: {func_name}\n代码: {func_content}...\n")
                    
                    if content_results:
                        context_parts.append("=== 按内容搜索的相似函数 ===")
                        for result in content_results[:2]:
                            func_name = result.get('name', 'Unknown')
                            func_content = result.get('content', '')[:200]
                            context_parts.append(f"函数: {func_name}\n代码: {func_content}...\n")
                    
                    logs.append(f"第 {round_num} 轮: 函数搜索找到 {len(name_results)} + {len(content_results)} 个结果")
                    return '\n'.join(context_parts) if context_parts else "未找到相关函数"
                else:
                    logs.append(f"第 {round_num} 轮: RAG不可用，使用传统函数搜索")
                    return self._get_traditional_context(specific_query)
            
            elif info_type == 'file':
                # 文件信息 - 从任务中获取文件相关信息
                file_info = []
                if hasattr(task, 'absolute_file_path') and task.absolute_file_path:
                    file_info.append(f"文件路径: {task.absolute_file_path}")
                if hasattr(task, 'contract_code') and task.contract_code:
                    file_info.append(f"合约代码: {task.contract_code[:300]}...")
                
                logs.append(f"第 {round_num} 轮: 获取文件信息，{len(file_info)} 项")
                return '\n'.join(file_info) if file_info else "未找到文件信息"
            
            elif info_type == 'upstream_downstream':
                # 上下游信息 - 使用get_call_tree_with_depth_limit获取实际代码内容
                upstream_downstream = []
                max_depth = 3  # 设置深度限制
                
                # 获取project_audit实例
                project_audit = getattr(self, 'project_audit', None) or self.context_data.get('project_audit')
                if project_audit and hasattr(project_audit, 'call_tree_builder'):
                    builder = project_audit.call_tree_builder
                    if hasattr(builder, 'get_call_tree_with_depth_limit'):
                        try:
                            # 获取upstream代码内容（使用深度限制）
                            limited_upstream = builder.get_call_tree_with_depth_limit(
                                self.call_trees, task.name, 'upstream', max_depth
                            )
                            if limited_upstream and limited_upstream.get('tree'):
                                upstream_content = self._extract_function_content_from_tree(limited_upstream['tree'])
                                if upstream_content:
                                    upstream_downstream.append(f"=== 上游函数代码 (深度{max_depth}) ===")
                                    upstream_downstream.append(upstream_content[:1000] + "..." if len(upstream_content) > 1000 else upstream_content)
                                    logs.append(f"第 {round_num} 轮: 获取upstream代码内容，{len(upstream_content)} 字符")
                            
                            # 获取downstream代码内容（使用深度限制）
                            limited_downstream = builder.get_call_tree_with_depth_limit(
                                self.call_trees, task.name, 'downstream', max_depth
                            )
                            if limited_downstream and limited_downstream.get('tree'):
                                downstream_content = self._extract_function_content_from_tree(limited_downstream['tree'])
                                if downstream_content:
                                    upstream_downstream.append(f"=== 下游函数代码 (深度{max_depth}) ===")
                                    upstream_downstream.append(downstream_content[:1000] + "..." if len(downstream_content) > 1000 else downstream_content)
                                    logs.append(f"第 {round_num} 轮: 获取downstream代码内容，{len(downstream_content)} 字符")
                            
                            # 添加统计信息
                            upstream_count = limited_upstream.get('total_count', 0) if limited_upstream else 0
                            downstream_count = limited_downstream.get('total_count', 0) if limited_downstream else 0
                            upstream_downstream.append(f"调用关系统计: 上游{upstream_count}个, 下游{downstream_count}个")
                            
                        except Exception as e:
                            logs.append(f"第 {round_num} 轮: 使用get_call_tree_with_depth_limit获取失败: {str(e)}")
                            # 备选方案：仅获取函数名
                            if self.call_trees:
                                for call_tree in self.call_trees:
                                    if call_tree.get('function_name') == task.name:
                                        upstream_info = call_tree.get('upstream', {})
                                        downstream_info = call_tree.get('downstream', {})
                                        if upstream_info:
                                            upstream_functions = list(upstream_info.keys())[:3]
                                            upstream_downstream.append(f"上游函数: {', '.join(upstream_functions)}")
                                        if downstream_info:
                                            downstream_functions = list(downstream_info.keys())[:3]
                                            upstream_downstream.append(f"下游函数: {', '.join(downstream_functions)}")
                                        break
                else:
                    logs.append(f"第 {round_num} 轮: call_tree_builder不可用，使用备选方案")
                    # 备选方案：直接从call_trees获取函数名
                    if self.call_trees:
                        for call_tree in self.call_trees:
                            if call_tree.get('function_name') == task.name:
                                upstream_info = call_tree.get('upstream', {})
                                downstream_info = call_tree.get('downstream', {})
                                if upstream_info:
                                    upstream_functions = list(upstream_info.keys())[:3]
                                    upstream_downstream.append(f"上游函数: {', '.join(upstream_functions)}")
                                if downstream_info:
                                    downstream_functions = list(downstream_info.keys())[:3]
                                    upstream_downstream.append(f"下游函数: {', '.join(downstream_functions)}")
                                upstream_count = call_tree.get('upstream_count', 0)
                                downstream_count = call_tree.get('downstream_count', 0)
                                upstream_downstream.append(f"调用关系统计: 上游{upstream_count}个, 下游{downstream_count}个")
                                break
                
                logs.append(f"第 {round_num} 轮: 获取上下游信息，{len(upstream_downstream)} 项")
                return '\n'.join(upstream_downstream) if upstream_downstream else "未找到调用关系信息"
            
            else:
                logs.append(f"第 {round_num} 轮: 未知信息类型: {info_type}")
                return f"未知信息类型: {info_type}"
                
        except Exception as e:
            logs.append(f"第 {round_num} 轮: 获取 {info_type} 信息失败: {str(e)}")
            return f"获取 {info_type} 信息失败: {str(e)}"
    
    def _get_all_additional_info(self, specific_query, task, logs, round_num):
        """同时获取所有类型的RAG信息"""
        all_info = {
            'function_info': [],
            'file_info': [],
            'upstream_downstream_info': [],
            'chunk_info': []
        }
        
        try:
            # 1. Function RAG搜索 (topk=5) - 包括三种搜索类型
            if self.rag_processor:
                # 按名称搜索
                name_results = self.rag_processor.search_functions_by_name(specific_query, 2)
                # 按内容搜索
                content_results = self.rag_processor.search_functions_by_content(specific_query, 2)
                # 按自然语言描述搜索
                natural_results = self.rag_processor.search_functions_by_natural_language(specific_query, 2)
                
                # 合并和去重，取前5个
                function_results = self._merge_and_deduplicate_functions(
                    name_results, content_results, natural_results, 5
                )
                
                for result in function_results:
                    func_name = result.get('name', 'Unknown')
                    func_content = result.get('content', '')[:300]  # 限制长度
                    all_info['function_info'].append({
                        'name': func_name,
                        'content': func_content,
                        'type': 'function'
                    })
                
                logs.append(f"第 {round_num} 轮: Function搜索找到 {len(function_results)} 个结果")
            
            # 2. File RAG搜索 (topk=2) - 已注释
            # if self.rag_processor:
            #     file_results = self.rag_processor.search_files_by_content(specific_query, 2)
            #     
            #     for result in file_results:
            #         file_path = result.get('file_path', 'Unknown')
            #         file_content = result.get('content', '')[:300]
            #         all_info['file_info'].append({
            #             'path': file_path,
            #             'content': file_content,
            #             'type': 'file'
            #         })
            #     
            #     logs.append(f"第 {round_num} 轮: File搜索找到 {len(file_results)} 个结果")
            
            # 3. Upstream/Downstream搜索 (level=3/4)
            upstream_downstream_results = self._get_upstream_downstream_with_levels(task, 3, 4, logs, round_num)
            all_info['upstream_downstream_info'] = upstream_downstream_results
            
            # 4. Chunk RAG搜索 (topk=3)
            if self.rag_processor:
                chunk_results = self.rag_processor.search_chunks_by_content(specific_query, 3)
                
                for result in chunk_results:
                    chunk_text = result.get('chunk_text', '')[:300]
                    original_file = result.get('original_file', 'Unknown')
                    all_info['chunk_info'].append({
                        'text': chunk_text,
                        'file': original_file,
                        'type': 'chunk'
                    })
                
                logs.append(f"第 {round_num} 轮: Chunk搜索找到 {len(chunk_results)} 个结果")
            
            # 5. 去重逻辑：从upstream/downstream中去除与function相同的
            all_info = self._remove_function_duplicates_from_upstream_downstream(all_info)
            
            return all_info
            
        except Exception as e:
            logs.append(f"第 {round_num} 轮: 获取所有额外信息失败: {str(e)}")
            return all_info
    
    def _merge_and_deduplicate_functions(self, name_results, content_results, natural_results, max_count):
        """合并和去重函数搜索结果（三种类型）"""
        seen_names = set()
        merged_results = []
        
        # 先加入按名称搜索的结果
        for result in name_results:
            func_name = result.get('name', '')
            if func_name and func_name not in seen_names:
                seen_names.add(func_name)
                merged_results.append(result)
                if len(merged_results) >= max_count:
                    break
        
        # 再加入按内容搜索的结果（去重）
        for result in content_results:
            func_name = result.get('name', '')
            if func_name and func_name not in seen_names:
                seen_names.add(func_name)
                merged_results.append(result)
                if len(merged_results) >= max_count:
                    break
        
        # 最后加入按自然语言搜索的结果（去重）
        for result in natural_results:
            func_name = result.get('name', '')
            if func_name and func_name not in seen_names:
                seen_names.add(func_name)
                merged_results.append(result)
                if len(merged_results) >= max_count:
                    break
        
        return merged_results[:max_count]
    
    def _get_upstream_downstream_with_levels(self, task, upstream_level, downstream_level, logs, round_num):
        """获取上下游信息（复用planning中的实现）"""
        upstream_downstream = []
        
        # 获取project_audit实例
        project_audit = getattr(self, 'project_audit', None) or self.context_data.get('project_audit')
        if not project_audit:
            return upstream_downstream
        
        try:
            # 复用planning中的方法获取downstream内容
            from planning.planning_processor import PlanningProcessor
            planning_processor = PlanningProcessor(None, project_audit)  # task_manager可以传None
            
            # 获取downstream内容（使用planning中的方法）
            downstream_content = planning_processor.get_downstream_content_with_call_tree(
                task.name, downstream_level
            )
            if downstream_content:
                upstream_downstream.append({
                    'content': downstream_content[:800],
                    'type': 'downstream',
                    'level': downstream_level,
                    'count': downstream_content.count('\n\n') + 1  # 简单估算函数数量
                })
                logs.append(f"第 {round_num} 轮: 获取downstream代码内容，深度{downstream_level}，{len(downstream_content)} 字符")
            
            # 获取upstream内容（复用planning的逻辑，但修改为upstream）
            upstream_content = self._get_upstream_content_with_call_tree(
                task.name, upstream_level, planning_processor
            )
            if upstream_content:
                upstream_downstream.append({
                    'content': upstream_content[:800],
                    'type': 'upstream',
                    'level': upstream_level,
                    'count': upstream_content.count('\n\n') + 1  # 简单估算函数数量
                })
                logs.append(f"第 {round_num} 轮: 获取upstream代码内容，深度{upstream_level}，{len(upstream_content)} 字符")
            
        except Exception as e:
            logs.append(f"第 {round_num} 轮: 复用planning方法获取上下游内容失败: {str(e)}")
        
        return upstream_downstream
    
    def _get_upstream_content_with_call_tree(self, func_name: str, max_depth: int, planning_processor) -> str:
        """获取upstream内容（参考planning中的downstream实现）"""
        contents = []
        
        # 查找对应的call tree
        if hasattr(planning_processor.project_audit, 'call_trees') and planning_processor.project_audit.call_trees:
            try:
                from tree_sitter_parsing.advanced_call_tree_builder import AdvancedCallTreeBuilder
                builder = AdvancedCallTreeBuilder()
                upstream_tree = builder.get_call_tree_with_depth_limit(
                    planning_processor.project_audit.call_trees, func_name, 'upstream', max_depth
                )
                
                if upstream_tree and upstream_tree.get('tree'):
                    contents = planning_processor._extract_contents_from_tree(upstream_tree['tree'])
            except Exception as e:
                print(f"    ⚠️ 使用高级call tree获取upstream失败: {e}")
                # 这里可以加入后备方案，但planning中没有upstream的fallback
        
        return '\n\n'.join(contents)
    
    def _remove_function_duplicates_from_upstream_downstream(self, all_info):
        """从upstream/downstream中去除与function相同的结果"""
        # 获取所有function名称
        function_names = set()
        for func_info in all_info['function_info']:
            function_names.add(func_info.get('name', ''))
        
        # 从upstream/downstream内容中移除包含相同functions的部分
        # 这里简化处理，主要是避免内容重复
        # 实际上，upstream/downstream和function的内容是不同的角度，可以保留
        
        return all_info
    
    def _format_all_additional_info(self, all_info):
        """格式化所有额外信息为字符串"""
        context_parts = []
        
        # Function信息
        if all_info['function_info']:
            context_parts.append("=== 相关函数 (Top 5) ===")
            for i, func in enumerate(all_info['function_info'], 1):
                context_parts.append(f"{i}. 函数: {func.get('name', 'Unknown')}")
                context_parts.append(f"   代码: {func.get('content', '')[:200]}...\n")
        
        # File信息 - 已注释
        # if all_info['file_info']:
        #     context_parts.append("=== 相关文件 (Top 2) ===")
        #     for i, file in enumerate(all_info['file_info'], 1):
        #         context_parts.append(f"{i}. 文件: {file.get('path', 'Unknown')}")
        #         context_parts.append(f"   内容: {file.get('content', '')[:200]}...\n")
        
        # Upstream/Downstream信息
        if all_info['upstream_downstream_info']:
            context_parts.append("=== 上下游关系信息 ===")
            for info in all_info['upstream_downstream_info']:
                level = info.get('level', 0)
                info_type = info.get('type', 'unknown')
                count = info.get('count', 0)
                context_parts.append(f"{info_type.title()}函数 (深度{level}, 共{count}个):")
                context_parts.append(f"{info.get('content', '')[:400]}...\n")
        
        # Chunk信息
        if all_info['chunk_info']:
            context_parts.append("=== 相关文档块 (Top 3) ===")
            for i, chunk in enumerate(all_info['chunk_info'], 1):
                context_parts.append(f"{i}. 文件: {chunk.get('file', 'Unknown')}")
                context_parts.append(f"   内容: {chunk.get('text', '')[:200]}...\n")
        
        return '\n'.join(context_parts) if context_parts else "未找到相关信息"

    def _aggregate_round_results(self, round_results, logs):
        """汇总三轮结果，生成最终判断"""
        logs.append("开始汇总三轮结果")
        
        # 统计各种结果
        yes_count = sum(1 for result in round_results if result == 'yes')
        no_count = sum(1 for result in round_results if result == 'no')
        not_sure_count = sum(1 for result in round_results if result == 'not_sure')
        
        logs.append(f"结果统计: yes={yes_count}, no={no_count}, not_sure={not_sure_count}")
        
        # 决策逻辑
        if yes_count >= 2:  # 至少2轮说yes
            final_short_result = "yes"
            decision_reason = f"3轮检测中{yes_count}轮确认存在漏洞"
        elif no_count >= 2:  # 至少2轮说no
            final_short_result = "no"
            decision_reason = f"3轮检测中{no_count}轮确认不存在漏洞"
        else:  # 结果不一致或都是not_sure
            if yes_count > no_count:
                final_short_result = "yes"
                decision_reason = f"3轮检测结果不一致，但{yes_count}轮倾向于存在漏洞"
            elif no_count > yes_count:
                final_short_result = "no"
                decision_reason = f"3轮检测结果不一致，但{no_count}轮倾向于不存在漏洞"
            else:
                final_short_result = "not_sure"
                decision_reason = f"3轮检测结果无法确定，需人工复核"
        
        # 生成详细结果
        detailed_result = f"""Agent化三轮检测结果:
轮次结果: {round_results}
统计: yes={yes_count}, no={no_count}, not_sure={not_sure_count}
最终判断: {final_short_result}
决策依据: {decision_reason}
"""
        
        logs.append(f"最终汇总: {final_short_result} - {decision_reason}")
        
        return final_short_result, detailed_result

    def _extract_function_names_from_tree(self, tree_data):
        """从调用树数据中提取函数名列表"""
        function_names = []
        
        try:
            if isinstance(tree_data, dict):
                for key, value in tree_data.items():
                    if isinstance(key, str) and '.' in key:  # 假设函数名格式为 ContractName.functionName
                        function_names.append(key)
                    elif isinstance(value, dict):
                        # 递归处理嵌套结构
                        nested_names = self._extract_function_names_from_tree(value)
                        function_names.extend(nested_names)
            elif isinstance(tree_data, list):
                for item in tree_data:
                    if isinstance(item, str) and '.' in item:
                        function_names.append(item)
                    elif isinstance(item, dict):
                        nested_names = self._extract_function_names_from_tree(item)
                        function_names.extend(nested_names)
        except Exception as e:
            print(f"⚠️ 提取函数名失败: {e}")
        
        return list(set(function_names))  # 去重

    def _extract_function_content_from_tree(self, tree_data):
        """从调用树数据中提取函数的实际代码内容"""
        function_contents = []
        
        try:
            if isinstance(tree_data, dict):
                for key, value in tree_data.items():
                    if isinstance(key, str) and '.' in key:  # 函数名格式为 ContractName.functionName
                        # 从self.functions中查找对应的函数内容
                        function_content = self._get_function_content_by_name(key)
                        if function_content:
                            function_contents.append(f"// {key}\n{function_content}")
                    
                    # 递归处理嵌套结构
                    if isinstance(value, dict):
                        nested_content = self._extract_function_content_from_tree(value)
                        if nested_content:
                            function_contents.append(nested_content)
            elif isinstance(tree_data, list):
                for item in tree_data:
                    if isinstance(item, str) and '.' in item:
                        function_content = self._get_function_content_by_name(item)
                        if function_content:
                            function_contents.append(f"// {item}\n{function_content}")
                    elif isinstance(item, dict):
                        nested_content = self._extract_function_content_from_tree(item)
                        if nested_content:
                            function_contents.append(nested_content)
        except Exception as e:
            print(f"⚠️ 提取函数内容失败: {e}")
        
        return '\n\n'.join(function_contents) if function_contents else ""

    def _get_function_content_by_name(self, function_name):
        """根据函数名从self.functions中获取函数内容"""
        try:
            for func in self.functions:
                if isinstance(func, dict) and func.get('name') == function_name:
                    return func.get('content', '')
            return ""
        except Exception as e:
            print(f"⚠️ 根据函数名获取内容失败: {e}")
            return "" 