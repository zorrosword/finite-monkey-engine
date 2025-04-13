import os
import pandas as pd
class CorePrompt:
    def core_prompt_assembled():
        return """
        # Critical Context #
        We have already confirmed that the code contains only one exploitable, \
        code-error based vulnerability due to error logic in the code, \
        and the vulnerability is include but [not limited] to the following vulnerabilities:

        """
    def directly_ask_prompt():
        return """
        Is there any exploitable vulnerability related to the vulnerability type I mentioned following in the code?
        """
    def core_prompt_pure():
        return """
        # Critical Context #
        We have already confirmed that the code contains only one exploitable, \
        code-error based vulnerability due to error logic in the code
        """
    
    def core_prompt_vul_type_liquidation():
        return """
        before you start, you need to know that this is some liquidation vulnerability, \

        """


    def optimize_prompt():
        return """
        We have already confirmed that the code contains only one code optimize point, \
        not a vulnerability, \
        and your job is to identify it.
        """
    
    def assumation_prompt():
        return """
        Based on the vulnerability information, answer whether the establishment of the attack depends on the code of other unknown or unprovided contracts within the project, or whether the establishment of the vulnerability is affected by any external calls or contract states. 
        
        """
    def assumation_prompt_old():
        return """
        Based on the vulnerability information, answer whether the establishment of the attack depends on the code of other unknown or unprovided contracts within the project, or whether the establishment of the vulnerability is affected by any external calls or contract states. 
        
        Based on the results of the answer, add the JSON result: {'analaysis':'xxxxxxx','result':'need In-project other contract'} or {'analaysis':'xxxxxxx','result':'dont need In-project other contract'}.

        """
    def category_check():
        return """

        Based on the vulnerability information, analysis first step by step, then based on the analysis,Determine whether this vulnerability belongs to the access control type of vulnerability, the data validation type of vulnerability, or the data processing type of vulnerability.
        return as {'analaysis':'xxxxxxx','result':'xxxx vulnerability'}



        """
# In AiEngine
    def extract_required_info_prompt():
        return """
        Please extract all information points that need further understanding or confirmation from the following analysis response.
        If the analysis explicitly states "no additional information needed" or similar, return empty.
        If the analysis mentions needing more information, extract these information points.
        
        Analysis response:
        {response}
        """

    def judge_prompt():
        return  """
        Please analyze if the following information points require internet search to understand better.
        The information might need internet search if it involves:
        1. Technical concepts or protocols that need explanation
        2. Specific vulnerabilities or CVEs
        3. Industry standards or best practices
        4. Historical incidents or known attack vectors
        
        Return ONLY a JSON response in this exact format, with no additional text:
        {{
            "needs_search": "yes/no",
            "reason": "brief explanation"
        }}
        
        Information to analyze:
        {0}
        """

# In PlanningV2
    def ask_openai_for_business_flow_prompt():
        return """
        Based on the code above, analyze the business flows that start with the {function_name} function, consisting of multiple function calls. The analysis should adhere to the following requirements:
        1. only output the one sub-business flows, and must start from {function_name}.
        2. The output business flows should only involve the list of functions of the contract itself (ignoring calls to other contracts or interfaces, as well as events).
        3. After step-by-step analysis, output one result in JSON format, with the structure: {{"{function_name}":[function1,function2,function3....]}}
        4. The business flows must include all involved functions without any omissions

        """

    def get_project_type(self):
        checklist_path = os.getenv("CHECKLIST_PATH", "src/knowledges/checklist.xlsx")
        checklist_sheet = os.getenv("CHECKLIST_SHEET", "Sheet1")
        df = pd.read_excel(checklist_path, sheet_name=checklist_sheet)
        df = df.dropna(subset=["project_type"])
        project_type = df["project_type"].tolist()
        project_type = list(set(project_type))
        return project_type

    def type_check_prompt(self):
        project_type_list = self.get_project_type()
        project_type_str = ", ".join(project_type_list)
        return """分析以下智能合约代码，判断它属于哪些业务类型。仅从以下类型中选择：\n"""+project_type_str+"\n"+"""
请以JSON格式返回结果，格式为：{{"business_types": ["type1", "type2"]}}

代码：
{0}
"""

# In ResProcessor
    def translate_prompt():
        return """请对以下漏洞描述翻译，用中文输出，请不要包含任何特殊字符或格式符号：
原漏洞描述：
{vul_res}
"""

    def group_prompt():
        return """将以下漏洞进行归集分组，用中文输出，必须严格遵循以下要求：
1. 被归集的多个漏洞必须发生在同一个函数中
2. 可能存在一个函数有多种漏洞，这种情况下依然把它们归集到一起
3. 必须按照如下JSON格式输出，可能有多组ID：
{{
    "groups": [
        {{
            "grouped_ids": [ID1, ID2...]
        }},
        {{
            "grouped_ids": [ID3, ID4...]
        }}
    ]
}}

以下是需要归集的漏洞列表：
{vuln_descriptions}
"""

    def merge_desc_prompt():
        return """请将以上同一函数中的多个漏洞描述合并成一段完整的描述，要求：
1. 合并后的描述要完整概括所有漏洞的所有细节，如果存在多个漏洞，一定要在一段话内分开描述，分点描述，详细描述
2. **必须**保持描述的准确性和完整性，同时保持逻辑易理解，不要晦涩难懂
3. 描述中必须附带有代码或代码段辅助解释，代码或代码段必须和描述互有交错，其最终目的是为了保证描述易懂,不要给出大段代码段
4. 每个漏洞的描述必须清晰，完整，不能遗漏任何关键点或代码或代码段或变量
5. 不要包含任何特殊字符或格式符号
6. 用中文输出，用markdown格式

以下是需要合并的漏洞描述：
{vuln_details}
"""

if __name__=="__main__":
    corePrompt = CorePrompt()
    print(corePrompt.type_check_prompt())