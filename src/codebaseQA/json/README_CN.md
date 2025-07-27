# JSON 输入目录

这个目录用于存储项目的业务流程JSON文件，用于直接加载业务流数据而无需生成Mermaid图。

## 📁 目录结构

```
src/codebaseQA/json/
├── {project_id_1}/
│   ├── business_flow_1.json
│   ├── business_flow_2.json
│   └── ...
├── {project_id_2}/
│   ├── business_flow_1.json
│   └── ...
└── README_CN.md (本文件)
```

## 📊 JSON文件格式

每个JSON文件应包含业务流数据，格式如下：

```json
{
  "flows": [
    {
      "name": "用户资产管理完整流程",
      "steps": [
        "Token.transfer",
        "Vault.deposit", 
        "RewardPool.stake",
        "Oracle.getPrice",
        "Liquidator.liquidate"
      ]
    },
    {
      "name": "权限验证与执行流程",
      "steps": [
        "UserManager.register",
        "AssetManager.withdraw",
        "SecurityChecker.validate"
      ]
    }
  ]
}
```

或者简化格式（单个业务流）：

```json
{
  "name": "业务流程名称",
  "steps": [
    "Contract.function1",
    "Contract.function2",
    "Contract.function3"
  ]
}
```

## 🎯 使用方式

1. **创建项目目录**：在`src/codebaseQA/json/`下创建以项目ID命名的文件夹
2. **添加JSON文件**：将业务流程JSON文件放入对应的项目目录
3. **运行分析**：系统会自动扫描并加载所有JSON文件中的业务流

## ✅ 数据要求

### 步骤格式要求
- **格式**：必须是 `文件名.函数名` 或 `合约名.函数名`
- **分隔符**：文件名和函数名之间用 `.` 连接
- **文件名**：不能包含文件后缀（如 .sol、.py 等）
- **示例**：
  - ✅ 正确：`Token.transfer`、`Vault.deposit`
  - ❌ 错误：`Token.sol.transfer`、`src/Token.transfer`

### 业务流要求
- 每个业务流应包含4-8个步骤
- 步骤应该在逻辑上连贯
- 业务流名称应描述完整的业务场景

## 🔄 处理流程

1. **文件扫描**：系统扫描 `src/codebaseQA/json/{project_id}/` 下的所有 `.json` 文件
2. **数据加载**：解析JSON文件，提取业务流数据
3. **函数匹配**：使用传统策略和LanceDB策略匹配函数
4. **任务创建**：基于匹配结果创建分析任务

## 🛠️ 相关代码文件

- `src/planning/business_flow_utils.py` - JSON文件加载和处理
- `src/planning/planning_processor.py` - 业务流处理和函数匹配
- `src/main.py` - 主要流程控制

## 💡 注意事项

- JSON文件名可以任意命名，系统会加载目录下所有的 `.json` 文件
- 支持多个JSON文件，每个文件可以包含多个业务流
- 确保JSON格式正确，避免语法错误
- 业务流的步骤会通过传统字符串匹配和LanceDB语义搜索进行函数匹配 