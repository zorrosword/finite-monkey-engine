class VulCheckPrompt:
    def vul_check_prompt():
        return """
        Please re-analyze the original code step by step without drawing conclusions initially. Based on the analysis results, provide a conclusion at the end: determine whether this vulnerability truly exists or likely exists
        """
    def vul_check_prompt_old():
        return """
        Please re-analyze the original code step by step without drawing conclusions initially. Based on the analysis results, provide a conclusion at the end: determine whether this vulnerability truly exists or not extist or not sure.
        return result in json as {"analysis":"xxxxxx(detailed analyasis of the code)","result":"yes"} or {"analysis":"xxxxxx(detailed analyasis of the code)","result":"no"} or {"analysis":"xxxxxx(detailed analyasis of the code)","result":"not sure"}
        you must output the analysis first, and then provide a conclusion based on the analysis at the end.
        """
    def vul_check_prompt_claude():
        return """
        First analyze this vulnerability, and then determine if it really exists based on the analysis result, beaware, the contract version is larger then 0.8.0, so overflow is not possible.
        """
    def vul_check_prompt_claude_no_overflow():
        return """
        # Guidelines #
        First analyze this vulnerability step by step, and then determine if it really exists based on the analysis result or need deeper function code.
        Please note the following points:
        0.If the vulnerability description indicates that no vulnerability is found, directly conclude that it [[does not exist]]
        1. If the vulnerability is an integer overflow vulnerability, directly conclude that the vulnerability [does not exist]
        2. If the vulnerability is a reentrancy vulnerability, directly conclude that the vulnerability [does not exist]
        3. If the vulnerability requires inserting new address transaction operations from external sources during function execution, directly determine it [does not exist], because transactions are atomic
        4. When assessing vulnerabilities in functions with permission controls, if the permission roles can be obtained, you still need to consider the vulnerability
        5. If more information is needed to confirm the vulnerability, please clearly state what content needs to be understood (e.g., specific function implementations, variable usage patterns, permission check logic, etc.)
        6. If the vulnerable function has an Only Owner/Only Admin/Only Governance modifier, directly conclude that the vulnerability [does not exist]
        7. Any vulnerability or risk that could cause potential losses is valid(even small losses), it doesn't necessarily need to cause major security issues
        
        # Response #
        1. Detailed analysis process
        2. Whether more information is needed (if yes, please specify what content needs to be understood and why)
        3. Preliminary conclusion based on current information
        """
    def vul_check_prompt_claude_no_overflow_final():
        return """
        # Guidelines #
        First analyze this vulnerability step by step, code by code, then determine if it really exists based on the analysis results.
        Please note the following points:
        0. If the vulnerability description indicates that no vulnerability is found, directly conclude that it [[does not exist]]
        1. If the vulnerability is an integer overflow vulnerability, directly conclude that the vulnerability [does not exist]
        2. If the vulnerability is a reentrancy vulnerability, directly conclude that the vulnerability [does not exist]
        3. If the vulnerability is a transaction atomicity vulnerability, directly conclude that the vulnerability [does not exist]
        4. When assessing vulnerabilities in functions with permission controls, if the permission roles can be obtained, you still need to consider the vulnerability
        5. Any vulnerability or risk that could cause potential losses is valid (even small losses), it doesn't necessarily need to cause major security issues
        6. If the vulnerable function has an onlyowner modifier, directly conclude that the vulnerability [does not exist]

        # Response #
        Please structure your response as follows:
        1. Detailed analysis process - Examine the code step by step
        2. Information assessment - State whether more information is needed (if yes, specify what content needs to be understood and why)
        3. Conclusion - Provide a final determination based on current information
        """

    def vul_check_prompt_agent_initial():
        return """
        # Smart Contract Vulnerability Analysis #
        
        You are a smart contract vulnerability detection expert. Please analyze the provided code against the specified vulnerability rules for an initial assessment.
        
        ## Analysis Guidelines ##
        1. **Overflow/Underflow**: Contract version is 0.8.0+, so integer overflow vulnerabilities do not exist
        2. **Reentrancy**: Direct reentrancy vulnerabilities do not exist due to transaction atomicity  
        3. **Transaction Atomicity**: Vulnerabilities requiring external address insertion during execution do not exist
        4. **Permission Controls**: Functions with onlyOwner/onlyAdmin/onlyGovernance modifiers typically do not have vulnerabilities
        5. **Valid Vulnerabilities**: Any vulnerability causing potential losses (even small) is considered valid
        6. **Need More Info**: If insufficient information exists to make a determination, clearly state what additional information is needed
        
        ## Your Task ##
        Analyze the provided code step-by-step against the vulnerability rules and provide:
        1. **Detailed Analysis**: Step-by-step examination of the code logic
        2. **Information Assessment**: Whether you have sufficient information to make a determination
        3. **Initial Conclusion**: Based on available information, does the vulnerability exist, not exist, or do you need more information?
        
        ## Response Format ##
        Provide a natural language response with:
        - Clear step-by-step analysis
        - Assessment of information completeness  
        - Initial conclusion (yes/no/need more information)
        - If more information is needed, specify exactly what information would help
        """

    def vul_check_prompt_agent_info_query():
        return """
        # Information Request Analysis #
        
        Based on your previous vulnerability analysis, you mentioned needing more information. I can provide the following types of information to help complete your analysis:
        
        ## Available Information Types ##
        1. **Function Information** - Search for related functions by name or content similarity
        2. **File Information** - Get information about related files or contracts  
        3. **Call Relationship Information** - Get upstream (callers) and downstream (called functions) information
        
        ## Your Task ##
        Select the most appropriate information type that would help you complete the vulnerability assessment.
        
        ## Response Format ##
        Respond with a natural language explanation of:
        - Which type of information would be most helpful
        - Specific query content (function names, contract names, call relationships, etc.)  
        - Why this information is needed to complete the vulnerability assessment
        """

    @staticmethod
    def vul_check_prompt_agent_initial_complete(vulnerability_result, business_flow_code):
        """组装完整的初步分析prompt"""
        base_prompt = VulCheckPrompt.vul_check_prompt_agent_initial()
        
        return f"""{base_prompt}

**Vulnerability Analysis Task**:
{vulnerability_result}

**Code to Analyze**: 
{business_flow_code}

Please analyze the code against the vulnerability analysis task and provide your assessment."""

    @staticmethod
    def vul_check_prompt_agent_json_extraction(natural_response):
        """提取初步分析结果的JSON prompt"""
        return f"""Based on the following vulnerability analysis, extract the key information into JSON format:

{natural_response}

Please extract and return ONLY the following JSON structure:
{{
    "initial_assessment": "yes/no/need_more_info",
    "additional_info_needed": "if more information is needed, describe what information is needed"
}}

Only return the JSON, no other explanation."""

    @staticmethod
    def vul_check_prompt_agent_info_query_complete(additional_info):
        """组装完整的信息查询prompt"""
        base_prompt = VulCheckPrompt.vul_check_prompt_agent_info_query()
        
        return f"""{base_prompt}

**Previous Analysis Context**:
{additional_info}

Please specify what type of information would be most helpful."""

    @staticmethod
    def vul_check_prompt_agent_info_extraction(info_natural_response):
        """提取信息类型的JSON prompt"""
        return f"""Based on the following response about information needs, extract the information type:

{info_natural_response}

Please return ONLY the following JSON structure:
{{
    "info_type": "function/file/upstream_downstream",
    "specific_query": "specific content to query",
    "query_reason": "why this information is needed"
}}

Only return the JSON, no other explanation."""

    @staticmethod
    def vul_check_prompt_agent_final_analysis(vulnerability_result, business_flow_code, assessment, additional_info, additional_context):
        """组装完整的最终分析prompt"""
        base_prompt = VulCheckPrompt.vul_check_prompt_agent_initial()
        
        return f"""{base_prompt}

**Original Vulnerability Analysis Task**:
{vulnerability_result}

**Original Code**:
{business_flow_code}

**Previous Initial Analysis**:
- Assessment: {assessment}
- Information Needed: {additional_info}

**Additional Information Retrieved**:
{additional_context}

Now please provide your final vulnerability assessment based on all available information."""

    @staticmethod
    def vul_check_prompt_agent_final_extraction(final_natural_response):
        """提取最终结果的JSON prompt"""
        return f"""Based on the following final vulnerability analysis, extract the conclusion:

{final_natural_response}

Please return ONLY the following JSON structure:
{{
    "final_result": "yes/no"
}}

Only return the JSON, no other explanation."""