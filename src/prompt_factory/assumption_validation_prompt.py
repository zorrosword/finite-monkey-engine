"""
假设验证相关的提示词工厂
用于在reasoning阶段验证代码假设是否成立
"""

class AssumptionValidationPrompt:
    """假设验证提示词类"""
    
    @staticmethod
    def get_assumption_validation_prompt(code: str, assumption_statement: str) -> str:
        """获取假设验证的提示词
        
        Args:
            code: 要分析的代码
            assumption_statement: 需要验证的假设陈述
            
        Returns:
            str: 完整的假设验证提示词
        """
        return f"""
You are an expert smart contract security auditor. Analyze the following code to validate whether the stated assumption is correct or represents a security vulnerability.

ASSUMPTION TO VALIDATE:
{assumption_statement}

CODE TO ANALYZE:
{code}

Determine if this assumption is CORRECT, INCORRECT, or PARTIALLY CORRECT based on the code analysis. Focus on potential security risks, missing safeguards, and attack vectors. Provide specific evidence from the code and actionable recommendations.

Begin your analysis now.
"""