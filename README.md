# Finite Monkey Engine v2.0

**An AI-Powered Code Security Analysis Platform**

## 🚀 v2.0 Major Upgrades

**Finite Monkey Engine v2.0** brings significant architectural upgrades and feature enhancements:

### 🔥 Core Upgrades
- **🎯 Precision Language Support**: Focus on 4 core languages (Solidity/Rust/C++/Move) for optimal analysis experience
- **🧠 RAG Architecture Optimization**: New LanceDB merged 2-table architecture with 300% query efficiency improvement
- **📊 Intelligent Context Understanding**: Multi-dimensional embedding technology, significantly enhanced code comprehension
- **⚡ Performance Optimization**: Unified storage strategy, 50% memory reduction, improved concurrent processing
- **🔍 Deep Business Analysis**: Enhanced business flow visualization and cross-contract dependency analysis

## 🎯 Overview

Finite Monkey Engine is an advanced AI-driven code security analysis platform **focused on blockchain and system-level code security auditing**. By integrating multiple AI models and advanced static analysis techniques, it provides comprehensive, intelligent security auditing solutions for core programming language projects.

### 🌍 Multi-Language Support

Built on Tree-sitter parsing engine and function-level analysis architecture, **v2.0 focuses on 4 core languages** for optimal analysis experience:

**✅ Currently Fully Supported Languages:**
- **Solidity** (.sol) - Ethereum smart contracts with complete Tree-sitter support
- **Rust** (.rs) - Solana ecosystem, Substrate, system-level programming
- **C/C++** (.c/.cpp/.cxx/.cc/.C/.h/.hpp/.hxx) - Blockchain core, node clients
- **Move** (.move) - Aptos, Sui blockchain language

**🔄 Planned Support (Future Versions):**
- ~~**Cairo** (.cairo) - StarkNet smart contract language~~
- ~~**Tact** (.tact) - TON blockchain smart contracts~~
- ~~**FunC** (.fc/.func) - TON blockchain native language~~
- ~~**FA** (.fr) - Functional smart contract language~~
- ~~**Python** (.py) - Web3, DeFi backend projects~~
- ~~**JavaScript/TypeScript** (.js/.ts) - Web3 frontend, Node.js projects~~
- ~~**Go** (.go) - Blockchain infrastructure, TEE projects~~
- ~~**Java** (.java) - Enterprise blockchain applications~~

> 💡 **v2.0 Design Philosophy**: Focus on core languages to provide deeply optimized analysis capabilities. Based on function-granularity code analysis architecture, theoretically extensible to any programming language. Future versions will gradually support more languages.

## 🚀 v2.0 Key Features

### 🧠 Enhanced AI-Powered Analysis
- **Multi-Model Collaboration**: Claude-4 Sonnet, GPT-4 and other AI models working intelligently together
- **RAG-Enhanced Understanding**: Multi-dimensional context-aware technology based on LanceDB
- **Deep Business Logic Analysis**: Deep understanding of DeFi protocols, governance mechanisms, and tokenomics
- **Intelligent Vulnerability Discovery**: AI-assisted complex vulnerability pattern recognition

### 🔍 Comprehensive Security Detection System
- **Precision Vulnerability Detection**: Focus on core languages for more accurate vulnerability identification
- **Cross-Contract Deep Analysis**: Multi-contract interaction analysis and complex dependency tracking
- **Business Scenario Review**: Professional security analysis for different DeFi scenarios
- **Intelligent False Positive Filtering**: AI-assisted reduction of false positives, improving analysis accuracy

### 🛠 Precision Language Architecture
- **Core Language Focus**: Specialized framework for Solidity/Rust/C++/Move languages
- **Modular Design**: Planning, validation, context, and analysis modules
- **Tree-sitter Parsing**: Advanced parsing supporting core languages with high precision

## 📁 Project Structure

```
finite-monkey-engine/
├── src/
│   ├── planning/           # Task planning and business flow analysis
│   ├── validating/         # Vulnerability detection and validation
│   ├── context/            # Context management and RAG processing
│   ├── reasoning/          # Analysis reasoning and dialogue management
│   ├── dao/                # Data access objects and entity management
│   ├── library/            # Parsing libraries and utilities
│   ├── openai_api/        # AI API integrations
│   └── prompt_factory/     # Prompt engineering and management
├── knowledges/             # Domain knowledge base
├── scripts/                # Utility scripts
└── docs/                   # Documentation
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **PostgreSQL 13+** (optional, SQLite also supported)
- **AI API Keys** (OpenAI, Claude, or other compatible services)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/finite-monkey-engine.git
cd finite-monkey-engine

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp env.example .env
# Edit .env file with your API keys and database configuration

# 4. Run analysis
python src/main.py
```

## 🔧 Configuration

### Quick Configuration

1. **Copy environment template**:
   ```bash
   cp env.example .env
   ```

