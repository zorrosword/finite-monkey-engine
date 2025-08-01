#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志配置模块
提供统一的日志配置和管理功能
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

def setup_logging(log_file_path=None, level=logging.INFO):
    """
    设置全局日志配置
    
    Args:
        log_file_path: 日志文件路径，如果为None则使用默认路径
        level: 日志级别
    """
    
    # 如果没有指定日志文件路径，使用默认路径
    if log_file_path is None:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = log_dir / f"finite_monkey_engine_{timestamp}.log"
    
    # 确保日志目录存在
    log_dir = Path(log_file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 清除现有的handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件handler
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # 配置root logger
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 记录日志配置信息
    logger = logging.getLogger(__name__)
    logger.info("="*80)
    logger.info("🚀 Finite Monkey Engine 日志系统启动")
    logger.info(f"📁 日志文件路径: {log_file_path}")
    logger.info(f"📊 日志级别: {logging.getLevelName(level)}")
    logger.info(f"🕐 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    return str(log_file_path)

def get_logger(name):
    """
    获取指定名称的logger
    
    Args:
        name: logger名称
        
    Returns:
        logging.Logger: 配置好的logger实例
    """
    return logging.getLogger(name)

def log_section_start(logger, section_name, description=""):
    """记录章节开始"""
    logger.info("="*60)
    logger.info(f"🔥 开始执行: {section_name}")
    if description:
        logger.info(f"📝 描述: {description}")
    logger.info("="*60)

def log_section_end(logger, section_name, duration=None):
    """记录章节结束"""
    logger.info("-"*60)
    logger.info(f"✅ 完成执行: {section_name}")
    if duration:
        logger.info(f"⏱️  执行时间: {duration:.2f}秒")
    logger.info("-"*60)

def log_step(logger, step_name, details=""):
    """记录执行步骤"""
    logger.info(f"🔹 {step_name}")
    if details:
        logger.info(f"   详情: {details}")

def log_error(logger, error_msg, exception=None):
    """记录错误信息"""
    logger.error(f"❌ 错误: {error_msg}")
    if exception:
        logger.error(f"   异常详情: {str(exception)}", exc_info=True)

def log_warning(logger, warning_msg):
    """记录警告信息"""
    logger.warning(f"⚠️  警告: {warning_msg}")

def log_success(logger, success_msg, details=""):
    """记录成功信息"""
    logger.info(f"✅ 成功: {success_msg}")
    if details:
        logger.info(f"   详情: {details}")

def log_data_info(logger, data_name, count, details=""):
    """记录数据信息"""
    logger.info(f"📊 {data_name}: {count}个")
    if details:
        logger.info(f"   详情: {details}") 