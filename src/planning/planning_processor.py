import json
import random
import csv
import sys
import os
import os.path
import uuid
from typing import List, Dict, Tuple, Optional

from dao.task_mgr import ProjectTaskMgr
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dao.entity import Project_Task
from openai_api.openai import extract_structured_json
from prompt_factory.core_prompt import CorePrompt
from prompt_factory.vul_prompt_common import VulPromptCommon
import json
from .business_flow_utils import BusinessFlowUtils
from .config_utils import ConfigUtils
from .complexity import complexity_calculator, COMPLEXITY_ANALYSIS_ENABLED
from .call_tree_utils import CallTreeUtils
from .assumption_validation import AssumptionValidator

# 直接使用tree_sitter_parsing而不是通过context
from tree_sitter_parsing import TreeSitterProjectAudit, parse_project, TreeSitterProjectFilter


class PlanningProcessor:
    """规划处理器，负责基于public函数downstream深度扫描的新planning逻辑"""
    
    def __init__(self, project_audit: TreeSitterProjectAudit, taskmgr: ProjectTaskMgr):
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
        
        # 初始化调用树工具
        self.call_tree_utils = CallTreeUtils(project_audit)
        
        # 初始化假设验证器
        self.assumption_validator = AssumptionValidator(self.call_tree_utils)
        
        # RAG功能（可选，如果需要的话）
        self.rag_processor = None
    
    def initialize_rag_processor(self, lancedb_path, project_id):
        """初始化RAG处理器（可选功能）"""
        try:
            from context.rag_processor import RAGProcessor
            # 正确传递参数：project_audit作为第一个参数
            self.rag_processor = RAGProcessor(self.project_audit, lancedb_path, project_id)
            print("✅ RAG处理器初始化完成")
            print(f"📊 基于 {len(self.functions_to_check)} 个tree-sitter解析的函数构建RAG")
            call_trees = getattr(self.project_audit, 'call_trees', [])
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
            elif func_name.endswith('.rs') or 'rs' in func.get('relative_file_path', '').lower():
                if visibility == 'pub' or visibility == 'public':
                    public_functions_by_lang['rust'].append(func)
            elif func_name.endswith('.cpp') or func_name.endswith('.c') or 'cpp' in func.get('relative_file_path', '').lower():
                if visibility == 'public' or not visibility:  # C++默认public
                    if "exec" in func_name:
                        public_functions_by_lang['cpp'].append(func)
            elif 'move' in func.get('relative_file_path', '').lower():
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
            # scan_record将在validation中赋值
            
            # 创建 Project_Task实例（UUID将自动生成）
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
                business_flow_code=business_flow_code,
                group=task.get('group', '')  # 任务组UUID
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


    def create_public_function_tasks_v3(self, max_depth: int = 5) -> List[Dict]:
        """为每个public函数创建新版任务（V3版本）
        使用call tree获取downstream内容，根据base_iteration_count创建多个任务
        
        根据scan_mode的不同：
        - PURE_SCAN: 忽略checklist，为每个public函数创建 base_iteration_count 个任务
        - 其他模式: 为每个public函数 + 每个rule_key 创建 base_iteration_count 个任务
        
        Args:
            max_depth: 最大深度限制
            
        Returns:
            List[Dict]: 任务列表，每个任务都有唯一的UUID
        """
        print("🚀 开始创建新版任务（V3）...")
        
        # 获取扫描配置
        scan_config = ConfigUtils.get_scan_configuration()
        scan_mode = scan_config['scan_mode']
        base_iteration_count = scan_config['base_iteration_count']
        
        print(f"📋 扫描模式: {scan_mode}")
        print(f"🔄 基础迭代次数: {base_iteration_count}")
        
        # 获取所有public函数
        public_functions_by_lang = self.find_public_functions_by_language()
        
        # 🎯 基于复杂度过滤函数（基于fishcake项目分析优化）
        # 过滤策略：认知复杂度=0 且 圈复杂度≤2 的简单函数将被跳过
        if COMPLEXITY_ANALYSIS_ENABLED:
            public_functions_by_lang = complexity_calculator.filter_functions_by_complexity(public_functions_by_lang)
        
        tasks = []
        task_id = 0
        
        # 根据scan_mode决定任务创建逻辑
        if scan_mode == 'PURE_SCAN':
            print("🎯 PURE_SCAN模式: 忽略所有checklist")
            
            for lang, public_funcs in public_functions_by_lang.items():
                if not public_funcs:
                    continue
                    
                print(f"\n📋 处理 {lang} 语言的 {len(public_funcs)} 个public函数...")
                
                for public_func in public_funcs:
                    func_name = public_func['name']                    
                    # print(f"  🔍 分析public函数: {func_name}")
                    
                    if "test" in str(func_name).lower():
                        print("发现测试函数，跳过")
                        continue

                    # 使用call tree获取downstream内容
                    downstream_content = self.call_tree_utils.get_downstream_content_with_call_tree(func_name, max_depth)
                    
                    # 检查是否需要降低迭代次数
                    actual_iteration_count = base_iteration_count
                    if public_func.get('reduced_iterations', False):
                        actual_iteration_count = 4  # 降低到4次
                        print(f"  🔄 检测到中等复杂函数，迭代次数降低到{actual_iteration_count}次")
                    
                    # 为每个public函数创建实际迭代次数个任务
                    for iteration in range(actual_iteration_count):
                        # 为每个iteration生成一个group UUID
                        group_uuid = str(uuid.uuid4())
                        
                        task_data = {
                            'task_id': task_id,
                            'iteration_index': iteration + 1,
                            'language': lang,
                            'root_function': public_func,
                            'rule_key': 'PURE_SCAN',
                            'rule_list': [],  # PURE_SCAN模式下无checklist
                            'downstream_content': downstream_content,
                            'max_depth': max_depth,
                            'task_type': 'public_function_pure_scan',
                            'group': group_uuid  # 为每个iteration分配一个group UUID
                        }
                        
                        tasks.append(task_data)
                        task_id += 1
                        
                        print(f"    ✅ 创建任务: PURE_SCAN - 迭代{iteration + 1}/{actual_iteration_count} (Group: {group_uuid[:8]}...)")
        
        else:
            # 非PURE_SCAN模式：使用checklist
            print(f"📄 标准模式: 使用checklist")
            
            # 获取所有检查规则
            all_checklists = VulPromptCommon.vul_prompt_common_new()
            
            for lang, public_funcs in public_functions_by_lang.items():
                if not public_funcs:
                    continue
                    
                print(f"\n📋 处理 {lang} 语言的 {len(public_funcs)} 个public函数...")
                
                for public_func in public_funcs:
                    func_name = public_func['name']
                    
                    # print(f"  🔍 分析public函数: {func_name}")
                    if "test" in str(func_name).lower():
                        print("发现测试函数，跳过")
                        continue

                    
                    # 使用call tree获取downstream内容
                    downstream_content = self.call_tree_utils.get_downstream_content_with_call_tree(func_name, max_depth)

                    # 加上root func 的content
                    downstream_content = public_func['content'] + '\n\n' + downstream_content
                    
                    # 检查是否需要降低迭代次数
                    actual_iteration_count = base_iteration_count
                    if public_func.get('reduced_iterations', False):
                        actual_iteration_count = 4  # 降低到4次
                        print(f"  🔄 检测到中等复杂函数，迭代次数降低到{actual_iteration_count}次")
                    
                    # 为每个检查类型创建实际迭代次数个任务
                    for rule_key, rule_list in all_checklists.items():
                        # 为每个rule_key, rule_list组合生成一个group UUID
                        group_uuid = str(uuid.uuid4())
                        
                        for iteration in range(actual_iteration_count):
                            task_data = {
                                'task_id': task_id,
                                'iteration_index': iteration + 1,
                                'language': lang,
                                'root_function': public_func,
                                'rule_key': rule_key,
                                'rule_list': rule_list,
                                'downstream_content': downstream_content,
                                'max_depth': max_depth,
                                'task_type': 'public_function_checklist_scan',
                                'group': group_uuid  # 为每个rule_key, rule_list组合分配一个group UUID
                            }
                            
                            tasks.append(task_data)
                            task_id += 1
                        
                        print(f"    ✅ 创建任务组: {rule_key} - {actual_iteration_count}个迭代 (Group: {group_uuid[:8]}...)")
                        
        if os.getenv("SCAN_MODE_AVA", "False").lower() == "true":
            #==========新的检测模式AVA(Assumption Violation Analysis)==========
            #在这个模式下会进行代码假设评估，并根据假设生成checklist，然后放入task后进行扫描
            print("🎯 AVA模式: 进行代码假设评估checklist生成")
            # 输入待测代码，输出checklist，对应的rule key叫做 assumption_violation
            # 然后根据checklist生成task，放入task
            
            # 使用多线程处理函数分析
            self.assumption_validator.process_ava_mode_with_threading(public_functions_by_lang, max_depth, tasks, task_id)


        
        print(f"\n🎉 任务创建完成！")
        print(f"  总计: {len(tasks)} 个任务")
        print(f"  扫描模式: {scan_mode}")
        print(f"  基础迭代次数: {base_iteration_count}")
        print(f"  最大深度: {max_depth}")
        
        return tasks
    
    
        

    

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
    
    

    def do_planning(self):
        """执行规划处理 - 调用process_for_common_project_mode方法"""
        return self.process_for_common_project_mode()
    