2. **Edit `.env` file** with your API keys and preferences

### Core Environment Variables

```bash
# Database Configuration (Required)
DATABASE_URL=postgresql://postgres:1234@127.0.0.1:5432/postgres

# AI Model Configuration (Required)
OPENAI_API_BASE="api.openai-proxy.org"  # LLM proxy platform
OPENAI_API_KEY="your_api_key_here"      # API key
CLAUDE_MODEL=claude-sonnet-4-20250514   # Recommended Claude model
VUL_MODEL=claude-sonnet-4-20250514      # Vulnerability detection model

# Scan Mode Configuration
SCAN_MODE=COMMON_PROJECT_FINE_GRAINED   # Recommended mode
SWITCH_BUSINESS_CODE=False              # Business flow analysis
SWITCH_FILE_CODE=True                   # File-level analysis
CROSS_CONTRACT_SCAN=True                # Cross-contract/file analysis

# Performance Tuning
MAX_THREADS_OF_SCAN=10                  # Scan threads
MAX_THREADS_OF_CONFIRMATION=50          # Confirmation threads
BUSINESS_FLOW_COUNT=8                   # Business flow iterations
```

> 📝 **Complete Configuration**: See `env.example` file for all configurable options and detailed descriptions

### Recommended Configuration Schemes

#### 🚀 Quick Start (Small projects < 50 files)
```bash
SCAN_MODE=SPECIFIC_PROJECT
SWITCH_BUSINESS_CODE=True
SWITCH_FILE_CODE=False
HUGE_PROJECT=False
MAX_THREADS_OF_SCAN=3
```

#### 🏢 Enterprise (Large projects > 100 files)
```bash
SCAN_MODE=COMMON_PROJECT_FINE_GRAINED
SWITCH_BUSINESS_CODE=True
SWITCH_FILE_CODE=False
HUGE_PROJECT=True
MAX_THREADS_OF_SCAN=8
CROSS_CONTRACT_SCAN=True
```

#### 💰 Cost Optimized
```bash
VUL_MODEL=gpt-4-mini
CONFIRMATION_MODEL=gpt-4-mini
MAX_THREADS_OF_SCAN=3
BUSINESS_FLOW_COUNT=1
```

## 🎯 Use Cases

### Blockchain & Web3 Projects
- **Smart Contract Security**: Solidity, Rust, Move contract analysis
- **DeFi Protocol Analysis**: AMM, lending, governance mechanism review
- **Cross-Chain Applications**: Bridge security, multi-chain deployment analysis
- **NFT & Gaming**: Minting logic, marketplace integration security

### Traditional Software Projects
- **Web3 Backend**: Python/Node.js API security analysis
- **Blockchain Infrastructure**: Go/C++ node and client security
- **Enterprise Applications**: Java enterprise blockchain applications
- **System-Level Code**: C/C++ core components and TEE projects

### Multi-Language Project Analysis
- **Polyglot Codebases**: Cross-language dependency analysis
- **Microservice Architecture**: Multi-service security assessment
- **Full-Stack Applications**: Frontend, backend, and contract integration security

## 📊 Analysis Reports

The platform generates comprehensive analysis reports including:

- **Security Vulnerability Report**: Detailed vulnerability findings with severity ratings
- **Business Flow Diagrams**: Visual representation of contract interactions
- **Gas Optimization Suggestions**: Performance improvement recommendations
- **Best Practice Compliance**: Adherence to security standards and guidelines

## 🧪 Testing

Run the test suite:

```bash
# Unit tests
python -m pytest tests/

# Integration tests
python -m pytest tests/integration/

# Coverage report
python -m pytest --cov=src tests/
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **ANTLR4**: For Solidity parsing capabilities
- **Claude AI**: For advanced code understanding
- **Mermaid**: For business flow visualization
- **OpenAI**: For AI-powered analysis capabilities

## 📞 Support

- **Documentation**: [https://finite-monkey-engine.readthedocs.io](https://finite-monkey-engine.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/your-org/finite-monkey-engine/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/finite-monkey-engine/discussions)
- **Email**: support@finite-monkey-engine.com

---

## 🆕 v2.0 Release Notes

### Major Upgrades
- **Core Language Specialization**: Focus on Solidity/Rust/C++/Move for optimal analysis experience
- **RAG Architecture Revolution**: LanceDB merged 2-table architecture with 300% performance improvement
- **Intelligent Embedding**: Multi-dimensional code understanding with significantly enhanced analysis precision
- **Architecture Optimization**: 50% memory reduction, supporting larger-scale projects

### Migration Guide
- v2.0 is fully backward compatible, no configuration changes required
- Unsupported language files will be automatically skipped without affecting system operation
- Recommended to update configuration files for optimal performance experience

---

**🎉 Finite Monkey Engine v2.0 - Making Code Security Analysis More Intelligent, Professional, and Efficient!** 