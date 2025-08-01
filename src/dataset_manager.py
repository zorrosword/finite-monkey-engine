#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据集管理器
从library/dataset_utils.py迁移而来，专门处理项目数据集
"""

import os
import json

def load_dataset(dataset_path, external_project_id=None, external_project_path=None):
    """
    加载数据集配置
    
    Args:
        dataset_path: 数据集基础路径
        external_project_id: 外部项目ID
        external_project_path: 外部项目路径
    
    Returns:
        dict: 项目配置字典
    """
    # Load projects from datasets.json
    if not external_project_id and not external_project_path:
        ds_json = os.path.join(dataset_path, "datasets.json")
        dj = json.load(open(ds_json, 'r', encoding='utf-8'))
        projects = {}
        for k, v in dj.items():
            v['base_path'] = dataset_path
            projects[k] = v

    # Handle external project input
    if external_project_id and external_project_path:
        projects = {}
        # Construct project data structure for the external project
        external_project = {
            'path': external_project_path,
            'base_path': dataset_path
        }

        # Add the external project to the projects dictionary
        projects[external_project_id] = external_project

    return projects


class Project(object):
    """项目配置类"""
    
    def __init__(self, id, project) -> None:
        self.id = id
        self.path = os.path.join(project['base_path'], project['path']) 