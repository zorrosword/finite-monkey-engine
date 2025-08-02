# CodebaseQA Component

## Overview

The CodebaseQA component provides intelligent code analysis and question-answering capabilities for smart contract codebases. It leverages advanced language models and vector embeddings to enable semantic search and contextual code understanding.

## Features

- **Semantic Code Search**: Find relevant code snippets using natural language queries
- **Vector Embeddings**: Store and retrieve code representations using LanceDB
- **Multi-language Support**: Analyze Solidity, Rust, C++, and Move code
- **Contextual Understanding**: Provide answers based on code context and relationships

## Architecture

### Core Components

- **LanceDB Integration**: Vector database for storing code embeddings
- **Embedding Generation**: Convert code snippets to vector representations
- **Query Processing**: Natural language to code search capabilities
- **Result Ranking**: Intelligent ranking of search results

### Database Schema

The component uses LanceDB tables for storing:
- Function embeddings and metadata
- File-level code representations
- Chunk-level document embeddings
- Search indices for fast retrieval

## Usage

### Basic Setup

```python
from codebaseQA import CodebaseQA

# Initialize with project path
qa_system = CodebaseQA("./src/codebaseQA/lancedb")

# Search for functions
results = qa_system.search_functions("access control vulnerability")
```

### Advanced Queries

```python
# Search by function name
name_results = qa_system.search_functions_by_name("transfer", k=5)

# Search by content similarity
content_results = qa_system.search_functions_by_content("reentrancy", k=5)

# Natural language search
nl_results = qa_system.search_functions_by_natural_language("function that handles user deposits", k=5)
```

## Integration

The CodebaseQA component integrates with:
- **Tree-sitter Parsing**: For code structure analysis
- **RAG Processor**: For enhanced retrieval capabilities
- **Planning Module**: For task-specific code search
- **Validation Module**: For vulnerability analysis support

## Configuration

### Environment Variables

- `LANCE_DB_PATH`: Path to LanceDB storage directory
- `EMBEDDING_MODEL`: OpenAI embedding model to use
- `VECTOR_DIMENSION`: Dimension of embedding vectors

### Database Tables

- `lancedb_function`: Function embeddings and metadata
- `lancedb_file`: File-level embeddings
- `lancedb_chunk`: Document chunk embeddings

## Performance

- **Search Speed**: Sub-second query response times
- **Accuracy**: High precision semantic matching
- **Scalability**: Supports large codebases with millions of lines
- **Memory Efficiency**: Optimized vector storage and retrieval

## Dependencies

- `lancedb`: Vector database for embeddings
- `openai`: For embedding generation
- `numpy`: For vector operations
- `tree-sitter`: For code parsing integration

## Development

### Adding New Languages

1. Implement language-specific parsers
2. Add embedding generation logic
3. Update search algorithms
4. Test with sample codebases

### Extending Search Capabilities

1. Implement new search methods
2. Add custom ranking algorithms
3. Integrate with external APIs
4. Optimize performance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests and documentation
5. Submit a pull request

## License

This component is part of the Finite Monkey Engine project and follows the same licensing terms. 