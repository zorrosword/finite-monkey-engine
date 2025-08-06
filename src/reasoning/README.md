# Reasoning Module

## Overview

The Reasoning module provides advanced vulnerability scanning and intelligent analysis capabilities for smart contract and blockchain code auditing. It implements sophisticated reasoning algorithms, dialogue-based analysis, and context-aware vulnerability detection to deliver high-accuracy security assessments.

## Core Components

### VulnerabilityScanner (`scanner.py`)
The main vulnerability detection engine featuring:
- **Intelligent Scanning**: AI-powered vulnerability detection with advanced reasoning
- **Dialogue Mode**: Interactive analysis with conversation history management
- **Multi-threading**: Concurrent scanning for improved performance
- **Context Integration**: Deep integration with project context and call graphs

### Utils Package (`utils/`)
Supporting utilities for enhanced scanning capabilities:

#### Dialogue Manager (`utils/dialogue_manager.py`)
Advanced conversation management system:
- **Conversation History**: Maintains context across multiple interactions
- **Session Management**: Tracks analysis sessions for projects
- **Context Preservation**: Preserves important findings across dialogue turns
- **Memory Optimization**: Intelligent history management for performance

#### Scan Utils (`utils/scan_utils.py`)
Specialized scanning utilities:
- **Filter Functions**: Advanced filtering for targeted analysis
- **Result Processing**: Intelligent result aggregation and deduplication
- **Performance Optimization**: Scanning performance enhancement utilities
- **Error Handling**: Robust error management for scanning operations

## Key Features

### 🧠 Advanced Reasoning Capabilities
- **Context-Aware Analysis**: Deep understanding of code context and business logic
- **Multi-step Reasoning**: Complex vulnerability detection through multi-stage analysis
- **Pattern Recognition**: Advanced pattern matching for sophisticated attack vectors
- **False Positive Reduction**: Intelligent filtering to minimize false alarms

### 💬 Dialogue-Based Analysis
- **Interactive Mode**: Conversational analysis for complex scenarios
- **History Management**: Maintains context across multiple analysis rounds
- **Iterative Refinement**: Continuous improvement through dialogue feedback
- **Expert System**: AI-powered expert consultation for complex cases

### 🎯 Smart Contract Specialization
- **DeFi Protocol Analysis**: Specialized analysis for decentralized finance protocols
- **Cross-chain Bridge Security**: Advanced detection for bridge vulnerabilities
- **MEV Attack Vectors**: Maximal Extractable Value vulnerability detection
- **Governance Mechanisms**: DAO and voting system security analysis

### ⚡ High-Performance Scanning
- **Concurrent Processing**: Multi-threaded analysis for large codebases
- **Intelligent Prioritization**: Smart task scheduling based on risk assessment
- **Resource Optimization**: Efficient memory and CPU utilization
- **Scalable Architecture**: Handles projects of varying complexity and size

## Architecture

```
Reasoning Module
├── VulnerabilityScanner (Main Engine)
│   ├── Standard Mode Scanning
│   ├── Dialogue Mode Analysis
│   ├── Threading Management
│   └── AI Model Integration
└── Utils (Supporting Components)
    └── ScanUtils
        ├── Filter Functions
        ├── Result Processing
        └── Performance Optimization
```

## Scanning Modes

### Standard Mode
Traditional vulnerability scanning with:
- **Batch Processing**: Efficient analysis of multiple functions
- **Parallel Execution**: Concurrent scanning for performance
- **Result Aggregation**: Intelligent result compilation
- **Progress Tracking**: Real-time scanning progress monitoring

### Dialogue Mode
Interactive analysis featuring:
- **Conversational Interface**: Natural language interaction with the AI
- **Context Continuity**: Maintains conversation history
- **Expert Consultation**: Access to specialized knowledge base
- **Iterative Analysis**: Refinement through multiple dialogue rounds

## Usage Examples

### Basic Vulnerability Scanning
```python
from reasoning.scanner import VulnerabilityScanner

# Initialize scanner with project audit data
scanner = VulnerabilityScanner(project_audit)

# Execute standard scanning
results = scanner.do_scan(task_manager, is_gpt4=True)
```

### Dialogue Mode Analysis
```python
import os

# Enable dialogue mode
os.environ["ENABLE_DIALOGUE_MODE"] = "true"

# Scanner will automatically use dialogue mode
results = scanner.do_scan(task_manager, filter_func=custom_filter)
```

### Custom Filtering
```python
# Define custom filter function
def high_risk_filter(task):
    return task.risk_level >= 8

# Apply custom filter during scanning
results = scanner.do_scan(
    task_manager, 
    filter_func=high_risk_filter,
    is_gpt4=True
)
```


## Integration Points

### Input Dependencies
- **Project Audit**: TreeSitterProjectAudit for code structure analysis
- **Task Manager**: ProjectTaskMgr for task lifecycle management
- **Prompt Factory**: Advanced prompt engineering for AI interactions
- **OpenAI API**: Integration with GPT models for analysis

### Output Consumers
- **Validation Module**: Receives scanning results for verification
- **Result Processor**: Aggregates and processes scan findings
- **Reporting System**: Generates comprehensive security reports
- **Database Storage**: Persists findings for historical analysis

## Configuration Options

The module supports various configuration through environment variables:

- `ENABLE_DIALOGUE_MODE`: Enable/disable interactive dialogue mode
- `MAX_CONCURRENT_SCANS`: Control parallel scanning threads
- `DIALOGUE_HISTORY_LIMIT`: Set conversation history retention limits
- `SCAN_TIMEOUT`: Configure timeout for individual scans

## AI Model Integration

### Supported Models
- **GPT-4**: Advanced reasoning and analysis capabilities
- **GPT-3.5**: Efficient scanning for standard use cases
- **Claude**: Alternative AI model for diverse perspectives
- **Custom Models**: Framework for integrating additional AI models

### Prompt Engineering
- **Dynamic Prompts**: Context-aware prompt generation
- **Model-specific Optimization**: Tailored prompts for different AI models
- **Chain-of-Thought**: Multi-step reasoning prompt strategies
- **Safety Measures**: Robust prompt injection prevention

## Performance Optimization

### Scanning Efficiency
- **Intelligent Batching**: Optimal task grouping for performance
- **Memory Management**: Efficient memory usage for large projects
- **Caching Strategy**: Smart caching of analysis results
- **Resource Monitoring**: Real-time resource usage tracking

### Quality Assurance
- **Result Validation**: Automated validation of scanning results
- **Consistency Checks**: Cross-validation between different analysis methods
- **Confidence Scoring**: Reliability metrics for findings
- **Continuous Learning**: Improvement through feedback analysis

## Error Handling and Resilience

- **Graceful Degradation**: Continues operation despite partial failures
- **Retry Mechanisms**: Intelligent retry strategies for transient failures
- **Error Recovery**: Automatic recovery from scanning interruptions
- **Logging Integration**: Comprehensive logging for debugging and monitoring

## Future Enhancements

- **Machine Learning Integration**: Advanced ML models for pattern recognition
- **Collaborative Analysis**: Multi-agent systems for complex analysis
- **Real-time Scanning**: Continuous monitoring and analysis capabilities
- **Custom Rule Engine**: User-defined vulnerability detection rules