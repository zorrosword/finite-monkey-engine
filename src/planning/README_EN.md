# Planning Module Refactoring Documentation

## Overview

This refactoring splits the original `planning_v2.py` file into multiple modules, improving code maintainability and reusability. The refactoring adopts a layered architecture, decomposing complex business logic into independent processors and utility modules.

## File Structure

```
src/planning/
├── __init__.py                  # Module initialization file
├── planning_v2.py              # Core entry class (simplified)
├── business_flow_processor.py  # Business flow processor
├── planning_processor.py       # Planning processor
├── business_flow_utils.py      # Business flow utility tools
├── json_utils.py               # JSON processing tools
├── function_utils.py           # Function processing tools
├── config_utils.py             # Configuration management tools
└── README.md                   # Chinese documentation
└── README_EN.md                # This English documentation
```

## Module Description

### 1. planning_v2.py (Core Entry)
Now very concise, mainly responsible for:
- `PlanningV2` class: Main planning engine entry point
- Initialize various processors
- Provide clean public API interface

### 2. business_flow_processor.py (Business Flow Processor)
Specifically handles business flow related complex logic:
- `get_all_business_flow()` - Main logic for getting all business flows
- `_process_contract_business_flows()` - Process business flows for a single contract
- `_process_function_business_flow()` - Process business flow for a single function
- `_get_function_code()` - Get function code
- `_get_business_flow_list()` - Get business flow list
- `_process_business_flow_response()` - Process business flow response
- `_extract_function_line_info()` - Extract function line information
- `_enhance_with_cross_contract_code()` - Cross-contract code enhancement
- `_enhance_business_flow_code()` - Business flow code enhancement

### 3. planning_processor.py (Planning Processor)
Specifically handles planning related complex logic:
- `do_planning()` - Main logic for executing planning
- `_prepare_planning()` - Prepare planning work
- `_filter_test_functions()` - Filter test functions
- `_get_business_flows_if_needed()` - Get business flows on demand
- `_process_all_functions()` - Process all functions
- `_process_single_function()` - Process single function
- `_handle_business_flow_planning()` - Handle business flow planning
- `_handle_function_code_planning()` - Handle function code planning
- `_generate_checklist_and_analysis()` - Generate checklist and analysis
- `_write_checklist_to_csv()` - Write to CSV file
- `_analyze_business_type()` - Analyze business type
- `_create_planning_task()` - Create planning task

### 4. business_flow_utils.py (Business Flow Utils)
Utility functions related to business flow processing:
- `ask_openai_for_business_flow()` - Ask OpenAI to get business flow
- `extract_and_concatenate_functions_content()` - Extract and concatenate function content
- `decode_business_flow_list_from_response()` - Decode business flow list from response
- `search_business_flow()` - Search business flow
- `identify_contexts()` - Identify contexts

### 5. json_utils.py (JSON Utils)
Utility functions related to JSON processing:
- `extract_filtered_functions()` - Extract function names from JSON string
- `extract_results()` - Extract results from text
- `merge_and_sort_rulesets()` - Merge and sort rule sets

### 6. function_utils.py (Function Utils)
Utility functions related to function processing:
- `extract_related_functions_by_level()` - Extract related functions by level

### 7. config_utils.py (Configuration Utils)
Utility functions related to configuration management:
- `should_exclude_in_planning()` - Determine if file should be excluded in planning
- `get_visibility_filter_by_language()` - Get visibility filter by programming language
- `get_scan_configuration()` - Get scan configuration

## Refactoring Architecture

### Layered Design
```
┌─────────────────────────────────────┐
│           PlanningV2                │  ← Entry Layer (Simplified API)
│         (Entry Point)               │
└─────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│       Processor Layer               │  ← Processor Layer (Core Business Logic)
│  ┌─────────────────────────────────┐│
│  │  BusinessFlowProcessor         ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  PlanningProcessor             ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│         Utils Layer                 │  ← Utils Layer (Pure Function Tools)
│  ┌─────────────┬─────────────────────│
│  │BusinessFlow │JsonUtils │Function ││
│  │Utils        │         │Utils    ││
│  └─────────────┴─────────────────────│
│  ┌─────────────────────────────────┐│
│  │          ConfigUtils           ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

## Refactoring Benefits

1. **Layered Architecture**: Clear layered design with distinct responsibilities
2. **Code Reuse**: Utility functions and processors can be reused in other modules
3. **Single Responsibility**: Each module focuses on specific functionality
4. **Easy to Test**: Easier to perform unit testing on individual components
5. **Easy to Maintain**: Modifying specific functionality only requires modifying corresponding module
6. **Easy to Extend**: Adding new functionality only requires adding new processors or utilities
7. **Code Readability**: Code structure is clearer and easier to understand

## Lines of Code Comparison

### Before Refactoring
- `planning_v2.py`: 786 lines (monolithic file)

### After Refactoring
- `planning_v2.py`: 48 lines (entry file, 94% reduction)
- `business_flow_processor.py`: 228 lines (business flow processor)
- `planning_processor.py`: 227 lines (planning processor)
- `business_flow_utils.py`: 148 lines (business flow utils)
- `json_utils.py`: 93 lines (JSON utils)
- `function_utils.py`: 116 lines (function utils)
- `config_utils.py`: 111 lines (configuration utils)

**Total**: The original 786 lines split into 7 files, each with clear responsibilities.

## Usage

### Basic Usage (Fully Compatible with Previous Version)
```python
from planning import PlanningV2

# Use core planning class (API unchanged)
planning = PlanningV2(project, taskmgr)
planning.do_planning()
```

### Advanced Usage (Using Specific Processors and Tools)
```python
from planning import (
    PlanningV2, 
    BusinessFlowProcessor, 
    PlanningProcessor,
    BusinessFlowUtils, 
    JsonUtils, 
    FunctionUtils, 
    ConfigUtils
)

# Use specific processors
business_flow_processor = BusinessFlowProcessor(project)
business_flows = business_flow_processor.get_all_business_flow(functions)

# Use utility functions
config = ConfigUtils.get_scan_configuration()
filtered_functions = JsonUtils.extract_filtered_functions(json_string)
```

## Compatibility

This refactoring maintains the original public API completely unchanged, so existing code can continue to work without any modifications. It also provides more fine-grained APIs for advanced users. 