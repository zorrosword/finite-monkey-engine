import json
import random
import csv
import sys
import os
import os.path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import List, Dict, Tuple, Optional

from dao.task_mgr import ProjectTaskMgr
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tqdm import tqdm
from dao.entity import Project_Task
from openai_api.openai import common_ask_for_json, ask_claude
from prompt_factory.core_prompt import CorePrompt
from prompt_factory.vul_prompt_common import VulPromptCommon
from prompt_factory.assumption_prompt import AssumptionPrompt
import json
from .business_flow_utils import BusinessFlowUtils
from .config_utils import ConfigUtils

# 直接使用tree_sitter_parsing而不是通过context
from tree_sitter_parsing import TreeSitterProjectAudit, parse_project, TreeSitterProjectFilter

# 复杂度分析相关导入
try:
    from tree_sitter import Language, Parser, Node
    import tree_sitter_solidity as ts_solidity
    # 尝试导入其他语言解析器
    try:
        import tree_sitter_rust as ts_rust
        RUST_AVAILABLE = True
    except ImportError:
        RUST_AVAILABLE = False
        
    try:
        import tree_sitter_cpp as ts_cpp
        CPP_AVAILABLE = True
    except ImportError:
        CPP_AVAILABLE = False
        
    try:
        import tree_sitter_move as ts_move
        MOVE_AVAILABLE = True
    except ImportError:
        MOVE_AVAILABLE = False
    
    COMPLEXITY_ANALYSIS_ENABLED = True
