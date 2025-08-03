import json
import os
import re
import numpy as np
import requests
from openai import OpenAI

# 全局模型配置缓存
_model_config = None

def get_model(model_key: str) -> str:
    """直接从JSON读取模型名称"""
    global _model_config
    if _model_config is None:
        config_path = os.path.join(os.path.dirname(__file__), 'model_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                _model_config = json.load(f)
        except:
            _model_config = {}
    
    return _model_config.get(model_key, 'gpt-4o-mini')

class JSONExtractError(Exception):
    def __init__(self, ErrorInfo):
        super().__init__(self)
        self.errorinfo=ErrorInfo
    def __str__(self):
        return self.errorinfo

def azure_openai(prompt):
    # Azure OpenAI配置
    api_key = os.environ.get('AZURE_API_KEY')
    api_base = os.environ.get('AZURE_API_BASE')
    api_version = os.environ.get('AZURE_API_VERSION')
    deployment_name = os.environ.get('AZURE_DEPLOYMENT_NAME')
    # 构建URL
    url = f"{api_base}openai/deployments/{deployment_name}/chat/completions?api-version={api_version}"
    # 设置请求头
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    # 设置请求体
    data = {
        "messages": [
            {"role": "system", "content": "你是一个熟悉智能合约与区块链安全的安全专家。"},
            {"role": "user", "content": prompt}
        ],
        # "max_tokens": 150
    }
    try:
        # 发送POST请求
        response = requests.post(url, headers=headers, json=data)
        # 检查响应状态
        response.raise_for_status()
        # 解析JSON响应
        result = response.json()
        # 打印响应
        return result['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print("Azure OpenAI测试失败。错误:", str(e))
        return None
    

def azure_openai_json(prompt):
    # Azure OpenAI配置
    api_key = os.environ.get('AZURE_API_KEY')
    api_base = os.environ.get('AZURE_API_BASE')
    api_version = os.environ.get('AZURE_API_VERSION')
    deployment_name = os.environ.get('AZURE_DEPLOYMENT_NAME')
    # 构建URL
    url = f"{api_base}openai/deployments/{deployment_name}/chat/completions?api-version={api_version}"
    # 设置请求头
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    # 设置请求体
    data = {
        "response_format": { "type": "json_object" },
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant designed to output JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    try:
        # 发送POST请求
        response = requests.post(url, headers=headers, json=data)
        # 检查响应状态
        response.raise_for_status()
        # 解析JSON响应
        result = response.json()
        # 打印响应
        return result['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print("Azure OpenAI测试失败。错误:", str(e))
        return None

    
def ask_openai_common(prompt):
        api_base = os.environ.get('OPENAI_API_BASE', 'api.openai.com')  # Replace with your actual OpenAI API base URL
        api_key = os.environ.get('OPENAI_API_KEY')  # Replace with your actual OpenAI API key
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": get_model('openai_general'),  # 使用模型管理器获取OpenAI模型
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        response = requests.post(f'https://{api_base}/v1/chat/completions', headers=headers, json=data)
        try:
            response_josn = response.json()
        except Exception as e:
            return ''
        if 'choices' not in response_josn:
            return ''
        return response_josn['choices'][0]['message']['content']
def ask_openai_for_json(prompt):
    api_base = os.environ.get('OPENAI_API_BASE', 'api.openai.com')  # Replace with your actual OpenAI API base URL
    api_key = os.environ.get('OPENAI_API_KEY')  # Replace with your actual OpenAI API key
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": get_model('ask_json'),
        "response_format": { "type": "json_object" },
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant designed to output JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    # response = requests.post(f'https://{api_base}/v1/chat/completions', headers=headers, json=data)
    # # if response.status_code != 200:
    # #     print(response.text)
    
    # response_josn = response.json()
    # if 'choices' not in response_josn:
    #     return ''
    # # print(response_josn['choices'][0]['message']['content'])
    # return response_josn['choices'][0]['message']['content']
    while True:
        try:
            response = requests.post(f'https://{api_base}/v1/chat/completions', headers=headers, json=data)
            response_json = response.json()
            if 'choices' not in response_json:
                return ''
            response_content = response_json['choices'][0]['message']['content']
            if "```json" in response_content:
                try:
                    cleaned_json = extract_json_string(response_content)
                    break
                except JSONExtractError as e:
                    print(e)
                    print("===Error in extracting json. Retry request===")
                    continue
            else:
                try:
                    decoded_content = json.loads(response_content)
                    if isinstance(decoded_content, dict):
                        cleaned_json = response_content
                        break
                    else:
                        print("===Unexpected JSON format. Retry request===")
                        print(response_content)
                        continue
                except json.JSONDecodeError as e:
                    print("===Error in decoding JSON. Retry request===")
                    continue
                except Exception as e:
                    print("===Unexpected error. Retry request===")
                    print(e)
                    continue
        except Exception as e:
            print("===Error in requesting LLM. Retry request===")
    return cleaned_json

def extract_json_string(response):
    json_pattern = re.compile(r'```json(.*?)```', re.DOTALL)
    response = response.strip()
    extracted_json = re.findall(json_pattern, response)
    if len(extracted_json) > 1:
        print("[DEBUG]⚠️Error json string:")
        print(response)
        raise JSONExtractError("⚠️Return JSON format error: More than one JSON format found")
    elif len(extracted_json) == 0:
        print("[DEBUG]⚠️Error json string:")
        print(response)
        raise JSONExtractError("⚠️Return JSON format error: No JSON format found")
    else:
        cleaned_json = extracted_json[0]
        data_json = json.loads(cleaned_json)
        if isinstance(data_json, dict):
            return cleaned_json
        else:
            print("[DEBUG]⚠️Error json string:")
            print(response)
            raise JSONExtractError("⚠️Return JSON format error: input format is not a JSON")

def common_ask_for_json(prompt):
    return ask_openai_for_json(prompt)
def ask_vul(prompt):
    model = get_model('vulnerability_detection')
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"vul API调用失败。错误: {str(e)}")
        return ""
def ask_claude(prompt):
    model = get_model('claude_general')
    api_key = os.environ.get('OPENAI_API_KEY','sk-0fzQWrcTc0DASaFT7Q0V0e7c24ZyHMKYgIDpXWrry8XHQAcj')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"Claude API调用失败。错误: {str(e)}")
        return ""
def ask_claude_37(prompt):
    model = 'claude-3-7-sonnet-20250219'
    # print("prompt:",prompt)
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    # print("api_base:",api_base)
    # print("api_key:",api_key)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"claude3.7 API调用失败。错误: {str(e)}")
        return ""
def ask_deepseek(prompt):
    model = 'deepseek-reasoner'
    # print("prompt:",prompt)
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    # print("api_base:",api_base)
    # print("api_key:",api_key)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"wokaai deepseek API调用失败。错误: {str(e)}")
        return ""
def cut_reasoning_content(input):
    if "</think>" not in input:
        print("No </think> tag found in input")
        return input
    return input.split("</think>")[1]

def ask_o3_mini_json(prompt):
    model = 'o3-mini'
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'response_format': { "type": "json_object" },
        'messages': [
            {
                'role': 'system',
                'content': 'You are a helpful assistant designed to output JSON.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"wokaai o3-mini API调用失败。错误: {str(e)}")
        return ""
def ask_grok3_deepsearch(prompt):
    model = 'grok-3-deepsearch'
    # print("prompt:",prompt)
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    # print("api_base:",api_base)
    # print("api_key:",api_key)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"wokaai deepseek API调用失败。错误: {str(e)}")
        return ""
def ask_o4_mini(prompt):
    model = 'o4-mini'
    # print("prompt:",prompt)
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    # print("api_base:",api_base)
    # print("api_key:",api_key)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"wokaai deepseek API调用失败。错误: {str(e)}")
        return ""
def ask_o3_mini(prompt):
    model = 'o3-mini'
    # print("prompt:",prompt)
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    # print("api_base:",api_base)
    # print("api_key:",api_key)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"wokaai deepseek API调用失败。错误: {str(e)}")
        return ""
def common_ask(prompt):
    model_type = os.environ.get('AZURE_OR_OPENAI', 'CLAUDE')
    if model_type == 'AZURE':
        return azure_openai(prompt)
    elif model_type == 'CLAUDE':
        return ask_claude(prompt)
    elif model_type == 'DEEPSEEK':
        return ask_deepseek(prompt)
    else:
        return ask_openai_common(prompt)

def clean_text(text: str) -> str:
    return str(text).replace(" ", "").replace("\n", "").replace("\r", "")

def common_get_embedding(text: str):
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    api_base = os.getenv('OPENAI_API_BASE', 'api.openai.com')
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    cleaned_text = clean_text(text)
    
    data = {
        "input": cleaned_text,
        "model": model,
        "encoding_format": "float"
    }

    try:
        response = requests.post(f'https://{api_base}/v1/embeddings', json=data, headers=headers)
        response.raise_for_status()
        embedding_data = response.json()
        return embedding_data['data'][0]['embedding']
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return list(np.zeros(3072))  # 返回长度为3072的全0数组

def common_ask_confirmation(prompt):
    model_type = get_model('confirmation')
    if model_type == 'CLAUDE':
        return ask_claude(prompt)
    elif model_type == 'DEEPSEEK':
        return ask_deepseek(prompt)
    else:
        return ask_openai_common(prompt)

def ask_claude_for_code_analysis(prompt):
    """专门用于代码分析和总结的Claude函数"""
    model = get_model('claude_code_analysis')  # 使用代码分析专用Claude模型
    api_key = os.environ.get('OPENAI_API_KEY', 'sk-4GquOBLR9GFUHXsUMcZXTXnEY53h2hUjAbc8bONO0k3xCr87')
    api_base = os.environ.get('OPENAI_API_BASE', 'api.openai-proxy.org')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': f'你是一个专业的代码架构分析师。请分析以下代码：\n\n{prompt}'
            }
        ],
        'max_tokens': 4096,  # 设置合理的token限制
        'temperature': 0.3   # 降低随机性，提高分析的一致性
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"Claude代码分析API调用失败。错误: {str(e)}")
        return ""

def ask_claude_for_mermaid_generation(prompt):
    """专门用于生成Mermaid图的Claude函数"""
    model = get_model('claude_mermaid_generation')
    api_key = os.environ.get('OPENAI_API_KEY', 'sk-4GquOBLR9GFUHXsUMcZXTXnEY53h2hUjAbc8bONO0k3xCr87')
    api_base = os.environ.get('OPENAI_API_BASE', 'api.openai-proxy.org')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'system',
                'content': '你是一个专业的代码可视化专家，擅长将代码架构转换为清晰的Mermaid图表。'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'max_tokens': 4096,
        'temperature': 0.2   # 更低的随机性，确保Mermaid语法准确
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"Claude Mermaid生成API调用失败。错误: {str(e)}")
        return ""

