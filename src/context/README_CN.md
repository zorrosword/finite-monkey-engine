# Context模块 - 上下文管理

Context模块负责管理和获取代码分析所需的各种上下文信息，包括调用树、业务流、语义搜索和网络搜索等功能。

## 核心组件

### 1. ContextFactory (上下文工厂)
统一管理所有上下文获取逻辑的入口类。

### 2. RAGProcessor (检索增强生成处理器) 🆕
基于LanceDB的多种embedding向量检索系统，采用**两表架构**设计：

#### 🔧 两表架构设计：
```
📊 函数级别表 (lancedb_function_{project_id})
├── content_embedding      # 基于函数源代码内容
├── name_embedding         # 基于"合约名.函数名"
├── natural_embedding      # 基于函数功能自然语言描述
└── 完整的函数metadata     # functions_to_check中的所有字段

📁 文件级别表 (lancedb_file_{project_id})
├── content_embedding      # 基于文件内容
├── natural_embedding      # 基于文件自然语言描述
└── 完整的文件metadata     # 相对路径、绝对路径、长度、具体内容等
```

#### 🎯 核心优势：
- **统一存储**：同一条记录包含多种embedding，避免数据分散
- **元数据完整**：每条记录包含完整的相关信息
- **查询效率**：可在同一表中使用不同embedding进行搜索
- **维护简单**：仅需管理两个表，结构清晰

### 3. ContextManager (上下文管理器)
处理传统的上下文获取逻辑。

### 4. CallTreeBuilder (调用树构建器)
构建函数调用关系树。

### 5. BusinessFlowProcessor (业务流处理器)
处理业务流相关的上下文。

## 使用示例

### 基本初始化

```python
from context import ContextFactory

# 初始化上下文工厂
context_factory = ContextFactory(project_audit)

# 初始化RAG处理器（自动构建两个表：函数表+文件表）
context_factory.initialize_rag_processor(
    functions_to_check=functions_list,
    db_path="./lancedb",
    project_id="my_project"
)
```

### 🆕 函数级别多种搜索方式

#### 1. 基于函数内容搜索
```python
# 使用代码片段搜索相似函数
results = context_factory.search_functions_by_content(
    query="function transfer(address to, uint256 amount)", 
    k=5
)
```

#### 2. 基于函数名称搜索  
```python
# 使用函数名搜索（合约名.函数名）
results = context_factory.search_functions_by_name(
    query="Token.transfer", 
    k=5
)
```

#### 3. 基于自然语言搜索
```python
# 使用自然语言描述搜索
results = context_factory.search_functions_by_natural_language(
    query="transfer tokens between accounts with approval", 
    k=5
)
```

### 🆕 文件级别多种搜索方式

#### 1. 基于文件内容搜索
```python
# 使用文件内容片段搜索
results = context_factory.search_files_by_content(
    query="pragma solidity ^0.8.0; contract Token", 
    k=5
)
```

#### 2. 基于文件自然语言搜索
```python
# 使用文件功能描述搜索
results = context_factory.search_files_by_natural_language(
    query="ERC20 token implementation with minting", 
    k=5
)
```

### 🆕 综合搜索接口

#### 函数级别综合搜索
```python
# 使用函数表的3种embedding进行综合搜索
function_results = context_factory.get_comprehensive_function_search_results(
    query="token transfer", 
    k=3
)

# 返回格式：
{
    'content_based': [...],      # 基于函数内容的搜索结果
    'name_based': [...],         # 基于函数名的搜索结果  
    'natural_language_based': [...] # 基于自然语言的搜索结果
}
```

#### 文件级别综合搜索
```python
# 使用文件表的2种embedding进行综合搜索
file_results = context_factory.get_comprehensive_file_search_results(
    query="token management", 
    k=3
)

# 返回格式：
{
    'content_based': [...],         # 基于文件内容的搜索结果
    'natural_language_based': [...] # 基于文件描述的搜索结果
}
```

