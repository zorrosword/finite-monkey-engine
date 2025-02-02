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
        First analyze this vulnerability step by step, and then determine if it really exists based on the analysis result or need deeper function code.
        Please note the following points:
        1. If the vulnerability is an integer overflow vulnerability, directly conclude that the vulnerability does not exist
        2. If the vulnerability is a reentrancy vulnerability, directly conclude that the vulnerability does not exist
        3. When assessing vulnerabilities in functions with permission controls, consider not only the functionality itself but also how easily these permission roles can be obtained, as functions with "permission protection" may still be vulnerable if the permissions are easily accessible
        4. If more information is needed to confirm the vulnerability, please clearly state what content needs to be understood (e.g., specific function implementations, variable usage patterns, permission check logic, etc.)
        
        Please format your output as follows:
        1. Detailed analysis process
        2. Whether more information is needed (if yes, please specify what content needs to be understood and why)
        3. Preliminary conclusion based on current information
        """
    def vul_check_prompt_claude_no_overflow_final():
        return """
        First analyze this vulnerability step by step, code by code, then determine if it really exists based on the analysis results.
        Please note the following points:
        1. If the vulnerability is an integer overflow vulnerability, directly conclude that the vulnerability does not exist
        2. If the vulnerability is a reentrancy vulnerability, directly conclude that the vulnerability does not exist
        3. When assessing vulnerabilities in functions with permission controls, consider not only the functionality itself but also how easily these permission roles can be obtained, as functions with "permission protection" may still be vulnerable if the permissions are easily accessible

        """