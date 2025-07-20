# Context Module - Context Acquisition and Management Module

## Overview

The Context module is extracted from the project's planning and validating modules, specifically responsible for context acquisition and management during smart contract auditing. This module unifies all context-related logic, including RAG construction, call tree analysis, business flow processing, etc.

## Module Structure

```
src/context/
├── __init__.py                    # Module initialization and API exports
├── context_factory.py            # Context factory - unified context creation entry point
├── context_manager.py            # Context manager - context lifecycle management
├── rag_processor.py               # RAG processor - retrieval augmented generation
├── call_tree_builder.py          # Call tree builder - function call relationship analysis
├── business_flow_processor.py    # Business flow processor - business flow context processing
├── function_utils.py             # Function utilities - function-related utility functions
└── README.md                     # This documentation
```

## Core Components

### 1. ContextFactory (context_factory.py)
**Unified context creation entry point**, providing various types of context acquisition capabilities:

#### Main Functions
- `create_rag_context()`: Create RAG-based context
- `create_call_tree_context()`: Create call tree-based context
- `create_business_flow_context()`: Create business flow-based context
- `create_hybrid_context()`: Create hybrid context combining multiple methods
- `search_similar_functions()`: Search for similar functions

#### Usage Example
```python
from context import ContextFactory

factory = ContextFactory(project, lancedb, table_name)

# Create RAG context
rag_context = factory.create_rag_context(function_name, k=5)

# Create call tree context
call_tree_context = factory.create_call_tree_context(function_name, depth=2)

# Create business flow context
business_flow_context = factory.create_business_flow_context(business_flow)

# Create hybrid context
hybrid_context = factory.create_hybrid_context(
    function_name, 
    include_rag=True, 
    include_call_tree=True,
    rag_k=3,
    call_tree_depth=1
)
```

### 2. ContextManager (context_manager.py)
**Context lifecycle management**, responsible for context state management and optimization:

#### Main Functions
- `manage_context_lifecycle()`: Manage complete context lifecycle
- `optimize_context_size()`: Optimize context size
- `cache_context()`: Cache context for reuse
- `validate_context()`: Validate context validity
- `merge_contexts()`: Merge multiple contexts

#### Usage Example
```python
from context import ContextManager

manager = ContextManager(max_context_size=4000)

# Manage context lifecycle
context = manager.manage_context_lifecycle(
    context_data, 
    cache_key="function_analysis_123"
)

# Optimize context size
optimized_context = manager.optimize_context_size(large_context)
```

### 3. RAGProcessor (rag_processor.py)
**Retrieval Augmented Generation processor**, providing semantic similarity-based context expansion:

#### Main Functions
- `process_rag_query()`: Process RAG queries
- `search_similar_functions()`: Search for semantically similar functions
- `expand_context_with_rag()`: Expand context using RAG
- `calculate_similarity()`: Calculate semantic similarity scores

#### Key Features
- **Semantic Search**: Based on embedding vectors for semantic similarity search
- **Relevance Ranking**: Automatically rank results by relevance
- **Context Expansion**: Intelligently expand context based on semantic relationships
- **Configurable Parameters**: Support various search parameters (k, threshold, etc.)

### 4. CallTreeBuilder (call_tree_builder.py)
**Function call relationship analyzer**, building and analyzing function call graphs:

#### Main Functions
- `build_call_tree()`: Build complete call tree
- `find_callers()`: Find functions that call the target function
- `find_callees()`: Find functions called by the target function
- `analyze_call_depth()`: Analyze call depth and complexity
- `extract_call_relationships()`: Extract call relationships

#### Key Features
- **Multi-layer Analysis**: Support multi-layer call relationship analysis
- **Bidirectional Search**: Support both caller and callee searches
- **Dependency Analysis**: Analyze function dependencies and impact scope
- **Performance Optimization**: Optimized algorithms for large-scale code analysis