except ImportError:
    print("⚠️ Tree-sitter模块未安装，复杂度过滤功能将被禁用")
    COMPLEXITY_ANALYSIS_ENABLED = False
    RUST_AVAILABLE = False
    CPP_AVAILABLE = False
    MOVE_AVAILABLE = False


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
            elif func_name.endswith('.rs') or 'rs' in func.get('relative_file_path', '').lower():
                if visibility == 'pub' or visibility == 'public':
                    public_functions_by_lang['rust'].append(func)
            elif func_name.endswith('.cpp') or func_name.endswith('.c') or 'cpp' in func.get('relative_file_path', '').lower():
                if visibility == 'public' or not visibility:  # C++默认public
                    if "exec" in func_name:
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
    
    def _calculate_simple_complexity(self, function_content: str, language: str = 'solidity') -> Dict:
        """简化版复杂度计算，支持多种语言
        
        Args:
            function_content: 函数代码内容
            language: 编程语言类型 ('solidity', 'rust', 'cpp', 'move')
            
        Returns:
            Dict: 包含圈复杂度和认知复杂度的字典
        """
        if not COMPLEXITY_ANALYSIS_ENABLED or not function_content:
            return {'cyclomatic': 1, 'cognitive': 0, 'should_skip': False}
        
        try:
            # 根据语言选择相应的解析器
            parser = Parser()
            parser_language = None
            function_node_types = []
            
            if language == 'solidity':
                parser_language = Language(ts_solidity.language())
                function_node_types = ['function_definition']
            elif language == 'rust' and RUST_AVAILABLE:
                parser_language = Language(ts_rust.language())
                function_node_types = ['function_item', 'function_signature_item']
            elif language == 'cpp' and CPP_AVAILABLE:
                parser_language = Language(ts_cpp.language())
                function_node_types = ['function_definition', 'function_declarator']
            elif language == 'move' and MOVE_AVAILABLE:
                parser_language = Language(ts_move.language())
                function_node_types = ['function_definition']
            else:
                print(f"⚠️ 不支持的语言或解析器未安装: {language}")
                return {'cyclomatic': 1, 'cognitive': 0, 'should_skip': False, 'should_reduce_iterations': False}
                
            if not parser_language:
                return {'cyclomatic': 1, 'cognitive': 0, 'should_skip': False, 'should_reduce_iterations': False}
                
            parser.language = parser_language
            
            # 解析代码
            tree = parser.parse(bytes(function_content, 'utf8'))
            
            # 查找函数定义节点
            function_node = None
            for node in self._walk_tree(tree.root_node):
                if node.type in function_node_types:
                    function_node = node
                    break
            
            if not function_node:
                return {'cyclomatic': 1, 'cognitive': 0, 'should_skip': False}
            
            # 计算圈复杂度
            cyclomatic = self._calculate_cyclomatic_complexity(function_node, language)
            
            # 计算认知复杂度
            cognitive = self._calculate_cognitive_complexity(function_node, language)
            
            # 判断是否应该跳过（基于fishcake分析的最佳阈值）
            # 过滤条件：认知复杂度=0且圈复杂度≤2，或者圈复杂度=2且认知复杂度=1，或者圈复杂度=3且认知复杂度=2
            should_skip = (cognitive == 0 and cyclomatic <= 2) or (cyclomatic == 2 and cognitive == 1) or (cyclomatic == 3 and cognitive == 2) # 关键逻辑
            
            # 🎯 判断是否为中等复杂度函数（需要降低迭代次数）
            # 基于tokenURI、buyFccAmount等函数的特征分析
            should_reduce_iterations = self._should_reduce_iterations(
                cognitive, cyclomatic, function_content
            )
            
            return {
                'cyclomatic': cyclomatic,
                'cognitive': cognitive, 
                'should_skip': should_skip,
                'should_reduce_iterations': should_reduce_iterations
            }
            
        except Exception as e:
            print(f"⚠️ 复杂度计算失败: {e}")
            return {'cyclomatic': 1, 'cognitive': 0, 'should_skip': False, 'should_reduce_iterations': False}
    
    def _walk_tree(self, node):
        """遍历AST树"""
        yield node
        for child in node.children:
            yield from self._walk_tree(child)
    
    def _calculate_cyclomatic_complexity(self, function_node, language: str = 'solidity') -> int:
        """计算圈复杂度，支持多种语言"""
        complexity = 1  # 基础路径
        
        # 根据语言定义决策点节点类型
        decision_nodes = self._get_decision_node_types(language)
        
        for node in self._walk_tree(function_node):
            # 决策点
            if node.type in decision_nodes['control_flow']:
                complexity += 1
            elif node.type in decision_nodes['conditional']:  # 三元运算符
                complexity += 1
            elif node.type == 'binary_expression':
                # 检查逻辑运算符
                operator = node.child_by_field_name('operator')
                if operator:
                    operator_text = operator.text.decode('utf8')
                    if operator_text in ['&&', '||', 'and', 'or']:
                        complexity += 1
        
        return complexity
    
    def _calculate_cognitive_complexity(self, function_node, language: str = 'solidity') -> int:
        """计算认知复杂度（简化版），支持多种语言"""
        # 根据语言定义决策点节点类型
        decision_nodes = self._get_decision_node_types(language)
        
        def calculate_recursive(node, nesting_level: int = 0) -> int:
            complexity = 0
            node_type = node.type
            
            # 基础增量结构
            if node_type in decision_nodes['control_flow']:
                complexity += 1 + nesting_level
                # 递归处理子节点，增加嵌套层级
                for child in node.children:
                    complexity += calculate_recursive(child, nesting_level + 1)
            elif node_type in decision_nodes['conditional']:
                complexity += 1 + nesting_level
            elif node_type == 'binary_expression':
                operator = node.child_by_field_name('operator')
                if operator and operator.text.decode('utf8') in ['&&', '||', 'and', 'or']:
                    complexity += 1
                # 不增加嵌套层级处理逻辑运算符
                for child in node.children:
                    complexity += calculate_recursive(child, nesting_level)
            else:
                # 继续遍历子节点，不增加嵌套层级
                for child in node.children:
                    complexity += calculate_recursive(child, nesting_level)
            
            return complexity
        
        return calculate_recursive(function_node)
    
    def _get_decision_node_types(self, language: str) -> Dict[str, List[str]]:
        """获取不同语言的决策节点类型"""
        node_types = {
            'solidity': {
                'control_flow': ['if_statement', 'while_statement', 'for_statement', 'try_statement'],
                'conditional': ['conditional_expression']
            },
            'rust': {
                'control_flow': ['if_expression', 'while_expression', 'for_expression', 'loop_expression', 'match_expression'],
                'conditional': ['if_let_expression']
            },
            'cpp': {
                'control_flow': ['if_statement', 'while_statement', 'for_statement', 'do_statement', 'switch_statement'],
                'conditional': ['conditional_expression']
            },
            'move': {
                'control_flow': ['if_expression', 'while_expression', 'loop_expression'],
                'conditional': ['conditional_expression']
            }
        }
        
        return node_types.get(language, node_types['solidity'])  # 默认使用solidity的节点类型
    
    def _should_reduce_iterations(self, cognitive: int, cyclomatic: int, function_content: str) -> bool:
        """判断是否应该降低迭代次数（基于fishcake项目分析）
        
        适用于像tokenURI、buyFccAmount等中等复杂度的数据处理型函数
        
        Args:
            cognitive: 认知复杂度
            cyclomatic: 圈复杂度  
            function_content: 函数代码内容
            
        Returns:
            bool: True表示应该降低迭代次数到3-4次
        """
        # 基于fishcake项目分析的特征识别
        
        # 1. 中等复杂度范围 (不是简单函数，也不是极复杂函数)
        if not (5 <= cognitive <= 20 and 3 <= cyclomatic <= 8):
            return False
            
        # 2. 识别数据处理型函数特征
        data_processing_indicators = [
            'view' in function_content,  # view函数通常是数据查询
            'returns (' in function_content,  # 有返回值
            function_content.count('return') >= 3,  # 多个return语句(如tokenURI)
            'if(' in function_content or 'if (' in function_content,  # 有条件分支
        ]
        
        # 3. 识别简单交易型函数特征  
        simple_transaction_indicators = [
            'transfer' in function_content.lower(),  # 包含转账操作
            'external' in function_content,  # 外部可调用
            function_content.count('require') <= 3,  # 检查条件不太多
            function_content.count('if') <= 2,  # 分支不太复杂
        ]
        
        # 4. 排除复杂业务逻辑函数的特征
        complex_business_indicators = [
            'for (' in function_content or 'for(' in function_content,  # 包含循环
            'while' in function_content,  # 包含while循环
            function_content.count('if') > 5,  # 分支过多
            cognitive > 20,  # 认知复杂度过高
            'nonReentrant' in function_content and cyclomatic > 6,  # 复杂的防重入函数
        ]
        
        # 5. 函数名模式识别 (基于实际案例)
        function_name_patterns = [
            'tokenURI' in function_content,  # 类似tokenURI的函数
            'buyFcc' in function_content,  # 类似buyFcc的函数  
            'updateNft' in function_content,  # 类似updateNft的函数
            'uri(' in function_content,  # URI相关函数
        ]
        
        # 判断逻辑：
        # - 是数据处理型 OR 简单交易型
        # - 且 没有复杂业务逻辑特征
        # - 或者 匹配特定函数名模式
        
        is_data_processing = sum(data_processing_indicators) >= 2
        is_simple_transaction = sum(simple_transaction_indicators) >= 2  
        has_complex_business = any(complex_business_indicators)
        matches_pattern = any(function_name_patterns)
        
        # 决策逻辑
        should_reduce = (
            (is_data_processing or is_simple_transaction or matches_pattern) and
            not has_complex_business
        )
        
        return should_reduce
    
    def filter_functions_by_complexity(self, public_functions_by_lang: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """基于复杂度过滤函数（基于fishcake项目分析优化）
        
        过滤策略：
        - 认知复杂度 = 0 且 圈复杂度 ≤ 2 → 跳过扫描（简单函数）
        - 圈复杂度 = 2 且 认知复杂度 = 1 → 跳过扫描（简单函数）
        - 圈复杂度 = 3 且 认知复杂度 = 2 → 跳过扫描（简单函数）
        - 其他函数 → 保留扫描（复杂函数）
        
        Args:
            public_functions_by_lang: 按语言分类的函数字典
            
        Returns:
            Dict: 过滤后的函数字典
        """
        if not COMPLEXITY_ANALYSIS_ENABLED:
            print("⚠️ 复杂度分析功能未启用，跳过过滤")
            return public_functions_by_lang
        
        filtered_functions = {
            'solidity': [],
            'rust': [],
            'cpp': [],
            'move': []
        }
        
        total_original = 0
        total_filtered = 0
        skipped_functions = []
        reduced_iteration_functions = []
        
        print("\n🎯 开始基于复杂度过滤函数...")
        print("📋 过滤策略: 认知复杂度=0且圈复杂度≤2，或者圈复杂度=2且认知复杂度=1，或者圈复杂度=3且认知复杂度=2的函数将被跳过")
        
        for lang, funcs in public_functions_by_lang.items():
            if not funcs:
                continue
                
            print(f"\n📄 分析 {lang} 语言的 {len(funcs)} 个函数...")
            
            for func in funcs:
                total_original += 1
                func_name = func.get('name', 'unknown')
                func_content = func.get('content', '')
                
                # 计算复杂度
                complexity = self._calculate_simple_complexity(func_content, lang)
                
                # 判断是否跳过
                if complexity['should_skip']:
                    skipped_functions.append({
                        'name': func_name,
                        'language': lang,
                        'cyclomatic': complexity['cyclomatic'],
                        'cognitive': complexity['cognitive']
                    })
                    print(f"  ⏭️  跳过简单函数: {func_name} (圈:{complexity['cyclomatic']}, 认知:{complexity['cognitive']})")
                else:
                    # 检查是否需要降低迭代次数
                    if complexity.get('should_reduce_iterations', False):
                        func['reduced_iterations'] = True  # 标记需要降低迭代次数
                        reduced_iteration_functions.append({
                            'name': func_name,
                            'language': lang,
                            'cyclomatic': complexity['cyclomatic'],
                            'cognitive': complexity['cognitive']
                        })
                        print(f"  🔄 中等复杂函数(降低迭代): {func_name} (圈:{complexity['cyclomatic']}, 认知:{complexity['cognitive']})")
                    else:
                        print(f"  ✅ 保留复杂函数: {func_name} (圈:{complexity['cyclomatic']}, 认知:{complexity['cognitive']})")
                    
                    filtered_functions[lang].append(func)
                    total_filtered += 1
        
        # 输出过滤统计
        skip_ratio = (total_original - total_filtered) / total_original * 100 if total_original > 0 else 0
        
        print(f"\n📊 过滤完成统计:")
        print(f"  原始函数数: {total_original}")
        print(f"  过滤后函数数: {total_filtered}")
        print(f"  跳过函数数: {len(skipped_functions)}")
        print(f"  降低迭代函数数: {len(reduced_iteration_functions)}")
        print(f"  节省扫描时间: {skip_ratio:.1f}%")
        
        # 显示保留的函数分布
        print(f"\n🎯 保留扫描的函数分布:")
        for lang, funcs in filtered_functions.items():
            if funcs:
                print(f"  📋 {lang}: {len(funcs)} 个函数需要扫描")
        
        # 显示跳过的函数列表（如果不多的话）
        if len(skipped_functions) <= 10:
            print(f"\n⏭️  跳过的简单函数列表:")
            for func in skipped_functions:
                print(f"  • {func['language']}.{func['name']} (圈:{func['cyclomatic']}, 认知:{func['cognitive']})")
        elif skipped_functions:
            print(f"\n⏭️  跳过了 {len(skipped_functions)} 个简单函数 (认知复杂度=0且圈复杂度≤2，或圈复杂度=2且认知复杂度=1，或圈复杂度=3且认知复杂度=2)")
        
        # 显示降低迭代次数的函数列表
        if reduced_iteration_functions:
            print(f"\n🔄 降低迭代次数的中等复杂函数列表:")
            for func in reduced_iteration_functions:
                print(f"  • {func['language']}.{func['name']} (圈:{func['cyclomatic']}, 认知:{func['cognitive']}) → 迭代次数降低到4次")
        
        return filtered_functions
    
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
        
        # 使用新的调用树格式查找当前函数的下游函数
        for call_tree in self.call_trees:
            # 使用完整的函数名匹配，适配新的 filename.function_name 格式
            if call_tree.get('function_name') == func_name:
                relationships = call_tree.get('relationships', {})
                downstream_funcs = relationships.get('downstream', {}).get(func_name, set())
                
                for downstream_func in downstream_funcs:
                    # 找到下游函数的完整信息
                    for func in self.functions_to_check:
                        if func['name'] == downstream_func:
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
        if os.getenv("COMPLEXITY_ANALYSIS_ENABLED", "False").lower() == "true":
            public_functions_by_lang = self.filter_functions_by_complexity(public_functions_by_lang)
        
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
                    
                    # 使用call tree获取downstream内容
                    downstream_content = self.get_downstream_content_with_call_tree(func_name, max_depth)
                    
                    # 检查是否需要降低迭代次数
                    actual_iteration_count = base_iteration_count
                    if public_func.get('reduced_iterations', False):
                        actual_iteration_count = 4  # 降低到4次
                        print(f"  🔄 检测到中等复杂函数，迭代次数降低到{actual_iteration_count}次")
                    
                    # 为每个public函数创建实际迭代次数个任务
                    for iteration in range(actual_iteration_count):
                        task_data = {
                            'task_id': task_id,
                            'iteration_index': iteration + 1,
                            'language': lang,
                            'root_function': public_func,
                            'rule_key': 'PURE_SCAN',
                            'rule_list': [],  # PURE_SCAN模式下无checklist
                            'downstream_content': downstream_content,
                            'max_depth': max_depth,
                            'task_type': 'public_function_pure_scan'
                        }
                        
                        tasks.append(task_data)
                        task_id += 1
                        
                        print(f"    ✅ 创建任务: PURE_SCAN - 迭代{iteration + 1}/{actual_iteration_count}")
        
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
                    
                    # 使用call tree获取downstream内容
                    downstream_content = self.get_downstream_content_with_call_tree(func_name, max_depth)

                    # 加上root func 的content
                    downstream_content = public_func['content'] + '\n\n' + downstream_content
                    
                    # 检查是否需要降低迭代次数
                    actual_iteration_count = base_iteration_count
                    if public_func.get('reduced_iterations', False):
                        actual_iteration_count = 4  # 降低到4次
                        print(f"  🔄 检测到中等复杂函数，迭代次数降低到{actual_iteration_count}次")
                    
                    # 为每个检查类型创建实际迭代次数个任务
                    for rule_key, rule_list in all_checklists.items():
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
                                'task_type': 'public_function_checklist_scan'
                            }
                            
                            tasks.append(task_data)
                            task_id += 1
                        
        if os.getenv("SCAN_MODE_AVA", "False").lower() == "true":
            #==========新的检测模式AVA(Assumption Violation Analysis)==========
            #在这个模式下会进行代码假设评估，并根据假设生成checklist，然后放入task后进行扫描
            print("🎯 AVA模式: 进行代码假设评估checklist生成")
            # 输入待测代码，输出checklist，对应的rule key叫做 assumption_violation
            # 然后根据checklist生成task，放入task
            
            # 使用多线程处理函数分析
            self._process_ava_mode_with_threading(public_functions_by_lang, max_depth, tasks, task_id)


        
        print(f"\n🎉 任务创建完成！")
        print(f"  总计: {len(tasks)} 个任务")
        print(f"  扫描模式: {scan_mode}")
        print(f"  基础迭代次数: {base_iteration_count}")
        print(f"  最大深度: {max_depth}")
        
        return tasks
    
    def get_downstream_content_with_call_tree(self, func_name: str, max_depth: int = 5) -> str:
        """使用call tree获取函数的downstream内容（使用统一的提取逻辑）
        
        Args:
            func_name: 函数名
            max_depth: 最大深度
            
        Returns:
            str: 拼接的downstream内容
        """
        if hasattr(self.project_audit, 'call_trees') and self.project_audit.call_trees:
            try:
                from tree_sitter_parsing.advanced_call_tree_builder import AdvancedCallTreeBuilder
                builder = AdvancedCallTreeBuilder()
                # 使用统一的内容提取方法
                return builder.get_call_content_with_direction(
                    self.project_audit.call_trees, func_name, 'downstream', max_depth
                )
            except Exception as e:
                print(f"    ⚠️ 使用统一call tree提取失败: {e}，使用简化方法")
                contents = self._get_downstream_content_fallback(func_name, max_depth)
                return '\n\n'.join(contents)
        else:
            contents = self._get_downstream_content_fallback(func_name, max_depth)
            return '\n\n'.join(contents)
    
    def get_upstream_content_with_call_tree(self, func_name: str, max_depth: int = 5) -> str:
        """使用call tree获取函数的upstream内容（使用统一的提取逻辑）
        
        Args:
            func_name: 函数名
            max_depth: 最大深度
            
        Returns:
            str: 拼接的upstream内容
        """
        if hasattr(self.project_audit, 'call_trees') and self.project_audit.call_trees:
            try:
                from tree_sitter_parsing.advanced_call_tree_builder import AdvancedCallTreeBuilder
                builder = AdvancedCallTreeBuilder()
                # 使用统一的内容提取方法
                return builder.get_call_content_with_direction(
                    self.project_audit.call_trees, func_name, 'upstream', max_depth
                )
            except Exception as e:
                print(f"    ⚠️ 使用统一call tree提取upstream失败: {e}")
                return ""
        else:
            return ""
    
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
        
        # 🎯 基于复杂度过滤函数（基于fishcake项目分析优化）
        # 过滤策略：认知复杂度=0 且 圈复杂度≤2 的简单函数将被跳过
        public_functions_by_lang = self.filter_functions_by_complexity(public_functions_by_lang)
        
        tasks = []
        task_id = 0
        
        for lang, public_funcs in public_functions_by_lang.items():
            if not public_funcs:
                continue
                
            print(f"\n📋 处理 {lang} 语言的 {len(public_funcs)} 个public函数...")
            
            for public_func in public_funcs:
                func_name = public_func['name']
                
                # print(f"  🔍 分析public函数: {func_name}")
                
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
            result = ask_claude(assumption_prompt)
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

    def do_planning(self):
        """执行规划处理 - 调用process_for_common_project_mode方法"""
        return self.process_for_common_project_mode()
    
    def _process_ava_mode_with_threading(self, public_functions_by_lang: Dict, max_depth: int, tasks: List, task_id: int):
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
                downstream_content = self.get_downstream_content_with_call_tree(func_name, max_depth)
                
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
                            'task_type': 'public_function_checklist_scan'
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