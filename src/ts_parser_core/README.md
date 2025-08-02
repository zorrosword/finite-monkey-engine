# TS Parser Core Module

## Overview

The TS Parser Core module provides the foundational parsing infrastructure for multi-language code analysis. It implements a modular, extensible parsing framework built on tree-sitter technology, supporting comprehensive analysis of various programming languages with specialized focus on smart contract and blockchain code security assessment.

## Core Components

### Multi-Language Analyzer (`ts_parser/multi_language_analyzer.py`)
The central analysis coordination engine featuring:
- **Unified Interface**: Single API for multi-language code analysis
- **Language Detection**: Automatic programming language identification
- **Modular Architecture**: Pluggable language-specific parsers
- **Analysis Coordination**: Orchestrates different analysis components
- **Result Aggregation**: Combines results from multiple language parsers

### Language-Specific Parsers (`ts_parser/parsers/`)
Specialized parsers for different programming languages:

#### Solidity Parser (`solidity_parser.py`)
- **Smart Contract Analysis**: Comprehensive Solidity code parsing
- **Function Extraction**: Identifies functions, modifiers, and events
- **State Variable Analysis**: Tracks state variables and their usage
- **Inheritance Tracking**: Analyzes contract inheritance patterns
- **Security Pattern Recognition**: Identifies common security patterns

#### Rust Parser (`rust_parser.py`)
- **Memory Safety Analysis**: Rust-specific memory management patterns
- **Ownership Tracking**: Analyzes ownership and borrowing patterns
- **Trait Implementation**: Tracks trait definitions and implementations
- **Module System**: Understands Rust's module system and visibility
- **Macro Analysis**: Handles Rust macro definitions and expansions

#### C++ Parser (`cpp_parser.py`)
- **Class Hierarchy**: Analyzes C++ class structures and inheritance
- **Template Analysis**: Handles C++ templates and specializations
- **Memory Management**: Tracks manual memory management patterns
- **STL Usage**: Analyzes Standard Template Library usage
- **Namespace Analysis**: Understands C++ namespace organization

#### Move Parser (`move_parser.py`)
- **Resource Management**: Move language resource analysis
- **Module System**: Move module structure and dependencies
- **Capability Analysis**: Tracks Move's capability-based security
- **Script Analysis**: Analyzes Move scripts and transactions
- **Resource Type Safety**: Ensures resource type safety patterns

### Data Structures (`ts_parser/data_structures.py`)
Core data structures for representing parsed code:
- **FunctionInfo**: Comprehensive function metadata
- **ModuleInfo**: Module and namespace information
- **CallGraphEdge**: Call relationship representation
- **StructInfo**: Structure and class definitions
- **LanguageFeatures**: Language-specific feature tracking

### Language Configurations (`ts_parser/language_configs.py`)
Configuration management for different languages:
- **Parser Settings**: Language-specific parsing parameters
- **Feature Flags**: Optional language feature processing
- **Output Formats**: Customizable result formatting
- **Performance Tuning**: Language-specific optimization settings

### Base Parser (`ts_parser/base_parser.py`)
Foundation parser class providing:
- **Common Interface**: Standardized parser API
- **Error Handling**: Robust error recovery mechanisms
- **Utility Functions**: Shared parsing utilities
- **Extension Points**: Framework for custom parser development

## Demo and Visualization

### Analysis Demo (`demo.py`)
Comprehensive demonstration system:
- **Interactive Analysis**: Command-line interface for code analysis
- **Multiple Input Formats**: Supports files, directories, and streams
- **Result Export**: JSON, XML, and custom format export
- **Performance Metrics**: Analysis timing and resource usage
- **Progress Tracking**: Real-time analysis progress indication

### Visualization Demo (`demo_visualization.py`)
Advanced visualization capabilities:
- **Call Graph Visualization**: Interactive call relationship graphs
- **Dependency Trees**: Hierarchical dependency visualization
- **Code Structure Maps**: Visual code organization representation
- **Metrics Dashboards**: Analysis metrics and statistics displays

### Dependency Demo (`dependency_demo.py`)
Specialized dependency analysis:
- **Cross-module Dependencies**: Inter-module relationship analysis
- **Circular Dependency Detection**: Identifies problematic dependencies
- **Dependency Graphs**: Comprehensive dependency mapping
- **Impact Analysis**: Assesses change impact across dependencies

## Key Features

### 🔧 Modular Architecture
- **Plugin System**: Extensible parser plugin framework
- **Language Independence**: Clean separation between language parsers
- **Configurable Pipeline**: Flexible analysis pipeline configuration
- **Custom Extensions**: Framework for adding new language support

### 🌍 Multi-Language Support
- **Comprehensive Coverage**: Support for major programming languages
- **Cross-Language Analysis**: Handles multi-language projects
- **Language Interop**: Analyzes cross-language interfaces and bindings
- **Unified Results**: Consistent result format across all languages

### 📊 Advanced Analysis Capabilities
- **Call Graph Generation**: Detailed function call relationship mapping
- **Dependency Analysis**: Comprehensive dependency tracking
- **Pattern Recognition**: Identifies common code patterns and structures
- **Metrics Collection**: Extensive code quality and complexity metrics

### 🚀 High Performance
- **Optimized Parsing**: Efficient tree-sitter based parsing
- **Memory Management**: Intelligent memory usage optimization
- **Parallel Processing**: Concurrent analysis for large projects
- **Caching System**: Smart caching of analysis results

## Architecture

