import lancedb
import os
import numpy as np
import pyarrow as pa
from typing import List, Dict, Any
from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from openai_api.openai import common_get_embedding, common_ask_for_json


class RAGProcessor:
    """RAG处理器，负责创建和管理基于LanceDB的检索增强生成系统"""
    
    def __init__(self, functions_to_check: List[Dict[str, Any]], db_path: str = "./lancedb", project_id: str = None):
        """
        初始化RAG处理器
        
        Args:
            functions_to_check: 需要处理的函数列表
            db_path: 数据库路径
            project_id: 项目ID，用于生成表名
        """
        os.makedirs(db_path, exist_ok=True)
        
        self.db = lancedb.connect(db_path)
        self.project_id = project_id
        
        # 定义两个表名
        self.table_name_function = f"lancedb_function_{project_id}" if project_id else "lancedb_function"
        self.table_name_file = f"lancedb_file_{project_id}" if project_id else "lancedb_file"
        
        # 为了向后兼容，提供一个默认的table_name属性，指向函数表
        self.table_name = self.table_name_function
        
        # 创建schemas
        self._create_schemas()
        
        # 检查表是否存在
        function_table_exists = self._table_exists(self.table_name_function)
        file_table_exists = self._table_exists(self.table_name_file)
        tables_exist = function_table_exists and file_table_exists
        
        # 只有在表存在的情况下才检查数据量
        functions_count_match = False
        files_count_match = False
        
        if function_table_exists:
            functions_count_match = self._check_data_count(self.table_name_function, len(functions_to_check))
        else:
            print(f"表 {self.table_name_function} 不存在，需要创建")
            
        if file_table_exists:
            unique_files = list(set(func['relative_file_path'] for func in functions_to_check))
            files_count_match = self._check_data_count(self.table_name_file, len(unique_files))
        else:
            print(f"表 {self.table_name_file} 不存在，需要创建")
        
        if tables_exist and functions_count_match and files_count_match:
            print(f"所有表已存在且数据量正确，跳过处理")
            return

        self._create_all_databases(functions_to_check)
    
    def _create_schemas(self):
        """创建两个表的schemas"""
        
        # 函数级别表schema（包含3种embedding）
        self.schema_function = pa.schema([
            # 基本标识字段
            pa.field("id", pa.string()),
            pa.field("name", pa.string()),
            
            # 3种embedding字段
            pa.field("content_embedding", pa.list_(pa.float32(), 3072)),        # 原始代码embedding
            pa.field("name_embedding", pa.list_(pa.float32(), 3072)),           # 函数名embedding  
            pa.field("natural_embedding", pa.list_(pa.float32(), 3072)),        # 自然语言embedding
            
            # 函数完整metadata（基于functions_to_check的字段）
            pa.field("content", pa.string()),
            pa.field("natural_description", pa.string()),
            pa.field("start_line", pa.int32()),
            pa.field("end_line", pa.int32()),
            pa.field("relative_file_path", pa.string()),
            pa.field("absolute_file_path", pa.string()),
            pa.field("contract_name", pa.string()),
            pa.field("contract_code", pa.string()),
            pa.field("modifiers", pa.list_(pa.string())),
            pa.field("visibility", pa.string()),
            pa.field("state_mutability", pa.string()),
            pa.field("function_name_only", pa.string()),  # 纯函数名（不含合约前缀）
            pa.field("full_name", pa.string())            # 合约名.函数名
        ])
        
        # 文件级别表schema（包含2种embedding）
        self.schema_file = pa.schema([
            # 基本标识字段
            pa.field("id", pa.string()),
            pa.field("file_path", pa.string()),
            
            # 2种embedding字段
            pa.field("content_embedding", pa.list_(pa.float32(), 3072)),        # 文件内容embedding
            pa.field("natural_embedding", pa.list_(pa.float32(), 3072)),        # 文件自然语言embedding
            
            # 文件完整metadata
            pa.field("file_content", pa.string()),
            pa.field("natural_description", pa.string()),
            pa.field("relative_file_path", pa.string()),
            pa.field("absolute_file_path", pa.string()),
            pa.field("file_length", pa.int32()),
            pa.field("functions_count", pa.int32()),
            pa.field("functions_list", pa.list_(pa.string())),
            pa.field("file_extension", pa.string())
        ])
        
    def _table_exists(self, table_name: str) -> bool:
        """检查指定表是否存在"""
        try:
            self.db.open_table(table_name)
            return True
        except Exception:
            return False

    def _check_data_count(self, table_name: str, expected_count: int) -> bool:
        """检查表中的数据数量是否匹配"""
        try:
            table = self.db.open_table(table_name)
            actual_count = table.count_rows()
            print(f"表 {table_name} 存在 {actual_count} 行数据，期望 {expected_count} 行")
            if actual_count == expected_count:
                print(f"✅ 表 {table_name} 数据量匹配")
                return True
            else:
                print(f"⚠️ 表 {table_name} 数据量不匹配，需要重建")
                return False
        except Exception as e:
            # 这里不应该执行到，因为调用者已经检查了表存在性
            print(f"⚠️ 检查表 {table_name} 数据量时发生错误: {str(e)}")
            return False

    def _translate_to_natural_language(self, content: str, function_name: str) -> str:
        """将函数内容翻译成自然语言描述"""
        prompt = f"""
Please explain the functionality of this function in natural language. 
Provide a clear, concise description of what this function does, its purpose, and its key operations.

Function name: {function_name}

Function code:
```
{content}
```

Please respond with a comprehensive explanation in English:
"""
        
        try:
            response = common_ask_for_json(prompt)
            # 如果返回的是JSON格式，提取实际的描述内容
            if isinstance(response, dict):
                return response.get('description', response.get('explanation', str(response)))
            return str(response)
        except Exception as e:
            print(f"Error translating function {function_name} to natural language: {str(e)}")
            return f"Function {function_name} - unable to generate description"

    def _generate_file_description(self, file_path: str, file_content: str, functions_list: List[str]) -> str:
        """为文件生成自然语言描述"""
        prompt = f"""
Please analyze this code file and provide a comprehensive description of its purpose and functionality.
Describe what this file does, its main components, and its role in the overall system.

File path: {file_path}
Functions in this file: {', '.join(functions_list[:10])}{'...' if len(functions_list) > 10 else ''}

File content (first 2000 characters):
```
{file_content[:2000]}
```

Please provide a detailed explanation in English covering:
1. The main purpose of this file
2. Key functionalities it provides
3. Important classes/contracts/modules it contains
4. Its role in the broader system architecture

Response format: A clear, structured description in English.
"""
        
        try:
            response = common_ask_for_json(prompt)
            if isinstance(response, dict):
                return response.get('description', response.get('explanation', str(response)))
            return str(response)
        except Exception as e:
            print(f"Error generating description for file {file_path}: {str(e)}")
            return f"File {file_path} - unable to generate description"

    def process_function(self, func: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个函数，生成3种embedding"""
        
        # 提取函数名信息
        func_name = func['name']
        if '.' in func_name:
            contract_name, function_name_only = func_name.split('.', 1)
        else:
            contract_name = func.get('contract_name', 'Unknown')
            function_name_only = func_name
        
        full_name = f"{contract_name}.{function_name_only}"
        
        # 生成自然语言描述
        natural_description = self._translate_to_natural_language(func['content'], func['name'])
        
        # 生成3种embedding
        content_embedding = common_get_embedding(func['content'])
        name_embedding = common_get_embedding(full_name)
        natural_embedding = common_get_embedding(natural_description)
        
        return {
            # 基本标识
            "id": f"{func['name']}_{func['start_line']}",
            "name": func['name'],
            
            # 3种embedding
            "content_embedding": content_embedding,
            "name_embedding": name_embedding, 
            "natural_embedding": natural_embedding,
            
            # 完整的函数metadata
            "content": func['content'],
            "natural_description": natural_description,
            "start_line": func['start_line'],
            "end_line": func['end_line'],
            "relative_file_path": func['relative_file_path'],
            "absolute_file_path": func.get('absolute_file_path', ''),
            "contract_name": contract_name,
            "contract_code": func.get('contract_code', ''),
            "modifiers": func.get('modifiers', []),
            "visibility": func.get('visibility', ''),
            "state_mutability": func.get('stateMutability', ''),
            "function_name_only": function_name_only,
            "full_name": full_name
        }

    def process_file(self, file_path: str, file_content: str, functions_list: List[str], 
                    absolute_file_path: str = "") -> Dict[str, Any]:
        """处理单个文件，生成2种embedding"""
        
        # 生成文件的自然语言描述
        natural_description = self._generate_file_description(file_path, file_content, functions_list)
        
        # 生成2种embedding
        content_embedding = common_get_embedding(file_content[:4000])  # 限制文件内容长度
        natural_embedding = common_get_embedding(natural_description)
        
        # 获取文件扩展名
        file_extension = os.path.splitext(file_path)[1] if '.' in file_path else ''
        
        return {
            # 基本标识
            "id": f"file_{file_path.replace('/', '_').replace('.', '_')}",
            "file_path": file_path,
            
            # 2种embedding
            "content_embedding": content_embedding,
            "natural_embedding": natural_embedding,
            
            # 完整的文件metadata
            "file_content": file_content,
            "natural_description": natural_description,
            "relative_file_path": file_path,
            "absolute_file_path": absolute_file_path,
            "file_length": len(file_content),
            "functions_count": len(functions_list),
            "functions_list": functions_list,
            "file_extension": file_extension
        }

    def _create_all_databases(self, functions_to_check: List[Dict[str, Any]]) -> None:
        """创建所有数据库表"""
        print(f"Creating database tables for {len(functions_to_check)} functions...")
        
        # 1. 创建函数级别表
        self._create_function_database(functions_to_check)
        
        # 2. 创建文件级别表
        self._create_file_database(functions_to_check)
        
        print("All database tables creation completed!")

    def _create_function_database(self, functions_to_check: List[Dict[str, Any]]) -> None:
        """创建函数级别数据库表"""
        print("Creating function-level embedding table...")
        
        table = self.db.create_table(self.table_name_function, schema=self.schema_function, mode="overwrite")
        table_lock = threading.Lock()
        max_workers = min(10, len(functions_to_check))  # 降低并发数，因为涉及多个embedding和LLM调用
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_func = {executor.submit(self.process_function, func): func for func in functions_to_check}
            
            with tqdm(total=len(functions_to_check), desc="Processing function embeddings", unit="function") as pbar:
                for future in as_completed(future_to_func):
                    func = future_to_func[future]
                    try:
                        processed_func = future.result()
                        with table_lock:
                            table.add([processed_func])
                        pbar.update(1)
                    except Exception as e:
                        print(f"Error processing function {func.get('name', 'unknown')}: {str(e)}")
                        pbar.update(1)
                        continue

    def _create_file_database(self, functions_to_check: List[Dict[str, Any]]) -> None:
        """创建文件级别数据库表"""
        print("Creating file-level embedding table...")
        
        # 按文件分组函数
        files_dict = {}
        for func in functions_to_check:
            file_path = func['relative_file_path']
            if file_path not in files_dict:
                files_dict[file_path] = {
                    'functions': [],
                    'content': func.get('contract_code', ''),  # 使用contract_code作为文件内容
                    'absolute_path': func.get('absolute_file_path', '')
                }
            files_dict[file_path]['functions'].append(func['name'])
        
        table = self.db.create_table(self.table_name_file, schema=self.schema_file, mode="overwrite")
        table_lock = threading.Lock()
        max_workers = min(10, len(files_dict))  # 更低的并发数，因为文件处理更耗时
        
        file_items = [(file_path, data['content'], data['functions'], data['absolute_path']) 
                     for file_path, data in files_dict.items()]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(self.process_file, file_path, content, functions, abs_path): file_path 
                             for file_path, content, functions, abs_path in file_items}
            
            with tqdm(total=len(file_items), desc="Processing file-level embeddings", unit="file") as pbar:
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        processed_file = future.result()
                        with table_lock:
                            table.add([processed_file])
                        pbar.update(1)
                    except Exception as e:
                        print(f"Error processing file {file_path}: {str(e)}")
                        pbar.update(1)
                        continue

    # ========== 搜索接口 ==========
    
    def search_functions_by_content(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """基于函数内容搜索相似函数"""
        query_embedding = common_get_embedding(query)
        table = self.db.open_table(self.table_name_function)
        return table.search(query_embedding, vector_column_name="content_embedding").limit(k).to_list()

    def search_functions_by_name(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """基于函数名称搜索相似函数"""
        query_embedding = common_get_embedding(query)
        table = self.db.open_table(self.table_name_function)
        return table.search(query_embedding, vector_column_name="name_embedding").limit(k).to_list()

    def search_functions_by_natural_language(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """基于自然语言描述搜索相似函数"""
        query_embedding = common_get_embedding(query)
        table = self.db.open_table(self.table_name_function)
        return table.search(query_embedding, vector_column_name="natural_embedding").limit(k).to_list()

    def search_files_by_content(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """基于文件内容搜索相似文件"""
        query_embedding = common_get_embedding(query)
        table = self.db.open_table(self.table_name_file)
        return table.search(query_embedding, vector_column_name="content_embedding").limit(k).to_list()

    def search_files_by_natural_language(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """基于文件自然语言描述搜索相似文件"""
        query_embedding = common_get_embedding(query)
        table = self.db.open_table(self.table_name_file)
        return table.search(query_embedding, vector_column_name="natural_embedding").limit(k).to_list()

    def search_similar_files(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似文件（默认使用自然语言embedding）"""
        return self.search_files_by_natural_language(query, k)

    # ========== 兼容性方法（保持原有接口） ==========
    
    def search_similar_functions(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似函数（默认使用内容embedding）"""
        return self.search_functions_by_content(query, k)

    def search_similar_functions_by_content(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """兼容性方法：基于内容搜索"""
        return self.search_functions_by_content(query, k)

    def search_similar_functions_by_name(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """兼容性方法：基于名称搜索"""
        return self.search_functions_by_name(query, k)

    def search_similar_functions_by_natural_language(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """兼容性方法：基于自然语言搜索"""
        return self.search_functions_by_natural_language(query, k)

    # ========== 数据获取方法 ==========
    
    def get_function_context(self, function_name: str) -> Dict[str, Any]:
        """获取特定函数的上下文信息"""
        table = self.db.open_table(self.table_name_function)
        try:
            # 尝试使用新的API
            results = table.filter(f"name = '{function_name}'").to_list()
        except AttributeError:
            # 如果filter方法不存在，回退到扫描整个表
            try:
                all_data = table.to_list()
            except AttributeError:
                try:
                    all_data = table.to_arrow().to_pylist()
                except AttributeError:
                    all_data = []
            results = [item for item in all_data if item.get('name') == function_name]
        return results[0] if results else None
    
    def get_functions_by_file(self, file_path: str) -> List[Dict[str, Any]]:
        """根据文件路径获取函数列表"""
        table = self.db.open_table(self.table_name_function)
        try:
            # 尝试使用新的API
            results = table.filter(f"relative_file_path = '{file_path}'").to_list()
        except AttributeError:
            # 如果filter方法不存在，回退到扫描整个表
            try:
                all_data = table.to_list()
            except AttributeError:
                try:
                    all_data = table.to_arrow().to_pylist()
                except AttributeError:
                    all_data = []
            results = [item for item in all_data if item.get('relative_file_path') == file_path]
        return results
    
    def get_functions_by_visibility(self, visibility: str) -> List[Dict[str, Any]]:
        """根据可见性获取函数列表"""
        table = self.db.open_table(self.table_name_function)
        try:
            # 尝试使用新的API
            results = table.filter(f"visibility = '{visibility}'").to_list()
        except AttributeError:
            # 如果filter方法不存在，回退到扫描整个表
            try:
                all_data = table.to_list()
            except AttributeError:
                try:
                    all_data = table.to_arrow().to_pylist()
                except AttributeError:
                    all_data = []
            results = [item for item in all_data if item.get('visibility') == visibility]
        return results
    
    def get_all_functions(self) -> List[Dict[str, Any]]:
        """获取所有函数"""
        table = self.db.open_table(self.table_name_function)
        try:
            return table.to_list()
        except AttributeError:
            # 如果to_list方法不存在，尝试其他方法
            try:
                return table.to_arrow().to_pylist()
            except AttributeError:
                # 如果都不存在，返回空列表
                print("Warning: Unable to retrieve data from function table")
                return []
    
    def get_all_files(self) -> List[Dict[str, Any]]:
        """获取所有文件"""
        table = self.db.open_table(self.table_name_file)
        try:
            return table.to_list()
        except AttributeError:
            # 如果to_list方法不存在，尝试其他方法
            try:
                return table.to_arrow().to_pylist()
            except AttributeError:
                # 如果都不存在，返回空列表
                print("Warning: Unable to retrieve data from file table")
                return []
    
    def get_file_by_path(self, file_path: str) -> Dict[str, Any]:
        """根据文件路径获取文件信息"""
        table = self.db.open_table(self.table_name_file)
        try:
            # 尝试使用新的API
            results = table.filter(f"relative_file_path = '{file_path}'").to_list()
        except AttributeError:
            # 如果filter方法不存在，回退到扫描整个表
            try:
                all_data = table.to_list()
            except AttributeError:
                try:
                    all_data = table.to_arrow().to_pylist()
                except AttributeError:
                    all_data = []
            results = [item for item in all_data if item.get('relative_file_path') == file_path]
        return results[0] if results else None
    
    # ========== 数据库管理方法 ==========
    
    def delete_all_tables(self) -> bool:
        """删除所有数据表"""
        try:
            self.db.drop_table(self.table_name_function)
            self.db.drop_table(self.table_name_file)
            return True
        except Exception as e:
            print(f"Error deleting tables: {str(e)}")
            return False
    
    def get_all_tables_info(self) -> Dict[str, Any]:
        """获取所有表的信息"""
        try:
            function_table = self.db.open_table(self.table_name_function)
            file_table = self.db.open_table(self.table_name_file)
            
            return {
                "function_table": {
                    "table_name": self.table_name_function,
                    "row_count": function_table.count_rows(),
                    "schema": self.schema_function,
                    "embedding_types": ["content_embedding", "name_embedding", "natural_embedding"]
                },
                "file_table": {
                    "table_name": self.table_name_file,
                    "row_count": file_table.count_rows(),
                    "schema": self.schema_file,
                    "embedding_types": ["content_embedding", "natural_embedding"]
                }
            }
        except Exception as e:
            print(f"Error getting tables info: {str(e)}")
            return None 