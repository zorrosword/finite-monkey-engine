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
# Database connection
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# API settings
OPENAI_API_BASE="api.example.com"
OPENAI_API_KEY=sk-your-api-key-here

# Model settings
VUL_MODEL_ID=gpt-4-turbo
CLAUDE_MODEL=claude-3-5-sonnet-20240620

# Azure configuration
AZURE_API_KEY="your-azure-api-key"
AZURE_API_BASE="https://your-resource.openai.azure.com/"
AZURE_API_VERSION="2024-02-15-preview"
AZURE_DEPLOYMENT_NAME="your-deployment"

# API selection
AZURE_OR_OPENAI="OPENAI"  # Options: OPENAI, AZURE, CLAUDE

# Scan parameters
BUSINESS_FLOW_COUNT=4
SWITCH_FUNCTION_CODE=False
SWITCH_BUSINESS_CODE=True
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

1. claude 3.5 sonnet in scanning provides better results with acceptable time cost, GPT-3 not fully tested
2. Deceptive prompt theory adaptable to any language with minor modifications
3. ANTLR AST parsing recommended for better code slicing results
4. Currently supports Solidity, plans to expand language support
5. DeepSeek-R1 is recommended for better confirmation results
## 🛡️ Scanning Features

- Excels at code understanding and logic vulnerability detection
- Weaker at control flow vulnerability detection
- Designed for real projects, not academic test cases

## 💡 Implementation Tips

- Progress automatically saved per scan
- claude-3.5-sonnet offers best performance in scanning compared to other models
- deepseek-R1 offers best performance in confirmation compared to other models
- 10 iterations for medium projects take about 4 hours
- Results include detailed categorization

## 📝 License

Apache License 2.0

## 🤝 Contributing

Pull Requests welcome!

---

*Note: Project name inspired by [Large Language Monkeys paper](https://arxiv.org/abs/2407.21787v1)*

Would you like me to explain or break down the code?