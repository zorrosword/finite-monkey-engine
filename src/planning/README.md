# Planning Module

## Overview

The Planning module is a sophisticated project scanning orchestrator designed for comprehensive code audit and vulnerability analysis. It provides intelligent planning capabilities to coordinate various components in the scanning pipeline, particularly for smart contract and blockchain code analysis.

## Core Components

### Planning (`planning.py`)
The main planning coordinator that orchestrates different planning components:
- **Project Audit Integration**: Works directly with TreeSitterProjectAudit instances
- **Task Management**: Coordinates with ProjectTaskMgr for task lifecycle management
- **RAG Integration**: Supports Retrieval-Augmented Generation for enhanced analysis
- **Business Flow Analysis**: Provides business context analysis capabilities

### PlanningProcessor (`planning_processor.py`)
The core planning engine responsible for:
- **Intelligent Scanning Strategy**: Determines optimal scanning approaches based on project characteristics
- **Context Generation**: Creates rich contextual information for vulnerability detection
- **Business Flow Processing**: Analyzes business logic patterns in code
- **Multi-mode Support**: Handles different scanning modes (common project, pure scan, checklist, etc.)

### Business Flow Utils (`business_flow_utils.py`)
Specialized utilities for business logic analysis:
- **Flow Pattern Recognition**: Identifies business flow patterns in code
- **Context Enrichment**: Adds business context to technical analysis
- **Smart Contract Logic**: Specialized handling for DeFi and blockchain protocols

### Configuration Utils (`config_utils.py`)
Configuration management for planning operations:
- **Dynamic Configuration**: Supports runtime configuration adjustments
- **Mode-specific Settings**: Different configurations for various scanning modes
- **Performance Tuning**: Optimization parameters for large codebases

## Key Features

### 🎯 Intelligent Project Analysis
- **Multi-language Support**: Handles Solidity, Rust, Go, C++, and other languages
- **Smart Contract Specialization**: Deep understanding of blockchain protocols
- **Dependency Analysis**: Tracks complex call relationships and dependencies

### 🔄 Adaptive Scanning Strategies
- **Mode-based Planning**: Different strategies for different project types
- **Resource Optimization**: Intelligent resource allocation for scanning tasks
- **Scalable Architecture**: Handles projects of various sizes efficiently

### 🧠 Context-Aware Processing
- **RAG Integration**: Leverages semantic search for enhanced analysis
- **Business Context**: Incorporates business logic understanding
- **Historical Knowledge**: Uses accumulated audit knowledge for better planning

### 📊 Task Orchestration
- **Priority Management**: Intelligent task prioritization
- **Parallel Processing**: Coordinates concurrent scanning operations
- **Progress Tracking**: Real-time monitoring of scanning progress

## Architecture

```
Planning Module
├── Planning (Main Coordinator)
│   ├── Project Audit Integration
│   ├── Task Management
│   └── RAG Initialization
├── PlanningProcessor (Core Engine)
│   ├── Scanning Strategy
│   ├── Context Generation
│   └── Mode Processing
├── Business Flow Utils
│   ├── Pattern Recognition
│   └── Context Enrichment
└── Configuration Utils
    ├── Dynamic Config
    └── Performance Tuning
```

## Usage Examples

### Basic Planning Setup
```python
from planning.planning import Planning
from dao.task_mgr import ProjectTaskMgr

# Initialize planning with project audit data
planning = Planning(project_audit, task_manager)

# Execute planning process
planning.do_planning()
```

### RAG-Enhanced Planning
```python
# Initialize with RAG capabilities
planning.initialize_rag_processor("./lancedb", project_id)

# Get business flow context
context = planning.get_business_flow_context(functions_to_check)
```

### Different Scanning Modes
```python
# Common project mode with depth control
planning.process_for_common_project_mode(max_depth=5)

# Generate planning files for review
planning.generate_planning_files()
```

## Configuration

The module supports various configuration options through environment variables:

- `SWITCH_BUSINESS_CODE`: Enable/disable business code analysis
- `SCAN_MODE`: Set scanning mode (SPECIFIC_PROJECT, COMMON_PROJECT, etc.)
- `MAX_PLANNING_DEPTH`: Control analysis depth for performance tuning

## Integration Points

### Input Dependencies
- **TreeSitterProjectAudit**: Project parsing and analysis data
- **ProjectTaskMgr**: Task management and database operations
- **RAGProcessor**: Semantic search and context enhancement

### Output Consumers
- **AI Engine**: Receives planning results for vulnerability scanning
- **Reasoning Module**: Uses planning context for intelligent analysis
- **Validation Module**: Leverages planning insights for confirmation

## Performance Considerations

- **Memory Optimization**: Efficient handling of large codebases
- **Caching Strategy**: Intelligent caching of planning results
- **Concurrent Processing**: Parallel planning for multiple components
- **Resource Management**: Adaptive resource allocation based on project size

## Future Enhancements

- **Machine Learning Integration**: AI-powered planning optimization
- **Custom Rule Support**: User-defined planning strategies
- **Advanced Metrics**: Enhanced planning effectiveness measurements
- **Cloud Integration**: Distributed planning for enterprise use cases