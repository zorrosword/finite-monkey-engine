# JSON业务流直接加载功能修改总结

## 📝 修改概述

根据用户需求，已修改系统逻辑，跳过MMD生成和提问生成JSON的步骤，直接从JSON文件加载业务流数据。

## 🔧 主要修改

### 1. 新增JSON目录结构

- **目录**: `src/codebaseQA/json/`
- **结构**: `src/codebaseQA/json/{project_id}/` 
- **文件**: 支持多个 `.json` 文件

### 2. 修改的文件

#### `src/planning/business_flow_utils.py`
- **新增函数**: `load_business_flows_from_json_files()`
  - 直接从JSON文件加载业务流数据
  - 支持多种JSON格式
  - 包含数据验证逻辑
  - **已注释掉AI清洗**: JSON情况下不进行AI清洗，直接使用验证过的数据

#### `src/planning/planning_processor.py`
- **修改方法**: `_extract_business_flows_from_mermaid()` → `_extract_business_flows()`
- **新增逻辑**: 优先从JSON文件加载，失败时回退到Mermaid文件

#### `src/main.py`
- **新增检查**: 优先检查JSON文件是否存在
- **逻辑调整**: JSON文件存在时跳过Mermaid生成

## 🎯 工作流程

### 原有流程
```
代码解析 → Mermaid生成 → AI提取JSON → 函数匹配 → 任务创建
```

### 新流程
```
代码解析 → JSON文件检查 → 直接加载JSON → 函数匹配 → 任务创建
                ↓ (JSON不存在时)
            Mermaid生成 → AI提取JSON → 函数匹配 → 任务创建
```

## 📊 支持的JSON格式

### 格式1: 标准格式
```json
{
  "flows": [
    {
      "name": "业务流程名称",
      "steps": ["Contract.function1", "Contract.function2"]
    }
  ]
}
```

### 格式2: 单个业务流
```json
{
  "name": "业务流程名称",
  "steps": ["Contract.function1", "Contract.function2"]
}
```

### 格式3: 数组格式
```json
[
  {
    "name": "业务流程名称1",
    "steps": ["Contract.function1", "Contract.function2"]
  },
  {
    "name": "业务流程名称2", 
    "steps": ["Contract.function3", "Contract.function4"]
  }
]
```

## ✅ 数据验证

### 步骤格式要求
- **格式**: `文件名.函数名` 或 `合约名.函数名`
- **不能包含**: 文件后缀 (.sol, .py 等)
- **不能包含**: 路径信息 (src/, contracts/ 等)

### 自动清洗
- **JSON文件**: 跳过AI清洗，直接使用数据（假设JSON数据格式已正确）
- **Mermaid文件**: 保留AI清洗逻辑，处理从Mermaid图提取的数据
  - 移除文件后缀
  - 修复分隔符
  - 处理特殊字符
  - 统一格式

## 🔄 兼容性

- **向后兼容**: 如果没有JSON文件，自动回退到Mermaid流程
- **并存支持**: JSON文件和Mermaid文件可以并存，JSON优先
- **函数匹配**: 保持原有的传统策略和LanceDB策略不变

## 📁 使用方法

1. **创建项目目录**:
   ```bash
   mkdir -p src/codebaseQA/json/{project_id}
   ```

2. **添加JSON文件**:
   ```bash
   # 可以添加多个JSON文件
   echo '{"flows": [...]}' > src/codebaseQA/json/{project_id}/business_flow_1.json
   echo '{"flows": [...]}' > src/codebaseQA/json/{project_id}/business_flow_2.json
   ```

3. **运行分析**:
   ```bash
   python src/main.py
   ```

## 🚀 优势

- **性能大幅提升**: 
  - 跳过Mermaid生成，减少AI调用
  - 跳过AI清洗步骤，直接使用JSON数据
  - 显著减少处理时间和API成本
- **可控性强**: 直接编辑JSON文件，精确控制业务流
- **批量支持**: 支持多个JSON文件，便于管理
- **格式灵活**: 支持多种JSON格式
- **调试友好**: 可以直接查看和修改业务流定义

## ⚠️ 注意事项

- **确保JSON文件格式正确**: 由于跳过了AI清洗，JSON数据格式必须严格正确
- **步骤名称格式**: 必须符合 `文件名.函数名` 格式，不能包含文件后缀
- **业务流设计**: 建议业务流包含4-8个步骤以确保覆盖足够的业务逻辑
- **文件命名**: JSON文件名可以任意命名，系统会加载目录下所有 `.json` 文件
- **数据验证**: 虽然跳过AI清洗，但仍会进行基本的JSON结构验证 