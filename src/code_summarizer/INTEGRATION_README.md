# Code Summarizer与Planning模块集成功能

## 🎯 功能概述

本文档描述了`code_summarizer`模块与`planning`模块的集成功能，实现了从Mermaid业务流程图中提取业务流，并在planning阶段使用这些业务流进行智能合约审计。

## 🚀 核心功能

### 1. 扫描时生成Mermaid文件
在项目扫描过程中，系统会自动：
- 收集所有代码文件内容
- 使用`smart_business_flow_analysis_from_content`生成Mermaid业务流程图
- 保存一个或多个`.mmd`文件到输出目录

### 2. Planning时从Mermaid提取业务流
在planning阶段，如果满足以下条件：
- 使用business flow mode (`SWITCH_BUSINESS_CODE=True`)
- 文件模式是false (`SWITCH_FILE_CODE=False`)

系统会：
- 从生成的Mermaid文件中提取业务流JSON
- 匹配业务流中的函数到`functions_to_check`
- 使用提取的业务流替代传统的业务流提取方式

## 📋 业务流提取Prompt

系统使用以下prompt从Mermaid图中提取业务流：

```
基于以上业务流程图，提取出业务流，以JSON格式输出，结构如下：
{
"flows": [
{
"name": "业务流1",
"steps": ["文件1.函数", "文件2.函数", "文件3.函数"]
},
{
"name": "业务流2", 
"steps": ["文件1.函数", "文件2.函数"]
}
]
}
```

## 🔄 完整工作流程

### 步骤1: 扫描阶段 (main.py)

```python
# 在scan_project函数中
def scan_project(project, db_engine):
    # ... 现有代码 ...
    
    # 🆕 生成Mermaid文件
    files_content = {}
    for func in project_audit.functions_to_check:
        file_path = func['relative_file_path']
        if file_path not in files_content:
            files_content[file_path] = func['contract_code']
    
    mermaid_result = smart_business_flow_analysis_from_content(
        files_content, 
        project.id,
        enable_reinforcement=True
    )
    
    # 保存mermaid文件到 ./output/{project_id}/
    # 将结果保存到project_audit以供后续使用
    project_audit.mermaid_result = mermaid_result
    project_audit.mermaid_output_dir = output_dir
```

### 步骤2: Planning阶段 (planning_processor.py)

```python
def _get_business_flows_if_needed(self, config: Dict) -> Dict:
    # 🆕 尝试从mermaid文件中提取业务流
    if hasattr(self.project, 'mermaid_output_dir') and self.project.mermaid_output_dir:
        mermaid_business_flows = self._extract_business_flows_from_mermaid()
        
        if mermaid_business_flows:
            return {
                'use_mermaid_flows': True,
                'mermaid_business_flows': mermaid_business_flows,
                # ... 其他字段
            }
    
    # 回退到传统方式
    # ... 现有逻辑
```

### 步骤3: 业务流处理 (business_flow_utils.py)

```python
# 新增功能
def extract_all_business_flows_from_mermaid_files(mermaid_output_dir, project_id):
    # 加载所有.mmd文件
    # 使用prompt提取业务流JSON
    # 返回业务流列表

def match_functions_from_business_flows(business_flows, functions_to_check):
    # 先匹配函数名，再匹配文件/合约名
    # 返回匹配的业务流和对应的函数
```

## 📁 文件结构

```
output/
└── {project_id}/
    ├── {project_id}_business_flow.mmd      # 小项目单一文件
    ├── {project_id}_{folder_name}.mmd      # 大项目文件夹级别
    └── {project_id}_global_overview.mmd    # 大项目全局概览
```

## 🎯 函数匹配策略

系统使用以下策略匹配业务流中的函数步骤：

1. **精确匹配**: `合约名.函数名` 或 `文件名.函数名`
2. **函数名匹配**: 如果精确匹配失败，尝试只匹配函数名
3. **优先级**: 优先匹配更具体的函数标识

### 匹配示例

```javascript
// 业务流步骤: "Token.transfer"
// 匹配到: functions_to_check中的 {name: "Token.transfer", ...}

// 业务流步骤: "transfer" 
// 匹配到: 第一个名为"transfer"的函数
```

## 🧪 测试功能

运行集成测试：

```bash
cd src
python test_smart_analyzer.py
```

测试包括：
- Mermaid业务流提取prompt测试
- 完整集成流程测试
- 函数匹配验证

## 🔧 配置要求

确保环境变量正确设置：

```bash
# 启用业务流扫描，禁用文件级别扫描
export SWITCH_BUSINESS_CODE=True
export SWITCH_FILE_CODE=False

# 其他相关配置
export SWITCH_FUNCTION_CODE=True  # 可选
```

## 📊 优势对比

| 特性 | 传统业务流提取 | 基于Mermaid的提取 |
|------|---------------|------------------|
| **数据来源** | AST分析 + AI分析 | Mermaid可视化图 |
| **准确性** | 依赖代码结构 | 基于整体业务理解 |
| **可视化** | 无 | 完整的流程图 |
| **扩展性** | 有限 | 支持复杂业务场景 |
| **调试性** | 较难 | 可视化，易于理解 |

## ⚡ 性能考虑

- **Mermaid生成**: 首次扫描时生成，后续复用
- **业务流提取**: 使用AI分析Mermaid图，比传统AST分析更高效
- **函数匹配**: 优化的索引策略，支持大型项目

## 🛠️ 故障排除

### 常见问题

1. **Mermaid文件未生成**
   - 检查`code_summarizer`模块是否正确导入
   - 验证`functions_to_check`数据是否有效

2. **业务流提取失败**
   - 检查Mermaid文件内容是否有效
   - 验证AI API配置是否正确

3. **函数匹配失败**
   - 检查函数名格式是否一致
   - 验证`functions_to_check`数据结构

### 调试模式

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔮 未来扩展

1. **增量更新**: 支持项目变更时的增量Mermaid更新
2. **自定义匹配**: 支持用户自定义函数匹配规则
3. **多格式支持**: 支持其他图表格式（如PlantUML）
4. **交互式优化**: 支持用户交互式优化业务流提取

## 🤝 贡献指南

1. 遵循现有代码风格
2. 添加适当的测试用例
3. 更新相关文档
4. 确保向后兼容性

---

**🎉 通过这个集成功能，智能合约审计变得更加智能和可视化！** 