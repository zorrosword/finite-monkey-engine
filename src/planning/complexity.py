"""
复杂度计算模块

提供代码复杂度计算功能，包括：
- 圈复杂度（Cyclomatic Complexity）计算
- 认知复杂度（Cognitive Complexity）计算
- 基于复杂度的函数过滤
- 多语言支持（Solidity, Rust, C++, Move）
"""

from typing import Dict, List
import json

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


class ComplexityCalculator:
    """复杂度计算器类"""
    
    def __init__(self):
        """初始化复杂度计算器"""
        pass
    
    def calculate_simple_complexity(self, function_content: str, language: str = 'solidity') -> Dict:
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
            elif node.type in ['binary_expression', 'bin_op_expr']:
                # 检查逻辑运算符
                operator = node.child_by_field_name('operator')
                if operator:
                    operator_text = operator.text.decode('utf8')
                    if operator_text in ['&&', '||', 'and', 'or']:
                        complexity += 1
                else:
                    # Move语言中可能需要遍历子节点寻找操作符
                    for child in node.children:
                        if child.type == 'binary_operator':
                            operator_text = child.text.decode('utf8')
                            if operator_text in ['&&', '||', 'and', 'or']:
                                complexity += 1
                                break
        
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
            elif node_type in ['binary_expression', 'bin_op_expr']:
                operator = node.child_by_field_name('operator')
                if operator and operator.text.decode('utf8') in ['&&', '||', 'and', 'or']:
                    complexity += 1
                else:
                    # Move语言中可能需要遍历子节点寻找操作符
                    for child in node.children:
                        if child.type == 'binary_operator':
                            operator_text = child.text.decode('utf8')
                            if operator_text in ['&&', '||', 'and', 'or']:
                                complexity += 1
                                break
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
                'control_flow': ['if_expr', 'while_expr', 'for_expr', 'loop_expr', 'match_expr'],
                'conditional': []
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
        - 函数内容长度 < 200 → 跳过扫描（短函数）
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
        print("📋 过滤策略: 认知复杂度=0且圈复杂度≤2，或者圈复杂度=2且认知复杂度=1，或者圈复杂度=3且认知复杂度=2，或者函数内容长度<200的函数将被跳过")
        
        for lang, funcs in public_functions_by_lang.items():
            if not funcs:
                continue
                
            print(f"\n📄 分析 {lang} 语言的 {len(funcs)} 个函数...")
            
            for func in funcs:
                total_original += 1
                func_name = func.get('name', 'unknown')
                func_content = func.get('content', '')
                
                # 计算复杂度
                complexity = self.calculate_simple_complexity(func_content, lang)
                
                # 判断是否跳过 - 添加内容长度过滤
                content_length = len(func_content)
                should_skip_by_length = content_length < 200
                
                if complexity['should_skip'] or should_skip_by_length:
                    skip_reason = []
                    if complexity['should_skip']:
                        skip_reason.append(f"圈:{complexity['cyclomatic']}, 认知:{complexity['cognitive']}")
                    if should_skip_by_length:
                        skip_reason.append(f"长度:{content_length}<200")
                    
                    skipped_functions.append({
                        'name': func_name,
                        'language': lang,
                        'cyclomatic': complexity['cyclomatic'],
                        'cognitive': complexity['cognitive'],
                        'content_length': content_length
                    })
                    print(f"  ⏭️  跳过函数: {func_name} ({', '.join(skip_reason)})")
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
                        print(f"  ✅ 保留复杂函数: {func_name} (圈:{complexity['cyclomatic']}, 认知:{complexity['cognitive']}),函数长度：{len(func_content)}")
                    
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
                print(f"  • {func['language']}.{func['name']} (圈:{func['cyclomatic']}, 认知:{func['cognitive']}, 长度:{func['content_length']})")
        elif skipped_functions:
            print(f"\n⏭️  跳过了 {len(skipped_functions)} 个简单函数 (认知复杂度=0且圈复杂度≤2，或圈复杂度=2且认知复杂度=1，或圈复杂度=3且认知复杂度=2，或函数内容长度<200)")
        
        # 显示降低迭代次数的函数列表
        if reduced_iteration_functions:
            print(f"\n🔄 降低迭代次数的中等复杂函数列表:")
            for func in reduced_iteration_functions:
                print(f"  • {func['language']}.{func['name']} (圈:{func['cyclomatic']}, 认知:{func['cognitive']}) → 迭代次数降低到4次")
        
        return filtered_functions


# 创建全局实例供外部使用
complexity_calculator = ComplexityCalculator()

# 导出便捷函数
def calculate_simple_complexity(function_content: str, language: str = 'solidity') -> Dict:
    """计算函数复杂度的便捷函数"""
    return complexity_calculator.calculate_simple_complexity(function_content, language)

def filter_functions_by_complexity(public_functions_by_lang: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """基于复杂度过滤函数的便捷函数"""
    return complexity_calculator.filter_functions_by_complexity(public_functions_by_lang)