def ask_claude_for_batch_analysis(files_content, analysis_type="overview"):
    """批量分析多个文件的关系"""
    model = get_model('claude_batch_analysis')
    api_key = os.environ.get('OPENAI_API_KEY', 'sk-4GquOBLR9GFUHXsUMcZXTXnEY53h2hUjAbc8bONO0k3xCr87')
    api_base = os.environ.get('OPENAI_API_BASE', 'api.openai-proxy.org')
    
    # 根据分析类型调整系统提示
    system_prompts = {
        "overview": "分析文件间的高层架构关系，关注模块和组件的整体结构",
        "detailed": "深入分析文件内部的函数、类和方法之间的详细关系",
        "dependencies": "专注分析文件间的依赖关系、导入关系和调用关系",
        "data_flow": "分析数据在不同文件和组件间的流动和传递关系"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'system',
                'content': f'''你是一个专业的代码架构分析师。当前分析类型：{analysis_type}
{system_prompts.get(analysis_type, system_prompts["overview"])}

请分析提供的代码文件并：
1. 识别主要的模块和组件
2. 理解文件间的关系和依赖
3. 发现重要的设计模式和架构决策
4. 生成清晰的关系描述'''
            },
            {
                'role': 'user',
                'content': files_content
            }
        ],
        'max_tokens': 4096,
        'temperature': 0.3
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"Claude批量分析API调用失败。错误: {str(e)}")
        return ""


