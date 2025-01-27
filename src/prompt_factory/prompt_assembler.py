from prompt_factory.core_prompt import CorePrompt
from prompt_factory.periphery_prompt import PeripheryPrompt
from prompt_factory.vul_check_prompt import VulCheckPrompt
class PromptAssembler:
    def assemble_prompt(code):
        ret_prompt=code+"\n"\
                    +PeripheryPrompt.role_set_rust_common()+"\n"\
                    +PeripheryPrompt.task_set_blockchain_common()+"\n"\
                    +CorePrompt.core_prompt()+"\n"\
                    +PeripheryPrompt.guidelines()
                    # +PeripheryPrompt.impact_list()
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
                +VulCheckPrompt.vul_check_prompt_claude_no_overflow()+"\n"
        return ret_prompt
    def assemble_vul_check_prompt_final(code,vul):
        ret_prompt=code+"\n"\
                +str(vul)+"\n"\
                +VulCheckPrompt.vul_check_prompt_claude_no_overflow_final()+"\n"
        return ret_prompt
    def brief_of_response():
        return """Based on the analysis response, please translate the response to JSON format. 
        The JSON format should be one of the following:
        {'brief of response':'xxx','result':'yes'} 
        {'brief of response':'xxx','result':'no'} 
        {'brief of response':'xxx','result':'not sure'}
        
        The 'brief of response' should contain a concise summary of the analysis,
        and the 'result' should reflect the final conclusion about the vulnerability's existence."""