# Knowledges 组件

## 概述

Knowledges 组件为智能合约安全分析提供全面的知识库。它包含精选的文档、漏洞模式和区块链开发的安全指南。

## 功能特性

- **安全知识库**: 全面的安全文档
- **漏洞模式**: 常见漏洞模式和示例
- **最佳实践**: 智能合约安全最佳实践
- **参考资料**: 技术参考资料和指南

## 架构

### 核心组件

- **安全文档**: 精选的安全知识
- **漏洞数据库**: 常见漏洞的模式数据库
- **最佳实践指南**: 安全指南和建议
- **参考资料**: 技术文档和示例

### 知识结构

组件将知识组织成以下类别：
- **访问控制**: 访问控制漏洞和模式
- **重入攻击**: 重入攻击模式和预防
- **算术**: 整数溢出/下溢模式
- **跨合约**: 跨合约交互安全
- **清算**: 清算机制安全
- **滑点**: 滑点保护机制

## 使用方法

### 访问知识库

```python
# 知识库以 markdown 文件形式组织
# 访问特定漏洞知识
access_control_knowledge = "./src/knowledges/access_control.md"
reentrancy_knowledge = "./src/knowledges/reentrancy.md"
arithmetic_knowledge = "./src/knowledges/arithmetic.md"
```

### 知识类别

- **7540properties**: ERC-7540 标准属性
- **Across**: 跨链桥安全
- **Arbitrum**: Arbitrum 特定安全考虑
- **Chainlink**: Chainlink 预言机安全
- **DAO**: 去中心化自治组织安全
- **Lending**: DeFi 借贷协议安全
- **Liquidation**: 清算机制安全
- **Uniswap V3**: Uniswap V3 特定安全模式

## 集成

Knowledges 组件与以下模块集成：

- **规划模块**: 为任务规划提供安全上下文
- **验证模块**: 为分析提供漏洞模式
- **提示工厂**: 用安全知识增强提示
- **推理模块**: 为漏洞推理提供上下文

## 配置

### 知识路径

```python
# 默认知识路径
KNOWLEDGE_BASE_PATH = "./src/knowledges"
VULNERABILITY_PATTERNS = "./src/knowledges/vulnerability_patterns"
SECURITY_GUIDELINES = "./src/knowledges/security_guidelines"
```

### 知识类别

- **核心漏洞**: 基本漏洞模式
- **协议特定**: 协议特定的安全考虑
- **高级模式**: 复杂漏洞模式
- **最佳实践**: 安全最佳实践和指南

## 性能

- **快速访问**: 优化的知识检索
- **结构化组织**: 组织良好的知识结构
- **全面覆盖**: 广泛的安全知识库
- **易于维护**: 简单的基于 markdown 的知识管理

## 依赖

- `markdown`: 用于知识文件解析
- `pathlib`: 用于文件路径处理
- `json`: 用于结构化知识数据
- `typing`: 用于类型提示

## 开发

### 添加新知识

1. 在适当类别中创建 markdown 文件
2. 遵循知识结构格式
3. 添加交叉引用和示例
4. 更新知识索引

### 扩展知识库

1. 定义新的知识类别
2. 实现知识检索方法
3. 添加知识验证
4. 更新文档

## API 参考

### 知识访问

```python
def load_knowledge(category: str, topic: str) -> str:
    """加载特定类别和主题的知识内容"""
    pass

def search_knowledge(query: str) -> List[str]:
    """在知识库中搜索相关内容"""
    pass

def get_vulnerability_patterns() -> Dict[str, str]:
    """获取所有漏洞模式"""
    pass
```

### 知识类别

- `access_control`: 访问控制漏洞
- `reentrancy`: 重入攻击模式
- `arithmetic`: 算术溢出/下溢
- `cross_contract`: 跨合约安全
- `liquidation`: 清算机制
- `slippage`: 滑点保护

## 错误处理

组件包含全面的错误处理：
- 缺少知识文件
- 无效的知识格式
- 搜索失败
- 知识损坏

## 贡献

1. Fork 仓库
2. 创建功能分支
3. 添加或更新知识内容
4. 遵循知识格式化指南
5. 提交拉取请求

## 知识指南

### 内容结构

- **概述**: 主题的简要描述
- **漏洞模式**: 常见漏洞模式
- **示例**: 代码示例和案例研究
- **预防**: 预防策略和最佳实践
- **参考资料**: 其他资源和参考资料

### 格式化标准

- 使用清晰简洁的语言
- 在适当的地方包含代码示例
- 提供实用的预防策略
- 保持一致的格式化

## 许可证

本组件是 Finite Monkey Engine 项目的一部分，遵循相同的许可条款。 