# Context Component

## Overview

The Context component provides context management and retrieval capabilities for the Finite Monkey Engine. It includes the RAG (Retrieval Augmented Generation) processor that enables intelligent code search and context enhancement for vulnerability analysis.

## Features

- **RAG Processor**: Advanced retrieval system for code context
- **Vector Embeddings**: Semantic search using OpenAI embeddings
- **Multi-level Search**: Function, file, and chunk-level retrieval
- **Context Enhancement**: Augment analysis with relevant code context

## Architecture

### Core Components

- **RAGProcessor**: Main class for retrieval operations
- **LanceDB Integration**: Vector database for embeddings
- **Embedding Generation**: Convert code to vector representations
- **Search Algorithms**: Multiple search strategies for different use cases

### Database Schema

The component manages three main LanceDB tables:
- `lancedb_function`: Function embeddings and metadata
- `lancedb_file`: File-level code representations  
- `lancedb_chunk`: Document chunk embeddings

## Usage

### Basic RAG Setup

```python
from context.rag_processor import RAGProcessor

# Initialize with project audit data
rag_processor = RAGProcessor(
    project_audit,
    lancedb_path="./src/codebaseQA/lancedb",
    project_id="my_project"
)

# Search for functions
results = rag_processor.search_functions_by_content("access control", k=5)
```

### Advanced Search Methods

```python
# Function search by name
name_results = rag_processor.search_functions_by_name("transfer", k=3)

# Function search by content
content_results = rag_processor.search_functions_by_content("reentrancy", k=3)

# Natural language search
nl_results = rag_processor.search_functions_by_natural_language(
    "function that handles user deposits", k=3
)

# File search
file_results = rag_processor.search_files_by_content("vulnerability", k=2)

# Chunk search
chunk_results = rag_processor.search_chunks_by_content("security", k=3)
```

## Integration

The Context component integrates with:

- **Planning Module**: Provides context for task planning
- **Validation Module**: Enhances vulnerability analysis with relevant code
- **Tree-sitter Parsing**: Uses parsed code structure for embeddings
- **Main Engine**: Central context management for the entire system

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Required for embedding generation
- `LANCE_DB_PATH`: Path to LanceDB storage
- `EMBEDDING_MODEL`: OpenAI embedding model (default: text-embedding-3-small)

### Database Configuration

```python
# Database table names
FUNCTION_TABLE = "lancedb_function"
FILE_TABLE = "lancedb_file" 
CHUNK_TABLE = "lancedb_chunk"

# Vector dimensions
EMBEDDING_DIMENSION = 1536  # text-embedding-3-small
```

## Performance

- **Search Speed**: Sub-second response times for most queries
- **Memory Efficiency**: Optimized vector storage and retrieval
- **Scalability**: Supports large codebases with millions of lines
- **Accuracy**: High precision semantic matching

## Dependencies

- `lancedb`: Vector database for embeddings
- `openai`: For embedding generation and API calls
- `numpy`: For vector operations
- `json`: For data serialization

## Development

### Adding New Search Methods

1. Implement search logic in RAGProcessor
2. Add corresponding database queries
3. Update result formatting
4. Add tests and documentation

### Extending Context Types

1. Define new embedding schemas
2. Implement embedding generation
3. Add search algorithms
4. Update integration points

## API Reference

### RAGProcessor Class

#### Methods

- `search_functions_by_name(query, k)`: Search functions by name
- `search_functions_by_content(query, k)`: Search functions by content
- `search_functions_by_natural_language(query, k)`: Natural language search
- `search_files_by_content(query, k)`: Search files by content
- `search_chunks_by_content(query, k)`: Search chunks by content
- `search_similar_chunks(chunk_id, k)`: Find similar chunks

#### Properties

- `project_audit`: Project audit data
- `lancedb_path`: LanceDB storage path
- `project_id`: Project identifier

## Error Handling

The component includes comprehensive error handling for:
- API failures
- Database connection issues
- Invalid queries
- Missing embeddings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests and documentation
5. Submit a pull request

## License

This component is part of the Finite Monkey Engine project and follows the same licensing terms. 