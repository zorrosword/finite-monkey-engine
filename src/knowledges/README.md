# Knowledges Component

## Overview

The Knowledges component provides a comprehensive knowledge base for smart contract security analysis. It contains curated documentation, vulnerability patterns, and security guidelines for blockchain development.

## Features

- **Security Knowledge Base**: Comprehensive security documentation
- **Vulnerability Patterns**: Common vulnerability patterns and examples
- **Best Practices**: Security best practices for smart contracts
- **Reference Materials**: Technical references and guidelines

## Architecture

### Core Components

- **Security Documentation**: Curated security knowledge
- **Vulnerability Database**: Pattern database for common vulnerabilities
- **Best Practice Guides**: Security guidelines and recommendations
- **Reference Materials**: Technical documentation and examples

### Knowledge Structure

The component organizes knowledge into categories:
- **Access Control**: Access control vulnerabilities and patterns
- **Reentrancy**: Reentrancy attack patterns and prevention
- **Arithmetic**: Integer overflow/underflow patterns
- **Cross-contract**: Cross-contract interaction security
- **Liquidation**: Liquidation mechanism security
- **Slippage**: Slippage protection mechanisms

## Usage

### Accessing Knowledge Base

```python
# Knowledge base is organized in markdown files
# Access specific vulnerability knowledge
access_control_knowledge = "./src/knowledges/access_control.md"
reentrancy_knowledge = "./src/knowledges/reentrancy.md"
arithmetic_knowledge = "./src/knowledges/arithmetic.md"
```

### Knowledge Categories

- **7540properties**: ERC-7540 standard properties
- **Across**: Cross-chain bridge security
- **Arbitrum**: Arbitrum-specific security considerations
- **Chainlink**: Chainlink oracle security
- **DAO**: Decentralized autonomous organization security
- **Lending**: DeFi lending protocol security
- **Liquidation**: Liquidation mechanism security
- **Uniswap V3**: Uniswap V3-specific security patterns

## Integration

The Knowledges component integrates with:

- **Planning Module**: Provides security context for task planning
- **Validation Module**: Supplies vulnerability patterns for analysis
- **Prompt Factory**: Enhances prompts with security knowledge
- **Reasoning Module**: Provides context for vulnerability reasoning

## Configuration

### Knowledge Paths

```python
# Default knowledge paths
KNOWLEDGE_BASE_PATH = "./src/knowledges"
VULNERABILITY_PATTERNS = "./src/knowledges/vulnerability_patterns"
SECURITY_GUIDELINES = "./src/knowledges/security_guidelines"
```

### Knowledge Categories

- **Core Vulnerabilities**: Basic vulnerability patterns
- **Protocol-Specific**: Protocol-specific security considerations
- **Advanced Patterns**: Complex vulnerability patterns
- **Best Practices**: Security best practices and guidelines

## Performance

- **Fast Access**: Optimized knowledge retrieval
- **Structured Organization**: Well-organized knowledge structure
- **Comprehensive Coverage**: Extensive security knowledge base
- **Easy Maintenance**: Simple markdown-based knowledge management

## Dependencies

- `markdown`: For knowledge file parsing
- `pathlib`: For file path handling
- `json`: For structured knowledge data
- `typing`: For type hints

## Development

### Adding New Knowledge

1. Create markdown file in appropriate category
2. Follow knowledge structure format
3. Add cross-references and examples
4. Update knowledge index

### Extending Knowledge Base

1. Define new knowledge categories
2. Implement knowledge retrieval methods
3. Add knowledge validation
4. Update documentation

## API Reference

### Knowledge Access

```python
def load_knowledge(category: str, topic: str) -> str:
    """Load knowledge content for specific category and topic"""
    pass

def search_knowledge(query: str) -> List[str]:
    """Search knowledge base for relevant content"""
    pass

def get_vulnerability_patterns() -> Dict[str, str]:
    """Get all vulnerability patterns"""
    pass
```

### Knowledge Categories

- `access_control`: Access control vulnerabilities
- `reentrancy`: Reentrancy attack patterns
- `arithmetic`: Arithmetic overflow/underflow
- `cross_contract`: Cross-contract security
- `liquidation`: Liquidation mechanisms
- `slippage`: Slippage protection

## Error Handling

The component includes comprehensive error handling for:
- Missing knowledge files
- Invalid knowledge formats
- Search failures
- Knowledge corruption

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add or update knowledge content
4. Follow knowledge formatting guidelines
5. Submit a pull request

## Knowledge Guidelines

### Content Structure

- **Overview**: Brief description of the topic
- **Vulnerability Patterns**: Common vulnerability patterns
- **Examples**: Code examples and case studies
- **Prevention**: Prevention strategies and best practices
- **References**: Additional resources and references

### Formatting Standards

- Use clear and concise language
- Include code examples where appropriate
- Provide practical prevention strategies
- Maintain consistent formatting

## License

This component is part of the Finite Monkey Engine project and follows the same licensing terms. 