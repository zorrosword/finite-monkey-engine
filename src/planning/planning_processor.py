import json
import random
import csv
import sys
import os
import os.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List, Dict, Tuple
from tqdm import tqdm
from dao.entity import Project_Task
from openai_api.openai import common_ask_for_json
from prompt_factory.core_prompt import CorePrompt
from prompt_factory.vul_prompt_common import VulPromptCommon
import json
from .business_flow_utils import BusinessFlowUtils
from .config_utils import ConfigUtils

# 直接使用tree_sitter_parsing而不是通过context
from tree_sitter_parsing import TreeSitterProjectAudit, parse_project, TreeSitterProjectFilter


class PlanningProcessor:
    """规划处理器，负责基于public函数downstream深度扫描的新planning逻辑"""
    
    def __init__(self, project_audit, taskmgr):
        """
        直接接受项目审计结果，而不是通过ContextFactory间接获取
        
        Args:
            project_audit: TreeSitterProjectAudit实例，包含解析后的项目数据
            taskmgr: 任务管理器
        """
        self.project_audit = project_audit
        self.taskmgr = taskmgr
        
        # 从project_audit获取核心数据
        self.functions = project_audit.functions
        self.functions_to_check = project_audit.functions_to_check
        self.call_trees = project_audit.call_trees
        
        # 为COMMON_PROJECT_FINE_GRAINED模式添加计数器
        self.fine_grained_counter = 0
        
        # RAG功能（可选，如果需要的话）
        self.rag_processor = None
    
    def initialize_rag_processor(self, lancedb_path, project_id):
        """初始化RAG处理器（可选功能）"""
        try:
            from context.rag_processor import RAGProcessor
            # 正确传递参数：functions_to_check作为第一个参数，并传递调用树数据
            call_trees = getattr(self.project_audit, 'call_trees', [])
            self.rag_processor = RAGProcessor(self.functions_to_check, lancedb_path, project_id, call_trees)
            print("✅ RAG处理器初始化完成")
            print(f"📊 基于 {len(self.functions_to_check)} 个tree-sitter解析的函数构建RAG")
            print(f"🔗 使用 {len(call_trees)} 个调用树构建关系型RAG")
        except ImportError:
            print("⚠️  RAG处理器不可用，将使用简化搜索")
            self.rag_processor = None
        except Exception as e:
            print(f"⚠️  RAG处理器初始化失败: {e}")
            self.rag_processor = None
    
    def find_public_functions_by_language(self) -> Dict[str, List[Dict]]:
        """根据语言类型查找所有public函数
        
        Returns:
            Dict[str, List[Dict]]: 按语言分类的public函数字典
        """
        public_functions_by_lang = {
            'solidity': [],
            'rust': [],
            'cpp': [],
            'move': []
        }
        
        for func in self.functions_to_check:
            # 检查可见性
            visibility = func.get('visibility', '').lower()
            func_name = func.get('name', '')
            
            # 判断语言类型和public可见性
            if func_name.endswith('.sol') or 'sol' in func.get('relative_file_path', '').lower():
                if visibility in ['public', 'external']:
                    public_functions_by_lang['solidity'].append(func)
            elif func_name.endswith('.rs') or 'rust' in func.get('relative_file_path', '').lower():
                if visibility == 'pub' or visibility == 'public':
                    public_functions_by_lang['rust'].append(func)
            elif func_name.endswith('.cpp') or func_name.endswith('.c') or 'cpp' in func.get('relative_file_path', '').lower():
                if visibility == 'public' or not visibility:  # C++默认public
                    public_functions_by_lang['cpp'].append(func)
            elif func_name.endswith('.move') or 'move' in func.get('relative_file_path', '').lower():
                if visibility == 'public' or visibility == 'public(friend)':
                    public_functions_by_lang['move'].append(func)
        
        # 打印统计信息
        total_public = sum(len(funcs) for funcs in public_functions_by_lang.values())
        print(f"🔍 发现 {total_public} 个public函数:")
        for lang, funcs in public_functions_by_lang.items():
            if funcs:
                print(f"  📋 {lang}: {len(funcs)} 个public函数")
        
        return public_functions_by_lang
    
    def convert_tasks_to_project_tasks_v3(self, tasks: List[Dict]) -> List[Project_Task]:
        """将任务数据转换为Project_Task实体（V3版本）"""
        project_tasks = []
        
        for task in tasks:
            root_function = task['root_function']
            rule_list = task['rule_list']
            downstream_content = task.get('downstream_content', '')
            
            # 构建business_flow_code: root func的内容 + 所有downstream的内容
            business_flow_code = root_function.get('content', '')
            if downstream_content:
                business_flow_code += '\n\n' + downstream_content
            
            # 创建Project_Task实例
            project_task = Project_Task(
                project_id=self.taskmgr.project_id,
                name=root_function.get('name', ''),  # 合约名+函数名用点连接
                content=root_function.get('content', ''),  # root function的内容
                rule=json.dumps(rule_list, ensure_ascii=False, indent=2),  # 原始的list
                rule_key=task.get('rule_key', ''),  # 规则key
                start_line=str(root_function.get('start_line', '')),
                end_line=str(root_function.get('end_line', '')),
                relative_file_path=root_function.get('relative_file_path', ''),
                absolute_file_path=root_function.get('absolute_file_path', ''),
                business_flow_code=business_flow_code
            )
            
            project_tasks.append(project_task)
        
        return project_tasks
    
    def create_database_tasks_v3(self, project_tasks: List[Project_Task]):
        """将Project_Task实体存储到数据库（V3版本）"""
        print(f"💾 开始存储 {len(project_tasks)} 个任务到数据库...")
        
        success_count = 0
        for project_task in project_tasks:
            try:
                self.taskmgr.save_task(project_task)
                success_count += 1
            except Exception as e:
                print(f"⚠️ 保存任务失败: {project_task.name} - {str(e)}")
        
        print(f"✅ 成功存储 {success_count}/{len(project_tasks)} 个任务")

    def extract_downstream_to_deepest(self, func_name: str, visited: set = None, depth: int = 0, max_depth: int = 10) -> List[Dict]:
        """深度提取某个函数的所有下游函数到最深层
        
        Args:
            func_name: 起始函数名
            visited: 已访问的函数集合（避免循环）
            depth: 当前深度
            max_depth: 最大深度限制
            
        Returns:
            List[Dict]: 下游函数链表，包含深度信息
        """
        if visited is None:
            visited = set()
        
        if func_name in visited or depth > max_depth:
            return []
        
        visited.add(func_name)
        downstream_chain = []
        
        # 在调用树中查找当前函数的下游函数
        for call_tree in self.call_trees:
            if call_tree.get('function_name') == func_name.split('.')[-1]:
                relationships = call_tree.get('relationships', {})
                func_name_short = func_name.split('.')[-1]
                downstream_funcs = relationships.get('downstream', {}).get(func_name_short, set())
                
                for downstream_func in downstream_funcs:
                    # 找到下游函数的完整信息
                    for func in self.functions_to_check:
                        if func['name'].split('.')[-1] == downstream_func:
                            downstream_info = {
                                'function': func,
                                'depth': depth + 1,
                                'parent': func_name
                            }
                            downstream_chain.append(downstream_info)
                            
                            # 递归获取更深层的下游函数
                            deeper_downstream = self.extract_downstream_to_deepest(
                                func['name'], visited.copy(), depth + 1, max_depth
                            )
                            downstream_chain.extend(deeper_downstream)
                            break
                break
        
        return downstream_chain

    def create_public_function_tasks_v3(self, max_depth: int = 5) -> List[Dict]:
        """为每个public函数创建新版任务（V3版本）
        使用call tree获取downstream内容，并使用all_checklists生成rule
        
        Args:
            max_depth: 最大深度限制
            
        Returns:
            List[Dict]: 任务列表
        """
        print("🚀 开始创建新版任务（V3）...")
        
        # 获取所有public函数
        public_functions_by_lang = self.find_public_functions_by_language()
        
        # 获取所有检查规则
        all_checklists = VulPromptCommon.vul_prompt_common_new()
        
        tasks = []
        task_id = 0
        
        for lang, public_funcs in public_functions_by_lang.items():
            if not public_funcs:
                continue
                
            print(f"\n📋 处理 {lang} 语言的 {len(public_funcs)} 个public函数...")
            
            for public_func in public_funcs:
                func_name = public_func['name']
                
                print(f"  🔍 分析public函数: {func_name}")
                
                # 使用call tree获取downstream内容
                downstream_content = self.get_downstream_content_with_call_tree(func_name, max_depth)
                
                # 为每个检查类型创建一个任务
                for rule_key, rule_list in all_checklists.items():
                    task_data = {
                        'task_id': task_id,
                        'language': lang,
                        'root_function': public_func,
                        'rule_key': rule_key,
                        'rule_list': rule_list,
                        'downstream_content': downstream_content,
                        'max_depth': max_depth,
                        'task_type': 'public_function_checklist_scan'
                    }
                    
                    tasks.append(task_data)
                    task_id += 1
                    
                    print(f"    ✅ 创建任务: {rule_key} - {len(rule_list)} 个检查项")
        
        print(f"\n✅ 总共创建 {len(tasks)} 个任务")
        return tasks
    
    def get_downstream_content_with_call_tree(self, func_name: str, max_depth: int = 5) -> str:
        """使用call tree获取函数的downstream内容
        
        Args:
            func_name: 函数名
            max_depth: 最大深度
            
        Returns:
            str: 拼接的downstream内容
        """
        contents = []
        
        # 查找对应的call tree
        if hasattr(self.project_audit, 'call_trees') and self.project_audit.call_trees:
            # 如果有AdvancedCallTreeBuilder，使用get_call_tree_with_depth_limit
            try:
                from tree_sitter_parsing.advanced_call_tree_builder import AdvancedCallTreeBuilder
                builder = AdvancedCallTreeBuilder()
                downstream_tree = builder.get_call_tree_with_depth_limit(
                    self.project_audit.call_trees, func_name, 'downstream', max_depth
                )
                
                if downstream_tree and downstream_tree.get('tree'):
                    contents = self._extract_contents_from_tree(downstream_tree['tree'])
            except Exception as e:
                print(f"    ⚠️ 使用高级call tree失败: {e}，使用简化方法")
                contents = self._get_downstream_content_fallback(func_name, max_depth)
        else:
            contents = self._get_downstream_content_fallback(func_name, max_depth)
        
        return '\n\n'.join(contents)
    
    def _extract_contents_from_tree(self, tree_node: Dict) -> List[str]:
        """从tree节点中提取所有函数内容"""
        contents = []
        
        if tree_node.get('function_data'):
            function_data = tree_node['function_data']
            if function_data.get('content'):
                contents.append(function_data['content'])
        
        # 递归处理子节点
        for child in tree_node.get('children', []):
            contents.extend(self._extract_contents_from_tree(child))
        
        return contents
    
    def _get_downstream_content_fallback(self, func_name: str, max_depth: int) -> List[str]:
        """简化的downstream内容获取方法"""
        downstream_chain = self.extract_downstream_to_deepest(func_name)
        contents = []
        
        for item in downstream_chain:
            if item.get('depth', 0) <= max_depth:
                function = item.get('function')
                if function and function.get('content'):
                    contents.append(function['content'])
        
        return contents
    
    def create_public_function_tasks(self) -> List[Dict]:
        """为每个public函数创建基于downstream深度扫描的任务（旧版本，已废弃）
        
        Returns:
            List[Dict]: 任务列表
        """
        print("🚀 开始基于public函数downstream深度扫描创建任务...")
        
        # 获取所有public函数
        public_functions_by_lang = self.find_public_functions_by_language()
        
        tasks = []
        task_id = 0
        
        for lang, public_funcs in public_functions_by_lang.items():
            if not public_funcs:
                continue
                
            print(f"\n📋 处理 {lang} 语言的 {len(public_funcs)} 个public函数...")
            
            for public_func in public_funcs:
                func_name = public_func['name']
                
                print(f"  🔍 分析public函数: {func_name}")
                
                # 提取该public函数的所有downstream函数
                downstream_chain = self.extract_downstream_to_deepest(func_name)
                
                if downstream_chain:
                    # 构建任务数据
                    all_functions = [public_func] + [item['function'] for item in downstream_chain]
                    
                    # 按深度分组
                    depth_groups = {}
                    depth_groups[0] = [public_func]
                    
                    for item in downstream_chain:
                        depth = item['depth']
                        if depth not in depth_groups:
                            depth_groups[depth] = []
                        depth_groups[depth].append(item['function'])
                    
                    max_depth = max(depth_groups.keys()) if depth_groups else 0
                    
                    task_data = {
                        'task_id': task_id,
                        'language': lang,
                        'root_function': public_func,
                        'downstream_chain': downstream_chain,
                        'all_functions': all_functions,
                        'depth_groups': depth_groups,
                        'max_depth': max_depth,
                        'total_functions': len(all_functions),
                        'task_type': 'public_downstream_scan'
                    }
                    
                    tasks.append(task_data)
                    task_id += 1
                    
                    print(f"    ✅ 创建任务: {len(all_functions)} 个函数, 最大深度: {max_depth}")
                    for depth, funcs in depth_groups.items():
                        print(f"      深度 {depth}: {len(funcs)} 个函数")
                else:
                    # 即使没有下游函数，也为单个public函数创建任务
                    task_data = {
                        'task_id': task_id,
                        'language': lang,
                        'root_function': public_func,
                        'downstream_chain': [],
                        'all_functions': [public_func],
                        'depth_groups': {0: [public_func]},
                        'max_depth': 0,
                        'total_functions': 1,
                        'task_type': 'public_single_scan'
                    }
                    
                    tasks.append(task_data)
                    task_id += 1
                    
                    print(f"    ✅ 创建单函数任务: {func_name}")
        
        print(f"\n🎉 总共创建了 {len(tasks)} 个基于public函数downstream的扫描任务")
        return tasks

    def create_database_tasks(self, tasks: List[Dict]) -> None:
        """将任务数据存储到数据库
        
        Args:
            tasks: 任务列表
        """
        print("💾 开始将任务存储到数据库...")
        
        for task_data in tasks:
            try:
                # 构建任务描述
                root_func = task_data['root_function']
                description = f"[{task_data['language'].upper()}] Public函数 {root_func['name']} 及其 {task_data['total_functions']-1} 个下游函数的深度扫描"
                
                # 构建函数列表描述
                functions_desc = [f"Root: {root_func['name']}"]
                for depth, funcs in task_data['depth_groups'].items():
                    if depth > 0:
                        func_names = [f['name'] for f in funcs]
                        functions_desc.append(f"深度{depth}: {', '.join(func_names)}")
                
                functions_detail = "; ".join(functions_desc)
                
                # 创建任务对象 - 使用Project_Task实体的正确参数
                task = Project_Task(
                    project_id=self.project_audit.project_id,
                    name=root_func['name'],
                    content=root_func.get('content', ''),
                    keyword='downstream_scan',
                    business_type='vulnerability_scan',
                    sub_business_type=task_data['language'],
                    function_type='public_function_downstream',
                    rule=f"Scan public function {root_func['name']} and its downstream call chain",
                    description=description,
                    start_line=str(root_func.get('start_line', '')),
                    end_line=str(root_func.get('end_line', '')),
                    relative_file_path=root_func.get('relative_file_path', ''),
                    absolute_file_path=root_func.get('absolute_file_path', ''),
                    title=f"Public Function Downstream Scan: {root_func['name']}",
                    business_flow_code=str(task_data['all_functions'])
                )
                
                # 保存到数据库
                self.taskmgr.add_task_in_one(task)
                
                print(f"  ✅ 保存任务: {description}")
                
            except Exception as e:
                print(f"❌ 保存任务失败: {e}")
                continue
        
        print(f"💾 任务存储完成，总共 {len(tasks)} 个任务")

    def process_for_common_project_mode(self, max_depth: int = 5) -> Dict:
        """新的COMMON_PROJECT模式处理逻辑 - 使用V3版本"""
        
        print("🎯 启动V3版本的Planning模式（使用call tree和all_checklists）")
        print("="*60)
        
        try:
            # 0. 检查project_id是否已经有任务
            existing_tasks = self.taskmgr.query_task_by_project_id(self.project_audit.project_id)
            if existing_tasks and len(existing_tasks) > 0:
                print(f"⚠️ 项目 {self.project_audit.project_id} 已经存在 {len(existing_tasks)} 个任务，跳过任务创建")
                return {
                    'success': True,
                    'message': f'项目 {self.project_audit.project_id} 已存在任务，跳过创建',
                    'tasks_created': 0,
                    'project_tasks_created': len(existing_tasks),
                    'tasks_by_language': {},
                    'max_depth_used': max_depth,
                    'skipped': True
                }
            
            # 1. 使用V3方法创建任务
            tasks = self.create_public_function_tasks_v3(max_depth)
            
            if not tasks:
                print("⚠️ 未创建任何任务，可能没有找到public函数")
                return {
                    'success': False,
                    'message': '未找到public函数',
                    'tasks_created': 0
                }
            
            # 2. 转换并存储任务到数据库
            project_tasks = self.convert_tasks_to_project_tasks_v3(tasks)
            self.create_database_tasks_v3(project_tasks)
            
            # 3. 返回处理结果
            result = {
                'success': True,
                'message': 'Planning任务创建成功',
                'tasks_created': len(tasks),
                'project_tasks_created': len(project_tasks),
                'tasks_by_language': {},
                'max_depth_used': max_depth
            }
            
            # 统计各语言任务数
            for task in tasks:
                lang = task['language']
                if lang not in result['tasks_by_language']:
                    result['tasks_by_language'][lang] = 0
                result['tasks_by_language'][lang] += 1
            
            print(f"\n🎉 V3 Planning处理完成:")
            print(f"  📊 创建任务: {result['tasks_created']} 个")
            print(f"  💾 存储到数据库: {result['project_tasks_created']} 个")
            print(f"  📏 使用最大深度: {result['max_depth_used']}")
            print(f"  🌐 语言分布: {result['tasks_by_language']}")
            print(f"  🔍 使用call tree获取downstream内容")
            print(f"  📋 使用all_checklists生成检查规则")
            
            return result
            
        except Exception as e:
            print(f"❌ Planning处理失败: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'message': f'Planning处理失败: {str(e)}',
                'tasks_created': 0
            }

    def search_functions_by_name(self, name_query, k=5):
        """按名称搜索函数（使用RAG或简化搜索）"""
        if self.rag_processor:
            return self.rag_processor.search_functions_by_name(name_query, k)
        else:
            # 简化的名称搜索
            results = []
            for func in self.functions_to_check:
                if name_query.lower() in func.get('name', '').lower():
                    results.append({
                        'function': func,
                        'score': 0.8,  # 简化评分
                        'reason': f"名称匹配: {name_query}"
                    })
                    if len(results) >= k:
                        break
            return results

    def search_functions_by_content(self, content_query, k=5):
        """按内容搜索函数（使用RAG或简化搜索）"""
        if self.rag_processor:
            return self.rag_processor.search_functions_by_content(content_query, k)
        else:
            # 简化的内容搜索
            results = []
            for func in self.functions_to_check:
                if content_query.lower() in func.get('content', '').lower():
                    results.append({
                        'function': func,
                        'score': 0.7,  # 简化评分
                        'reason': f"内容匹配: {content_query}"
                    })
                    if len(results) >= k:
                        break
            return results

    def get_available_rag_types(self) -> Dict[str, str]:
        """获取可用的RAG类型列表
        
        Returns:
            Dict[str, str]: RAG类型名称和描述的字典
        """
        if not self.rag_processor:
            return {}
        
        return {
            # 基础RAG类型
            'name': '名字检索 - 基于函数名称的精确匹配',
            'content': '内容检索 - 基于函数源代码内容的语义相似性',
            'natural': '自然语言检索 - 基于AI生成的功能描述的语义理解',
            
            # 关系型RAG类型
            'upstream': '上游函数检索 - 基于调用此函数的上游函数内容',
            'downstream': '下游函数检索 - 基于此函数调用的下游函数内容',
            
            # 专门的关系表RAG类型
            'upstream_natural': '上游自然语言关系检索 - 基于上游函数的自然语言描述',
            'downstream_natural': '下游自然语言关系检索 - 基于下游函数的自然语言描述',
            'upstream_content': '上游内容关系检索 - 基于上游函数的代码内容',
            'downstream_content': '下游内容关系检索 - 基于下游函数的代码内容',
            
            # 文件级RAG类型
            'file_content': '文件内容检索 - 基于整个文件的内容',
            'file_natural': '文件自然语言检索 - 基于文件的自然语言描述'
        }
    
    def do_planning(self):
        """执行规划处理 - 调用process_for_common_project_mode方法"""
        return self.process_for_common_project_mode() 