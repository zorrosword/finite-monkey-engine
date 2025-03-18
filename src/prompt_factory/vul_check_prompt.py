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