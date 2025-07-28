from prompt_factory.checklist_pipeline_prompt import ChecklistPipelinePrompt
from openai_api.openai import *
import os

class ChecklistGenerator:
    def __init__(self):
        self.iteration_rounds = int(os.getenv("CHECKLIST_ITERATION_ROUNDS", "1"))

    def generate_checklist(self, code_to_be_tested):
        # 第一步：获取业务描述
        business_description_prompt = ChecklistPipelinePrompt.extract_business_prompt(code_to_be_tested)
        business_description = ask_grok4_via_openrouter(business_description_prompt)
        
        current_checklist = None
        for round in range(self.iteration_rounds):
            print(f"\n执行第 {round + 1} 轮检查清单生成...")
            
            # 第一轮或开始新一轮
            checklist_prompt = (ChecklistPipelinePrompt.generate_checklist_prompt(business_description) 
                              if current_checklist is None 
                              else ChecklistPipelinePrompt.generate_add_on_checklist_prompt(business_description,current_checklist))
            
            # 并行获取各个模型的checklist
            claude_response = ask_grok4_via_openrouter(checklist_prompt)
            ds_response = ask_grok4_via_openrouter(checklist_prompt)
            o3_response = ask_o3_mini(checklist_prompt)
            gpt_response = ask_openai_common(checklist_prompt)
            
            # 合并所有模型的结果
            consensus_prompt = ChecklistPipelinePrompt.generate_consensus_prompt([
                claude_response, ds_response, o3_response, gpt_response
            ])
            current_checklist = ask_grok4_via_openrouter(consensus_prompt)
            
            print(f"第 {round + 1} 轮检查清单生成完成")
        
        return business_description,current_checklist
    
