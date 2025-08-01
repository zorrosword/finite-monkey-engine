#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的模型配置管理器
"""

import json
import os

# 全局配置缓存
_config = None

def _load_config():
    """加载配置文件"""
    global _config
    if _config is not None:
        return _config
    
    config_path = os.path.join(os.path.dirname(__file__), 'model_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            _config = json.load(f)
            return _config
    except FileNotFoundError:
        print(f"⚠️ 模型配置文件未找到: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"⚠️ 模型配置文件JSON格式错误: {e}")
        return {}

def get_model(model_key: str) -> str:
    """
    获取指定模型的配置
    
    Args:
        model_key: 模型键名（如 'agent_initial_analysis'）
        
    Returns:
        模型名称
    """
    config = _load_config()
    model_config = config.get(model_key, {})
    
    if not model_config:
        print(f"⚠️ 未找到模型配置: {model_key}")
        return "gpt-4o-mini"  # 默认模型
    
    # 从环境变量获取，如果没有则使用默认值
    env_var = model_config.get('env_var')
    default_model = model_config.get('default', 'gpt-4o-mini')
    
    if env_var:
        return os.environ.get(env_var, default_model)
    else:
        return default_model