#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DAO组件工具函数
从library/utils.py迁移而来
"""

import hashlib

def str_hash(str):
    """生成字符串的MD5哈希值"""
    md5_hash = hashlib.md5()
    md5_hash.update(str.encode('utf-8'))
    md5_result = md5_hash.hexdigest()
    return md5_result 