#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Group Summary Prompt
用于总结同组任务已发现漏洞结果的提示词工厂
"""


class GroupSummaryPrompt:
    """同组结果总结提示词类"""
    
    @staticmethod
    def get_group_results_summary_prompt(group_results: list) -> str:
        """获取用于总结同组结果的提示词
        
        Args:
            group_results: 同组任务的结果列表，格式为 [{'task_name': str, 'rule_key': str, 'result': str}, ...]
            
        Returns:
            str: 完整的总结提示词
        """
        if not group_results:
            return ""
        
        # 构建结果列表文本
        results_text = ""
        for i, item in enumerate(group_results, 1):
            task_name = item.get('task_name', 'Unknown')
            rule_key = item.get('rule_key', 'Unknown')
            result = item.get('result', '')
            
            results_text += f"""
## 任务 {i}: {task_name}
**检测规则:** {rule_key}
**检测结果:**
{result}

{'=' * 60}
"""
        
        prompt = f"""Please summarize the vulnerabilities found in the following security analysis results:

{results_text}

Simply list what vulnerabilities were found. Format your response as:

**Found Vulnerabilities:**
- [Vulnerability 1]: [Brief description]
- [Vulnerability 2]: [Brief description]
- [Additional vulnerabilities if any]

Keep it concise and focus only on the actual security issues found."""
        
        return prompt
    
    @staticmethod
    def get_enhanced_reasoning_prompt_prefix() -> str:
        """获取增强推理prompt的前缀说明"""
        return """## 🔍 Previous Vulnerability Analysis Results ##

The following vulnerabilities have already been identified by other analysis tasks in the same task group. These tasks analyzed the same or closely related code components using different security rules and detection methods.

**IMPORTANT INSTRUCTIONS:**
1. **DO NOT re-detect or re-report** any of the vulnerabilities listed below
2. **Focus on discovering NEW and DIFFERENT** security issues not covered in the previous findings
3. **If you find variations or extensions** of the known vulnerabilities, clearly explain how your finding differs from the existing ones
4. **Prioritize unexplored attack vectors** and security aspects not mentioned in the previous analysis

**Previously Identified Vulnerabilities:**
"""
