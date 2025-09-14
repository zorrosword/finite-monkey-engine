#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Group Result Summarizer
用于总结同组任务的已有结果，避免重复检测相同漏洞
"""

from typing import List, Optional
from dao.entity import Project_Task


class GroupResultSummarizer:
    """同组结果总结器"""
    
    @staticmethod
    def summarize_group_results(tasks_with_results: List[Project_Task]) -> Optional[str]:
        """使用LLM总结同组任务的已有结果
        
        Args:
            tasks_with_results: 同组中已有结果的任务列表
            
        Returns:
            str: LLM生成的总结文本，如果没有有效结果则返回None
        """
        if not tasks_with_results:
            return None
        
        # 过滤出有非空结果的任务
        valid_tasks = []
        for task in tasks_with_results:
            result = task.result
            if result and result.strip():
                valid_tasks.append({
                    'task_name': task.name,
                    'rule_key': task.rule_key,
                    'result': result
                })
        
        if not valid_tasks:
            return None
        
        # 使用LLM进行总结
        try:
            from prompt_factory.group_summary_prompt import GroupSummaryPrompt
            from openai_api.openai import summarize_group_vulnerability_results
            
            # 构建总结提示词
            summary_prompt = GroupSummaryPrompt.get_group_results_summary_prompt(valid_tasks)
            
            # 调用LLM进行总结
            llm_summary = summarize_group_vulnerability_results(summary_prompt)
            
            return llm_summary if llm_summary.strip() else None
            
        except Exception as e:
            print(f"⚠️ LLM总结失败，使用备用方法: {e}")
            # 备用方法：简单文本拼接
            return GroupResultSummarizer._create_fallback_summary(valid_tasks)
    
    @staticmethod
    def _create_fallback_summary(valid_tasks: List[dict]) -> str:
        """创建备用总结（当LLM调用失败时使用）
        
        Args:
            valid_tasks: 有效任务列表
            
        Returns:
            str: 简单的文本总结
        """
        if not valid_tasks:
            return ""
        
        summary_parts = []
        summary_parts.append("**Found Vulnerabilities:**")
        
        for task in valid_tasks:
            task_name = task['task_name']
            rule_key = task['rule_key']
            result = task['result']
            
            # 简单截取结果的前100个字符作为摘要
            result_summary = result[:100] + "..." if len(result) > 100 else result
            result_summary = result_summary.replace('\n', ' ').strip()
            
            # 尝试从任务名称中提取函数名
            function_name = task_name.split('.')[-1] if '.' in task_name else task_name
            
            summary_parts.append(f"- {rule_key.replace('_', ' ').title()} in {function_name}: {result_summary}")
        
        return "\n".join(summary_parts)
    
