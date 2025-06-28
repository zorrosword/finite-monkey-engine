import os
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from .analysis_processor import AnalysisProcessor
from ..utils.check_utils import CheckUtils


class ConfirmationProcessor:
    """漏洞确认处理器，负责执行多线程的漏洞确认检查"""
    
    def __init__(self, analysis_processor: AnalysisProcessor):
        self.analysis_processor = analysis_processor
    
    def execute_vulnerability_confirmation(self, task_manager):
        """执行漏洞确认检查"""
        tasks = task_manager.get_task_list()
        if len(tasks) == 0:
            return []

        # 定义线程池中的线程数量, 从env获取
        max_threads = int(os.getenv("MAX_THREADS_OF_CONFIRMATION", 5))

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [
                executor.submit(self._process_single_task_check, task, task_manager) 
                for task in tasks
            ]

            with tqdm(total=len(tasks), desc="Checking vulnerabilities") as pbar:
                for future in as_completed(futures):
                    future.result()  # 等待每个任务完成
                    pbar.update(1)  # 更新进度条

        return tasks
    
    def _process_single_task_check(self, task, task_manager):
        """处理单个任务的漏洞检查"""
        print("\n" + "="*80)
        print(f"🔍 开始处理任务 ID: {task.id}")
        print("="*80)
        
        # 检查任务是否已处理
        if CheckUtils.is_task_already_processed(task):
            print("\n🔄 该任务已处理完成，跳过...")
            return
        
        # 委托给分析处理器进行具体的分析工作
        self.analysis_processor.process_task_analysis(task, task_manager) 