```
TS Parser Core Module
├── MultiLanguageAnalyzer (Central Coordinator)
│   ├── Language Detection
│   ├── Parser Management
│   ├── Result Aggregation
│   └── Analysis Orchestration
├── Language Parsers
│   ├── Solidity Parser
│   │   ├── Contract Analysis
│   │   ├── Function Extraction
│   │   └── Security Patterns
│   ├── Rust Parser
│   │   ├── Ownership Analysis
│   │   ├── Trait Tracking
│   │   └── Memory Safety
│   ├── C++ Parser
│   │   ├── Class Hierarchy
│   │   ├── Template Analysis
│   │   └── Memory Management
│   └── Move Parser
│       ├── Resource Management
│       ├── Capability Analysis
│       └── Type Safety
├── Data Structures
│   ├── Function Metadata
│   ├── Module Information
│   ├── Call Relationships
│   └── Language Features
└── Demo & Visualization
    ├── Interactive Analysis
    ├── Visual Representations
    └── Dependency Mapping
```

## Usage Examples

### Basic Multi-Language Analysis
```python
from ts_parser_core import MultiLanguageAnalyzer, LanguageType

# Initialize analyzer
analyzer = MultiLanguageAnalyzer()

# Analyze a Solidity file
solidity_result = analyzer.analyze_file(
    "contract.sol", 
    LanguageType.SOLIDITY
)

# Analyze a Rust file
rust_result = analyzer.analyze_file(
    "main.rs", 
    LanguageType.RUST
)

# Get combined results
all_functions = analyzer.get_all_functions()
all_modules = analyzer.get_all_modules()
```

### Advanced Project Analysis
```python
# Analyze entire project directory
project_results = analyzer.analyze_directory(
    "/path/to/project",
    recursive=True,
    include_patterns=["*.sol", "*.rs", "*.cpp"],
    exclude_patterns=["test/*", "*.test.*"]
)

# Get call graph
call_graph = analyzer.get_call_graph(LanguageType.SOLIDITY)

# Get statistics
stats = analyzer.get_statistics(LanguageType.SOLIDITY)
print(f"Functions: {stats['functions_count']}")
print(f"Modules: {stats['modules_count']}")
```

### Custom Analysis Pipeline
```python
from ts_parser_core.ts_parser.language_configs import LanguageConfig

# Create custom configuration
config = LanguageConfig(
    extract_comments=True,
    analyze_complexity=True,
    track_dependencies=True,
    generate_metrics=True
)

# Analyze with custom config
analyzer.set_language_config(LanguageType.SOLIDITY, config)
results = analyzer.analyze_file("contract.sol", LanguageType.SOLIDITY)
```

### Visualization and Export
```python
# Export results to JSON
analyzer.export_results("analysis_results.json", format="json")

# Generate call graph visualization
analyzer.visualize_call_graph(
    LanguageType.SOLIDITY,
    output_file="call_graph.html",
    format="interactive"
)

# Create dependency graph
analyzer.create_dependency_graph(
    output_file="dependencies.svg",
    include_external=True
)
```

## Language Support Matrix

| Language | Parsing | Call Graph | Dependencies | Security | Status |
|----------|---------|------------|--------------|----------|--------|
| Solidity | ✅ | ✅ | ✅ | ✅ | Complete |
| Rust | ✅ | ✅ | ✅ | ✅ | Complete |
| C++ | ✅ | ✅ | ✅ | ⚡ | In Progress |
| Move | ✅ | ✅ | ✅ | ⚡ | In Progress |
| Go | ⚡ | ⚡ | ⚡ | ❌ | Planned |
| Python | ⚡ | ⚡ | ⚡ | ❌ | Planned |

- ✅ Complete
- ⚡ In Progress
- ❌ Planned

## Configuration Options

### Global Settings
- **Analysis Depth**: Control the depth of analysis
- **Memory Limits**: Set memory usage constraints
- **Timeout Settings**: Configure analysis timeouts
- **Output Formats**: Customize result output formats

### Language-Specific Settings
- **Parser Options**: Language-specific parsing parameters
- **Feature Flags**: Enable/disable specific language features
- **Pattern Recognition**: Custom pattern recognition rules
- **Security Analysis**: Security-specific analysis options

## Integration Points

### Input Sources
- **File System**: Direct file and directory analysis
- **Version Control**: Git repository integration
- **Archive Support**: Compressed file analysis
- **Stream Processing**: Real-time code analysis

### Output Consumers
- **Tree-sitter Parsing**: Integration with parsing module
- **Vulnerability Analysis**: Security assessment pipelines
- **Documentation Tools**: Code documentation generators
- **IDE Integration**: Development environment plugins

## Performance Considerations

### Optimization Strategies
- **Lazy Loading**: On-demand parser initialization
- **Result Caching**: Intelligent caching of analysis results
- **Parallel Processing**: Multi-threaded analysis execution
- **Memory Pooling**: Efficient memory management

### Scalability Features
- **Large Project Support**: Handles enterprise-scale codebases
- **Incremental Analysis**: Supports partial project updates
- **Resource Monitoring**: Real-time resource usage tracking
- **Adaptive Processing**: Adjusts processing based on available resources

## Extension and Customization

### Adding New Languages
1. **Create Parser Class**: Extend base parser for new language
2. **Define Data Structures**: Specify language-specific structures
3. **Configure Grammar**: Set up tree-sitter grammar
4. **Register Parser**: Add to analyzer registry
5. **Test Integration**: Comprehensive testing and validation

### Custom Analysis Rules
- **Pattern Definitions**: Define custom code patterns
- **Security Rules**: Implement security-specific analysis
- **Quality Metrics**: Custom code quality measurements
- **Reporting Rules**: Customized result formatting

## Future Enhancements

- **Machine Learning Integration**: AI-powered pattern recognition
- **Real-time Analysis**: Live code analysis capabilities
- **Cloud Processing**: Distributed analysis infrastructure
- **Advanced Visualization**: 3D code structure representations
- **IDE Plugin Framework**: Comprehensive development environment integration