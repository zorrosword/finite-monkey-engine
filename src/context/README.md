# Context Module - 上下文获取和管理模块

## 概述

Context模块是从项目的planning模块和validating模块中抽取出来的，专门负责智能合约审计过程中的上下文获取和管理。这个模块统一了所有与上下文相关的逻辑，包括RAG构造、调用树分析、业务流处理等。

## 模块结构

```
src/context/
├── __init__.py                    # 模块初始化文件
├── context_manager.py             # 上下文管理器
├── call_tree_builder.py           # 调用树构造器
├── rag_processor.py               # RAG处理器
├── business_flow_processor.py     # 业务流处理器
├── function_utils.py              # 函数工具类
├── context_factory.py             # 上下文工厂类
└── README.md                      # 本文档
```

## 核心组件

### 1. ContextManager - 上下文管理器
负责获取和管理分析所需的额外上下文信息。

**主要功能：**
- 通过语义搜索获取相关函数
- 从调用树中提取相关函数信息
- 处理网络搜索获取额外信息
- 带重试机制的上下文获取

### 2. CallTreeBuilder - 调用树构造器
负责分析函数之间的调用关系并构建调用树。

**主要功能：**
- 分析函数之间的调用关系
- 构建上游和下游调用树
- 支持多线程处理
- 提取状态变量信息

### 3. RAGProcessor - RAG处理器
负责创建和管理基于LanceDB的检索增强生成系统。

**主要功能：**
- 创建函数向量数据库
- 语义搜索相似函数
- 支持多种查询方式
- 并发处理函数嵌入

### 4. BusinessFlowProcessor - 业务流处理器
负责处理业务流相关的复杂逻辑。

**主要功能：**
- 提取所有函数的业务流
- 处理跨合约扩展代码
- 增强业务流代码
- 按可见性过滤函数

### 5. FunctionUtils - 函数工具类
提供各种函数处理相关的工具方法。

**主要功能：**
- 统一的相关函数提取接口（支持不同返回格式）
- 函数过滤和分组
- 计算函数复杂度
- 分析函数依赖关系

**重要改进：** 统一了原来planning和validating模块中两个不同的`extract_related_functions_by_level`实现，通过`return_pairs`参数控制返回格式。

### 6. ContextFactory - 上下文工厂类
统一管理所有上下文获取逻辑的工厂类。

**主要功能：**
- 统一的上下文获取接口
- 管理各个处理器的生命周期
- 提供综合上下文获取方法
- 资源清理和管理

## 使用示例

### 基本使用

```python
from context import ContextFactory

# 初始化上下文工厂
factory = ContextFactory(project_audit, lancedb, lance_table_name)

# 初始化RAG处理器
factory.initialize_rag_processor(functions_to_check, db_path, project_id)

# 构建调用树
call_trees = factory.build_call_trees(functions_to_check)

# 获取业务流上下文
business_flow_data = factory.get_business_flow_context(functions_to_check)

# 搜索相似函数
similar_functions = factory.search_similar_functions("transfer", k=5)

# 获取综合上下文
comprehensive_context = factory.get_comprehensive_context(
    function_name="transfer",
    query_contents=["token transfer", "balance check"],
    level=3,
    include_semantic=True,
    include_internet=False
)
```

### 高级使用

```python
# 直接使用特定处理器
context_manager = ContextManager(project_audit, lancedb, lance_table_name)
call_tree_builder = CallTreeBuilder()
rag_processor = RAGProcessor(functions_to_check, db_path, project_id)

# 获取函数依赖关系
dependencies = factory.get_function_dependencies("transfer", all_functions)

# 合并多个上下文
merged_context = factory.merge_contexts([context1, context2, context3])
```

## 迁移指南

### 从原始模块迁移

1. **统一使用ContextFactory（推荐方式）**：
   ```python
   # 原来的代码
   from planning.function_utils import FunctionUtils
   from validating.utils.context_manager import ContextManager
   from codebaseQA.rag_processor import RAGProcessor
   
   # 新的代码 - 统一通过工厂类访问
   from context import ContextFactory
   
   # 创建工厂实例
   factory = ContextFactory(project_audit, lancedb, lance_table_name)
   factory.initialize_rag_processor(functions_to_check, db_path, project_id)
   
   # 通过工厂访问所有功能
   related_functions = factory.get_related_functions_by_level(function_names, level)
   similar_functions = factory.search_similar_functions(query, k)
   business_flow_data = factory.get_business_flow_context(functions_to_check)
   ```

2. **如果需要直接访问特定组件**：
   ```python
   # 直接导入特定组件
   from context import ContextManager, RAGProcessor, FunctionUtils
   
   # 但仍推荐通过ContextFactory统一管理
   from context import ContextFactory
   ```

### 主要变更

1. **模块路径变更**：所有相关类都迁移到了`context`模块下
2. **接口统一**：通过`ContextFactory`提供统一的接口
3. **依赖简化**：减少了模块间的耦合
4. **功能增强**：添加了更多的工具方法和配置选项

## 配置说明

### 默认配置

```python
# 调用树构建配置
max_workers = 1  # 最大线程数
level = 3        # 分析层级深度

# RAG配置
db_path = "./lancedb"  # 数据库路径
k = 5                  # 搜索结果数量

# 业务流配置
threshold = 100        # 函数长度阈值
```

### 环境变量

```bash
# 启用网络搜索
export ENABLE_INTERNET_SEARCH=true
```

## 性能优化

1. **并发处理**：调用树构建和RAG处理器都支持多线程
2. **缓存机制**：RAG处理器会检查现有数据避免重复处理
3. **延迟初始化**：大部分处理器采用延迟初始化
4. **资源管理**：提供清理方法释放资源

## 故障排除

### 常见问题

1. **导入错误**：确保更新了所有模块的import语句
2. **数据库连接问题**：检查LanceDB的连接配置
3. **内存不足**：大项目可能需要增加内存限制
4. **性能问题**：调整线程数和批处理大小

### 调试技巧

1. 开启详细日志输出
2. 使用单线程模式进行调试
3. 检查数据库表的创建状态
4. 验证函数数据的完整性

## 贡献指南

1. 遵循现有的代码风格
2. 添加适当的类型注解
3. 编写单元测试
4. 更新文档

## 许可证

本模块遵循项目的整体许可证。 