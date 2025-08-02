# Tree-sitter Parsing Module

## Overview

The Tree-sitter Parsing module provides comprehensive code analysis and parsing capabilities for multi-language projects. It leverages the powerful tree-sitter parsing library to build detailed Abstract Syntax Trees (ASTs), extract function definitions, analyze call relationships, and create sophisticated code representations for vulnerability analysis.

## Core Components

### TreeSitterProjectAudit (`project_audit.py`)
The main project analysis coordinator featuring:
- **Multi-language Parsing**: Support for Solidity, Rust, Go, C++, and more
- **Function Extraction**: Comprehensive function and method identification
- **Call Graph Generation**: Advanced call relationship analysis
- **Document Chunking**: Intelligent code segmentation for analysis
- **Database Integration**: Optional database storage for parsed results

### ProjectParser (`project_parser.py`)
Advanced project parsing engine with:
- **Parallel Processing**: Concurrent parsing for improved performance
- **Language Detection**: Automatic programming language identification
- **Filter System**: Configurable filtering for targeted analysis
- **Metadata Extraction**: Rich metadata collection from parsed code

### Call Tree Builder (`call_tree_builder.py`)
Sophisticated call relationship analysis:
- **Function Call Tracking**: Identifies and maps function calls
- **Cross-reference Analysis**: Tracks relationships between functions
- **Dependency Mapping**: Creates comprehensive dependency graphs
- **Contextual Analysis**: Understands call context and parameters

### Advanced Call Tree Builder (`advanced_call_tree_builder.py`)
Enhanced call analysis with:
- **Deep Analysis**: Advanced call pattern recognition
- **Complex Relationships**: Handles indirect and dynamic calls
- **Performance Optimization**: Optimized algorithms for large codebases
- **Pattern Recognition**: Identifies common code patterns and structures

### Document Chunker (`document_chunker.py`)
Intelligent code segmentation system:
- **Semantic Chunking**: Creates meaningful code segments
- **Context Preservation**: Maintains logical code boundaries
- **Configurable Sizing**: Flexible chunk size configuration
- **Overlap Management**: Handles overlapping contexts for continuity

### Chunk Configuration (`chunk_config.py`)
Configuration management for chunking operations:
- **Language-specific Settings**: Tailored configurations for different languages
- **Performance Tuning**: Optimization parameters for various project sizes
- **Custom Rules**: User-defined chunking strategies
- **Template Management**: Predefined configuration templates

## Key Features

### 🌳 Advanced AST Analysis
- **Precise Parsing**: Accurate syntax tree generation for multiple languages
- **Rich Metadata**: Comprehensive code structure information
- **Error Handling**: Robust parsing with graceful error recovery
- **Performance Optimized**: Efficient parsing for large codebases

### 🔗 Sophisticated Call Analysis
- **Function Mapping**: Complete function identification and cataloging
- **Call Relationship Tracking**: Detailed call graph construction
- **Cross-language Support**: Handles multi-language projects seamlessly
- **Dynamic Analysis**: Supports runtime call pattern analysis

### 📊 Intelligent Code Segmentation
- **Context-aware Chunking**: Maintains logical code boundaries
- **Overlap Strategy**: Smart overlapping for context preservation
- **Size Optimization**: Balanced chunk sizes for analysis efficiency
- **Metadata Enrichment**: Enhanced chunks with structural information

### 🚀 High-Performance Processing
- **Parallel Parsing**: Concurrent processing for multiple files
- **Memory Optimization**: Efficient memory usage for large projects
- **Caching System**: Intelligent caching of parsing results
- **Incremental Processing**: Support for incremental project updates

## Architecture

```
Tree-sitter Parsing Module
├── TreeSitterProjectAudit (Main Coordinator)
│   ├── Project Management
│   ├── Multi-language Support
│   ├── Call Graph Integration
│   └── Database Coordination
├── ProjectParser (Parsing Engine)
│   ├── Language Detection
│   ├── Parallel Processing
│   ├── Filter System
│   └── Metadata Extraction
├── Call Tree Builders
│   ├── Basic Call Analysis
│   ├── Advanced Patterns
│   ├── Relationship Mapping
│   └── Performance Optimization
└── Document Processing
    ├── Intelligent Chunking
    ├── Configuration Management
    ├── Context Preservation
    └── Template System
```

## Supported Languages

### Primary Support
- **Solidity**: Complete smart contract analysis support
- **Rust**: Comprehensive Rust language parsing
- **Go**: Full Go language support with module analysis
- **C++**: Advanced C++ parsing with template support

### Extended Support
- **Python**: Python code analysis capabilities
- **JavaScript/TypeScript**: Web technology support
- **Java**: Enterprise Java application analysis
- **C**: System-level C code parsing

## Usage Examples

