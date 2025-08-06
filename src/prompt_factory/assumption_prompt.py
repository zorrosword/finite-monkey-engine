"""
假设分析相关的提示词工厂
"""

class AssumptionPrompt:
    """假设分析提示词类"""
    
    @staticmethod
    def get_assumption_analysis_prompt(downstream_content: str) -> str:
        """获取假设分析的提示词
        
        Args:
            downstream_content: 下游代码内容
            
        Returns:
            str: 完整的假设分析提示词
        """
        return f"""
Analyze in depth all business logic-related assumptions made by the developer in this code.

For each assumption you identify, provide a comprehensive analysis that integrates ALL the following information into ONE complete assumption statement:

- Detailed description of the specific business scenario assumed
- Description of the business object targeted by the assumption  
- Content of the assumption and expectation made by the developer
- Dependency conditions that must be met for this assumption to hold true
- Corresponding code snippet that reflects this assumption

Please ensure your analysis covers all implicit assumptions in the following dimensions:
- Business logic assumptions: Assumptions about business processes, rules, and constraints
- Data structure assumptions: Assumptions about data storage, indexing, and relationships  
- Security assumptions: Assumptions about permission controls, attack prevention, and asset security
- User behavior assumptions: Assumptions about user operation patterns and interaction methods
- System architecture assumptions: Assumptions about technical implementation, scalability, and compatibility
- Economic model assumptions: Assumptions about tokenomics, incentive mechanisms, and value flow
- Integration assumptions: Assumptions about external systems, third-party services, and cross-chain interactions

IMPORTANT OUTPUT FORMAT:
- Write each complete assumption as a single comprehensive paragraph in natural language
- Separate each assumption using exactly "<|ASSUMPTION_SPLIT|>"  
- Do NOT use any JSON format, bullet points, or numbered lists
- Each assumption should be self-contained and include all relevant dimensions
- Start directly with the first assumption, no introductory text

Example format:
This code assumes that users will always have sufficient balance before attempting a transfer, which involves the business scenario of token transfers between accounts where the balance tracking system accurately reflects user holdings, and the security assumption that msg.sender authentication prevents unauthorized access, with the dependency that the ERC20 standard's balance mapping is consistently maintained across all operations as shown in the require(balanceOf[msg.sender] >= amount) check.
<|ASSUMPTION_SPLIT|>
This code assumes that external contract calls will not re-enter the current function maliciously, involving the business scenario of inter-contract interactions where the system architecture relies on external contracts behaving predictably, with security assumptions about call stack isolation and the economic model assumption that gas costs will prevent excessive recursive calls, as evidenced by the lack of reentrancy guards around external calls.

Code to analyze:
{downstream_content}
"""

