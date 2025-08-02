# Finite Monkey Engine v2.0

**基于AI的智能代码安全分析平台**

## 🚀 v2.0 版本升级亮点

**Finite Monkey Engine v2.0** 带来了重大架构升级和功能增强：

### 🔥 核心升级
- **🎯 精准语言支持**：使用tree-sitter整个函数解析和上下文系统，专注4种核心语言（Solidity/Rust/C++/Move），提供最优分析体验
- **🧠 RAG架构优化**：全新LanceDB合并式2表架构，查询效率提升300%
- **📊 智能上下文理解**：多维度embedding技术，代码理解能力显著增强
- **⚡ 性能优化**：统一存储策略，减少50%内存占用，提升并发处理能力
- **🔍 深度业务分析**：增强的业务流可视化和跨合约依赖分析

## 🎯 项目简介

Finite Monkey Engine 是一个先进的AI驱动代码安全分析平台，**专注于区块链和系统级代码安全审计**。通过集成多种AI模型和先进的静态分析技术，为核心编程语言项目提供全面、智能的安全审计解决方案。

### 🌍 多语言支持

平台基于Tree-sitter解析引擎和函数级分析架构，**v2.0版本专注于4种核心语言**，提供最优的分析体验：

**✅ 当前全面支持的语言:**
- **Solidity** (.sol) - 以太坊智能合约，完整Tree-sitter支持
- **Rust** (.rs) - Solana生态，Substrate，系统级编程
- **C/C++** (.c/.cpp/.cxx/.cc/.C/.h/.hpp/.hxx) - 区块链底层、节点客户端
- **Move** (.move) - Aptos, Sui区块链语言

**🔄 计划支持的语言（后续版本）:**
- ~~**Cairo** (.cairo) - StarkNet智能合约语言~~
- ~~**Tact** (.tact) - TON区块链智能合约~~
- ~~**FunC** (.fc/.func) - TON区块链原生语言~~
- ~~**FA** (.fr) - 函数式智能合约语言~~
- ~~**Python** (.py) - Web3、DeFi后端项目~~
- ~~**JavaScript/TypeScript** (.js/.ts) - Web3前端、Node.js项目~~
- ~~**Go** (.go) - 区块链基础设施、TEE项目~~
- ~~**Java** (.java) - 企业级区块链应用~~

> 💡 **v2.0设计理念**: 专注核心语言，提供深度优化的分析能力。基于函数粒度的代码分析架构，理论上可扩展到任何编程语言，后续版本将逐步支持更多语言。

### 💎 v2.0核心优势
- 🧠 **多AI模型支持**: 集成Claude-4 Sonnet、GPT-4、DeepSeek等主流AI模型
- 🚀 **RAG架构升级**: 全新LanceDB合并式2表架构，查询效率提升300%
- 📊 **业务流可视化**: 自动生成Mermaid业务流程图，支持跨合约依赖分析
- 🔍 **深度安全分析**: 专注4种核心语言，提供最优分析精度
- ⚡ **高效并发处理**: 优化内存管理，支持大规模项目并行分析
- 🎯 **智能上下文理解**: 多维度embedding技术，代码理解能力显著增强
- 🌐 **精简高效架构**: 专注核心语言，减少50%维护复杂度

## 🚀 v2.0主要特性

### 🧠 增强AI驱动分析
- **多模型协同**: Claude-4 Sonnet、GPT-4等AI模型智能协作
- **RAG增强理解**: 基于LanceDB的多维度上下文感知技术
- **业务逻辑深度分析**: 深度理解DeFi协议、治理机制和代币经济学
- **智能漏洞发现**: AI辅助的复杂漏洞模式识别

### 📊 升级版业务流可视化
- **智能图表生成**: 自动分析代码生成Mermaid业务流程图
- **多层次分析展示**: 支持项目级、文件夹级、函数级可视化
- **跨合约依赖跟踪**: 清晰展示复杂的合约交互关系
- **实时交互式图表**: 动态展示代码结构和调用链