### Basic Project Parsing
```python
from tree_sitter_parsing import TreeSitterProjectAudit

# Initialize project audit
project_audit = TreeSitterProjectAudit(
    project_id="my_project",
    project_path="/path/to/project",
    db_engine=engine  # Optional database engine
)

# Parse the project
project_audit.parse()

# Access results
functions = project_audit.functions
call_trees = project_audit.call_trees
chunks = project_audit.chunks
```

### Advanced Parsing with Filters
```python
from tree_sitter_parsing.project_parser import TreeSitterProjectFilter

# Create custom filter
filter_config = TreeSitterProjectFilter(
    languages=["solidity", "rust"],
    max_file_size=1000000,  # 1MB limit
    exclude_patterns=["test/*", "*.md"]
)

# Parse with custom filter
project_audit = TreeSitterProjectAudit(
    project_id="filtered_project",
    project_path="/path/to/project"
)

# Apply filter during parsing
filtered_results = project_audit.parse_with_filter(filter_config)
```

### Call Graph Analysis
```python
# Access call graph information
call_graphs = project_audit.call_graphs
statistics = project_audit.get_call_graph_statistics()

print(f"Total functions: {statistics['total_functions']}")
print(f"Call relationships: {statistics['total_edges']}")
print(f"Connected components: {statistics['components']}")
```

### Document Chunking
```python
from tree_sitter_parsing.document_chunker import DocumentChunker
from tree_sitter_parsing.chunk_config import ChunkConfig

# Configure chunking
config = ChunkConfig(
    chunk_size=1000,
    overlap_size=200,
    preserve_functions=True
)

# Create chunker
chunker = DocumentChunker(config)

# Process document
chunks = chunker.chunk_document(file_path, language="solidity")
```

## Configuration Options

### Parsing Configuration
- **Language Settings**: Language-specific parsing parameters
- **Performance Tuning**: Memory and CPU optimization settings
- **Filter Options**: File inclusion/exclusion criteria
- **Output Control**: Result format and storage options

### Chunking Configuration
- **Chunk Size**: Target size for code segments
- **Overlap Strategy**: Context preservation settings
- **Boundary Rules**: Logical boundary preservation rules
- **Metadata Options**: Additional information inclusion

### Call Analysis Configuration
- **Depth Limits**: Maximum analysis depth for performance
- **Pattern Recognition**: Custom pattern identification rules
- **Relationship Types**: Types of relationships to track
- **Performance Limits**: Resource usage constraints

## Integration Points

### Input Sources
- **File System**: Direct file system parsing
- **Git Repositories**: Version control system integration
- **Archive Files**: Compressed file format support
- **Stream Input**: Real-time parsing from data streams

### Output Consumers
- **RAG Processor**: Semantic search and context enhancement
- **Planning Module**: Project analysis planning
- **Vulnerability Scanner**: Security analysis integration
- **Database Storage**: Persistent storage of parsing results

## Performance Optimization

### Parsing Efficiency
- **Parallel Processing**: Multi-threaded parsing for large projects
- **Memory Management**: Efficient memory usage and cleanup
- **Caching Strategy**: Intelligent result caching
- **Incremental Updates**: Support for partial project updates

### Scalability Features
- **Large Project Support**: Handles enterprise-scale codebases
- **Resource Monitoring**: Real-time resource usage tracking
- **Adaptive Processing**: Adjusts processing based on system resources
- **Progress Tracking**: Detailed progress reporting for long operations

## Error Handling and Resilience

### Robust Parsing
- **Syntax Error Recovery**: Continues parsing despite syntax errors
- **Partial Results**: Provides partial results for incomplete parsing
- **Error Reporting**: Comprehensive error logging and reporting
- **Fallback Mechanisms**: Alternative parsing strategies for edge cases

### Quality Assurance
- **Validation Pipeline**: Multi-stage result validation
- **Consistency Checks**: Cross-validation between different analysis methods
- **Accuracy Metrics**: Parsing accuracy measurement and reporting
- **Regression Testing**: Continuous quality assurance through testing

## Advanced Features

### Multi-language Projects
- **Cross-language Analysis**: Handles projects with multiple languages
- **Interface Detection**: Identifies language interfaces and bindings
- **Dependency Tracking**: Tracks dependencies across language boundaries
- **Unified Representation**: Creates unified project representations

### Custom Extensions
- **Plugin System**: Framework for custom parsing extensions
- **Custom Grammars**: Support for additional programming languages
- **Rule Customization**: User-defined parsing and analysis rules
- **Template Extensions**: Custom configuration templates

## Future Enhancements

- **Real-time Parsing**: Live parsing for IDE integration
- **Machine Learning Integration**: AI-powered pattern recognition
- **Distributed Processing**: Cloud-based parsing for large projects
- **Advanced Visualization**: Interactive code structure visualization