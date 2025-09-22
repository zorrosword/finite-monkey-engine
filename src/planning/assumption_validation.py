"""
假设验证模块 (Assumption Validation Analysis - AVA)

提供代码假设验证相关的功能，包括：
- 使用Claude分析代码假设
- 解析假设分析结果
- 多线程处理AVA模式的函数分析
- 生成假设验证任务
"""

import os
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from tqdm import tqdm

from openai_api.openai import analyze_code_assumptions
from prompt_factory.assumption_prompt import AssumptionPrompt


class AssumptionValidator:
    """假设验证器类"""
    
    def __init__(self, call_tree_utils):
        """
        初始化假设验证器
        
        Args:
            call_tree_utils: CallTreeUtils实例，用于获取调用树内容
        """
        self.call_tree_utils = call_tree_utils
    
    def analyze_code_assumptions(self, downstream_content: str) -> str:
        """使用Claude分析代码中的业务逻辑假设
        
        Args:
            downstream_content: 下游代码内容
            
        Returns:
            str: Claude分析的原始结果
        """
        assumption_prompt = AssumptionPrompt.get_assumption_analysis_prompt(downstream_content)
        
        try:
            print("🤖 正在使用Claude分析代码假设...")
            result = analyze_code_assumptions(assumption_prompt)
            print("✅ Claude分析完成")
            return result
        except Exception as e:
            print(f"❌ Claude分析失败: {e}")
            return ""
    
    def parse_assumptions_from_text(self, raw_assumptions: str) -> List[str]:
        """从Claude的原始输出中解析assumption列表
        
        Args:
            raw_assumptions: Claude分析的原始结果（使用<|ASSUMPTION_SPLIT|>分割）
            
        Returns:
            List[str]: 解析后的assumption列表
        """
        if not raw_assumptions:
            return []
            
        try:
            print("🧹 正在解析assumption结果...")
            
            # 使用<|ASSUMPTION_SPLIT|>分割字符串
            assumptions_raw = raw_assumptions.strip().split("<|ASSUMPTION_SPLIT|>")
            
            # 清理每个assumption，去除前后空白和空行
            assumptions_list = []
            for assumption in assumptions_raw:
                cleaned_assumption = assumption.strip()
                if cleaned_assumption:  # 过滤空字符串
                    assumptions_list.append(cleaned_assumption)
            
            print(f"✅ 解析完成，提取到 {len(assumptions_list)} 个假设")
            return assumptions_list
            
        except Exception as e:
            print(f"❌ 解析失败: {e}")
            return []

    def process_ava_mode_with_threading(self, public_functions_by_lang: Dict, max_depth: int, tasks: List, task_id: int):
        """使用多线程处理AVA模式的函数分析
        
        Args:
            public_functions_by_lang: 按语言分组的public函数
            max_depth: 最大深度
            tasks: 任务列表（引用传递）
            task_id: 当前任务ID
        """
        # 获取线程数配置，默认为4
        max_workers = int(os.getenv("AVA_THREAD_COUNT", "4"))
        print(f"🚀 使用 {max_workers} 个线程进行并发处理")
        
        # 为了线程安全，使用锁保护共享资源
        tasks_lock = threading.Lock()
        task_id_lock = threading.Lock()
        task_id_counter = [task_id]  # 使用列表来实现引用传递
        
        # 收集所有需要处理的函数
        all_functions = []
        for lang, public_funcs in public_functions_by_lang.items():
            if public_funcs:
                for public_func in public_funcs:
                    all_functions.append((lang, public_func))
        
        print(f"📋 总计需要处理 {len(all_functions)} 个函数")
        
        def process_single_function(lang_func_pair):
            """处理单个函数的假设分析"""
            lang, public_func = lang_func_pair
            func_name = public_func['name']
            
            try:
                # 使用call tree获取downstream内容
                downstream_content = self.call_tree_utils.get_downstream_content_with_call_tree(func_name, max_depth)
                
                # 加上root func的content
                downstream_content = public_func['content'] + '\n\n' + downstream_content
                
                print(f"  🔍 正在为函数 {func_name} 生成假设评估清单...")
                
                # 使用Claude分析代码假设
                raw_assumptions = self.analyze_code_assumptions(downstream_content)
                
                # 解析分割格式的结果
                assumption_violation_checklist = self.parse_assumptions_from_text(raw_assumptions)
                
                if not assumption_violation_checklist:
                    print(f"  ⚠️ 函数 {func_name} 未能生成有效的假设清单，跳过...")
                    return []
                
                actual_iteration_count = 2
                function_tasks = []
                
                # 为每个assumption statement创建单独的任务
                for assumption_statement in assumption_violation_checklist:
                    # 为每个assumption statement分配一个group UUID
                    group_uuid = str(uuid.uuid4())
                    
                    for iteration in range(actual_iteration_count):
                        # 线程安全地获取task_id
                        with task_id_lock:
                            current_task_id = task_id_counter[0]
                            task_id_counter[0] += 1
                        
                        task_data = {
                            'task_id': current_task_id,
                            'iteration_index': iteration + 1,
                            'language': lang,
                            'root_function': public_func,
                            'rule_key': "assumption_violation",
                            'rule_list': assumption_statement,  # 每个任务只处理一个assumption
                            'downstream_content': downstream_content,
                            'max_depth': max_depth,
                            'task_type': 'public_function_checklist_scan',
                            'group': group_uuid  # 为每个assumption statement分配一个group UUID
                        }
                        
                        function_tasks.append(task_data)
                
                total_tasks_created = len(assumption_violation_checklist) * actual_iteration_count
                print(f"  ✅ 为函数 {func_name} 创建了 {total_tasks_created} 个任务 ({len(assumption_violation_checklist)} 个假设 × {actual_iteration_count} 次迭代)")
                
                return function_tasks
                
            except Exception as e:
                print(f"  ❌ 处理函数 {func_name} 时出错: {e}")
                return []
        
        # 使用ThreadPoolExecutor进行并发处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_function = {
                executor.submit(process_single_function, lang_func_pair): lang_func_pair
                for lang_func_pair in all_functions
            }
            
            # 使用进度条显示处理进度
            with tqdm(total=len(all_functions), desc="处理函数假设分析") as pbar:
                for future in as_completed(future_to_function):
                    lang_func_pair = future_to_function[future]
                    lang, public_func = lang_func_pair
                    
                    try:
                        function_tasks = future.result()
                        
                        # 线程安全地添加任务到主列表
                        if function_tasks:
                            with tasks_lock:
                                tasks.extend(function_tasks)
                        
                    except Exception as e:
                        func_name = public_func['name']
                        print(f"❌ 函数 {func_name} 处理失败: {e}")
                    
                    pbar.update(1)
        
        print(f"🎉 多线程处理完成！共创建了 {len([t for t in tasks if t.get('rule_key') == 'assumption_violation'])} 个AVA任务")


