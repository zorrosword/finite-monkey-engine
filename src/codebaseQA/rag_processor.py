import lancedb
import os
import numpy as np
import requests
import pyarrow as pa
from typing import List, Dict, Any
from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from openai_api.openai import common_get_embedding

class RAGProcessor:
    def __init__(self, functions_to_check: List[Dict[str, Any]], db_path: str = "./lancedb", project_id:str=None):
        os.makedirs(db_path, exist_ok=True)
        
        self.db = lancedb.connect(db_path)
        self.table_name = f"lancedb_{project_id}"
        
        # 创建schema
        self.schema = pa.schema([
            pa.field("id", pa.string()),
            pa.field("name", pa.string()),
            pa.field("content", pa.string()),
            pa.field("start_line", pa.int32()),
            pa.field("end_line", pa.int32()),
            pa.field("file_path", pa.string()),
            pa.field("embedding", pa.list_(pa.float32(), 3072)),
            pa.field("modifiers", pa.list_(pa.string())),
            pa.field("visibility", pa.string()),
            pa.field("state_mutability", pa.string())
        ])

        # 检查表是否存在且数据量匹配
        if self.table_exists() and self.check_data_count(len(functions_to_check)):
            print(f"Table {self.table_name} already exists with correct data count. Skipping processing.")
            return

        self._create_database(functions_to_check)
        

    def table_exists(self) -> bool:
        """检查表是否存在"""
        try:
            self.db.open_table(self.table_name)
            return True
        except Exception:
            return False

    def check_data_count(self, expected_count: int) -> bool:
        """检查表中的数据数量是否匹配"""
        try:
            table = self.db.open_table(self.table_name)
            actual_count = len(table.to_lance())
            return actual_count == expected_count
        except Exception:
            return False

    def process_function(self, func: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": f"{func['name']}_{func['start_line']}",
            "name": func['name'],
            "content": func['content'],
            "start_line": func['start_line'],
            "end_line": func['end_line'],
            "file_path": func['relative_file_path'],
            "embedding": common_get_embedding(func['content']),
            "modifiers": func.get('modifiers', []),
            "visibility": func.get('visibility', ''),
            "state_mutability": func.get('stateMutability', '')
        }

    def _create_database(self, functions_to_check: List[Dict[str, Any]]) -> None:
        print(f"Processing {len(functions_to_check)} functions...")
        
        # 创建表
        table = self.db.create_table(self.table_name, schema=self.schema, mode="overwrite")
        
        # 用于线程安全的锁
        table_lock = threading.Lock()
        
        # 多线程处理函数
        max_workers = min(5, len(functions_to_check))  # 限制最大线程数
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_func = {executor.submit(self.process_function, func): func for func in functions_to_check}
            
            # 使用 tqdm 显示进度
            with tqdm(total=len(functions_to_check), desc="Processing functions", unit="function") as pbar:
                for future in as_completed(future_to_func):
                    func = future_to_func[future]
                    try:
                        processed_func = future.result()
                        # 线程安全地将数据添加到表中
                        with table_lock:
                            table.add([processed_func])
                        pbar.update(1)
                    except Exception as e:
                        print(f"Error processing function {func.get('name', 'unknown')}: {str(e)}")
                        pbar.update(1)
                        continue

        print("Database creation completed!")

    def search_similar_functions(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        query_embedding = common_get_embedding(query)
        table = self.db.open_table(self.table_name)
        return table.search(query_embedding).limit(k).to_list()

    def get_function_context(self, function_name: str) -> Dict[str, Any]:
        table = self.db.open_table(self.table_name)
        results = table.filter(f"name = '{function_name}'").to_list()
        return results[0] if results else None