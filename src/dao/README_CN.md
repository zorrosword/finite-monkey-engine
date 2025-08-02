# DAO 组件

## 概述

DAO（数据访问对象）组件为 Finite Monkey Engine 提供数据持久化和管理功能。它使用 SQLAlchemy 和 SQLite 处理项目任务、缓存和数据库操作。

## 功能特性

- **项目任务管理**: 项目任务的 CRUD 操作
- **缓存系统**: 智能缓存以优化性能
- **数据库操作**: 基于 SQLAlchemy 的数据持久化
- **实体管理**: 项目实体的结构化数据模型

## 架构

### 核心组件

- **ProjectTaskMgr**: 主任务管理类
- **CacheManager**: 性能缓存系统
- **实体模型**: SQLAlchemy 实体定义
- **数据库工具**: 数据库连接和实用函数

### 数据库模式

组件管理多个数据库表：
- `project_task`: 主任务存储表
- `prompt_cache2`: 提示响应的缓存表
- 用于数据管理的其他实用表

## 使用方法

### 基本任务管理

```python
from dao import ProjectTaskMgr, CacheManager

# 初始化任务管理器
task_mgr = ProjectTaskMgr(project_id="my_project")

# 创建新任务
task_data = {
    'name': 'TestContract.transfer',
    'content': 'function transfer() public { }',
    'rule': 'access_control_checklist',
    'rule_key': 'access_control'
}
task = task_mgr.create_task(task_data)

# 查询任务
tasks = task_mgr.query_task_by_project_id("my_project")
```

### 缓存操作

```python
# 初始化缓存管理器
cache_mgr = CacheManager()

# 存储缓存条目
cache_mgr.set_cache("prompt_key", "cached_response")

# 检索缓存条目
response = cache_mgr.get_cache("prompt_key")

# 清除缓存
cache_mgr.clear_cache()
```

## 集成

DAO 组件与以下模块集成：

- **规划模块**: 存储和检索规划任务
- **验证模块**: 管理验证任务数据
- **主引擎**: 为整个系统提供数据持久化
- **结果处理器**: 存储分析结果和报告

## 配置

### 数据库配置

```python
# 数据库连接字符串
DATABASE_URL = "sqlite:///project_tasks.db"

# 表配置
PROJECT_TASK_TABLE = "project_task"
CACHE_TABLE = "prompt_cache2"
```

### 环境变量

- `DATABASE_URL`: 数据库连接字符串
- `CACHE_TTL`: 缓存生存时间（秒）
- `MAX_CACHE_SIZE`: 最大缓存大小（条目数）

## 性能

- **查询优化**: 索引数据库查询以实现快速检索
- **缓存策略**: 智能缓存减少冗余操作
- **连接池**: 高效的数据库连接管理
- **批量操作**: 支持批量数据操作

## 依赖

- `sqlalchemy`: 数据库操作的 ORM
- `sqlite3`: 数据库后端
- `json`: 用于数据序列化
- `datetime`: 用于时间戳处理

## 开发

### 添加新实体

1. 在 `entity.py` 中定义 SQLAlchemy 模型
2. 添加相应的管理器方法
3. 更新数据库模式
4. 添加迁移脚本

### 扩展缓存

1. 实现新的缓存策略
2. 添加缓存失效逻辑
3. 优化缓存性能
4. 添加缓存监控

## API 参考

### ProjectTaskMgr 类

#### 方法

- `create_task(task_data)`: 创建新的项目任务
- `query_task_by_project_id(project_id)`: 按项目查询任务
- `update_task(task_id, updates)`: 更新现有任务
- `delete_task(task_id)`: 删除任务
- `save_task(task)`: 将任务保存到数据库

#### 属性

- `project_id`: 当前项目标识符
- `engine`: 数据库引擎实例
- `session`: 数据库会话

### CacheManager 类

#### 方法

- `set_cache(key, value)`: 存储缓存条目
- `get_cache(key)`: 检索缓存条目
- `clear_cache()`: 清除所有缓存条目
- `invalidate_cache(key)`: 使特定缓存条目失效

## 错误处理

组件包含全面的错误处理：
- 数据库连接失败
- 事务回滚
- 缓存损坏
- 数据验证错误

## 贡献

1. Fork 仓库
2. 创建功能分支
3. 实现您的更改
4. 添加测试和文档
5. 提交拉取请求

## 许可证

本组件是 Finite Monkey Engine 项目的一部分，遵循相同的许可条款。 