# ========== 漏洞检测多轮分析专用函数 ==========

def ask_agent_initial_analysis(prompt):
    """
    代理初始分析 - 执行初步漏洞检测分析
    环境变量: AGENT_INITIAL_MODEL (默认: claude-3-haiku-20240307)
    """
    model = get_model('agent_initial_analysis')
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"代理初始分析API调用失败。错误: {str(e)}")
        return ""


def ask_agent_json_extraction(prompt):
    """
    代理JSON提取 - 从自然语言中提取结构化JSON
    环境变量: AGENT_JSON_MODEL (默认: gpt-4o-mini)
    """
    model = get_model('agent_json_extraction')
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"代理JSON提取API调用失败。错误: {str(e)}")
        return ""


def ask_agent_info_query(prompt):
    """
    代理信息查询 - 确定需要什么类型的额外信息
    环境变量: AGENT_INFO_QUERY_MODEL (默认: claude-3-sonnet-20240229)
    """
    model = get_model('agent_info_query')
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"代理信息查询API调用失败。错误: {str(e)}")
        return ""


def ask_agent_info_extraction(prompt):
    """
    代理信息提取 - 从自然语言中提取信息类型和查询内容
    环境变量: AGENT_INFO_EXTRACT_MODEL (默认: gpt-4o-mini)
    """
    model = get_model('agent_info_extraction')
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"代理信息提取API调用失败。错误: {str(e)}")
        return ""


def ask_agent_final_analysis(prompt):
    """
    代理最终分析 - 基于所有收集的信息做最终判断
    环境变量: AGENT_FINAL_MODEL (默认: claude-opus-4-20250514)
    """
    model = get_model('agent_final_analysis')
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', '4.0.wokaai.com')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        response = requests.post(f'https://{api_base}/v1/chat/completions', 
                               headers=headers, 
                               json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return ""
    except requests.exceptions.RequestException as e:
        print(f"代理最终分析API调用失败。错误: {str(e)}")
        return ""



