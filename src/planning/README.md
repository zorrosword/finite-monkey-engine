# Planning 模块重构说明

## 概述

本次重构将原来的 `planning_v2.py` 文件拆分为多个模块，提高了代码的可维护性和可复用性。重构采用分层架构，将复杂的业务逻辑拆分为独立的处理器和工具模块。

## 文件结构

```
src/planning/
├── __init__.py                  # 模块初始化文件
├── planning_v2.py              # 核心入口类（已简化）
├── business_flow_processor.py  # 业务流处理器
├── planning_processor.py       # 规划处理器
├── business_flow_utils.py      # 业务流处理工具
├── json_utils.py               # JSON处理工具
├── function_utils.py           # 函数处理工具
├── config_utils.py             # 配置管理工具
└── README.md                   # 本文档
```

## 模块说明

### 1. planning_v2.py（核心入口）
现在非常简洁，主要负责：
- `PlanningV2` 类：主要的规划引擎入口
- 初始化各种处理器
- 提供简洁的公共API接口

### 2. business_flow_processor.py（业务流处理器）
专门处理业务流相关的复杂逻辑：
- `get_all_business_flow()` - 获取所有业务流的主逻辑
- `_process_contract_business_flows()` - 处理单个合约的业务流
- `_process_function_business_flow()` - 处理单个函数的业务流
- `_get_function_code()` - 获取函数代码
- `_get_business_flow_list()` - 获取业务流列表
- `_process_business_flow_response()` - 处理业务流响应
- `_extract_function_line_info()` - 提取函数行信息
- `_enhance_with_cross_contract_code()` - 跨合约代码增强
- `_enhance_business_flow_code()` - 业务流代码增强

### 3. planning_processor.py（规划处理器）
专门处理规划相关的复杂逻辑：
- `do_planning()` - 执行规划的主逻辑
- `_prepare_planning()` - 准备规划工作
- `_filter_test_functions()` - 过滤测试函数
- `_get_business_flows_if_needed()` - 按需获取业务流
- `_process_all_functions()` - 处理所有函数
- `_process_single_function()` - 处理单个函数
- `_handle_business_flow_planning()` - 处理业务流规划
- `_handle_function_code_planning()` - 处理函数代码规划
- `_generate_checklist_and_analysis()` - 生成检查清单和分析
- `_write_checklist_to_csv()` - 写入CSV文件
- `_analyze_business_type()` - 分析业务类型
- `_create_planning_task()` - 创建规划任务

### 4. business_flow_utils.py（业务流工具）
业务流处理相关的工具函数：
- `ask_openai_for_business_flow()` - 询问OpenAI获取业务流
- `extract_and_concatenate_functions_content()` - 提取和拼接函数内容
- `decode_business_flow_list_from_response()` - 从响应解码业务流列表
- `search_business_flow()` - 搜索业务流
- `identify_contexts()` - 识别上下文

### 5. json_utils.py（JSON工具）
JSON处理相关的工具函数：
- `extract_filtered_functions()` - 从JSON字符串提取函数名
- `extract_results()` - 提取文本中的结果
- `merge_and_sort_rulesets()` - 合并和排序规则集

### 6. function_utils.py（函数工具）
函数处理相关的工具函数：
- `extract_related_functions_by_level()` - 按层级提取相关函数

### 7. config_utils.py（配置工具）
配置管理相关的工具函数：
- `should_exclude_in_planning()` - 判断文件是否应该在规划中排除
- `get_visibility_filter_by_language()` - 根据编程语言获取可见性过滤器
- `get_scan_configuration()` - 获取扫描配置

## 重构架构

### 分层设计
```
┌─────────────────────────────────────┐
│           PlanningV2                │  ← 入口层（简化的API）
│         (Entry Point)               │
└─────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│       Processor Layer               │  ← 处理器层（核心业务逻辑）
│  ┌─────────────────────────────────┐│
│  │  BusinessFlowProcessor         ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  PlanningProcessor             ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│         Utils Layer                 │  ← 工具层（纯函数工具）
│  ┌─────────────┬─────────────────────│
│  │BusinessFlow │JsonUtils │Function ││
│  │Utils        │         │Utils    ││
│  └─────────────┴─────────────────────│
│  ┌─────────────────────────────────┐│
│  │          ConfigUtils           ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

## 重构优势

1. **分层架构**: 清晰的分层设计，职责分明
2. **代码复用**: 工具函数和处理器可以在其他模块中复用
3. **单一职责**: 每个模块专注于特定功能
4. **易于测试**: 更容易对单个组件进行单元测试
5. **易于维护**: 修改特定功能只需修改对应模块
6. **易于扩展**: 新增功能时只需添加新的处理器或工具
7. **代码可读性**: 代码结构更清晰，更容易理解

## 代码行数对比

### 重构前
- `planning_v2.py`: 786 行（巨型文件）

### 重构后
- `planning_v2.py`: 48 行（入口文件，减少 94%）
- `business_flow_processor.py`: 228 行（业务流处理器）
- `planning_processor.py`: 227 行（规划处理器）
- `business_flow_utils.py`: 148 行（业务流工具）
- `json_utils.py`: 93 行（JSON工具）
- `function_utils.py`: 116 行（函数工具）
- `config_utils.py`: 111 行（配置工具）

**总计**: 原来的 786 行拆分为 7 个文件，每个文件都有明确的职责。

## 使用方式

### 基本使用（与之前完全兼容）
```python
from planning import PlanningV2

# 使用核心规划类（API不变）
planning = PlanningV2(project, taskmgr)
planning.do_planning()
```

### 高级使用（使用具体的处理器和工具）
```python
from planning import (
    PlanningV2, 
    BusinessFlowProcessor, 
    PlanningProcessor,
    BusinessFlowUtils, 
    JsonUtils, 
    FunctionUtils, 
    ConfigUtils
)

# 使用特定的处理器
business_flow_processor = BusinessFlowProcessor(project)
business_flows = business_flow_processor.get_all_business_flow(functions)

# 使用工具函数
config = ConfigUtils.get_scan_configuration()
filtered_functions = JsonUtils.extract_filtered_functions(json_string)
```

## 兼容性

这次重构保持了原有的公共API完全不变，现有代码无需任何修改即可继续使用。同时提供了更细粒度的API供高级用户使用。 