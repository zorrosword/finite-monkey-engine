from prompt_factory.checklists_prompt import ChecklistsPrompt
from prompt_factory.core_prompt import CorePrompt
from prompt_factory.periphery_prompt import PeripheryPrompt
from prompt_factory.vul_prompt import VulPrompt
from prompt_factory.vul_check_prompt import VulCheckPrompt
from prompt_factory.vul_prompt_common import VulPromptCommon
import os
import pandas as pd

class PromptAssembler:
    def assemble_prompt_common(code):
        ret_prompt=code+"\n"\
                    +PeripheryPrompt.role_set_solidity_common()+"\n"\
                    +PeripheryPrompt.task_set_blockchain_common()+"\n"\
                    +CorePrompt.core_prompt_assembled()+"\n"\
                    +VulPrompt.vul_prompt_common_new()+"\n"\
                    +PeripheryPrompt.guidelines()+"\n"\
                    +PeripheryPrompt.jailbreak_prompt()

                    
        return ret_prompt
    def assemble_prompt_common_fine_grained(code, prompt_index=None):
        ret_prompt=code+"\n"\
                    +PeripheryPrompt.role_set_solidity_common()+"\n"\
                    +PeripheryPrompt.task_set_blockchain_common()+"\n"\
                    +CorePrompt.core_prompt_assembled()+"\n"\
                    +str(VulPromptCommon.vul_prompt_common_new(prompt_index))+"\n"\
                    +PeripheryPrompt.guidelines()+"\n"\
                    +PeripheryPrompt.jailbreak_prompt()

                    
        return ret_prompt
    def assemble_prompt_pure(code):
        ret_prompt=code+"\n"\
                    +PeripheryPrompt.optimized_head_prompt_reasoning()+"\n"\
                    +PeripheryPrompt.role_set_go_common()+"\n"\
                    +PeripheryPrompt.task_set_blockchain_common()+"\n"\
                    +CorePrompt.core_prompt_pure()+"\n"\
                    +PeripheryPrompt.guidelines()+"\n"\
                    +PeripheryPrompt.jailbreak_prompt()+"\n"\
                    +PeripheryPrompt.optimized_tail_prompt_reasoning()

                    
        return ret_prompt
    
    @staticmethod
    def _get_vul_prompts(business_type):
        vul_prompts = []
        for type in business_type:
            if type == "chainlink":
                vul_prompts.append(VulPrompt.vul_prompt_chainlink())
            elif type == "dao":
                vul_prompts.append(VulPrompt.vul_prompt_dao())
            elif type == "inline assembly":
                vul_prompts.append(VulPrompt.vul_prompt_inline_assembly())
            elif type == "lending":
                vul_prompts.append(VulPrompt.vul_prompt_lending())
            elif type == "liquidation":
                vul_prompts.append(VulPrompt.vul_prompt_liquidation())
            elif type == "liquidity manager":
                vul_prompts.append(VulPrompt.vul_prompt_liquidity_manager())
            elif type == "signature":
                vul_prompts.append(VulPrompt.vul_prompt_signature_replay())
            elif type == "slippage":
                vul_prompts.append(VulPrompt.vul_prompt_slippage())
            elif type == "univ3":
                vul_prompts.append(VulPrompt.vul_prompt_univ3())
            elif type == "other":
                vul_prompts.append(VulPrompt.vul_prompt_common_new())
        return "\n\n".join(vul_prompts)
    
    @staticmethod
    def _get_checklist_from_knowledge(business_type):
        def get_from_xlsx(business_type):
            checklist_path = os.getenv("CHECKLIST_PATH", "src/knowledges/checklist.xlsx")
            checklist_sheet = os.getenv("CHECKLIST_SHEET", "Sheet1")
            df = pd.read_excel(checklist_path, sheet_name=checklist_sheet)
            checklist = df[df["project_type"] == business_type]["checklist"].values[0]
            return business_type + "\n" + checklist
        
        return "\n\n".join([get_from_xlsx(type) for type in business_type])

    def assemble_prompt_for_specific_project_directly_ask(code, business_type):
        combined_vul_prompt = PromptAssembler._get_vul_prompts(business_type)
        
        ret_prompt = code+"\n"\
                    +PeripheryPrompt.role_set_solidity_common()+"\n"\
                    +CorePrompt.directly_ask_prompt()+"\n"\
                    +combined_vul_prompt+"\n"\
                    +PeripheryPrompt.guidelines()+"\n"\
                    +PeripheryPrompt.jailbreak_prompt()
                    
        return ret_prompt
        
    def assemble_prompt_for_specific_project(code, business_type):
        # combined_vul_prompt = PromptAssembler._get_vul_prompts(business_type)
        combined_vul_prompt = PromptAssembler._get_checklist_from_knowledge(business_type)
        
        ret_prompt = code+"\n"\
                    +PeripheryPrompt.role_set_solidity_common()+"\n"\
                    +PeripheryPrompt.task_set_blockchain_common()+"\n"\
                    +CorePrompt.core_prompt_assembled()+"\n"\
                    +combined_vul_prompt+"\n"\
                    +PeripheryPrompt.guidelines()+"\n"\
                    +PeripheryPrompt.jailbreak_prompt()
                    
        return ret_prompt
    def assemble_optimize_prompt(code):
        ret_prompt=code+"\n"\
                    +PeripheryPrompt.role_set_rust_common()+"\n"\
                    +PeripheryPrompt.task_set_blockchain_common()+"\n"\
                    +CorePrompt.optimize_prompt()+"\n"
        return ret_prompt
    def assemble_vul_check_prompt(code,vul):
        ret_prompt=code+"\n"\
                +str(vul)+"\n"\
                +PeripheryPrompt.optimized_head_prompt_validating()+"\n"\
                +VulCheckPrompt.vul_check_prompt_claude_no_overflow()+"\n"\
                +PeripheryPrompt.optimized_tail_prompt_validating()
        return ret_prompt
    def assemble_vul_check_prompt_final(code,vul):
        ret_prompt=code+"\n"\
                +str(vul)+"\n"\
                +PeripheryPrompt.optimized_head_prompt_validating()+"\n"\
                +VulCheckPrompt.vul_check_prompt_claude_no_overflow_final()+"\n"\
                +PeripheryPrompt.optimized_tail_prompt_validating()
        return ret_prompt
    
    def assemble_checklists_prompt(code):
        ret_prompt=code+"\n"\
                    +ChecklistsPrompt.checklists_prompt()+"\n"
        return ret_prompt
    def assemble_checklists_prompt_for_scan(code,checklist_response):
        ret_prompt = code+"\n"\
                    +PeripheryPrompt.role_set_solidity_common()+"\n"\
                    +PeripheryPrompt.task_set_blockchain_common()+"\n"\
                    +CorePrompt.core_prompt_assembled()+"\n"\
                    +"<checklist>"+"\n"\
                    +checklist_response+"\n"\
                    +"</checklist>"+"\n"\
                    +PeripheryPrompt.guidelines()+"\n"\
                    +PeripheryPrompt.jailbreak_prompt()+"\n"\
                    +PeripheryPrompt.optimized_tail_prompt_reasoning()
        return ret_prompt
    def brief_of_response():
        return """Based on the analysis response, please translate the response to JSON format. 
        The JSON format should be one of the following:
        {'brief of response':'xxx','result':'yes'} 
        {'brief of response':'xxx','result':'no'} 
        {'brief of response':'xxx','result':'need creator to decide'}
        
        The 'brief of response' should contain a concise summary of the analysis,
        and the 'result' should reflect the final conclusion about the vulnerability's existence."""

    @staticmethod
    def confirmation_analysis_prompt(task_content: str, comprehensive_analysis: str) -> str:
        """构建确认分析提示"""
        return f"""
你是一个专业的智能合约安全审计专家。请对以下综合分析结果进行确认评估。

**原始任务内容:**
{task_content}

**综合分析结果:**
{comprehensive_analysis}

**确认要求:**
1. 仔细审查分析结果的准确性和完整性
2. 验证漏洞判断是否合理
3. 检查分析逻辑是否严密
4. 确认风险评级是否恰当

**请以JSON格式回复你的确认结果:**
{{"brief_of_response": "你的简要分析总结", "result": "yes/no/not_sure"}}

其中:
- "brief_of_response": 对分析结果的简要总结和评价
- "result": 
  - "yes": 确认存在漏洞
  - "no": 确认不存在漏洞  
  - "not_sure": 需要更多信息或分析不确定
"""

if __name__=="__main__":
    prompt = PromptAssembler()
    checklists = prompt._get_checklist_from_knowledge(["Decentralized Exchanges (DEX)","Token Standards (ERC-721/ERC-1155)","Event-Driven Automation"])
    print(checklists)