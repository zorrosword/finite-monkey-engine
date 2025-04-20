# FiniteMonkey

<p align="center">
  <img src="image.jpeg" width="500">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg">
  <img src="https://img.shields.io/badge/version-1.0-green.svg">
  <img src="https://img.shields.io/badge/bounties-$60,000+-yellow.svg">
</p>

FiniteMonkey is an intelligent vulnerability mining engine based on large language models, requiring no pre-trained knowledge base or fine-tuning. Its core feature is using task-driven and prompt engineering approaches to guide models in vulnerability analysis through carefully designed prompts.

## 🌟 Core Concepts

- **Task-driven rather than problem-driven**
- **Prompt-driven rather than code-driven**
- **Focus on prompt design rather than model design**
- **Leverage "deception" and hallucination as key mechanisms**

## 🏆 Achievements

As of May 2024, this tool has helped discover over $60,000 worth of bug bounties.

## 🚀 Latest Updates

**2024.11.19**: Released version 1.0 - Validated LLM-based auditing and productization feasibility

**Earlier Updates:**
- 2024.08.02: Project renamed to finite-monkey-engine
- 2024.08.01: Added Func, Tact language support
- 2024.07.23: Added Cairo, Move language support
- 2024.07.01: Updated license
- 2024.06.01: Added Python language support
- 2024.05.18: Improved false positive rate (~20%)
- 2024.05.16: Added cross-contract vulnerability confirmation
- 2024.04.29: Added basic Rust language support

## 📋 Requirements

- PostgreSQL database
- OpenAI API access
- Python environment

## 🛠️ Installation & Configuration

1. Place project in `src/dataset/agent-v1-c4` directory

2. Configure project in `datasets.json`:
```json
{
    "StEverVault2": {
        "path": "StEverVault",
        "files": [],
        "functions": []
    }
}
```

3. Create database using `src/db.sql`

4. Configure `.env`:
```env
# 数据库连接URL，使用PostgreSQL数据库
DATABASE_URL=postgresql://postgres:1234@127.0.0.1:5432/postgres

# 所有llm的基础URL（llm中转平台），用于API请求
OPENAI_API_BASE="api.openai-proxy.org"

# 用于文本嵌入的模型名称
EMBEDDING_MODEL="text-embedding-3-large"

# llm中转平台的API密钥
OPENAI_API_KEY=your-api-key

# 确认模型的选择，使用DeepSeek模型
CONFIRMATION_MODEL="DEEPSEEK"

# OpenAI模型的选择，使用GPT-4 Turbo
OPENAI_MODEL=gpt-4-turbo

# Claude模型的选择，使用Claude 3.5 Sonnet版本
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# 扫描模式设置
# 可选值：SPECIFIC_PROJECT(特定项目CHECKLIST) / OPTIMIZE(代码建议模式) 
# / COMMON_PROJECT(通用项目CHECKLIST一次性提问) / PURE_SCAN(纯扫描) 
# / CHECKLIST(检查清单自动生成) / CHECKLIST_PIPELINE(检查清单自动生成+pipeline)
# / COMMON_PROJECT_FINE_GRAINED(通用项目CHECKLIST逐个提问，成本会提升10倍，效果当前最好)
SCAN_MODE=COMMON_PROJECT_FINE_GRAINED

# API服务提供商选择
# 可选值：OPENAI / AZURE / CLAUDE / DEEPSEEK
AZURE_OR_OPENAI="OPENAI"

# 确认阶段的最大线程数
MAX_THREADS_OF_CONFIRMATION=50

# 扫描阶段的最大线程数
MAX_THREADS_OF_SCAN=10

# 业务流程重复数量
BUSINESS_FLOW_COUNT=10

# 是否启用函数代码扫描
SWITCH_FUNCTION_CODE=False

# 是否启用业务代码扫描
SWITCH_BUSINESS_CODE=True

# 最大确认轮数
MAX_CONFIRMATION_ROUNDS=2

# 每轮询问次数
REQUESTS_PER_CONFIRMATION_ROUND=3

# JSON模型ID
JSON_MODEL_ID="gpt-4-turbo"

# 是否启用网络搜索
ENABLE_INTERNET_SEARCH=False

# 设置项目清单生成迭代轮数
PROJECT_TYPE_ITERATION_ROUNDS=3

# 设置检查清单生成迭代轮数
CHECKLIST_ITERATION_ROUNDS=3

# 是否启用对话模式
ENABLE_DIALOGUE_MODE=True

```

## 🌈 Supported Languages

- Solidity (.sol)
- Rust (.rs)
- Python (.py)
- Move (.move)
- Cairo (.cairo)
- Tact (.tact)
- Func (.fc)
- Java (.java)
- Pseudo-Solidity (.fr) - For scanning Solidity pseudocode

## 📊 Scan Results Guide

1. If interrupted due to network/API issues, resume scanning using the same project_id in main.py
3. Results include detailed annotations:
   - Focus on entries marked "yes" in result column
   - Filter "dont need In-project other contract" in category column
   - Check specific code in business_flow_code column
   - Find code location in name column

## 🎯 Important Notes

- Best suited for logic vulnerability mining in real projects
- Not recommended for academic vulnerability testing
- GPT-4-turbo recommended for best results
- Average scan time for medium-sized projects: 2-3 hours
- Estimated cost for 10 iterations on medium projects: $20-30
- Current false positive rate: 30-65% (depends on project size)

## 🔍 Technical Notes
1. Claude 3.5 Sonnet provides better scanning results while maintaining acceptable time costs
2. Deceptive prompt theory can be adapted to any language with minor modifications
3. ANTLR AST parsing recommended for better code slicing results
4. Currently supports multiple languages with plans for expansion
5. DeepSeek recommended for better confirmation results
6. New dialogue mode support enables more flexible interaction
7. Supports multi-round iteration for project types and checklist generation

## 🛡️ Scanning Features

- Excels at code understanding and logic vulnerability detection
- Weaker at control flow vulnerability detection
- Designed for real projects, not academic test cases

## 💡 Implementation Tips

- Progress automatically saved for each scan
- Claude-3.5-Sonnet provides best performance for scanning compared to other models
- DeepSeek provides best performance for confirmation compared to other models
- 10 iterations for medium-sized projects takes about 4 hours
- Results include detailed categorization
- Supports fine-grained common project checklist with individual questioning mode
- Configurable confirmation rounds and queries per round
- Flexible thread control with separate settings for scanning and confirmation phases

## 📝 License

Apache License 2.0

## 🤝 Contributing

Pull Requests welcome!

---

*Note: Project name inspired by [Large Language Monkeys paper](https://arxiv.org/abs/2407.21787v1)*

Would you like me to explain or break down the code?