#### 全局综合搜索
```python
# 同时搜索函数和文件的所有embedding类型
all_results = context_factory.get_comprehensive_search_results(
    query="token transfer", 
    k=3
)

# 返回格式：
{
    'functions': {
        'content_based': [...],
        'name_based': [...], 
        'natural_language_based': [...]
    },
    'files': {
        'content_based': [...],
        'natural_language_based': [...]
    }
}
```

### 🆕 增强的综合上下文
```python
# 获取包含所有embedding类型的综合上下文
context = context_factory.get_comprehensive_context(
    function_name="Token.transfer",
    query_contents=["transfer", "balance"],
    level=2,
    include_semantic=True,
    include_internet=False,
    use_all_embedding_types=True  # 🆕 启用所有embedding类型
)

# 返回的context现在包含：
{
    'function_details': {...},        # 函数完整信息（包含3种embedding）
    'similar_functions': {...},       # 函数相似性搜索结果
    'related_files': {...},          # 相关文件搜索结果 🆕
    'call_tree_context': '...',
    'semantic_context': '...',
    'internet_context': '...'
}
```

### 🆕 数据获取接口

#### 函数级别数据获取
```python
# 获取特定函数的完整信息（包含3种embedding）
function_info = context_factory.get_function_context("Token.transfer")

# 返回包含所有metadata的函数信息：
{
    'content_embedding': [...],      # 3072维向量
    'name_embedding': [...],         # 3072维向量
    'natural_embedding': [...],      # 3072维向量
    'content': 'function transfer...',
    'natural_description': 'This function transfers...',
    'start_line': 45,
    'end_line': 60,
    'relative_file_path': 'contracts/Token.sol',
    'absolute_file_path': '/path/to/Token.sol',
    'contract_name': 'Token',
    'visibility': 'public',
    # ... 其他所有函数metadata
}
```

#### 文件级别数据获取
```python
# 获取特定文件的完整信息（包含2种embedding）
file_info = context_factory.get_file_context("contracts/Token.sol")

# 返回包含所有metadata的文件信息：
{
    'content_embedding': [...],      # 3072维向量
    'natural_embedding': [...],      # 3072维向量
    'file_content': 'pragma solidity...',
    'natural_description': 'This file implements...',
    'relative_file_path': 'contracts/Token.sol',
    'absolute_file_path': '/path/to/Token.sol',
    'file_length': 2048,
    'functions_count': 15,
    'functions_list': ['Token.transfer', 'Token.approve', ...],
    'file_extension': '.sol'
}
```

## 🆕 自然语言生成

### 函数描述生成
系统会自动将函数代码翻译成自然语言描述：

```
输入函数代码：
function transfer(address to, uint256 amount) public returns (bool) {
    require(balanceOf[msg.sender] >= amount, "Insufficient balance");
    balanceOf[msg.sender] -= amount;
    balanceOf[to] += amount;
    emit Transfer(msg.sender, to, amount);
    return true;
}

自动生成描述（存储在natural_description字段）：
"This function transfers a specified amount of tokens from the caller's account 
to a designated recipient address. It validates sufficient balance, updates 
account balances, emits a Transfer event, and returns success status."
```

### 文件描述生成
系统会为每个文件生成综合的自然语言描述：

```
输入：Token.sol文件内容 + 函数列表

自动生成描述（存储在natural_description字段）：
"This file implements a standard ERC20 token contract providing core 
functionality for token transfers, balance management, and allowance mechanisms. 
Key components include transfer functions, approval systems, and event logging 
for blockchain transparency."
```

## 🔄 数据库Schema详情

### 函数表Schema
```python
schema_function = pa.schema([
    # 基本标识
    pa.field("id", pa.string()),
    pa.field("name", pa.string()),
    
    # 🎯 3种embedding字段
    pa.field("content_embedding", pa.list_(pa.float32(), 3072)),    # 原始代码
    pa.field("name_embedding", pa.list_(pa.float32(), 3072)),       # 函数名
    pa.field("natural_embedding", pa.list_(pa.float32(), 3072)),    # 自然语言
    
    # 📝 完整的函数metadata
    pa.field("content", pa.string()),
    pa.field("natural_description", pa.string()),
    pa.field("start_line", pa.int32()),
    pa.field("end_line", pa.int32()),
    pa.field("relative_file_path", pa.string()),
    pa.field("absolute_file_path", pa.string()),
    pa.field("contract_name", pa.string()),
    pa.field("contract_code", pa.string()),
    pa.field("modifiers", pa.list_(pa.string())),
    pa.field("visibility", pa.string()),
    pa.field("state_mutability", pa.string()),
    pa.field("function_name_only", pa.string()),
    pa.field("full_name", pa.string())
])
```

