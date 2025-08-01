import os
import simplejson
from typing import Dict
import re
from antlr4.CommonTokenStream import CommonTokenStream
from antlr4.InputStream import InputStream as ANTLRInputStream

from .parser.SolidityLexer import SolidityLexer
from .parser.SolidityParser import SolidityParser

from .sgp_visitor import SGPVisitorOptions, SGPVisitor,SolidityInfoVisitor
from .sgp_error_listener import SGPErrorListener
from .ast_node_types import SourceUnit
from .tokens import build_token_list
from .utils import string_from_snake_to_camel_case


class ParserError(Exception):
    """
    An exception raised when the parser encounters an error.            
    """

    def __init__(self, errors) -> None:
        """
        Parameters
        ----------
        errors : List[Dict[str, Any]] - A list of errors encountered by the parser.        
        """
        super().__init__()
        error = errors[0]
        self.message = f"{error['message']} ({error['line']}:{error['column']})"
        self.errors = errors


def parse(
    input_string: str,
    options: SGPVisitorOptions = SGPVisitorOptions(),
    dump_json: bool = False,
    dump_path: str = "./out",
) -> SourceUnit:
    """
    Parse a Solidity source string into an AST.

    Parameters
    ----------
    input_string : str - The Solidity source string to parse.
    options : SGPVisitorOptions - Options to pass to the parser.
    dump_json : bool - Whether to dump the AST as a JSON file.
    dump_path : str - The path to dump the AST JSON file to.

    Returns
    -------
    SourceUnit - The root of an AST of the Solidity source string.    
    """

    input_stream = ANTLRInputStream(input_string)
    lexer = SolidityLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = SolidityParser(token_stream)

    listener = SGPErrorListener()
    lexer.removeErrorListeners()
    lexer.addErrorListener(listener)

    parser.removeErrorListeners()
    parser.addErrorListener(listener)
    source_unit = parser.sourceUnit()


    ast_builder = SGPVisitor(options)
    try:
        source_unit: SourceUnit = ast_builder.visit(source_unit)
    except Exception as e:
        raise Exception("AST was not generated")
    else:
        if source_unit is None:
            raise Exception("AST was not generated")

    # TODO: sort it out
    token_list = []
    if options.tokens:
        token_list = build_token_list(token_stream.getTokens(), options)

    if not options.errors_tolerant and listener.has_errors():
        raise ParserError(errors=listener.get_errors())

    if options.errors_tolerant and listener.has_errors():
        source_unit.errors = listener.get_errors()

    # TODO: sort it out
    if options.tokens:
        source_unit["tokens"] = token_list

    if dump_json:
        os.makedirs(dump_path, exist_ok=True)
        with open(os.path.join(dump_path, "ast.json"), "w") as f:
            s = simplejson.dumps(
                source_unit,
                default=lambda obj: {
                    string_from_snake_to_camel_case(k): v
                    for k, v in obj.__dict__.items()
                },
            )
            f.write(s)
    return source_unit

