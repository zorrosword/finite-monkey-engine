import json
from typing import List, Dict, Tuple
from prompt_factory.prompt_assembler import PromptAssembler
from openai_api.openai import common_ask_confirmation, common_ask_for_json


class CheckUtils:
    """检查相关的工具函数类"""
    
    @staticmethod
    def get_code_to_analyze(task) -> str:
        """获取要分析的代码"""
        function_code = task.content
        if_business_flow_scan = task.if_business_flow_scan
        business_flow_code = task.business_flow_code
        business_flow_context = task.business_flow_context
        
        return business_flow_code + "\n" + business_flow_context if if_business_flow_scan == "1" else function_code
    
    @staticmethod
    def is_task_already_processed(task) -> bool:
        """检查任务是否已经处理过"""
        result_CN = task.get_result_CN()
        category_mark = task.get_category()
        
        return (result_CN is not None and len(result_CN) > 0 and result_CN != "None" and
                category_mark is not None and len(category_mark) > 0)
    
    @staticmethod
    def process_round_response(round_response: str) -> str:
        """
        处理每轮分析的响应，提取结果状态，增加防御性编程
        
        Args:
            round_response: 当前轮次的响应
            
        Returns:
            str: 提取的结果状态
        """
        prompt_translate_to_json = PromptAssembler.brief_of_response()
        
        # 使用 common_ask_for_json 获取 JSON 响应
        round_json_response = str(common_ask_for_json(round_response + "\n" + prompt_translate_to_json))
        print("\n📋 JSON Response Length:")
        print(len(round_json_response))
        
        try:
            cleaned_response = round_json_response
            print(f"\n🔍 清理后的响应: {cleaned_response}")
            
            # 解析 JSON
            response_data = json.loads(cleaned_response)
            
            # 获取结果状态，使用 get 方法提供默认值
            result_status = response_data.get("result", "not sure").lower()
            
            print(f"\n🎯 提取的结果状态: {result_status}")
            print(f"📏 结果状态长度: {len(result_status)}")
            
            # 验证结果状态的有效性
            valid_statuses = {"yes", "no", "need creator to decide", "confirmed"}
            if not any(status in result_status for status in valid_statuses):
                print("\n⚠️ 无效的结果状态 - 标记为 'not sure'")
                return "not sure"
            
            return result_status
        
        except json.JSONDecodeError as e:
            print(f"\n⚠️ JSON 解析错误: {str(e)} - 标记为 'not sure'")
            return "not sure"
        except Exception as e:
            print(f"\n⚠️ 意外错误: {str(e)} - 标记为 'not sure'")
            return "not sure"
    
    @staticmethod
    def collect_analysis_results_by_rounds(analysis_collection: List, round_results: List[List[str]]) -> Tuple[str, str]:
        """按轮次收集和格式化分析结果 - 新的确认逻辑"""
        print("\n📊 开始按轮次分析确认结果...")
        
        strong_confirmation_found = False
        round_summaries = []
        
        for round_num, round_result in enumerate(round_results, 1):
            yes_count = sum(1 for r in round_result if "yes" in r or "confirmed" in r)
            no_count = sum(1 for r in round_result if "no" in r and "vulnerability" in r)
            total_count = len(round_result)
            
            round_summary = f"第{round_num}轮: {yes_count}个yes, {no_count}个no, 共{total_count}次询问"
            round_summaries.append(round_summary)
            print(f"   {round_summary}")
            
            # 检查是否满足强确认条件
            if yes_count >= 3 or (yes_count >= 2 and no_count == 0):
                strong_confirmation_found = True
                print(f"   ✅ 第{round_num}轮满足强确认条件!")
        
        # 根据新逻辑确定最终结果
        if strong_confirmation_found:
            response_final = "yes"
            print("\n⚠️ 最终结果: 漏洞已确认 (发现强确认轮次)")
            decision_reason = "发现至少一轮强确认(3个yes或2个yes且无no)"
        else:
            # 如果没有强确认，使用改进的总体逻辑
            all_results = [result for round_result in round_results for result in round_result]
            total_yes = sum(1 for r in all_results if "yes" in r or "confirmed" in r)
            total_no = sum(1 for r in all_results if "no" in r and "vulnerability" in r)
            
            # 改进的判断逻辑：比较yes和no的数量
            if total_yes >= 2 and total_yes > total_no:
                response_final = "yes"
                print("\n⚠️ 最终结果: 漏洞已确认 (总体yes更多)")
                decision_reason = f"总体确认: {total_yes}个yes > {total_no}个no"
            elif total_no >= 2 and total_no > total_yes:
                response_final = "no"
                print("\n✅ 最终结果: 无漏洞 (总体no更多)")
                decision_reason = f"总体否定: {total_no}个no > {total_yes}个yes"
            elif total_yes >= 2 and total_no >= 2 and total_yes == total_no:
                response_final = "not sure"
                print("\n❓ 最终结果: 不确定 (yes和no数量相等)")
                decision_reason = f"结果平分: {total_yes}个yes = {total_no}个no"
            elif total_yes >= 2:
                response_final = "yes"
                print("\n⚠️ 最终结果: 漏洞已确认 (总体2+ 次确认)")
                decision_reason = f"总体确认: {total_yes}个yes, {total_no}个no"
            elif total_no >= 2:
                response_final = "no"
                print("\n✅ 最终结果: 无漏洞 (总体2+ 次否定)")
                decision_reason = f"总体否定: {total_yes}个yes, {total_no}个no"
            else:
                response_final = "not sure"
                print("\n❓ 最终结果: 不确定 (结果不明确)")
                decision_reason = f"结果不明确: {total_yes}个yes, {total_no}个no"
        
        # 生成详细的分析报告
        detailed_report = []
        detailed_report.append("=== 按轮次确认分析报告 ===")
        for summary in round_summaries:
            detailed_report.append(summary)
        detailed_report.append(f"判断依据: {decision_reason}")
        detailed_report.append(f"最终结果: {response_final}")
        
        final_response = "\n".join(detailed_report)
        
        # 添加最终结论到分析集合
        analysis_collection.append("=== 最终结论 (新逻辑) ===")
        analysis_collection.append(f"结果: {response_final}")
        analysis_collection.append(f"判断依据: {decision_reason}")
        analysis_collection.extend(detailed_report)
        
        return response_final, final_response
    
    @staticmethod
    def collect_analysis_results(analysis_collection: List, confirmation_results: List[str]) -> Tuple[str, str]:
        """收集和格式化分析结果 - 兼容性方法"""
        # 为了保持向后兼容，如果传入的是简单列表，使用原有逻辑
        yes_count = sum(1 for r in confirmation_results if "yes" in r or "confirmed" in r)
        no_count = sum(1 for r in confirmation_results if "no" in r and "vulnerability" in r)
        
        if yes_count >= 2:
            response_final = "yes"
            print("\n⚠️ 最终结果: 漏洞已确认 (2+ 次确认)")
        elif no_count >= 2:
            response_final = "no"
            print("\n✅ 最终结果: 无漏洞 (2+ 次否定)")
        else:
            response_final = "not sure"
            print("\n❓ 最终结果: 不确定 (结果不明确)")
        
        final_response = "\n".join([f"Round {i+1} Analysis:\n{resp}" for i, resp in enumerate(confirmation_results)])
        
        # 添加最终结论
        analysis_collection.append("=== 最终结论 ===")
        analysis_collection.append(f"结果: {response_final}")
        analysis_collection.append(f"详细说明: {final_response}")
        
        return response_final, final_response
    
    @staticmethod
    def format_analysis_results(analysis_collection: List) -> str:
        """格式化所有收集的结果"""
        formatted_results = "\n\n".join(str(item or '').strip() for item in analysis_collection)
        # 在更新数据库之前清理字符串
        return formatted_results.replace('\x00', '')
    
    @staticmethod
    def update_task_results(task_manager, task_id: int, result: str, response_final: str, 
                           final_response: str, formatted_results: str):
        """更新任务结果到数据库"""
        task_manager.update_result(task_id, result, response_final, final_response)
        task_manager.update_category(task_id, formatted_results)
    
    @staticmethod
    def should_skip_early(result_status: str) -> bool:
        """判断是否应该提前退出"""
        return "no" in result_status
    
    @staticmethod
    def perform_confirmation_round(code_to_be_tested: str, result: str, 
                                 round_num: int, request_num: int) -> str:
        """执行确认轮次"""
        prompt = PromptAssembler.assemble_vul_check_prompt_final(code_to_be_tested, result)
        sub_round_response = common_ask_confirmation(prompt)
        
        print(f"\n📋 第 {round_num + 1} 轮第 {request_num + 1} 次询问结果长度: {len(sub_round_response)}")
        
        return sub_round_response
    
    @staticmethod
    def print_task_summary(time_cost: float, confirmation_count: int, response_final: str):
        """打印任务摘要"""
        print("\n=== Task Summary ===")
        print(f"⏱️ Time cost: {time_cost:.2f} seconds")
        print(f"📝 Analyses performed: {confirmation_count}")
        print(f"🏁 Final status Length: {len(response_final)}")
        print("=" * 80 + "\n") 