### 5. BusinessFlowProcessor (business_flow_processor.py)
**Business flow context processor**, providing business flow-specific context processing:

#### Main Functions
- `process_business_flow_context()`: Process business flow context
- `expand_business_flow()`: Expand business flow context
- `analyze_flow_relationships()`: Analyze relationships between business flows
- `extract_flow_functions()`: Extract functions from business flows

#### Key Features
- **Business Logic Understanding**: Deep understanding of business flow logic
- **Context Enrichment**: Enrich context based on business flow characteristics
- **Relationship Analysis**: Analyze relationships and dependencies between business flows
- **Integration Support**: Seamlessly integrate with planning and validation modules

### 6. FunctionUtils (function_utils.py)
**Function utility functions**, providing various function processing utilities:

#### Main Functions
- `extract_function_signature()`: Extract function signatures
- `parse_function_parameters()`: Parse function parameters
- `calculate_function_complexity()`: Calculate function complexity
- `compare_function_similarity()`: Compare function similarity
- `format_function_context()`: Format function context

## Integration Architecture

### With Planning Module
```python
# In planning module
from context import ContextFactory, ContextManager

# Create context for planning
context_factory = ContextFactory(project, lancedb, table_name)
context_manager = ContextManager()

# Get enhanced context for business flows
for business_flow in business_flows:
    context = context_factory.create_business_flow_context(business_flow)
    optimized_context = context_manager.optimize_context_size(context)
    # Use context for planning tasks
```

### With Validating Module
```python
# In validating module
from context import ContextFactory, RAGProcessor, CallTreeBuilder

# Create context for vulnerability analysis
rag_processor = RAGProcessor(lancedb, table_name)
call_tree_builder = CallTreeBuilder(project)

# Get context for vulnerability checking
for function in functions_to_check:
    rag_context = rag_processor.search_similar_functions(function.name, k=5)
    call_tree_context = call_tree_builder.build_call_tree(function.name, depth=2)
    # Combine contexts for comprehensive analysis
```

## Configuration and Performance

### Configuration Options
```python
# RAG processor configuration
rag_config = {
    'embedding_model': 'text-embedding-3-large',
    'similarity_threshold': 0.7,
    'max_results': 10,
    'cache_embeddings': True
}

# Call tree builder configuration
call_tree_config = {
    'max_depth': 3,
    'include_external_calls': False,
    'analysis_timeout': 30,
    'cache_results': True
}

# Context manager configuration
context_config = {
    'max_context_size': 4000,
    'compression_enabled': True,
    'cache_duration': 3600,
    'optimization_level': 'balanced'
}
```

### Performance Optimization
1. **Intelligent Caching**: Multi-level caching strategy to avoid duplicate computations
2. **Lazy Loading**: Load context on demand to reduce memory usage
3. **Parallel Processing**: Parallel processing of multiple context requests
4. **Size Optimization**: Intelligent context size optimization to balance completeness and efficiency

## Usage Patterns

### 1. Simple Context Creation
```python
from context import ContextFactory

factory = ContextFactory(project, lancedb, table_name)
context = factory.create_rag_context("transfer", k=3)
```

### 2. Complex Context Workflow
```python
from context import ContextFactory, ContextManager, RAGProcessor, CallTreeBuilder

# Initialize components
factory = ContextFactory(project, lancedb, table_name)
manager = ContextManager(max_context_size=4000)
rag_processor = RAGProcessor(lancedb, table_name)
call_tree_builder = CallTreeBuilder(project)

# Create comprehensive context
function_name = "processTransaction"

# Step 1: Get RAG context
rag_context = rag_processor.search_similar_functions(function_name, k=5)

# Step 2: Get call tree context
call_tree_context = call_tree_builder.build_call_tree(function_name, depth=2)

# Step 3: Merge contexts
combined_context = manager.merge_contexts([rag_context, call_tree_context])

# Step 4: Optimize context
final_context = manager.optimize_context_size(combined_context)
```

