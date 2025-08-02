#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文档分块器配置文件

提供各种分块策略的预设配置和自定义配置选项
"""

import os
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass


@dataclass
class ChunkConfig:
    """分块配置数据类"""
    split_by: Literal["word", "sentence", "page", "passage", "token"] = "word"
    chunk_size: int = 800
    chunk_overlap: int = 200
    batch_size: int = 1000
    encoding: str = 'utf-8'
    max_file_size_mb: float = 50.0
    include_extensions: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    long_text_mode: bool = False


class ChunkConfigManager:
    """分块配置管理器"""
    
    # 预设配置
    PRESET_CONFIGS = {
        # 默认配置 - 适用于一般项目
        "default": ChunkConfig(
            split_by="word",
            chunk_size=800,
            chunk_overlap=200,
            max_file_size_mb=10.0,
            exclude_patterns=['.git', '__pycache__', '.pyc', '.log', '.tmp', '.cache']
        ),
        
        # 代码项目配置 - 适用于代码审计，包含所有文件（除了排除的）
        "code_project": ChunkConfig(
            split_by="word",
            chunk_size=1000,
            chunk_overlap=250,
            max_file_size_mb=20.0,
            exclude_patterns=[
                '.git', '__pycache__', '.pyc', '.log', '.tmp', '.cache',
                'node_modules', '.next', 'dist', 'build', '.vscode',
                '.idea', '.DS_Store', 'coverage', '.nyc_output', '.bin',
                '.dll', '.so', '.dylib', '.exe', '.zip', '.tar', '.gz',
                '.rar', '.7z', '.jar', '.war', '.ear', '.deb', '.rpm',
                '.dmg', '.iso', '.img', '.vdi', '.vmdk', '.qcow2'
            ]
        ),
        
        # 长文本配置 - 适用于文档、小说等
        "long_text": ChunkConfig(
            split_by="passage",
            chunk_size=8,
            chunk_overlap=3,
            batch_size=500,
            max_file_size_mb=200.0,
            include_extensions=[
                '.txt', '.md', '.rst', '.doc', '.docx',
                '.pdf', '.rtf', '.odt', '.epub', '.mobi',
                '.html', '.xml'
            ],
            exclude_patterns=['.git', '.cache', '.tmp'],
            long_text_mode=True
        ),
        
        # 学术论文配置
        "academic": ChunkConfig(
            split_by="passage", 
            chunk_size=6,
            chunk_overlap=2,
            max_file_size_mb=100.0,
            include_extensions=['.txt', '.md', '.tex', '.pdf', '.doc', '.docx'],
            exclude_patterns=['.git', '.cache', '.tmp', '.aux', '.log', '.bbl'],
            long_text_mode=True
        ),
        
        # 技术文档配置
        "tech_docs": ChunkConfig(
            split_by="passage",
            chunk_size=5,
            chunk_overlap=2,
            max_file_size_mb=50.0,
            include_extensions=['.md', '.rst', '.txt', '.html', '.xml'],
            exclude_patterns=['.git', '.cache', '.tmp'],
            long_text_mode=True
        ),
        
        # 小文件精确分割配置
        "precise": ChunkConfig(
            split_by="sentence",
            chunk_size=3,
            chunk_overlap=1,
            max_file_size_mb=10.0,
            exclude_patterns=['.git', '__pycache__', '.pyc', '.log', '.tmp']
        ),
        
        # 大上下文配置 - 保持更多上下文信息
        "large_context": ChunkConfig(
            split_by="passage",
            chunk_size=12,
            chunk_overlap=4,
            max_file_size_mb=500.0,
            long_text_mode=True,
            exclude_patterns=['.git', '.cache', '.tmp']
        ),
        
        # Token分割配置 - 适用于LLM处理
        "token_based": ChunkConfig(
            split_by="token",
            chunk_size=512,
            chunk_overlap=50,
            max_file_size_mb=100.0,
            exclude_patterns=['.git', '__pycache__', '.pyc', '.log', '.tmp']
        )
    }
    
    @classmethod
    def get_config(cls, preset_name: str = "default") -> ChunkConfig:
        """
        获取预设配置
        
        Args:
            preset_name: 预设配置名称
            
        Returns:
            ChunkConfig: 配置对象
        """
        if preset_name not in cls.PRESET_CONFIGS:
            print(f"⚠️  未知的预设配置: {preset_name}，使用默认配置")
            preset_name = "default"
        
        config = cls.PRESET_CONFIGS[preset_name]
        print(f"📋 使用预设配置: {preset_name}")
        print(f"  - 分割策略: {config.split_by}")
        print(f"  - 块大小: {config.chunk_size}")
        print(f"  - 重叠大小: {config.chunk_overlap}")
        print(f"  - 长文本模式: {'是' if config.long_text_mode else '否'}")
        
        return config
    
    @classmethod
    def get_config_for_project_type(cls, project_type: str = "code") -> ChunkConfig:
        """
        根据项目类型获取配置
        
        Args:
            project_type: 项目类型 ('code', 'docs', 'long_text', 'academic', etc.)
            
        Returns:
            ChunkConfig: 项目类型对应的配置
        """
        type_mapping = {
            'code': 'code_project',
            'project': 'code_project', 
            'docs': 'tech_docs',
            'documentation': 'tech_docs',
            'long_text': 'long_text',
            'novel': 'long_text',
            'book': 'long_text',
            'academic': 'academic',
            'paper': 'academic',
            'research': 'academic',
            'precise': 'precise',
            'context': 'large_context',
            'token': 'token_based',
            'llm': 'token_based'
        }
        
        preset = type_mapping.get(project_type.lower(), 'code_project')
        return cls.get_config(preset)
    
    @classmethod
    def create_custom_config(
        cls,
        base_preset: str = "default",
        **overrides
    ) -> ChunkConfig:
        """
        基于预设配置创建自定义配置
        
        Args:
            base_preset: 基础预设配置名称
            **overrides: 要覆盖的参数
            
        Returns:
            ChunkConfig: 自定义配置对象
        """
        config = cls.get_config(base_preset)
        
        # 应用覆盖参数
        for key, value in overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
                print(f"  ✏️  覆盖参数 {key}: {value}")
            else:
                print(f"  ⚠️  未知参数 {key}，已忽略")
        
        return config
    
    @classmethod
    def list_presets(cls) -> None:
        """列出所有可用的预设配置"""
        print("📋 可用的预设配置:")
        print("=" * 60)
        
        for name, config in cls.PRESET_CONFIGS.items():
            print(f"\n🔧 {name}:")
            print(f"  - 分割策略: {config.split_by}")
            print(f"  - 块大小: {config.chunk_size}")
            print(f"  - 重叠: {config.chunk_overlap}")
            print(f"  - 最大文件: {config.max_file_size_mb}MB")
            print(f"  - 长文本模式: {'是' if config.long_text_mode else '否'}")
            
            if config.include_extensions:
                ext_preview = config.include_extensions[:5]
                ext_str = ', '.join(ext_preview)
                if len(config.include_extensions) > 5:
                    ext_str += f" ... (+{len(config.include_extensions) - 5}个)"
                print(f"  - 支持格式: {ext_str}")
        
        print(f"\n💡 使用方法:")
        print(f"  - Python: ChunkConfigManager.get_config('preset_name')")
        print(f"  - 环境变量: export CHUNK_PRESET=preset_name")


def get_project_chunk_config(project_type: str = "code") -> ChunkConfig:
    """
    获取项目分块配置的便捷函数
    
    Args:
        project_type: 项目类型，默认为'code'
        
    Returns:
        ChunkConfig: 项目分块配置
    """
    return ChunkConfigManager.get_config_for_project_type(project_type)


def get_chunk_config_for_type(doc_type: str) -> ChunkConfig:
    """
    根据文档类型获取推荐配置
    
    Args:
        doc_type: 文档类型 ('code', 'long_text', 'academic', 'tech_docs', etc.)
        
    Returns:
        ChunkConfig: 推荐配置
    """
    return ChunkConfigManager.get_config_for_project_type(doc_type)


if __name__ == "__main__":
    # 演示配置功能
    print("🎯 文档分块器配置演示\n")
    
    # 列出所有预设
    ChunkConfigManager.list_presets()
    
    print(f"\n" + "=" * 60)
    print("🧪 配置测试:")
    
    # 测试不同配置
    configs_to_test = ['default', 'code_project', 'long_text', 'academic']
    
    for config_name in configs_to_test:
        print(f"\n📋 测试配置: {config_name}")
        config = ChunkConfigManager.get_config(config_name)
        print(f"  配置详情: {config}")
    
    print(f"\n🔧 自定义配置示例:")
    custom_config = ChunkConfigManager.create_custom_config(
        'long_text',
        chunk_size=10,
        chunk_overlap=4,
        max_file_size_mb=300.0
    )
    print(f"  自定义结果: {custom_config}")
    
    print(f"\n✅ 配置演示完成!")