### 文件表Schema
```python
schema_file = pa.schema([
    # 基本标识
    pa.field("id", pa.string()),
    pa.field("file_path", pa.string()),
    
    # 🎯 2种embedding字段
    pa.field("content_embedding", pa.list_(pa.float32(), 3072)),    # 文件内容
    pa.field("natural_embedding", pa.list_(pa.float32(), 3072)),    # 自然语言
    
    # 📁 完整的文件metadata
    pa.field("file_content", pa.string()),
    pa.field("natural_description", pa.string()),
    pa.field("relative_file_path", pa.string()),
    pa.field("absolute_file_path", pa.string()),
    pa.field("file_length", pa.int32()),
    pa.field("functions_count", pa.int32()),
    pa.field("functions_list", pa.list_(pa.string())),
    pa.field("file_extension", pa.string())
])
```

## ⚡ 性能优化

### 1. **并行处理策略**
```python
# 函数表处理：降低并发数，因为涉及3种embedding + LLM调用
max_workers = min(3, len(functions_to_check))

# 文件表处理：更低并发数，因为文件处理更耗时
max_workers = min(2, len(files_dict))
```

### 2. **智能缓存机制**
```python
# 检查两个表是否都存在且数据量匹配
tables_exist = (
    self._table_exists(self.table_name_function) and
    self._table_exists(self.table_name_file)
)

if tables_exist and functions_count_match and files_count_match:
    print("All tables already exist with correct data count. Skipping processing.")
    return
```

### 3. **向量搜索优化**
```python
# 使用vector_column_name指定具体的embedding字段进行搜索
table.search(query_embedding, vector_column_name="content_embedding").limit(k).to_list()
table.search(query_embedding, vector_column_name="name_embedding").limit(k).to_list()
table.search(query_embedding, vector_column_name="natural_embedding").limit(k).to_list()
```

## 📊 架构对比

### 原始架构 vs 新架构
```bash
# 🔴 原始架构（分散式）
lancedb_content_{project_id}     # 内容embedding
lancedb_name_{project_id}        # 名称embedding
lancedb_natural_{project_id}     # 自然语言embedding
lancedb_file_{project_id}        # 文件embedding

# 🟢 新架构（合并式）
lancedb_function_{project_id}    # 函数：3种embedding + 完整metadata
lancedb_file_{project_id}        # 文件：2种embedding + 完整metadata
```

### 🎯 新架构优势
1. **数据一致性**：同一实体的多种embedding保存在同一记录中
2. **查询便利性**：可以在一次查询中获取完整的实体信息
3. **维护简便性**：减少表数量，降低管理复杂度
4. **性能提升**：减少跨表查询，提高检索效率

## 兼容性

所有原有的搜索接口都得到保留：
- `search_similar_functions()` - 默认使用content embedding搜索
- `get_function_context()` - 从函数表获取完整函数信息
- `get_functions_by_file()` - 从函数表按文件筛选
- `get_functions_by_visibility()` - 从函数表按可见性筛选

新功能完全向后兼容，不会影响现有代码的使用。

## 配置要求

### 环境变量
```bash
# Embedding模型配置
EMBEDDING_MODEL="text-embedding-3-large"
EMBEDDING_API_BASE="api.openai-proxy.org"
EMBEDDING_API_KEY="your-api-key"

# JSON处理模型（用于自然语言生成）
JSON_MODEL_API_BASE="api.openai-proxy.org"
JSON_MODEL_API_KEY="your-api-key"
JSON_MODEL_ID="gpt-4.1"
```

### 依赖包
```txt
lancedb>=0.3.0
pyarrow>=10.0.0
openai>=1.0.0
numpy>=1.21.0
tqdm>=4.64.0
``` 