### 3. Business Flow Context Processing
```python
from context import ContextFactory, BusinessFlowProcessor

factory = ContextFactory(project, lancedb, table_name)
flow_processor = BusinessFlowProcessor(factory)

# Process business flow context
business_flow = {
    'name': 'Token Transfer Flow',
    'functions': ['transfer', 'approve', 'transferFrom']
}

# Get enhanced business flow context
flow_context = flow_processor.process_business_flow_context(business_flow)
expanded_context = flow_processor.expand_business_flow(flow_context)
```

## API Reference

### ContextFactory
```python
class ContextFactory:
    def __init__(self, project, lancedb, table_name)
    def create_rag_context(self, query, k=5, threshold=0.7) -> str
    def create_call_tree_context(self, function_name, depth=2) -> str
    def create_business_flow_context(self, business_flow) -> str
    def create_hybrid_context(self, function_name, **kwargs) -> str
    def search_similar_functions(self, query, k=5) -> List[Dict]
```

### ContextManager
```python
class ContextManager:
    def __init__(self, max_context_size=4000)
    def manage_context_lifecycle(self, context_data, cache_key=None) -> str
    def optimize_context_size(self, context) -> str
    def cache_context(self, context, key, duration=3600) -> bool
    def validate_context(self, context) -> bool
    def merge_contexts(self, contexts) -> str
```

### RAGProcessor
```python
class RAGProcessor:
    def __init__(self, lancedb, table_name)
    def process_rag_query(self, query, k=5) -> List[Dict]
    def search_similar_functions(self, function_name, k=5) -> List[Dict]
    def expand_context_with_rag(self, base_context, query, k=3) -> str
    def calculate_similarity(self, query, candidates) -> List[float]
```

### CallTreeBuilder
```python
class CallTreeBuilder:
    def __init__(self, project)
    def build_call_tree(self, function_name, depth=2) -> Dict
    def find_callers(self, function_name) -> List[str]
    def find_callees(self, function_name) -> List[str]
    def analyze_call_depth(self, function_name) -> int
    def extract_call_relationships(self, functions) -> Dict
```

## Testing

### Unit Testing
```python
# Test RAG processor
def test_rag_processor():
    processor = RAGProcessor(mock_lancedb, "test_table")
    results = processor.search_similar_functions("transfer", k=3)
    assert len(results) <= 3
    assert all('similarity_score' in result for result in results)

# Test call tree builder
def test_call_tree_builder():
    builder = CallTreeBuilder(mock_project)
    tree = builder.build_call_tree("main_function", depth=2)
    assert 'callers' in tree
    assert 'callees' in tree
```

### Integration Testing
```python
def test_context_factory_integration():
    factory = ContextFactory(test_project, test_lancedb, "test_table")
    context = factory.create_hybrid_context(
        "test_function",
        include_rag=True,
        include_call_tree=True
    )
    assert len(context) > 0
    assert "test_function" in context
```

## Benefits

1. **Unified Interface**: Provides unified context creation and management interfaces
2. **Modular Design**: Each component can be used independently or in combination
3. **High Performance**: Optimized algorithms and caching strategies
4. **High Scalability**: Supports analysis of large-scale projects
5. **Easy Integration**: Seamlessly integrates with other modules
6. **Highly Configurable**: Rich configuration options to meet different needs

## Future Roadmap

1. **Machine Learning Enhancement**: Integrate more advanced ML models for context understanding
2. **Real-time Updates**: Support real-time context updates and incremental analysis
3. **Visualization**: Provide context visualization tools for better understanding
4. **Custom Plugins**: Support custom context processors and analyzers
5. **Performance Monitoring**: Add detailed performance monitoring and optimization suggestions

---

**🔍 Intelligent context management for enhanced smart contract analysis - Making code understanding more accurate and comprehensive!** 