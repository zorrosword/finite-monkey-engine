from prompt_factory.checklist_pipeline_prompt import ChecklistPipelinePrompt
from openai_api.openai import *
import os
import csv

class ChecklistGeneratorWithoutCode:
    def __init__(self):
        self.project_type_iteration_rounds = int(os.getenv("PROJECT_TYPE_ITERATION_ROUNDS", "1"))
        self.iteration_rounds = int(os.getenv("CHECKLIST_ITERATION_ROUNDS", "1"))
    
    def list_all_project_type(self, language):
        current_project_type = None
        for round in range(self.project_type_iteration_rounds):
            print(f"\n执行第 {round + 1} 轮项目类型列表生成...")
            # 第一轮或开始新一轮
            project_type_prompt = (ChecklistPipelinePrompt.list_project_types_for_specific_language(language) 
                                  if current_project_type is None 
                                  else ChecklistPipelinePrompt.complement_project_type_list(language, current_project_type))
            
            # 获取项目类型列表
            claude_response = ask_claude(project_type_prompt)
            ds_response = ask_deepseek(project_type_prompt)
            o3_response = ask_o3_mini(project_type_prompt)
            gpt_response = ask_openai_common(project_type_prompt)

            # 合并所有模型的结果
            merge_prompt = ChecklistPipelinePrompt.merge_project_type_list(language, [
                claude_response, ds_response, o3_response, gpt_response
            ])

            current_project_type = ask_deepseek(merge_prompt)
            
            # Check if the CSV file exists and write results
            output_file = f"{language}_project_type_results.csv"
            file_exists = os.path.isfile(output_file)

            with open(output_file, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                # Write headers only if the file is new
                if not file_exists:
                    writer.writerow(["round", "claude", "deepseek", "o3", "gpt-4-turbo", "merge_result"])
                # Append the current round's data
                writer.writerow([round + 1, claude_response, ds_response, o3_response, gpt_response, current_project_type])

            print(f"第 {round + 1} 轮项目类型列表生成完成")
        
        return current_project_type
    
    def generate_checklist(self, language, project_type_list):
        current_checklist = None
        for round in range(self.iteration_rounds):
            print(f"\n执行第 {round + 1} 轮检查清单生成...")
            # 第一轮或开始新一轮
            checklist_prompt = (ChecklistPipelinePrompt.generate_checklist_for_project_type(project_type_list) 
                                if current_checklist is None 
                                else ChecklistPipelinePrompt.complement_checklist(current_checklist))
            
            # 获取检查清单
            claude_response = ask_claude(checklist_prompt)
            ds_response = ask_deepseek(checklist_prompt)
            o3_response = ask_o3_mini(checklist_prompt)
            gpt_response = ask_openai_common(checklist_prompt)

            # 合并所有模型的结果
            merge_prompt = ChecklistPipelinePrompt.merge_checklist([
                claude_response, ds_response, o3_response, gpt_response
            ])

            current_checklist = ask_deepseek(merge_prompt)
            
            # Check if the CSV file exists and write results
            output_file = f"{language}_checklist_results.csv"
            file_exists = os.path.isfile(output_file)

            with open(output_file, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                # Write headers only if the file is new
                if not file_exists:
                    writer.writerow(["round", "claude", "deepseek", "o3", "gpt-4-turbo", "merge_result"])
                # Append the current round's data
                writer.writerow([round + 1, claude_response, ds_response, o3_response, gpt_response, current_checklist])

            print(f"第 {round + 1} 轮检查清单生成完成")
        
        return current_checklist

    
if __name__ == "__main__":
    language = "solidity"
    generator = ChecklistGeneratorWithoutCode()
    project_type_list = generator.list_all_project_type(language)
    checklist = generator.generate_checklist(language, project_type_list)