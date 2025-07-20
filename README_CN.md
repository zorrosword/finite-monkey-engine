# Finite Monkey Engine

**基于AI的智能合约安全分析平台**

## 🎯 概述

Finite Monkey Engine是一个先进的智能合约安全分析平台，利用AI和前沿分析技术为区块链项目提供全面的漏洞检测和业务流分析。

## 🚀 核心功能

### 🧠 AI驱动分析
- **Claude-4 Sonnet集成**：利用先进的语言模型进行智能代码理解
- **多模态分析**：结合静态分析和AI驱动的语义理解
- **上下文感知检测**：具备业务逻辑理解的智能漏洞检测

### 📊 业务流可视化
- **Mermaid图表自动生成**：自动生成业务流程图
- **交互式分析**：合约交互和依赖关系的可视化表示
- **多层次粒度**：项目级、文件夹级和函数级分析

### 🔍 高级安全功能
- **全面漏洞检测**：检测常见和复杂的智能合约漏洞
- **业务逻辑分析**：理解DeFi协议、治理机制和代币经济学
- **跨合约分析**：多合约交互分析和依赖关系跟踪

### 🛠 模块化架构
- **规划模块**：智能任务规划和业务流提取
- **验证模块**：全面的漏洞检查和验证
- **上下文模块**：具备RAG和调用树分析的高级上下文管理
- **代码总结器**：具备强化学习能力的智能代码分析

## 📁 项目结构

```
finite-monkey-engine/
├── src/
│   ├── planning/           # 任务规划和业务流分析
│   ├── validating/         # 漏洞检测和验证
│   ├── context/            # 上下文管理和RAG处理
│   ├── code_summarizer/    # AI驱动的代码分析和总结
│   ├── reasoning/          # 分析推理和对话管理
│   ├── dao/                # 数据访问对象和实体管理
│   ├── library/            # 解析库和工具
│   ├── openai_api/        # AI API集成
│   └── prompt_factory/     # 提示工程和管理
├── knowledges/             # 领域知识库
├── scripts/                # 实用脚本
└── docs/                   # 文档
```

## 🚀 快速开始

### 前置要求

- Python 3.9+
- Node.js 16+ (用于某些分析功能)
- OpenAI API密钥或兼容的AI服务

### 安装

1. **克隆代码库**
   ```bash
   git clone https://github.com/your-org/finite-monkey-engine.git
   cd finite-monkey-engine
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境**
   ```bash
   cp .env.example .env
   # 编辑.env文件，配置您的API密钥和设置
   ```

4. **运行分析**
   ```bash
   python src/main.py
   ```

## 🔧 配置

### 分析模式

平台支持多种分析模式：

- **业务流模式** (`SWITCH_BUSINESS_CODE=True`)：专注于业务逻辑分析
- **文件级模式** (`SWITCH_FILE_CODE=True`)：全面的逐文件分析
- **细粒度模式** (`SCAN_MODE=COMMON_PROJECT_FINE_GRAINED`)：详细的漏洞扫描

### 环境变量

```bash
# 分析配置
SWITCH_BUSINESS_CODE=True
SWITCH_FILE_CODE=False
SCAN_MODE=COMMON_PROJECT_FINE_GRAINED

# AI配置
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# 输出配置
OUTPUT_DIR=./output
MERMAID_OUTPUT_DIR=src/codebaseQA/mermaid_output
```

## 🎯 使用场景

### DeFi协议分析
- **流动性池安全**：AMM和借贷协议分析
- **治理机制审查**：DAO治理和投票系统分析
- **代币经济学验证**：代币经济学和分配机制审查

### NFT项目安全
- **铸造逻辑分析**：NFT铸造机制和访问控制审查
- **市场集成**：二级市场集成安全分析
- **版税机制审查**：创作者版税和费用分配分析

### 跨链协议分析
- **桥接安全评估**：跨链桥接机制分析
- **多链部署**：不同链上的一致性安全
- **互操作性审查**：协议交互和依赖关系分析

## 📊 分析报告

平台生成全面的分析报告，包括：

- **安全漏洞报告**：详细的漏洞发现和严重性评级
- **业务流图表**：合约交互的可视化表示
- **Gas优化建议**：性能改进建议
- **最佳实践合规性**：安全标准和指南的遵循情况

## 🧪 测试

运行测试套件：

```bash
# 单元测试
python -m pytest tests/

# 集成测试
python -m pytest tests/integration/

# 覆盖率报告
python -m pytest --cov=src tests/
```

## 🤝 贡献

我们欢迎贡献！请查看我们的[贡献指南](CONTRIBUTING.md)了解详情。

1. Fork代码库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启Pull Request

## 📄 许可证

此项目基于Apache License 2.0许可证 - 请查看[LICENSE](LICENSE)文件了解详情。

## 🙏 致谢

- **ANTLR4**：提供Solidity解析能力
- **Claude AI**：提供高级代码理解
- **Mermaid**：提供业务流可视化
- **OpenAI**：提供AI驱动的分析能力

## 📞 支持

- **文档**：[https://finite-monkey-engine.readthedocs.io](https://finite-monkey-engine.readthedocs.io)
- **问题**：[GitHub Issues](https://github.com/your-org/finite-monkey-engine/issues)
- **讨论**：[GitHub Discussions](https://github.com/your-org/finite-monkey-engine/discussions)
- **邮件**：support@finite-monkey-engine.com

---

**🎉 Finite Monkey Engine - 让智能合约安全分析变得智能和可访问！**