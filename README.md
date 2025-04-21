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
# Database connection URL, using PostgreSQL database
DATABASE_URL=postgresql://postgres:1234@127.0.0.1:5432/postgres

# Base URL for all LLMs (LLM proxy platform), used for API requests
OPENAI_API_BASE="api.openai-proxy.org"

# Model name used for text embeddings
EMBEDDING_MODEL="text-embedding-3-large"

# API key for LLM proxy platform
OPENAI_API_KEY=your-api-key

# Confirmation model selection, using DeepSeek model
CONFIRMATION_MODEL="DEEPSEEK"

# OpenAI model selection, using GPT-4 Turbo
OPENAI_MODEL=gpt-4-turbo

# Claude model selection, using Claude 3.5 Sonnet version
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Scan mode settings
# Available values: SPECIFIC_PROJECT (specific project checklist) / OPTIMIZE (code suggestion mode)
# / COMMON_PROJECT (common project checklist single query) / PURE_SCAN (pure scanning)
# / CHECKLIST (automatic checklist generation) / CHECKLIST_PIPELINE (checklist generation + pipeline)
# / COMMON_PROJECT_FINE_GRAINED (common project checklist individual queries, 10x cost increase, currently best results)
SCAN_MODE=COMMON_PROJECT_FINE_GRAINED

# API service provider selection
# Available values: OPENAI / AZURE / CLAUDE / DEEPSEEK
AZURE_OR_OPENAI="OPENAI"

# Maximum threads for confirmation phase
MAX_THREADS_OF_CONFIRMATION=50

# Maximum threads for scanning phase
MAX_THREADS_OF_SCAN=10

# Business flow repeat count
BUSINESS_FLOW_COUNT=10

# Enable function code scanning
SWITCH_FUNCTION_CODE=False

# Enable business code scanning
SWITCH_BUSINESS_CODE=True

# Maximum confirmation rounds
MAX_CONFIRMATION_ROUNDS=2

# Requests per confirmation round
REQUESTS_PER_CONFIRMATION_ROUND=3

# JSON model ID
JSON_MODEL_ID="gpt-4-turbo"

# Enable internet search
ENABLE_INTERNET_SEARCH=False

# Set project type generation iteration rounds
PROJECT_TYPE_ITERATION_ROUNDS=3

# Set checklist generation iteration rounds
CHECKLIST_ITERATION_ROUNDS=3

# Enable dialogue mode
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