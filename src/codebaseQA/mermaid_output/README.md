# Mermaid Output Directory

This directory is used to store Mermaid chart files generated from smart contract business flow analysis.

## 📁 Directory Structure

```
src/codebaseQA/mermaid_output/
├── {project_id_1}/
│   ├── {project_id_1}_business_flow.mmd
│   ├── {project_id_1}_contracts.mmd
│   ├── {project_id_1}_scripts.mmd
│   ├── {project_id_1}_tests.mmd
│   └── {project_id_1}_global_overview.mmd
├── {project_id_2}/
│   └── {project_id_2}_business_flow.mmd
└── README.md
```

## 📊 File Types

### Small Projects (<30 files)
- `{project_id}_business_flow.mmd` - Complete business flow sequence diagram

### Large Projects (≥30 files) 
- `{project_id}_{folder_name}.mmd` - Folder-level business flow diagrams
- `{project_id}_global_overview.mmd` - Project-level architecture overview

## 🔄 Generation Process

1. **Scanning Phase**: Smart Code Summarizer analyzes project files
2. **Strategy Selection**: Choose incremental or folder-based analysis
3. **Mermaid Generation**: Generate corresponding .mmd files
4. **Business Flow Extraction**: Planning module extracts business flows from Mermaid files

## 🎯 Usage

### In Planning Module
```python
# Extract business flows from Mermaid files
mermaid_flows = extract_all_business_flows_from_mermaid_files(
    mermaid_output_dir="src/codebaseQA/mermaid_output", 
    project_id="my_project"
)
```

### File Formats
- **File Extension**: `.mmd`
- **Content Format**: Standard Mermaid syntax
- **Encoding**: UTF-8

## 🛠️ Maintenance

### Cleanup Policy
- Files are automatically overwritten for the same project_id
- Manual cleanup may be required for discontinued projects
- Recommend periodic cleanup of old project directories

### File Size Management
- Large projects may generate multiple large files
- Monitor disk space usage
- Consider compression for long-term storage

## 🔍 Troubleshooting

### Common Issues
1. **Empty files**: Check if Smart Code Summarizer ran successfully
2. **Missing files**: Verify project_id matches and files were generated
3. **Corrupt Mermaid syntax**: Validate with Mermaid editor

### Debug Tips
- Check generation logs in Smart Code Summarizer
- Validate Mermaid syntax using online editors
- Verify file permissions and disk space

---

**📈 Generated Mermaid diagrams provide visual representation of smart contract business flows for enhanced analysis and understanding.** 