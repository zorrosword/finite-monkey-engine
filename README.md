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

## 📋 Prerequisites

### Python Environment
- Python 3.11 (recommended, as Python 3.12 has package compatibility issues)
- Use conda for environment management:
```bash
conda create -n py311 python=3.11
conda activate py311
```

### PostgreSQL Database
1. Install PostgreSQL:
```bash
# Install and start PostgreSQL (macOS)
brew install postgresql
brew services start postgresql
initdb /usr/local/var/postgres -E utf8

# Connect to database
psql postgres

# Check databases
\l

# Set password for database user
\password [your_username]

# Exit connection
exit
```

2. Install pgAdmin from [https://www.pgadmin.org/download/](https://www.pgadmin.org/download/) for database management
   - Host: 127.0.0.1
   - Port: 5432
   - Username: your database owner username
   - Password: as set above

### AI API Configuration
Purchase AI API access from [https://platform.closeai-asia.com/account/billing](https://platform.closeai-asia.com/account/billing)
Get your API key from Developer Mode -> Key Management

## 🛠️ Installation & Setup

### 1. Get the Code
```bash
git clone https://github.com/BradMoonUESTC/finite-monkey-engine.git
cd finite-monkey-engine
pip install -r requirements.txt
```

### 2. Database Setup
Execute the SQL file `src/db.sql` in pgAdmin to create the required tables. If you encounter ownership errors, modify `OWNER TO "postgres"` to use your actual database username.

### 3. Sample Data (Optional)
Download the `concise_project_code` directory from [Google Drive](https://drive.google.com/drive/folders/1M3Fn3FOBX2EFAvBkXG4GVOT0ZlCmJgjQ) and place the files in `finite-monkey-engine/src/dataset/agent-v1-c4/`

### 4. Environment Configuration
Create `src/.env` file with the following configuration:

```env
# =============================================================================
# 数据库配置 / Database Configuration
# =============================================================================

# 数据库连接URL，使用PostgreSQL数据库
# Database connection URL using PostgreSQL
DATABASE_URL=postgresql://postgres:your_password@127.0.0.1:5432/your_database

# =============================================================================
# LLM API配置 / LLM API Configuration
# =============================================================================

# 所有LLM的基础URL（LLM中转平台），用于API请求
# Base URL for all LLM requests (LLM proxy platform)
OPENAI_API_BASE="api.openai-proxy.org"

# LLM中转平台的API密钥
# API key for LLM proxy platform
OPENAI_API_KEY="sk-your_openai_api_key_here"

# =============================================================================
# 嵌入模型配置 / Embedding Model Configuration
# =============================================================================

# 用于文本嵌入的模型名称
# Model name used for text embeddings
EMBEDDING_MODEL="text-embedding-3-large"
EMBEDDING_API_BASE="api.openai-proxy.org"
EMBEDDING_API_KEY="sk-your_embedding_api_key_here"

# =============================================================================
# JSON模型配置 / JSON Model Configuration
# =============================================================================

JSON_MODEL_API_BASE="api.openai-proxy.org"
JSON_MODEL_API_KEY="sk-your_json_model_api_key_here"
JSON_MODEL_ID="gpt-4o-mini"

# =============================================================================
# 模型选择配置 / Model Selection Configuration
# =============================================================================

# 确认模型的选择
# Confirmation model selection
# 可选值: OPENAI / AZURE / CLAUDE / DEEPSEEK
CONFIRMATION_MODEL="OPENAI"

# OpenAI模型的选择
# OpenAI model selection
OPENAI_MODEL="gpt-4o-mini"

# Claude模型的选择
# Claude model selection
CLAUDE_MODEL="claude-3-5-sonnet-20241022"

# 漏洞扫描模型
# Vulnerability scanning model
VUL_MODEL="gpt-4o-mini"

# =============================================================================
# 扫描模式配置 / Scan Mode Configuration
# =============================================================================

# 扫描模式设置
# Scan mode setting
# 可选值: SPECIFIC_PROJECT / OPTIMIZE / COMMON_PROJECT / PURE_SCAN 
# / CHECKLIST / CHECKLIST_PIPELINE / COMMON_PROJECT_FINE_GRAINED
SCAN_MODE="PURE_SCAN"

# API服务提供商选择
# API service provider selection
# 可选值: OPENAI / AZURE / CLAUDE / DEEPSEEK
AZURE_OR_OPENAI="OPENAI"

# =============================================================================
# 性能配置 / Performance Configuration
# =============================================================================

# 确认阶段的最大线程数
# Maximum number of threads for confirmation phase
MAX_THREADS_OF_CONFIRMATION=10

# 扫描阶段的最大线程数
# Maximum number of threads for scanning phase
MAX_THREADS_OF_SCAN=5

# 业务流程重复数量
# Business flow repeat count
BUSINESS_FLOW_COUNT=5

# 最大确认轮数
# Maximum number of confirmation rounds
MAX_CONFIRMATION_ROUNDS=2

# 每轮询问次数
# Number of requests per round
REQUESTS_PER_CONFIRMATION_ROUND=3

# =============================================================================
# 功能开关配置 / Feature Switch Configuration
# =============================================================================

# 是否启用函数代码扫描
# Whether to enable function code scanning
SWITCH_FUNCTION_CODE=False

# 是否启用业务代码扫描
# Whether to enable business code scanning
SWITCH_BUSINESS_CODE=True

# 是否启用文件代码扫描
# Whether to enable file code scanning
SWITCH_FILE_CODE=False

# 是否启用网络搜索
# Whether to enable internet search
ENABLE_INTERNET_SEARCH=False

# 是否启用对话模式
# Whether to enable dialogue mode
ENABLE_DIALOGUE_MODE=False

# 是否启用跨合约扫描
# Whether to enable cross-contract scanning
CROSS_CONTRACT_SCAN=True

# =============================================================================
# 迭代配置 / Iteration Configuration
# =============================================================================

# 项目清单生成迭代轮数
# Number of iterations for project types generation
PROJECT_TYPE_ITERATION_ROUNDS=3

# 检查清单生成迭代轮数
# Number of iterations for checklist generation
CHECKLIST_ITERATION_ROUNDS=3

# 规划阶段的长度阈值
# Length threshold for planning phase
THRESHOLD_OF_PLANNING=150
```

### 5. Project Configuration
Edit `src/dataset/agent-v1-c4/datasets.json` to configure your projects:

```json
{
    "YourProjectName": {
        "path": "relative_path_to_your_project",
        "files": [],
        "functions": [],
        "exclude_in_planning": "true",
        "exclude_directory": ["access", "errors", "events", "lib", "storage"]
    }
}
```

**Planning Optimization Notes:**
- `THRESHOLD_OF_PLANNING`: Functions shorter than this value will be treated as context rather than main scanning targets
- `exclude_in_planning` and `exclude_directory`: Contracts in specified directories will be treated as context only

## 🚀 Usage

### Running with Sample Data
1. Choose a project name from `src/dataset/agent-v1-c4/datasets.json`
2. Edit `src/main.py` line 146 to set the `project_id`:
```python
if __name__ == '__main__':
    switch_production_or_test = 'test'  # prod / test
    if switch_production_or_test == 'test':
        start_time = time.time()
        db_url_from = os.environ.get("DATABASE_URL")
        engine = create_engine(db_url_from)
        
        dataset_base = "./src/dataset/agent-v1-c4"
        projects = load_dataset(dataset_base)
        project_id = 'YourProjectName'  # Set your project name here
        project_path = ''
        project = Project(project_id, projects[project_id])
```
3. Run the scanner:
```bash
python src/main.py
```

### Running with New Projects
1. Place your code in `finite-monkey-engine/src/dataset/agent-v1-c4/` (recommended to include only files that need auditing)
2. Add project configuration to `src/dataset/agent-v1-c4/datasets.json`
3. Update `project_id` in `src/main.py`
4. Execute `python src/main.py`

### Analyzing Results
Check the `project_tasks_amazing_prompt` database table for scan results. Each record requires manual analysis to determine if it represents a valid vulnerability.

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
2. Results include detailed annotations:
   - Focus on entries marked "yes" in result column
   - Filter "dont need In-project other contract" in category column
   - Check specific code in business_flow_code column
   - Find code location in name column

## 📝 License

Apache License 2.0

## 🤝 Contributing

Pull Requests welcome!

---

*Note: Project name inspired by [Large Language Monkeys paper](https://arxiv.org/abs/2407.21787v1)*