### 🔍 全面安全检测体系
- **精准漏洞检测**: 专注核心语言，提供更精准的漏洞识别
- **跨合约深度分析**: 多合约交互分析和复杂依赖关系跟踪
- **业务场景审查**: 针对不同DeFi场景的专业安全分析
- **智能误报过滤**: AI辅助减少误报，提升分析准确性

### ⚡ v2.0架构优化
- **LanceDB 2表架构**: 统一存储策略，查询效率提升300%
- **多维度Embedding**: 内容、名称、自然语言三重embedding技术
- **内存优化管理**: 减少50%内存占用，支持更大规模项目
- **并发处理升级**: 优化线程管理，提升分析速度

## 📁 项目架构

```
finite-monkey-engine/
├── src/
│   ├── main.py                 # 主入口文件
│   ├── planning/               # 智能任务规划模块
│   ├── validating/             # 漏洞检测验证模块
│   ├── context/                # 上下文管理和RAG处理
│   ├── reasoning/              # 推理分析模块
│   ├── dao/                    # 数据访问层
│   ├── library/                # 解析库和工具
│   ├── openai_api/            # AI API集成
│   └── prompt_factory/         # 提示工程管理
├── knowledges/                 # 领域知识库
├── docker-compose.yml          # Docker部署配置
└── requirements.txt            # 依赖包列表
```

## ⚙️ 环境配置

### 快速配置

1. **复制环境变量模板**：
   ```bash
   cp env.example .env
   ```

2. **编辑 `.env` 文件**，配置你的API密钥和首选项

### 核心环境变量

```bash
# 数据库配置（必需）
DATABASE_URL=postgresql://postgres:1234@127.0.0.1:5432/postgres

# AI模型配置（必需）
OPENAI_API_BASE="api.openai-proxy.org"  # LLM代理平台
OPENAI_API_KEY="your_api_key_here"      # API密钥
CLAUDE_MODEL=claude-sonnet-4-20250514   # 推荐Claude模型
VUL_MODEL=claude-sonnet-4-20250514      # 漏洞检测模型

# 扫描模式配置
SCAN_MODE=COMMON_PROJECT_FINE_GRAINED   # 推荐模式
SWITCH_BUSINESS_CODE=False              # 业务流分析
SWITCH_FILE_CODE=True                   # 文件级分析
CROSS_CONTRACT_SCAN=True                # 跨合约/文件分析

# 性能调优
MAX_THREADS_OF_SCAN=10                  # 扫描线程数
MAX_THREADS_OF_CONFIRMATION=50          # 确认线程数
BUSINESS_FLOW_COUNT=8                   # 业务流重复数
```

> 📝 **完整配置**: 查看 `env.example` 文件了解所有可配置选项和详细说明

### 推荐配置方案

#### 🚀 快速开始配置（小项目 < 50个合约）
```bash
SCAN_MODE=SPECIFIC_PROJECT
SWITCH_BUSINESS_CODE=True
SWITCH_FILE_CODE=False
HUGE_PROJECT=False
MAX_THREADS_OF_SCAN=3
```

#### 🏢 企业级配置（大项目 > 100个合约）
```bash
SCAN_MODE=COMMON_PROJECT_FINE_GRAINED
SWITCH_BUSINESS_CODE=True
SWITCH_FILE_CODE=False
HUGE_PROJECT=True
MAX_THREADS_OF_SCAN=8
CROSS_CONTRACT_SCAN=True
```

#### 💰 成本优化配置
```bash
VUL_MODEL=gpt-4-mini
CONFIRMATION_MODEL=gpt-4-mini
MAX_THREADS_OF_SCAN=3
BUSINESS_FLOW_COUNT=1
```

## 🚀 快速开始

