import json
import os
import threading


class DialogueHistory:
    """对话历史管理器，用于管理扫描过程中的对话历史记录"""
    
    def __init__(self, project_id: str):
        self._history = {}  # 格式: {task_name: {prompt_index: [responses]}}
        self._lock = threading.Lock()
        self.project_id = project_id
        self.base_dir = os.path.join("src", "chat_history", project_id)
        
    def _get_task_dir(self, task_name: str) -> str:
        """获取任务的目录路径"""
        return os.path.join(self.base_dir, task_name)
        
    def _get_history_file(self, task_name: str, prompt_index: int = None) -> str:
        """获取历史记录文件的路径"""
        task_dir = self._get_task_dir(task_name)
        if prompt_index is not None:
            # 对于 COMMON_PROJECT_FINE_GRAINED 模式
            return os.path.join(task_dir, str(prompt_index), "chat_history")
        return os.path.join(task_dir, "chat_history")
        
    def _ensure_dir_exists(self, directory: str):
        """确保目录存在"""
        os.makedirs(directory, exist_ok=True)
        
    def _load_history_from_file(self, task_name: str, prompt_index: int = None):
        """从文件加载历史记录"""
        history_file = self._get_history_file(task_name, prompt_index)
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️ 警告：历史记录文件 {history_file} 格式错误")
                return []
            except Exception as e:
                print(f"⚠️ 警告：读取历史记录文件 {history_file} 时出错: {str(e)}")
                return []
        return []
        
    def _save_history_to_file(self, task_name: str, responses: list, prompt_index: int = None):
        """保存历史记录到文件"""
        history_file = self._get_history_file(task_name, prompt_index)
        self._ensure_dir_exists(os.path.dirname(history_file))
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(responses, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 警告：保存历史记录到文件 {history_file} 时出错: {str(e)}")

    def add_response(self, task_name: str, prompt_index: int, response: str):
        """添加新的响应"""
        with self._lock:
            if task_name not in self._history:
                self._history[task_name] = {}
            if prompt_index not in self._history[task_name]:
                # 从文件加载已有历史
                self._history[task_name][prompt_index] = self._load_history_from_file(task_name, prompt_index)
            
            self._history[task_name][prompt_index].append(response)
            # 保存到文件
            self._save_history_to_file(task_name, self._history[task_name][prompt_index], prompt_index)

    def get_history(self, task_name: str, prompt_index: int = None) -> list:
        """获取历史记录"""
        with self._lock:
            if task_name not in self._history:
                self._history[task_name] = {}
            
            if prompt_index is not None:
                if prompt_index not in self._history[task_name]:
                    # 从文件加载历史
                    self._history[task_name][prompt_index] = self._load_history_from_file(task_name, prompt_index)
                return self._history[task_name].get(prompt_index, [])
            
            # 如果没有指定 prompt_index，加载所有历史
            all_responses = []
            history_dir = self._get_task_dir(task_name)
            if os.path.exists(history_dir):
                if os.path.exists(self._get_history_file(task_name)):
                    # 非 COMMON_PROJECT_FINE_GRAINED 模式
                    all_responses.extend(self._load_history_from_file(task_name))
                else:
                    # COMMON_PROJECT_FINE_GRAINED 模式
                    for index_dir in os.listdir(history_dir):
                        if os.path.isdir(os.path.join(history_dir, index_dir)):
                            responses = self._load_history_from_file(task_name, int(index_dir))
                            all_responses.extend(responses)
            return all_responses

    def clear(self):
        """清除所有历史记录"""
        with self._lock:
            self._history.clear()
            if os.path.exists(self.base_dir):
                import shutil
                shutil.rmtree(self.base_dir) 