# 规划模块

## 概述

规划模块是一个专业的项目扫描编排器，专为全面的代码审计和漏洞分析而设计。它提供智能规划能力，协调扫描流水线中的各个组件，特别针对智能合约和区块链代码分析进行了优化。

## 核心组件

### Planning (`planning.py`)
主要的规划协调器，负责编排不同的规划组件：
- **项目审计集成**：直接与TreeSitterProjectAudit实例协作
- **任务管理**：与ProjectTaskMgr协调任务生命周期管理
- **RAG集成**：支持检索增强生成以提升分析能力
- **业务流分析**：提供业务上下文分析功能

### PlanningProcessor (`planning_processor.py`)
核心规划引擎，负责：
- **智能扫描策略**：根据项目特征确定最优扫描方法
- **上下文生成**：为漏洞检测创建丰富的上下文信息
- **业务流处理**：分析代码中的业务逻辑模式
- **多模式支持**：处理不同的扫描模式（通用项目、纯扫描、检查清单等）

### Business Flow Utils (`business_flow_utils.py`)
专门用于业务逻辑分析的工具：
- **流程模式识别**：识别代码中的业务流程模式
- **上下文丰富化**：为技术分析添加业务上下文
- **智能合约逻辑**：专门处理DeFi和区块链协议

### Configuration Utils (`config_utils.py`)
规划操作的配置管理：
- **动态配置**：支持运行时配置调整
- **模式特定设置**：不同扫描模式的专门配置
- **性能调优**：大型代码库的优化参数

## 主要特性

### 🎯 智能项目分析
- **多语言支持**：处理Solidity、Rust、Go、C++等多种语言
- **智能合约专业化**：深度理解区块链协议
- **依赖分析**：跟踪复杂的调用关系和依赖

### 🔄 自适应扫描策略
- **基于模式的规划**：针对不同项目类型的不同策略
- **资源优化**：扫描任务的智能资源分配
- **可扩展架构**：高效处理各种规模的项目

### 🧠 上下文感知处理
- **RAG集成**：利用语义搜索增强分析
- **业务上下文**：融入业务逻辑理解
- **历史知识**：使用累积的审计知识改进规划

### 📊 任务编排
- **优先级管理**：智能任务优先级排序
- **并行处理**：协调并发扫描操作
- **进度跟踪**：扫描进度的实时监控

## 架构设计

```
规划模块
├── Planning (主协调器)
│   ├── 项目审计集成
│   ├── 任务管理
│   └── RAG初始化
├── PlanningProcessor (核心引擎)
│   ├── 扫描策略
│   ├── 上下文生成
│   └── 模式处理
├── Business Flow Utils
│   ├── 模式识别
│   └── 上下文丰富化
└── Configuration Utils
    ├── 动态配置
    └── 性能调优
```

## 使用示例

### 基础规划设置
```python
from planning.planning import Planning
from dao.task_mgr import ProjectTaskMgr

# 使用项目审计数据初始化规划
planning = Planning(project_audit, task_manager)

# 执行规划过程
planning.do_planning()
```

### RAG增强规划
```python
# 使用RAG功能初始化
planning.initialize_rag_processor("./lancedb", project_id)

# 获取业务流上下文
context = planning.get_business_flow_context(functions_to_check)
```

### 不同扫描模式
```python
# 带深度控制的通用项目模式
planning.process_for_common_project_mode(max_depth=5)

# 生成规划文件用于审查
planning.generate_planning_files()
```

## 配置选项

模块通过环境变量支持各种配置选项：

- `SWITCH_BUSINESS_CODE`：启用/禁用业务代码分析
- `SCAN_MODE`：设置扫描模式（SPECIFIC_PROJECT、COMMON_PROJECT等）
- `MAX_PLANNING_DEPTH`：控制分析深度以进行性能调优

## 集成接口

### 输入依赖
- **TreeSitterProjectAudit**：项目解析和分析数据
- **ProjectTaskMgr**：任务管理和数据库操作
- **RAGProcessor**：语义搜索和上下文增强

### 输出消费者
- **AI引擎**：接收规划结果进行漏洞扫描
- **推理模块**：使用规划上下文进行智能分析
- **验证模块**：利用规划洞察进行确认

## 性能考虑

- **内存优化**：大型代码库的高效处理
- **缓存策略**：规划结果的智能缓存
- **并发处理**：多组件的并行规划
- **资源管理**：基于项目规模的自适应资源分配

## 未来增强

- **机器学习集成**：AI驱动的规划优化
- **自定义规则支持**：用户定义的规划策略
- **高级指标**：增强的规划有效性测量
- **云集成**：企业级的分布式规划