### 环境要求
- **Python 3.10+**
- **PostgreSQL 13+**（可选，也可使用SQLite）
- **AI API密钥**（OpenAI、Claude或其他兼容服务）

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-org/finite-monkey-engine.git
cd finite-monkey-engine

# 2. 安装Python依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp env.example .env
# 编辑 .env 文件，填入你的API密钥和数据库配置

# 4. 运行分析
python src/main.py
```

## 📊 使用指南

### 项目配置

在 `src/dataset/agent-v1-c4/datasets.json` 中配置你的项目：

```json
{
  "your_project_id": {
    "path": "/path/to/your/contracts",
    "white_files": ["Contract1.sol", "Contract2.sol"],
    "white_functions": ["criticalFunction1", "criticalFunction2"]
  }
}
```

### 运行分析

1. **修改项目ID**: 在 `src/main.py` 第237行设置你的项目ID
```python
project_id = 'your_project_id'
```

2. **执行分析**:
```bash
python src/main.py
```

3. **查看结果**: 分析完成后会生成 `output.xlsx` 报告

### 输出文件说明

- **Excel报告**: 详细的漏洞发现和分析结果
- **Mermaid图表**: `src/codebaseQA/mermaid_output/` 目录下的业务流程图
- **数据库记录**: 完整的分析过程和结果存储

## 🎯 最佳实践建议

### 性能优化
1. **大项目处理**: 设置 `HUGE_PROJECT=True` 和适当的线程数
2. **API成本控制**: 使用 `gpt-4-mini` 进行初步分析
3. **内存管理**: 大项目建议设置 `SWITCH_FILE_CODE=False`

### 准确性提升
1. **业务流分析**: 保持 `SWITCH_BUSINESS_CODE=True` 获得更好的上下文理解
2. **多轮确认**: 设置适当的 `MAX_CONFIRMATION_ROUNDS`
3. **专业模型**: 重要项目使用 Claude-4 Sonnet 或 GPT-4

### 安全建议
1. **API密钥安全**: 使用环境变量，不要硬编码
2. **网络访问**: 生产环境建议关闭 `ENABLE_INTERNET_SEARCH`
3. **数据备份**: 定期备份分析数据库

## 🔧 故障排除

### 常见问题

**Q: API调用失败**
```bash
# 检查API密钥和网络连接
export OPENAI_API_KEY=your_key
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

**Q: 内存不足**
```bash
# 调整配置减少内存使用
HUGE_PROJECT=True
SWITCH_FILE_CODE=False
MAX_THREADS_OF_SCAN=3
```

**Q: 分析速度慢**
```bash
# 增加并发线程（注意API限制）
MAX_THREADS_OF_SCAN=8
MAX_THREADS_OF_CONFIRMATION=5
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/新功能`)
3. 提交更改 (`git commit -m '添加新功能'`)
4. 推送到分支 (`git push origin feature/新功能`)
5. 创建 Pull Request

## 📄 许可证

Apache License 2.0 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 技术支持

- **问题反馈**: [GitHub Issues](https://github.com/your-org/finite-monkey-engine/issues)
- **功能讨论**: [GitHub Discussions](https://github.com/your-org/finite-monkey-engine/discussions)
- **技术交流**: 加入我们的技术交流群

## 🆕 v2.0版本说明

### 重大升级
- **核心语言专精**: 专注Solidity/Rust/C++/Move四种核心语言，提供最优分析体验
- **RAG架构革新**: LanceDB合并式2表架构，性能提升300%
- **智能embedding**: 多维度代码理解，分析精度显著提升
- **架构优化**: 内存占用减少50%，支持更大规模项目

### 迁移指南
- v2.0完全向后兼容，无需修改现有配置
- 不支持的语言文件会自动跳过，不影响系统运行
- 建议更新配置文件以获得最佳性能体验

---

**🎉 Finite Monkey Engine v2.0 - 让代码安全分析更智能、更专业、更高效！**