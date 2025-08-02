# DAO Component

## Overview

The DAO (Data Access Object) component provides data persistence and management capabilities for the Finite Monkey Engine. It handles project tasks, caching, and database operations using SQLAlchemy and SQLite.

## Features

- **Project Task Management**: CRUD operations for project tasks
- **Caching System**: Intelligent caching for performance optimization
- **Database Operations**: SQLAlchemy-based data persistence
- **Entity Management**: Structured data models for project entities

## Architecture

### Core Components

- **ProjectTaskMgr**: Main task management class
- **CacheManager**: Caching system for performance
- **Entity Models**: SQLAlchemy entity definitions
- **Database Utils**: Database connection and utility functions

### Database Schema

The component manages several database tables:
- `project_task`: Main task storage table
- `prompt_cache2`: Caching table for prompt responses
- Additional utility tables for data management

## Usage

### Basic Task Management

```python
from dao import ProjectTaskMgr, CacheManager

# Initialize task manager
task_mgr = ProjectTaskMgr(project_id="my_project")

# Create a new task
task_data = {
    'name': 'TestContract.transfer',
    'content': 'function transfer() public { }',
    'rule': 'access_control_checklist',
    'rule_key': 'access_control'
}
task = task_mgr.create_task(task_data)

# Query tasks
tasks = task_mgr.query_task_by_project_id("my_project")
```

### Caching Operations

```python
# Initialize cache manager
cache_mgr = CacheManager()

# Store cache entry
cache_mgr.set_cache("prompt_key", "cached_response")

# Retrieve cache entry
response = cache_mgr.get_cache("prompt_key")

# Clear cache
cache_mgr.clear_cache()
```

## Integration

The DAO component integrates with:

- **Planning Module**: Stores and retrieves planning tasks
- **Validation Module**: Manages validation task data
- **Main Engine**: Provides data persistence for the entire system
- **Result Processor**: Stores analysis results and reports

## Configuration

### Database Configuration

```python
# Database connection string
DATABASE_URL = "sqlite:///project_tasks.db"

# Table configurations
PROJECT_TASK_TABLE = "project_task"
CACHE_TABLE = "prompt_cache2"
```

### Environment Variables

- `DATABASE_URL`: Database connection string
- `CACHE_TTL`: Cache time-to-live in seconds
- `MAX_CACHE_SIZE`: Maximum cache size in entries

## Performance

- **Query Optimization**: Indexed database queries for fast retrieval
- **Caching Strategy**: Intelligent caching reduces redundant operations
- **Connection Pooling**: Efficient database connection management
- **Batch Operations**: Support for bulk data operations

## Dependencies

- `sqlalchemy`: ORM for database operations
- `sqlite3`: Database backend
- `json`: For data serialization
- `datetime`: For timestamp handling

## Development

### Adding New Entities

1. Define SQLAlchemy model in `entity.py`
2. Add corresponding manager methods
3. Update database schema
4. Add migration scripts

### Extending Caching

1. Implement new cache strategies
2. Add cache invalidation logic
3. Optimize cache performance
4. Add cache monitoring

## API Reference

### ProjectTaskMgr Class

#### Methods

- `create_task(task_data)`: Create a new project task
- `query_task_by_project_id(project_id)`: Query tasks by project
- `update_task(task_id, updates)`: Update existing task
- `delete_task(task_id)`: Delete a task
- `save_task(task)`: Save task to database

#### Properties

- `project_id`: Current project identifier
- `engine`: Database engine instance
- `session`: Database session

### CacheManager Class

#### Methods

- `set_cache(key, value)`: Store cache entry
- `get_cache(key)`: Retrieve cache entry
- `clear_cache()`: Clear all cache entries
- `invalidate_cache(key)`: Invalidate specific cache entry

## Error Handling

The component includes comprehensive error handling for:
- Database connection failures
- Transaction rollbacks
- Cache corruption
- Data validation errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests and documentation
5. Submit a pull request

## License

This component is part of the Finite Monkey Engine project and follows the same licensing terms. 