# 便捷函数，用于创建AssumptionValidator实例
def create_assumption_validator(call_tree_utils) -> AssumptionValidator:
    """创建AssumptionValidator实例的便捷函数"""
    return AssumptionValidator(call_tree_utils)


# 便捷函数，用于直接调用功能
def analyze_code_assumptions_standalone(downstream_content: str) -> str:
    """分析代码假设的便捷函数（独立版本，不需要实例）"""
    assumption_prompt = AssumptionPrompt.get_assumption_analysis_prompt(downstream_content)
    
    try:
        print("🤖 正在使用Claude分析代码假设...")
        result = analyze_code_assumptions(assumption_prompt)
        print("✅ Claude分析完成")
        return result
    except Exception as e:
        print(f"❌ Claude分析失败: {e}")
        return ""


def parse_assumptions_from_text_standalone(raw_assumptions: str) -> List[str]:
    """解析假设文本的便捷函数（独立版本，不需要实例）"""
    if not raw_assumptions:
        return []
        
    try:
        print("🧹 正在解析assumption结果...")
        
        # 使用<|ASSUMPTION_SPLIT|>分割字符串
        assumptions_raw = raw_assumptions.strip().split("<|ASSUMPTION_SPLIT|>")
        
        # 清理每个assumption，去除前后空白和空行
        assumptions_list = []
        for assumption in assumptions_raw:
            cleaned_assumption = assumption.strip()
            if cleaned_assumption:  # 过滤空字符串
                assumptions_list.append(cleaned_assumption)
        
        print(f"✅ 解析完成，提取到 {len(assumptions_list)} 个假设")
        return assumptions_list
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return []
