import os
import time
from typing import List, Tuple

from context.context_manager import ContextManager
from ..utils.check_utils import CheckUtils
from prompt_factory.prompt_assembler import PromptAssembler
from openai_api.openai import common_ask_confirmation


class AnalysisProcessor:
    """Analysis processor responsible for executing specific vulnerability analysis logic"""
    
    def __init__(self, context_manager: ContextManager):
        self.context_manager = context_manager
    
    def process_task_analysis(self, task, task_manager):
        """Process analysis for a single task"""
        # Collect all analysis results
        analysis_collection = []
        
        starttime = time.time()
        result = task.get_result(False)
        
        print("\n🔍 Starting vulnerability confirmation process...")
        
        # Get code to be analyzed
        code_to_be_tested = CheckUtils.get_code_to_analyze(task)
        print(f"\n📊 Analysis code type: {'Business flow code' if task.if_business_flow_scan=='1' else 'Function code'}")
        
        # First round analysis
        response_final, final_response = self._perform_initial_analysis(
            code_to_be_tested, result, analysis_collection
        )
        
        # If initial analysis shows no vulnerability, end directly
        if response_final == "no":
            formatted_results = CheckUtils.format_analysis_results(analysis_collection)
            CheckUtils.update_task_results(task_manager, task.id, result, response_final, final_response, formatted_results)
            
            endtime = time.time()
            CheckUtils.print_task_summary(endtime - starttime, 1, response_final)
            return
        
        # Execute multi-round confirmation
        response_final, final_response = self._perform_multi_round_confirmation(
            code_to_be_tested, result, analysis_collection
        )
        
        # Update results
        formatted_results = CheckUtils.format_analysis_results(analysis_collection)
        CheckUtils.update_task_results(task_manager, task.id, result, response_final, final_response, formatted_results)
        
        endtime = time.time()
        CheckUtils.print_task_summary(endtime - starttime, len(analysis_collection), response_final)
    
    def _perform_initial_analysis(self, code_to_be_tested: str, result: str, analysis_collection: List) -> Tuple:
        """Execute initial analysis"""
        print("\n=== First Round Analysis Start ===")
        print("📝 Analyzing potential vulnerabilities...")
        prompt = PromptAssembler.assemble_vul_check_prompt(code_to_be_tested, result)
        
        initial_response = common_ask_confirmation(prompt)
        if not initial_response or initial_response == "":
            print(f"❌ Error: Empty response received")
            return "not sure", "Empty response"
        
        print("\n📊 Initial Analysis Result Length:")
        print("-" * 80)
        print(len(initial_response))
        print("-" * 80)

        # Collect initial analysis results
        analysis_collection.extend([
            "=== Initial Analysis Results ===",
            initial_response
        ])

        # Process initial response
        initial_result_status = CheckUtils.process_round_response(initial_response)
        analysis_collection.extend([
            "=== Initial Analysis Status ===",
            initial_result_status
        ])

        # Extract required information
        required_info = self.context_manager.extract_required_info(initial_response)
        if required_info:
            analysis_collection.append("=== Information Requiring Further Analysis ===")
            analysis_collection.extend(required_info)

        if CheckUtils.should_skip_early(initial_result_status):
            print("\n🛑 Initial analysis shows clear 'no vulnerability' - stopping further analysis")
            return "no", "Analysis stopped after initial round due to clear 'no vulnerability' result"
        
        return None, None  # Continue with multi-round confirmation
    
    def _perform_multi_round_confirmation(self, code_to_be_tested: str, result: str, analysis_collection: List) -> Tuple:
        """Execute multi-round confirmation analysis"""
        # Set maximum confirmation rounds
        max_rounds = int(os.getenv("MAX_CONFIRMATION_ROUNDS", 3))
        request_per_round = int(os.getenv("REQUESTS_PER_CONFIRMATION_ROUND", 3))
        
        # Collect results by rounds - new data structure
        round_results = []  # Each element is a list of results from one round
        
        # Each round starts from original code, maintaining independence between rounds
        base_code = code_to_be_tested
        
        for round_num in range(max_rounds):
            print(f"\n=== Confirmation Round {round_num + 1}/{max_rounds} (Independent Round) ===")
            
            # Current round results
            current_round_results = []
            
            # Each round starts from base code, not dependent on previous round results
            current_code = base_code
            round_context_enhanced = False
            round_has_early_exit = False
            
            # Intra-round context enhancement and multiple queries
            for request_num in range(request_per_round):
                print(f"\n🔍 Round {round_num + 1} - Request {request_num + 1} / {request_per_round}")
                
                # Intra-round context enhancement: can enhance context starting from 2nd request
                if request_num > 0 and not round_context_enhanced:
                    current_code = self._enhance_context_within_round(
                        base_code, analysis_collection, round_num
                    )
                    round_context_enhanced = True
                
                # Use current context for query
                sub_round_response = CheckUtils.perform_confirmation_round(
                    current_code, result, round_num, request_num
                )
                
                # Collect analysis results
                analysis_collection.extend([
                    f"=== Round {round_num + 1} Request {request_num + 1} Analysis Results ===",
                    sub_round_response
                ])
                
                # Process response results
                if len(sub_round_response) == 0:
                    print(f"\n❌ Invalid response: Round {round_num + 1} Request {request_num + 1} result is empty")
                    continue
                    
                sub_result_status = CheckUtils.process_round_response(sub_round_response)
                analysis_collection.extend([
                    f"=== Round {round_num + 1} Request {request_num + 1} Analysis Status ===",
                    sub_result_status
                ])
                print(f"Round {round_num + 1} Request {request_num + 1} analysis status: {sub_result_status}")
                
                # Add to current round results
                current_round_results.append(sub_result_status)
                
                # Check if early exit is needed (but don't exit immediately with new logic)
                if CheckUtils.should_skip_early(sub_result_status):
                    print(f"\n⚠️ Round {round_num + 1} Request {request_num + 1} found 'no vulnerability' result")
                    round_has_early_exit = True
                    # Note: Don't exit immediately here, record status and let new logic decide
            
            # Add current round results to total results
            if current_round_results:  # Only add when round has results
                round_results.append(current_round_results)
                print(f"\n📋 Round {round_num + 1} completed, collected {len(current_round_results)} results")
                
                # [NEW] Check if current round meets strong confirmation criteria (3 yes)
                yes_count = sum(1 for r in current_round_results if "yes" in r or "confirmed" in r)
                no_count = sum(1 for r in current_round_results if "no" in r and "vulnerability" in r)
                
                if yes_count >= 3:
                    print(f"\n🎯 Round {round_num + 1} received {yes_count} yes responses, meeting strong confirmation criteria, directly confirming vulnerability exists!")
                    print("🚀 Terminating subsequent analysis early to save resources")
                    
                    # Return confirmation result directly
                    decision_reason = f"Round {round_num + 1} strong confirmation: {yes_count} yes responses"
                    final_response = f"=== Early Confirmation ===\nRound {round_num + 1}: {yes_count} yes, {no_count} no\nDecision basis: {decision_reason}\nFinal result: yes"
                    
                    # Add final conclusion to analysis collection
                    analysis_collection.extend([
                        "=== Final Conclusion (Early Confirmation) ===",
                        "Result: yes",
                        f"Decision basis: {decision_reason}",
                        "Early termination reason: Single round meets strong confirmation criteria"
                    ])
                    
                    return "yes", final_response
            
            # If 'no' appears in this round, record but don't exit immediately (let new logic decide)
            if round_has_early_exit:
                print(f"\n📝 Round {round_num + 1} shows 'no vulnerability' result, continuing subsequent rounds for complete evaluation")
        
        # Use new round-by-round analysis method
        print(f"\n🔍 Starting new round-by-round confirmation logic with {len(round_results)} round results")
        return CheckUtils.collect_analysis_results_by_rounds(analysis_collection, round_results)
    
    def _enhance_context_within_round(self, base_code: str, analysis_collection: List, round_num: int) -> str:
        """Intra-round context enhancement"""
        print(f"\n📈 Intra-round context enhancement...")
        
        # Extract required information based on first result of this round
        if len(analysis_collection) >= 2:
            last_response_in_round = analysis_collection[-2]
            required_info = self.context_manager.extract_required_info(last_response_in_round)
            
            if required_info:
                print(f"\n🔍 Intra-round additional information needed: {len(required_info)} items")
                
                # Intra-round internet search
                internet_info = self.context_manager.get_additional_internet_info(required_info)
                # Intra-round context retrieval
                additional_context = self.context_manager.get_additional_context(required_info)
                
                enhanced_context = []
                if internet_info:
                    enhanced_context.extend([
                        "=== Internet Search Results ===",
                        internet_info
                    ])
                    analysis_collection.extend([
                        f"=== Round {round_num + 1} Intra-round Internet Search Results ===",
                        internet_info
                    ])
                
                if additional_context:
                    enhanced_context.extend([
                        "=== Additional Context ===",
                        additional_context
                    ])
                    analysis_collection.extend([
                        f"=== Round {round_num + 1} Intra-round Additional Context ===",
                        additional_context
                    ])
                
                if enhanced_context:
                    enhanced_code = base_code + "\n\n" + "\n\n".join(enhanced_context)
                    print(f"\n📦 Intra-round context enhancement completed (total length: {len(enhanced_code)} characters)")
                    return enhanced_code
        
        return base_code 