def find_tact_functions(text, filename, hash):
    regex = r"((?:init|receive|fun\s+\w+)\s*\([^)]*\)(?:\s*:\s*\w+)?\s*\{)"
    matches = re.finditer(regex, text)

    functions = []
    lines = text.split('\n')
    line_starts = {i: sum(len(line) + 1 for line in lines[:i]) for i in range(len(lines))}

    # 先收集所有函数体，构建完整的函数代码
    function_bodies = []
    for match in matches:
        brace_count = 1
        function_body_start = match.start()
        inside_braces = True

        for i in range(match.end(), len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1

            if inside_braces and brace_count == 0:
                function_body_end = i + 1
                function_bodies.append(text[function_body_start:function_body_end])
                break

    # 完整的函数代码字符串
    contract_code = "\n".join(function_bodies).strip()

    # 再次遍历匹配，创建函数定义
    for match in re.finditer(regex, text):
        start_line_number = next(i for i, pos in line_starts.items() if pos > match.start()) - 1
        function_header = match.group(1)
        
        brace_count = 1
        function_body_start = match.start()
        inside_braces = True

        for i in range(match.end(), len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1

            if inside_braces and brace_count == 0:
                function_body_end = i + 1
                end_line_number = next(i for i, pos in line_starts.items() if pos > function_body_end) - 1
                function_body = text[function_body_start:function_body_end]
                function_body_lines = function_body.count('\n') + 1
                break

        # Extract function name and handle init and receive separately
        if function_header.startswith('init'):
            func_name = 'init'
            modifier = 'init'
        elif function_header.startswith('receive'):
            func_name = 'receive'
            modifier = 'receive'
        else:
            func_name = re.search(r'fun\s+(\w+)', function_header).group(1)
            modifier = 'fun'
        
        # Extract return type if present
        return_type = None
        if ':' in function_header:
            return_type = re.search(r':\s*(\w+)', function_header).group(1)
        if func_name=="receive":
            func_name=func_name+"_"+str(start_line_number)
        functions.append({
            'type': 'FunctionDefinition',
            'name': "special_"+func_name,
            'start_line': start_line_number + 1,
            'end_line': end_line_number,
            'offset_start': 0,
            'offset_end': 0,
            'content': function_body,
            'contract_name': os.path.splitext(filename)[0],
            'contract_code': contract_code,
            'modifiers': [modifier],
            'stateMutability': None,
            'returnParameters': return_type,
            'visibility': 'public',  # Assuming all functions are public in FunC
            'node_count': function_body_lines
        })

    return functions
def find_func_functions(text, filename, hash):
    regex = r"((?:\w+|\(\))\s+\w+\s*\([^)]*\)(?:\s+\w+)*\s*\{)"
    matches = re.finditer(regex, text)

    functions = []
    lines = text.split('\n')
    line_starts = {i: sum(len(line) + 1 for line in lines[:i]) for i in range(len(lines))}

    # First, collect all function bodies to construct the complete contract code
    function_bodies = []
    for match in matches:
        brace_count = 1
        function_body_start = match.start()
        inside_braces = True

        for i in range(match.end(), len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1

            if inside_braces and brace_count == 0:
                function_body_end = i + 1
                function_bodies.append(text[function_body_start:function_body_end])
                break

    # Complete contract code string
    contract_code = "\n".join(function_bodies).strip()

    # Iterate through matches again to create function definitions
    for match in re.finditer(regex, text):
        start_line_number = next(i for i, pos in line_starts.items() if pos > match.start()) - 1
        function_header = match.group(1)
        
        brace_count = 1
        function_body_start = match.start()
        inside_braces = True

        for i in range(match.end(), len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1

            if inside_braces and brace_count == 0:
                function_body_end = i + 1
                end_line_number = next(i for i, pos in line_starts.items() if pos > function_body_end) - 1
                function_body = text[function_body_start:function_body_end]
                function_body_lines = function_body.count('\n') + 1
                break

        # Extract function name
        func_name = re.search(r'\s(\w+)\s*\(', function_header).group(1)
        
        # Extract initial modifier (if any)
        initial_modifier = re.search(r'^(\w+|\(\))', function_header).group(1)
        
        # Extract additional modifiers after the parentheses
        additional_modifiers = re.findall(r'\)\s+(\w+)', function_header)
        
        all_modifiers = [initial_modifier] if initial_modifier != '()' else []
        all_modifiers.extend(additional_modifiers)
        
        functions.append({
            'type': 'FunctionDefinition',
            'name': func_name,
            'start_line': start_line_number + 1,
            'end_line': end_line_number,
            'offset_start': 0,
            'offset_end': 0,
            'content': function_body,
            'contract_name': filename.replace('.fc', ''),
            'contract_code': contract_code,
            'modifiers': all_modifiers,
            'stateMutability': None,
            'returnParameters': None,
            'visibility': 'public',  # Assuming all functions are public in FunC
            'node_count': function_body_lines
        })

    return functions
def find_rust_functions(text, filename,hash):
    regex = r"((?:pub(?:\s*\([^)]*\))?\s+)?fn\s+\w+(?:<[^>]*>)?\s*\([^{]*\)(?:\s*->\s*[^{]*)?\s*\{)"
    matches = re.finditer(regex, text)

    # 函数列表
    functions = []

    # 将文本分割成行，用于更容易地计算行号
    lines = text.split('\n')
    line_starts = {i: sum(len(line) + 1 for line in lines[:i]) for i in range(len(lines))}

    # 先收集所有函数体，构建完整的函数代码
    function_bodies = []
    for match in matches:
        brace_count = 1
        function_body_start = match.start()
        inside_braces = True

        for i in range(match.end(), len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1

            if inside_braces and brace_count == 0:
                function_body_end = i + 1
                function_bodies.append(text[function_body_start:function_body_end])
                break

    # 完整的函数代码字符串
    contract_code = "\n".join(function_bodies).strip()

    # 再次遍历匹配，创建函数定义
    for match in re.finditer(regex, text):
        start_line_number = next(i for i, pos in line_starts.items() if pos > match.start()) - 1
        brace_count = 1
        function_body_start = match.start()
        inside_braces = True

        for i in range(match.end(), len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1

            if inside_braces and brace_count == 0:
                function_body_end = i + 1
                # Modified part starts here
                end_line_number = next((i for i, pos in line_starts.items() if pos > function_body_end), len(lines)) - 1
                # Modified part ends here
                function_body = text[function_body_start:function_body_end]
                function_body_lines = function_body.count('\n') + 1
                visibility = 'public' if 'pub' in match.group(1) else 'private'
                functions.append({
                    'type': 'FunctionDefinition',
                    'name': 'special_'+re.search(r'\bfn\s+(\w+)', match.group(1)).group(1),
                    'start_line': start_line_number + 1,
                    'end_line': end_line_number,
                    'offset_start': 0,
                    'offset_end': 0,
                    'content': function_body,
                    'contract_name': filename.replace('.rs',''),
                    'contract_code': contract_code,
                    'modifiers': [],
                    'stateMutability': None,
                    'returnParameters': None,
                    'visibility': visibility,
                    'node_count': function_body_lines
                })
                break

    return functions
def find_java_functions(text, filename, hash):
    # 匹配Java方法定义的正则表达式
    regex = r"""
        # 注解部分（支持多行注解和嵌套括号）
        (?:@[\w.]+                     # 注解名称
            (?:\s*\(                   # 开始括号
                (?:[^()]|\([^()]*\))*  # 注解参数，支持嵌套括号
            \))?                       # 结束括号
        \s*)*
        
        # 所有可能的修饰符组合
        (?:(?:public|private|protected|
            static|final|native|
            synchronized|abstract|
            transient|volatile|strictfp|
            default)\s+)*
        
        # 泛型返回类型（支持嵌套泛型）
        (?:<(?:[^<>]|<[^<>]*>)*>\s*)?
        
        # 返回类型
        (?:(?:[\w.$][\w.$]*\s*(?:\[\s*\]\s*)*)|\s*void\s+)
        
        # 方法名（排除非法情况）
        (?<!new\s)
        (?<!return\s)
        (?<!throw\s)
        (?<!super\.)
        (?<!this\.)
        (?<!\.)  # 防止匹配方法调用
        ([\w$]+)\s*
        
        # 方法的泛型参数
        (?:<(?:[^<>]|<[^<>]*>)*>\s*)?
        
        # 参数列表（支持复杂参数）
        \(\s*
        (?:
            (?:
                (?:final\s+)?              # 可选的final修饰符
                (?:[\w.$][\w.$]*\s*       # 参数类型
                    (?:<(?:[^<>]|<[^<>]*>)*>\s*)?  # 参数的泛型部分
                    (?:\[\s*\]\s*)*        # 数组标记
                    \s+[\w$]+              # 参数名
                    (?:\s*,\s*)?           # 可能的逗号
                )*
            )?
        )\s*\)
        
        # throws声明（可选）
        (?:\s*throws\s+
            (?:[\w.$][\w.$]*
                (?:\s*,\s*[\w.$][\w.$]*)*
            )?
        )?
        
        # 方法体或分号
        \s*(?:\{|;)
        
        # 负向前瞻，确保不是在catch块或其他非方法上下文中
        (?!\s*catch\b)
    """
    
    functions = []
    matches = re.finditer(regex, text, re.VERBOSE | re.MULTILINE | re.DOTALL)
    
    # 用于计算行号
    lines = text.split('\n')
    line_starts = {i: sum(len(line) + 1 for line in lines[:i]) for i in range(len(lines))}

    # 用于记录找到的所有完整函数体，供后续处理
    all_function_bodies = []
    
    for match in matches:
        match_text = match.group()
        
        # 跳过常见的误匹配情况
        if any([
            'catch' in match_text,                    # catch块
            'super.' in match_text,                   # super调用
            'this.' in match_text,                    # this调用
            '.clone()' in match_text,                 # 方法调用
            match_text.strip().startswith('return'),  # return语句
            'new ' in text[max(0, match.start()-4):match.start()], # 构造器表达式
            '=>' in match_text,                       # lambda表达式
        ]):
            continue

        # 获取方法名
        method_name = match.group(1)
        
        # 处理方法体
        if match_text.strip().endswith(';'):
            # 对于没有方法体的方法，只保留接口方法和抽象方法
            if not ('abstract' in match_text.lower() or 'interface' in text[:match.start()].lower()):
                continue
            function_body = match_text
            start_pos = match.start()
            end_pos = match.end()
            function_body_lines = 1
        else:
            # 处理有方法体的方法
            brace_count = 1
            start_pos = match.start()
            i = match.end()
            
            # 寻找匹配的结束大括号
            while i < len(text) and brace_count > 0:
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                i += 1
            
            if brace_count == 0:
                end_pos = i
                function_body = text[start_pos:end_pos]
                function_body_lines = function_body.count('\n') + 1
            else:
                continue

        # 计算行号
        start_line = sum(1 for _ in text[:start_pos].splitlines())
        end_line = sum(1 for _ in text[:end_pos].splitlines())
        
        # 确定可见性
        visibility = 'package'  # 默认包级别访问权限
        if 'public' in match_text:
            visibility = 'public'
        elif 'private' in match_text:
            visibility = 'private'
        elif 'protected' in match_text:
            visibility = 'protected'

        # 获取修饰符
        modifiers = []
        modifier_list = ['static', 'final', 'native', 'synchronized', 
                        'abstract', 'transient', 'volatile', 'strictfp']
        for modifier in modifier_list:
            if re.search(r'\b' + modifier + r'\b', match_text):
                modifiers.append(modifier)

        # 记录函数体用于后续处理
        all_function_bodies.append(function_body)
        
        # 创建函数信息对象
        function_info = {
            'type': 'FunctionDefinition',
            'name': 'special_' + method_name,
            'start_line': start_line + 1,
            'end_line': end_line,
            'offset_start': start_pos,
            'offset_end': end_pos,
            'content': function_body,
            'contract_name': filename.replace('.java', ''),
            'contract_code': '\n'.join(all_function_bodies),
            'modifiers': modifiers,
            'stateMutability': None,
            'returnParameters': None,
            'visibility': visibility,
            'node_count': function_body_lines
        }
        
        functions.append(function_info)

    return functions
def find_move_functions(text, filename, hash):
    # regex = r"((?:public\s+)?(?:entry\s+)?(?:native\s+)?(?:inline\s+)?fun\s+(?:<[^>]+>\s*)?(\w+)\s*(?:<[^>]+>)?\s*\([^)]*\)(?:\s*:\s*[^{]+)?(?:\s+acquires\s+[^{]+)?\s*\{)"
    regex = r"((?:public\s+)?(?:entry\s+)?(?:native\s+)?(?:inline\s+)?fun\s+(?:<[^>]+>\s*)?(\w+)\s*(?:<[^>]+>)?\s*\([^)]*\)(?:\s*:\s*[^{]+)?(?:\s+acquires\s+[^{]+)?\s*(?:\{|;))"
    matches = re.finditer(regex, text)

    functions = []
    lines = text.split('\n')
    line_starts = {i: sum(len(line) + 1 for line in lines[:i]) for i in range(len(lines))}

    function_bodies = []
    for match in matches:
        if match.group(1).strip().endswith(';'):  # native function
            function_bodies.append(match.group(1))
        else:
            brace_count = 1
            function_body_start = match.start()
            inside_braces = True

            for i in range(match.end(), len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1

                if inside_braces and brace_count == 0:
                    function_body_end = i + 1
                    function_bodies.append(text[function_body_start:function_body_end])
                    break

    contract_code = "\n".join(function_bodies).strip()

    for match in re.finditer(regex, text):
        start_line_number = next(i for i, pos in line_starts.items() if pos > match.start()) - 1
        
        if match.group(1).strip().endswith(';'):  # native function
            function_body = match.group(1)
            end_line_number = start_line_number
            function_body_lines = 1
        else:
            brace_count = 1
            function_body_start = match.start()
            inside_braces = True

            for i in range(match.end(), len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1

                if inside_braces and brace_count == 0:
                    function_body_end = i + 1
                    end_line_number = next(i for i, pos in line_starts.items() if pos > function_body_end) - 1
                    function_body = text[function_body_start:function_body_end]
                    function_body_lines = function_body.count('\n') + 1
                    break

        visibility = 'public' if 'public' in match.group(1) else 'private'
        is_native = 'native' in match.group(1)
        
        functions.append({
            'type': 'FunctionDefinition',
            'name':  'special_' + match.group(2),
            'start_line': start_line_number + 1,
            'end_line': end_line_number,
            'offset_start': 0,
            'offset_end': 0,
            'content': function_body,
            'header': match.group(1).strip(),  # 新增：函数头部
            'contract_name': filename.replace('.move', ''),
            'contract_code': text,
            'modifiers': ['native'] if is_native else [],
            'stateMutability': None,
            'returnParameters': None,
            'visibility': visibility,
            'node_count': function_body_lines
        })

    return functions
def find_go_functions(text, filename, hash):
    # 匹配函数名，忽略接收器和参数列表的具体内容
    regex = r"""
        func\s*                            # func关键字和空白
        (?:\([^)]*\)\s+)?                 # 忽略接收器部分
        ([A-Za-z_][A-Za-z0-9_]*)         # 函数名
        \s*\(                             # 函数参数开始
    """
    matches = re.finditer(regex, text, re.VERBOSE)

    functions = []
    lines = text.split('\n')
    line_starts = {i: sum(len(line) + 1 for line in lines[:i]) for i in range(len(lines))}

    for match in matches:
        function_body_start = match.start()
        start_line_number = next(i for i, pos in line_starts.items() if pos > function_body_start) - 1
        
        # 提取函数名
        func_name = match.group(1)
        
        # Find the end of the function body
        brace_count = 1
        function_body_end = function_body_start
        
        # 找到函数体的开始 '{'
        for i in range(match.end(), len(text)):
            if text[i] == '{':
                function_body_end = i + 1
                break
        
        # 找到匹配的结束大括号
        for i in range(function_body_end, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    function_body_end = i + 1
                    break

        end_line_number = next(i for i, pos in line_starts.items() if pos > function_body_end) - 1
        function_body = text[function_body_start:function_body_end]
        function_body_lines = function_body.count('\n') + 1
        functions.append({
            'type': 'FunctionDefinition',
            'name': 'special_'+func_name,  # 使用提取的函数名
            'start_line': start_line_number + 1,
            'end_line': end_line_number,
            'offset_start': 0,
            'offset_end': 0,
            'content': function_body,
            'contract_name': filename.replace('.go', ''),
            'contract_code': text,
            'modifiers': [],
            'stateMutability': None,
            'returnParameters': None,
            'visibility': 'public',
            'node_count': function_body_lines
        })

    return functions
def find_python_functions(text, filename, hash_value):
    # 更新后的正则表达式，使返回类型部分可选
    regex = r"def\s+(\w+)\s*\((.*?)\)(?:\s*->\s*(\w+))?\s*:"
    matches = re.finditer(regex, text)

    # 函数列表
    functions = []

    # 将文本分割成行，用于更容易地计算行号
    lines = text.split('\n')
    line_starts = {i: sum(len(line) + 1 for line in lines[:i]) for i in range(len(lines))}

    # 遍历匹配，创建函数定义
    if any(matches):  # 如果有匹配的函数定义
        for match in matches:
            start_line_number = next(i for i, pos in line_starts.items() if pos > match.start()) - 1
            indent_level = len(lines[start_line_number]) - len(lines[start_line_number].lstrip())

            # 查找函数体的结束
            end_line_number = start_line_number + 1
            while end_line_number < len(lines):
                line = lines[end_line_number]
                if line.strip() and (len(line) - len(line.lstrip()) <= indent_level):
                    break
                end_line_number += 1
            end_line_number -= 1  # Adjust to include last valid line of the function

            # 构建函数体
            function_body = '\n'.join(lines[start_line_number:end_line_number+1])
            function_body_lines = function_body.count('\n') + 1

            functions.append({
                'type': 'FunctionDefinition',
                'name': "function"+match.group(1),  # 函数名
                'start_line': start_line_number + 1,
                'end_line': end_line_number + 1,
                'offset_start': 0,
                'offset_end': 0,
                'content': function_body,
                'contract_name': filename.replace('.py', ''),
                'contract_code': text.strip(),  # 整个代码
                'modifiers': [],
                'stateMutability': None,
                'returnParameters': None,
                'visibility': 'public',
                'node_count': function_body_lines
            })
    else:  # 如果没有找到函数定义
        function_body_lines = len(lines)
        functions.append({
            'type': 'FunctionDefinition',
            'name': "function"+filename.split('.')[0]+"all",  # 使用文件名作为函数名
            'start_line': 1,
            'end_line': function_body_lines,
            'offset_start': 0,
            'offset_end': 0,
            'content': text.strip(),
            'contract_name': filename.replace('.py', ''),
            'contract_code': text.strip(),
            'modifiers': [],
            'stateMutability': None,
            'returnParameters': None,
            'visibility': 'public',
            'node_count': function_body_lines
        })

    return functions
def find_cairo_functions(text, filename,hash):
    regex = r"((?:pub(?:\s*\([^)]*\))?\s+)?fn\s+\w+(?:<[^>]*>)?\s*\([^{]*\)(?:\s*->\s*[^{]*)?\s*\{)"
    matches = re.finditer(regex, text)

    # 函数列表
    functions = []

    # 将文本分割成行，用于更容易地计算行号
    lines = text.split('\n')
    line_starts = {i: sum(len(line) + 1 for line in lines[:i]) for i in range(len(lines))}

    # 先收集所有函数体，构建完整的函数代码
    function_bodies = []
    for match in matches:
        brace_count = 1
        function_body_start = match.start()
        inside_braces = True

        for i in range(match.end(), len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1

            if inside_braces and brace_count == 0:
                function_body_end = i + 1
                function_bodies.append(text[function_body_start:function_body_end])
                break

    # 完整的函数代码字符串
    contract_code = "\n".join(function_bodies).strip()

    # 再次遍历匹配，创建函数定义
    for match in re.finditer(regex, text):
        start_line_number = next(i for i, pos in line_starts.items() if pos > match.start()) - 1
        brace_count = 1
        function_body_start = match.start()
        inside_braces = True

        for i in range(match.end(), len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1

            if inside_braces and brace_count == 0:
                function_body_end = i + 1
                end_line_number = next(i for i, pos in line_starts.items() if pos > function_body_end) - 1
                function_body = text[function_body_start:function_body_end]
                function_body_lines = function_body.count('\n') + 1
                visibility = 'public'
                functions.append({
                    'type': 'FunctionDefinition',
                    'name': 'special_'+re.search(r'\bfn\s+(\w+)', match.group(1)).group(1),  # Extract function name from match
                    'start_line': start_line_number + 1,
                    'end_line': end_line_number,
                    'offset_start': 0,
                    'offset_end': 0,
                    'content': function_body,
                    'contract_name': filename.replace('.cairo',''),
                    'contract_code': "",
                    'modifiers': [],
                    'stateMutability': None,
                    'returnParameters': None,
                    'visibility': visibility,
                    'node_count': function_body_lines
                })
                break

    return functions
def find_fa_functions(text, filename, hash):
    regex = r"function\s+(?:0x[a-fA-F0-9]+|\w+)\s*\([^{]*\)(?:\s*(?:private|public|nonPayable|payable))?\s*\{"
    matches = re.finditer(regex, text)

    functions = []
    lines = text.split('\n')
    line_starts = {i: sum(len(line) + 1 for line in lines[:i]) for i in range(len(lines))}

    # First collect all function bodies to build complete contract code
    function_bodies = []
    for match in matches:
        brace_count = 1
        function_body_start = match.start()
        inside_braces = True

        for i in range(match.end(), len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1

            if inside_braces and brace_count == 0:
                function_body_end = i + 1
                function_bodies.append(text[function_body_start:function_body_end])
                break

    # Complete contract code string
    contract_code = "\n".join(function_bodies).strip()

    # Iterate through matches again to create function definitions
    for match in re.finditer(regex, text):
        start_line_number = next(i for i, pos in line_starts.items() if pos > match.start()) - 1
        brace_count = 1
        function_body_start = match.start()
        inside_braces = True

        for i in range(match.end(), len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1

            if inside_braces and brace_count == 0:
                function_body_end = i + 1
                end_line_number = next(i for i, pos in line_starts.items() if pos > function_body_end) - 1
                function_body = text[function_body_start:function_body_end]
                function_body_lines = function_body.count('\n') + 1
                break

        # Extract function name and modifiers
        function_header = text[match.start():match.end()]
        func_name = re.search(r'function\s+(0x[a-fA-F0-9]+|\w+)', function_header).group(1)
        modifiers = []
        
        # Check for modifiers
        if 'private' in function_header:
            modifiers.append('private')
        if 'public' in function_header:
            modifiers.append('public')
        if 'payable' in function_header:
            modifiers.append('payable')
        if 'nonPayable' in function_header:
            modifiers.append('nonPayable')
        if 'external' in function_header:
            modifiers.append('external')

        functions.append({
            'type': 'FunctionDefinition',
            'name': 'special_' + func_name,
            'start_line': start_line_number + 1,
            'end_line': end_line_number,
            'offset_start': 0,
            'offset_end': 0,
            'content': function_body,
            'contract_name': filename.replace('.fr', ''),
            'contract_code': contract_code,
            'modifiers': modifiers,
            'stateMutability': None,
            'returnParameters': None,
            'visibility': 'public' if 'public' or 'external' in modifiers else 'private',
            'node_count': function_body_lines
        })

    return functions

def find_c_cpp_functions(text, filename, hash):
    # 匹配C/C++函数定义的正则表达式
    # 支持普通函数、成员函数、构造函数、析构函数、操作符重载等
    regex = r"""
        # 可选的修饰符 (static, extern, inline, constexpr, virtual, explicit等)
        (?:(?:static|extern|inline|constexpr|virtual|override|final|explicit)\s+)*
        
        # 返回类型或构造函数 (这是可选的，因为构造函数没有返回类型)
        (?:
            # 返回类型 (包含复杂模板、指针、引用等)
            (?:
                (?:const\s+|volatile\s+|unsigned\s+|signed\s+|long\s+|short\s+)*  # 类型修饰符
                (?:[\w_][\w_:]*\s*(?:<[^<>{}]*>)?\s*)                              # 基本类型名和简单模板
                (?:\s*\*|\s*&|\s*&&)*\s*                                           # 指针/引用修饰符
            )\s+
        )?
        
        # 函数名 (支持类成员函数、析构函数、操作符重载、构造函数等)
        (
            (?:[\w_]+::)+[\w_]+                                           # 类成员函数 (Class::function)
            |(?:[\w_]+::)*~[\w_]+                                         # 析构函数
            |(?:[\w_]+::)*operator\s*(?:[+\-*/%^&|~!=<>]+|\(\)|\[\]|<<|>>|->|\+=|-=|\*=|/=|%=) # 操作符重载
            |[\w_]+                                                       # 普通函数名
        )\s*
        
        # 参数列表 (支持多行)
        \([^{}]*\)\s*
        
        # 可选的C++修饰符 (const, noexcept, throw, override, final等)
        (?:const\s+|volatile\s+|noexcept\s*(?:\([^)]*\))?\s*|throw\s*\([^)]*\)\s*|override\s+|final\s+)*
        
        # 可选的初始化列表 (构造函数可能有)
        (?::\s*[^{}]+?)?\s*
        
        # 函数体开始
        \{
    """
    
    matches = re.finditer(regex, text, re.VERBOSE | re.MULTILINE)
    
    functions = []
    lines = text.split('\n')
    line_starts = {i: sum(len(line) + 1 for line in lines[:i]) for i in range(len(lines))}

    # 先收集所有函数体，构建完整的函数代码
    function_bodies = []
    for match in matches:
        match_text = match.group()
        
        # 跳过一些常见的误匹配情况
        if any([
            'if' in match_text and '(' in match_text,     # if语句
            'for' in match_text and '(' in match_text,    # for循环
            'while' in match_text and '(' in match_text,  # while循环
            'switch' in match_text and '(' in match_text, # switch语句
            'sizeof' in match_text,                        # sizeof操作符
            'typedef' in match_text,                       # typedef声明
            match_text.strip().startswith('return'),       # return语句
            '::' in match_text and '->' in match_text,     # 成员访问
        ]):
            continue
            
        brace_count = 1
        function_body_start = match.start()
        inside_braces = True

        for i in range(match.end(), len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1

            if inside_braces and brace_count == 0:
                function_body_end = i + 1
                function_bodies.append(text[function_body_start:function_body_end])
                break

    # 完整的函数代码字符串
    contract_code = "\n".join(function_bodies).strip()

    # 再次遍历匹配，创建函数定义
    for match in re.finditer(regex, text, re.VERBOSE | re.MULTILINE):
        match_text = match.group()
        
        # 跳过误匹配情况
        if any([
            'if' in match_text and '(' in match_text,
            'for' in match_text and '(' in match_text,
            'while' in match_text and '(' in match_text,
            'switch' in match_text and '(' in match_text,
            'sizeof' in match_text,
            'typedef' in match_text,
            match_text.strip().startswith('return'),
            '::' in match_text and '->' in match_text,
        ]):
            continue
            
        # 修复边界情况：如果匹配开始位置超过文件最后一行，使用最后一行
        start_line_number = next((i for i, pos in line_starts.items() if pos > match.start()), len(lines)) - 1
        
        # 获取函数名
        func_name = match.group(1)
        
        brace_count = 1
        function_body_start = match.start()
        inside_braces = True

        for i in range(match.end(), len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1

            if inside_braces and brace_count == 0:
                function_body_end = i + 1
                # 修复边界情况：如果函数体结束位置超过文件最后一行，使用最后一行
                end_line_number = next((i for i, pos in line_starts.items() if pos > function_body_end), len(lines)) - 1
                function_body = text[function_body_start:function_body_end]
                function_body_lines = function_body.count('\n') + 1
                break

        # 提取修饰符
        modifiers = []
        modifier_list = ['static', 'extern', 'inline', 'constexpr', 'virtual', 'override', 'final']
        for modifier in modifier_list:
            if re.search(r'\b' + modifier + r'\b', match_text):
                modifiers.append(modifier)

        # 确定可见性 (C/C++中没有严格的可见性概念，主要看存储类)
        visibility = 'public'  # 默认为public
        if 'static' in modifiers:
            visibility = 'private'  # static函数通常是内部链接
        elif 'extern' in modifiers:
            visibility = 'public'   # extern函数是外部链接

        functions.append({
            'type': 'FunctionDefinition',
            'name': 'special_' + func_name,  # 恢复special_前缀以保持架构一致性
            'start_line': start_line_number + 1,
            'end_line': end_line_number,
            'offset_start': 0,
            'offset_end': 0,
            'content': function_body,
            'contract_name': os.path.splitext(filename)[0],  # 更可靠的扩展名移除方法
            'contract_code': contract_code,
            'modifiers': modifiers,
            'stateMutability': None,
            'returnParameters': None,
            'visibility': visibility,
            'node_count': function_body_lines
        })

    return functions

def get_antlr_parsing(path):
    with open(path, 'r', encoding='utf-8', errors="ignore") as file:
        code = file.read()
        hash_value=hash(code)
    filename = os.path.basename(path)
    if ".rs" in str(path):
        rust_functions = find_rust_functions(code, filename,hash_value)
        return rust_functions
    if ".py" in str(path):
        python_functions = find_python_functions(code, filename,hash_value)
        return python_functions
    if ".move" in str(path):
        move_functions = find_move_functions(code, filename,hash_value)
        return move_functions
    if ".cairo" in str(path):
        cairo_functions = find_cairo_functions(code, filename,hash_value)
        return cairo_functions
    if ".tact" in str(path):
        tact_functions = find_tact_functions(code, filename,hash_value)
        return tact_functions
    if ".fc" in str(path):
        func_functions = find_func_functions(code, filename,hash_value)
        return func_functions
    if ".fr" in str(path):  # Add FA file handling
        fa_functions = find_fa_functions(code, filename,hash_value)
        return fa_functions
    if ".java" in str(path):
        java_functions = find_java_functions(code, filename,hash_value)
        return java_functions
    if ".go" in str(path):
        go_functions = find_go_functions(code, filename,hash_value)
        return go_functions
    if any(ext in str(path) for ext in [".c", ".cpp", ".cxx", ".cc", ".C"]):  # Add C/C++ file handling
        c_cpp_functions = find_c_cpp_functions(code, filename,hash_value)
        return c_cpp_functions
    else:
        input_stream = ANTLRInputStream(code)
        lexer = SolidityLexer(input_stream)
        token_stream = CommonTokenStream(lexer)
        parser = SolidityParser(token_stream)
        tree = parser.sourceUnit()

        visitor = SolidityInfoVisitor(code)
        visitor.visit(tree)

        return visitor.results



def get_antlr_ast(path):
    with open(path, 'r', encoding='utf-8', errors="ignore") as file:
        code = file.read()

    parse(code,dump_json=True,dump_path="./")
