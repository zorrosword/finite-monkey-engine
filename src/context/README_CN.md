# Context 组件

## 概述

Context 组件为 Finite Monkey Engine 提供上下文管理和检索功能。它包含 RAG（检索增强生成）处理器，为漏洞分析提供智能代码搜索和上下文增强功能。

## 功能特性

- **RAG 处理器**: 用于代码上下文的高级检索系统
- **向量嵌入**: 使用 OpenAI 嵌入进行语义搜索
- **多级搜索**: 函数、文件和块级检索
- **上下文增强**: 用相关代码上下文增强分析

## 架构

### 核心组件

- **RAGProcessor**: 检索操作的主类
- **LanceDB 集成**: 用于嵌入的向量数据库
- **嵌入生成**: 将代码转换为向量表示
- **搜索算法**: 针对不同用例的多种搜索策略

### 数据库模式

组件管理三个主要的 LanceDB 表：
- `lancedb_function`: 函数嵌入和元数据
- `lancedb_file`: 文件级代码表示
- `lancedb_chunk`: 文档块嵌入

## 使用方法

### 基本 RAG 设置

```python
from context.rag_processor import RAGProcessor

# 使用项目审计数据初始化
rag_processor = RAGProcessor(
    project_audit,
    lancedb_path="./src/codebaseQA/lancedb",
    project_id="my_project"
)

# 搜索函数
results = rag_processor.search_functions_by_content("访问控制", k=5)
```

### 高级搜索方法

```python
# 按函数名搜索
name_results = rag_processor.search_functions_by_name("transfer", k=3)

# 按内容搜索函数
content_results = rag_processor.search_functions_by_content("重入攻击", k=3)

# 自然语言搜索
nl_results = rag_processor.search_functions_by_natural_language(
    "处理用户存款的函数", k=3
)

# 文件搜索
file_results = rag_processor.search_files_by_content("漏洞", k=2)

# 块搜索
chunk_results = rag_processor.search_chunks_by_content("安全", k=3)
```

## 集成

Context 组件与以下模块集成：

- **规划模块**: 为任务规划提供上下文
- **验证模块**: 用相关代码增强漏洞分析
- **Tree-sitter 解析**: 使用解析的代码结构进行嵌入
- **主引擎**: 整个系统的中央上下文管理

## 配置

### 环境变量

- `OPENAI_API_KEY`: 嵌入生成所需
- `LANCE_DB_PATH`: LanceDB 存储路径
- `EMBEDDING_MODEL`: OpenAI 嵌入模型（默认：text-embedding-3-small）

### 数据库配置

```python
# 数据库表名
FUNCTION_TABLE = "lancedb_function"
FILE_TABLE = "lancedb_file"
CHUNK_TABLE = "lancedb_chunk"

# 向量维度
EMBEDDING_DIMENSION = 1536  # text-embedding-3-small
```

## 性能

- **搜索速度**: 大多数查询的亚秒级响应时间
- **内存效率**: 优化的向量存储和检索
- **可扩展性**: 支持数百万行代码的大型代码库
- **准确性**: 高精度语义匹配

## 依赖

- `lancedb`: 用于嵌入的向量数据库
- `openai`: 用于嵌入生成和 API 调用
- `numpy`: 用于向量操作
- `json`: 用于数据序列化

## 开发

### 添加新的搜索方法

1. 在 RAGProcessor 中实现搜索逻辑
2. 添加相应的数据库查询
3. 更新结果格式化
4. 添加测试和文档

### 扩展上下文类型

1. 定义新的嵌入模式
2. 实现嵌入生成
3. 添加搜索算法
4. 更新集成点

## API 参考

### RAGProcessor 类

#### 方法

- `search_functions_by_name(query, k)`: 按名称搜索函数
- `search_functions_by_content(query, k)`: 按内容搜索函数
- `search_functions_by_natural_language(query, k)`: 自然语言搜索
- `search_files_by_content(query, k)`: 按内容搜索文件
- `search_chunks_by_content(query, k)`: 按内容搜索块
- `search_similar_chunks(chunk_id, k)`: 查找相似块

#### 属性

- `project_audit`: 项目审计数据
- `lancedb_path`: LanceDB 存储路径
- `project_id`: 项目标识符

## 错误处理

组件包含全面的错误处理：
- API 失败
- 数据库连接问题
- 无效查询
- 缺少嵌入

## 贡献

1. Fork 仓库
2. 创建功能分支
3. 实现您的更改
4. 添加测试和文档
5. 提交拉取请求

## 许可证

本组件是 Finite Monkey Engine 项目的一部分，遵循相同的许可条款。 