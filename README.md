# Finite Monkey Engine

**An AI-Powered Smart Contract Security Analysis Platform**

## 🎯 Overview

Finite Monkey Engine is an advanced smart contract security analysis platform that leverages AI and cutting-edge analysis techniques to provide comprehensive vulnerability detection and business flow analysis for blockchain projects.

## 🚀 Key Features

### 🧠 AI-Powered Analysis
- **Claude-4 Sonnet Integration**: Utilizes advanced language models for intelligent code understanding
- **Multi-modal Analysis**: Combines static analysis with AI-driven semantic understanding
- **Context-Aware Detection**: Smart vulnerability detection with business logic understanding

### 📊 Business Flow Visualization
- **Mermaid Diagram Generation**: Automatic generation of business flow diagrams
- **Interactive Analysis**: Visual representation of contract interactions and dependencies
- **Multi-level Granularity**: Project-level, folder-level, and function-level analysis

### 🔍 Advanced Security Features
- **Comprehensive Vulnerability Detection**: Detection of common and complex smart contract vulnerabilities
- **Business Logic Analysis**: Understanding of DeFi protocols, governance mechanisms, and token economics
- **Cross-Contract Analysis**: Multi-contract interaction analysis and dependency tracking

### 🛠 Modular Architecture
- **Planning Module**: Intelligent task planning and business flow extraction
- **Validation Module**: Comprehensive vulnerability checking and validation
- **Context Module**: Advanced context management with RAG and call tree analysis
- **Code Summarizer**: Smart code analysis with reinforcement learning capabilities

## 📁 Project Structure

```
finite-monkey-engine/
├── src/
│   ├── planning/           # Task planning and business flow analysis
│   ├── validating/         # Vulnerability detection and validation
│   ├── context/            # Context management and RAG processing
│   ├── code_summarizer/    # AI-powered code analysis and summarization
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

- Python 3.9+
- Node.js 16+ (for certain analysis features)
- OpenAI API key or compatible AI service

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/finite-monkey-engine.git
   cd finite-monkey-engine
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Run the analysis**
   ```bash
   python src/main.py
   ```

## 🔧 Configuration

### Analysis Modes

The platform supports multiple analysis modes:

- **Business Flow Mode** (`SWITCH_BUSINESS_CODE=True`): Focus on business logic analysis
- **File-Level Mode** (`SWITCH_FILE_CODE=True`): Comprehensive file-by-file analysis
- **Fine-Grained Mode** (`SCAN_MODE=COMMON_PROJECT_FINE_GRAINED`): Detailed vulnerability scanning

### Environment Variables

```bash
# Analysis Configuration
SWITCH_BUSINESS_CODE=True
SWITCH_FILE_CODE=False
SCAN_MODE=COMMON_PROJECT_FINE_GRAINED

# AI Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# Output Configuration
OUTPUT_DIR=./output
MERMAID_OUTPUT_DIR=src/codebaseQA/mermaid_output
```

## 🎯 Use Cases

### DeFi Protocol Analysis
- **Liquidity Pool Security**: Analysis of AMM and lending protocols
- **Governance Mechanism Review**: DAO governance and voting system analysis
- **Token Economics Validation**: Tokenomics and distribution mechanism review

### NFT Project Security
- **Minting Logic Analysis**: NFT minting mechanism and access control review
- **Marketplace Integration**: Secondary market integration security analysis
- **Royalty Mechanism Review**: Creator royalty and fee distribution analysis

### Cross-Chain Protocol Analysis
- **Bridge Security Assessment**: Cross-chain bridge mechanism analysis
- **Multi-Chain Deployment**: Consistent security across different chains
- **Interoperability Review**: Protocol interaction and dependency analysis

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

**🎉 Finite Monkey Engine - Making Smart Contract Security Analysis Intelligent and Accessible!** 