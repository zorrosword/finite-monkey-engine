# Prompt Factory Module

## Overview

The Prompt Factory module is a sophisticated prompt engineering and assembly system designed for AI-powered code analysis and vulnerability detection. It provides a comprehensive collection of specialized prompts optimized for smart contract auditing, blockchain analysis, and multi-language code security assessment.

## Core Components

### Prompt Assembler (`prompt_assembler.py`)
The central prompt assembly engine that combines various prompt components:
- **Multi-mode Assembly**: Different prompt strategies for various scanning modes
- **Dynamic Composition**: Runtime prompt customization based on context
- **Template Management**: Efficient prompt template organization
- **Quality Optimization**: Fine-tuned prompts for maximum AI effectiveness

### Vulnerability Prompts (`vul_prompt.py`, `vul_prompt_common.py`, `vul_check_prompt.py`)
Specialized prompts for vulnerability detection:
- **Smart Contract Vulnerabilities**: Comprehensive coverage of DeFi and blockchain-specific issues
- **Common Patterns**: Generic vulnerability patterns across languages
- **Verification Prompts**: Specialized prompts for vulnerability confirmation
- **Business Logic**: Prompts for complex business flow analysis

### Core Prompts (`core_prompt.py`)
Foundational prompt structures:
- **Base Templates**: Core prompt frameworks for different analysis types
- **Role Definitions**: AI role and behavior specifications
- **Task Instructions**: Clear and precise task definitions
- **Output Formatting**: Structured response format guidelines

### Periphery Prompts (`periphery_prompt.py`)
Supporting prompt components:
- **Context Setting**: Environment and role establishment
- **Guidelines**: Analysis guidelines and best practices
- **Safety Instructions**: Prompt injection prevention and safety measures
- **Language-specific**: Tailored prompts for different programming languages

### Checklist Prompts (`checklist_pipeline_prompt.py`, `checklists_prompt.py`)
Systematic checklist-based analysis:
- **Pipeline Integration**: Checklist processing within analysis pipelines
- **Comprehensive Coverage**: Extensive security checklist templates
- **Customizable Checklists**: User-defined checklist support
- **Progress Tracking**: Checklist completion monitoring

## Key Features

### 🎯 Specialized Prompt Engineering
- **Domain Expertise**: Deep understanding of blockchain and smart contract security
- **Multi-language Support**: Optimized prompts for Solidity, Rust, Go, C++, and more
- **Context-Aware**: Dynamic prompt adaptation based on code context
- **Performance Optimized**: Engineered for maximum AI model effectiveness

### 🔧 Modular Architecture
- **Component-based Design**: Reusable prompt components for efficient assembly
- **Template System**: Flexible template management for different use cases
- **Configuration Driven**: Easy customization through configuration parameters
- **Extensible Framework**: Simple addition of new prompt types and strategies

### 🛡️ Security-Focused Design
- **Vulnerability Coverage**: Comprehensive vulnerability pattern coverage
- **Business Logic Analysis**: Specialized prompts for complex business flow analysis
- **False Positive Reduction**: Carefully crafted prompts to minimize false alarms
- **Verification Support**: Multi-stage verification prompt strategies

### 📊 Quality Assurance
- **Prompt Validation**: Built-in prompt quality validation
- **A/B Testing Support**: Framework for prompt effectiveness testing
- **Metrics Integration**: Performance tracking and optimization
- **Continuous Improvement**: Data-driven prompt refinement

## Architecture

```
Prompt Factory Module
├── Prompt Assembler (Central Engine)
│   ├── Multi-mode Assembly
│   ├── Dynamic Composition
│   └── Template Management
├── Vulnerability Prompts
│   ├── Smart Contract Specific
│   ├── Common Patterns
│   └── Verification Logic
├── Core Prompts
│   ├── Base Templates
│   ├── Role Definitions
│   └── Task Instructions
├── Periphery Prompts
│   ├── Context Setting
│   ├── Guidelines
│   └── Safety Instructions
└── Checklist Prompts
    ├── Pipeline Integration
    └── Systematic Analysis
```

## Prompt Types and Modes

### Scanning Modes
- **Common Mode**: General-purpose vulnerability scanning
- **Fine-grained Mode**: Detailed analysis with specific vulnerability focus
- **Pure Mode**: Clean analysis without business context
- **Checklist Mode**: Systematic checklist-based analysis

### Vulnerability Categories
- **Access Control**: Authorization and permission issues
- **Reentrancy**: Cross-function call vulnerabilities
- **Oracle Manipulation**: Price feed and data source attacks
- **Flash Loan Attacks**: MEV and arbitrage vulnerabilities
- **Governance Attacks**: DAO and voting mechanism issues
- **Bridge Security**: Cross-chain protocol vulnerabilities

## Usage Examples

### Basic Prompt Assembly
```python
from prompt_factory.prompt_assembler import PromptAssembler

# Assemble common vulnerability scanning prompt
code = "function transfer(address to, uint256 amount) { ... }"
prompt = PromptAssembler.assemble_prompt_common(code)
```

### Fine-grained Analysis
```python
# Assemble fine-grained prompt with specific vulnerability focus
prompt_index = 1  # Specific vulnerability type
prompt = PromptAssembler.assemble_prompt_common_fine_grained(code, prompt_index)
```

### Pure Analysis Mode
```python
# Assemble pure analysis prompt without business context
prompt = PromptAssembler.assemble_prompt_pure(code)
```

### Checklist-based Analysis
```python
from prompt_factory.checklist_pipeline_prompt import ChecklistPipelinePrompt

# Generate checklist-based analysis prompt
checklist_prompt = ChecklistPipelinePrompt.generate_checklist_prompt(vulnerability_type)
```

## Prompt Customization

### Business Type Integration
```python
# Get vulnerability prompts for specific business types
business_types = ["defi", "nft", "dao"]
vul_prompts = PromptAssembler._get_vul_prompts(business_types)
```

### Language-specific Prompts
```python
# Solidity-specific role setting
role_prompt = PeripheryPrompt.role_set_solidity_common()

# Go-specific role setting
role_prompt = PeripheryPrompt.role_set_go_common()
```

## Configuration

The module supports extensive configuration through:

- **Prompt Templates**: Customizable prompt templates for different scenarios
- **Business Type Mapping**: Vulnerability prompt mapping for different business domains
- **Language Settings**: Language-specific prompt adaptations
- **Quality Parameters**: Prompt quality and effectiveness tuning

## Integration Points

### Input Sources
- **Code Analysis**: Direct code input for vulnerability analysis
- **Business Context**: Business flow and domain-specific information
- **Project Metadata**: Project type and characteristics

### Output Consumers
- **AI Models**: OpenAI GPT, Claude, and other language models
- **Reasoning Module**: Advanced reasoning and analysis engines
- **Validation Systems**: Multi-stage verification processes

## Best Practices

### Prompt Engineering
- **Clear Instructions**: Precise and unambiguous task definitions
- **Context Provision**: Adequate context for accurate analysis
- **Output Structuring**: Well-defined response formats
- **Safety Measures**: Robust prompt injection prevention

### Performance Optimization
- **Token Efficiency**: Optimized prompt length for cost effectiveness
- **Response Quality**: Balanced prompts for high-quality outputs
- **Caching Strategy**: Intelligent prompt caching for repeated patterns
- **Version Control**: Systematic prompt version management

## Future Enhancements

- **AI-Generated Prompts**: Machine learning-powered prompt generation
- **Dynamic Adaptation**: Real-time prompt optimization based on performance
- **Multi-modal Support**: Integration with code visualization and analysis
- **Community Contributions**: Framework for community-driven prompt improvements