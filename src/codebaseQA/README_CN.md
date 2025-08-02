# CodebaseQA 组件

## 概述

CodebaseQA 组件为智能合约代码库提供智能代码分析和问答功能。它利用先进的语言模型和向量嵌入技术，实现语义搜索和上下文代码理解。

## 功能特性

- **语义代码搜索**: 使用自然语言查询查找相关代码片段
- **向量嵌入**: 使用 LanceDB 存储和检索代码表示
- **多语言支持**: 分析 Solidity、Rust、C++ 和 Move 代码
- **上下文理解**: 基于代码上下文和关系提供答案

## 架构

### 核心组件

- **LanceDB 集成**: 用于存储代码嵌入的向量数据库
- **嵌入生成**: 将代码片段转换为向量表示
- **查询处理**: 自然语言到代码搜索功能
- **结果排序**: 智能搜索结果排序

### 数据库模式

组件使用 LanceDB 表存储：
- 函数嵌入和元数据
- 文件级代码表示
- 文档块级嵌入
- 快速检索的搜索索引

## 使用方法

### 基本设置

```python
from codebaseQA import CodebaseQA

# 使用项目路径初始化
qa_system = CodebaseQA("./src/codebaseQA/lancedb")

# 搜索函数
results = qa_system.search_functions("访问控制漏洞")
```

### 高级查询

```python
# 按函数名搜索
name_results = qa_system.search_functions_by_name("transfer", k=5)

# 按内容相似性搜索
content_results = qa_system.search_functions_by_content("重入攻击", k=5)

# 自然语言搜索
nl_results = qa_system.search_functions_by_natural_language("处理用户存款的函数", k=5)
```

## 集成

CodebaseQA 组件与以下模块集成：
- **Tree-sitter 解析**: 用于代码结构分析
- **RAG 处理器**: 用于增强检索功能
- **规划模块**: 用于任务特定的代码搜索
- **验证模块**: 用于漏洞分析支持

## 配置

### 环境变量

- `LANCE_DB_PATH`: LanceDB 存储目录路径
- `EMBEDDING_MODEL`: 使用的 OpenAI 嵌入模型
- `VECTOR_DIMENSION`: 嵌入向量维度

### 数据库表

- `lancedb_function`: 函数嵌入和元数据
- `lancedb_file`: 文件级嵌入
- `lancedb_chunk`: 文档块嵌入

## 性能

- **搜索速度**: 亚秒级查询响应时间
- **准确性**: 高精度语义匹配
- **可扩展性**: 支持数百万行代码的大型代码库
- **内存效率**: 优化的向量存储和检索

## 依赖

- `lancedb`: 用于嵌入的向量数据库
- `openai`: 用于嵌入生成
- `numpy`: 用于向量操作
- `tree-sitter`: 用于代码解析集成

## 开发

### 添加新语言

1. 实现特定语言的解析器
2. 添加嵌入生成逻辑
3. 更新搜索算法
4. 使用示例代码库测试

### 扩展搜索功能

1. 实现新的搜索方法
2. 添加自定义排序算法
3. 与外部 API 集成
4. 优化性能

## 贡献

1. Fork 仓库
2. 创建功能分支
3. 实现您的更改
4. 添加测试和文档
5. 提交拉取请求

## 许可证

本组件是 Finite Monkey Engine 项目的一部分，遵循相同的许可条款。 