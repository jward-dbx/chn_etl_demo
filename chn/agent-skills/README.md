# Databricks Agent Skills Collection

## Overview

This collection provides comprehensive agent skills for Databricks Assistant, focused on enterprise data engineering best practices, governance, and metadata-driven frameworks.

## Skills Included

### 1. 🏗️ ETL Silver Layer Development (`etl-silver-layer/`)

Complete framework for building production-grade silver layer ETL pipelines.

**Features:**
- Standardized column naming conventions
- Required metadata columns (6 mandatory fields)
- Data quality framework
- Unit testing infrastructure
- SCD Type 2 implementation
- Databricks Asset Bundles
- Performance optimization patterns

**Use Cases:**
- Building new silver layer tables
- Implementing data quality checks
- Creating Delta Live Tables pipelines
- Setting up CI/CD for ETL

### 2. 📋 Audit Columns Standard (`audit-columns-standard/`)

Enforces standardized audit columns for tracking data lineage, changes, and compliance.

**Features:**
- Required audit columns (created_at, updated_at, created_by, etc.)
- Validation functions
- Merge/update patterns
- Audit history tables
- Compliance tracking

**Use Cases:**
- Adding audit trails to tables
- Tracking data lineage
- Compliance reporting
- Change auditing

### 3. 🏷️ Tagging Standards (`tagging-standards/`)

Comprehensive tagging taxonomy for all Databricks artifacts.

**Features:**
- Required tags for all artifacts
- Tag registry with controlled vocabularies
- Validation and compliance tracking
- Cost center tracking
- Governance dashboards

**Use Cases:**
- Organizing data assets
- Cost chargeback
- Data discovery
- Compliance tracking
- Access control

### 4. 🎯 Metadata-Driven Framework (`metadata-framework/`)

Patterns for building configuration-driven ETL frameworks.

**Features:**
- Pipeline registry
- Transformation rules
- Data quality rules
- Execution tracking
- Generic pipeline engines
- Schema registry

**Use Cases:**
- Building scalable ETL frameworks
- Configuration-driven pipelines
- Centralized pipeline management
- Dynamic transformations

## Installation

### Option 1: Upload All Skills to Databricks

```bash
# Upload all skills at once
databricks workspace import-dir \
  ./agent-skills \
  /Users/<your-email>/.assistant/skills
```

### Option 2: Upload Individual Skills

```bash
# Upload specific skill
databricks workspace import-dir \
  ./agent-skills/etl-silver-layer \
  /Users/<your-email>/.assistant/skills/etl-silver-layer
```

## Usage with Databricks Assistant

Once uploaded, skills are automatically loaded by Databricks Assistant when relevant to your questions.

### Example Interactions

**ETL Development:**
- "Help me create a silver layer pipeline for customer data"
- "What are the standard column naming conventions?"
- "Generate unit tests for my transformation"

**Audit Columns:**
- "What audit columns do I need on this table?"
- "Help me add audit tracking to my DataFrame"
- "Validate audit columns on my tables"

**Tagging:**
- "What tags should I apply to this table?"
- "Help me tag all tables in my schema"
- "Generate a tagging compliance report"

**Metadata Framework:**
- "Help me create a metadata-driven pipeline"
- "How do I register a pipeline in metadata?"
- "Build a generic pipeline engine"

## Skill Statistics

| Skill | Files | Lines of Code | Templates | Examples |
|-------|-------|---------------|-----------|----------|
| ETL Silver Layer | 19 | ~6,500 | 5 | 4 |
| Audit Columns | 2 | ~600 | Multiple patterns | Yes |
| Tagging Standards | 2 | ~750 | Multiple patterns | Yes |
| Metadata Framework | 2 | ~700 | Multiple patterns | Yes |
| **Total** | **25** | **~8,550** | **Many** | **Many** |

## Architecture

### Consistency Mechanisms

All skills enforce these consistency principles:

1. **Standardized Naming**
   - snake_case column names
   - Entity prefixes
   - Type suffixes (_at, _amount, _count)
   - Boolean prefixes (is_, has_, needs_)

2. **Required Metadata**
   - Audit columns on every table
   - Tags on every artifact
   - Lineage tracking
   - Version control

3. **Data Quality**
   - Built-in validation rules
   - Quality scoring
   - Automated checks
   - Quarantine patterns

4. **Governance**
   - Centralized registries
   - Compliance tracking
   - Access control
   - Cost attribution

### Integration Points

Skills work together:

```
ETL Silver Layer
  ↓ Uses
Audit Columns (tracking)
  ↓ Uses
Tagging Standards (governance)
  ↓ Managed by
Metadata Framework (configuration)
```

## Best Practices

### 1. Start with Standards

Begin with `etl-silver-layer` to understand core principles, then add audit columns and tagging.

### 2. Enforce Compliance

Use validation functions to check compliance before deployment:

```python
# Validate audit columns
validate_audit_columns(df, "customers")

# Validate tags
validate_table_tags("main", "silver", "customers")

# Validate schema
validate_silver_schema(schema)
```

### 3. Metadata-Driven Development

Use the metadata framework for large-scale ETL:

```python
# Register once
register_pipeline({...})

# Execute many times
pipeline = MetadataDrivenPipeline(spark, "pipeline_id")
pipeline.execute()
```

### 4. Documentation

- Keep skill documentation updated
- Document custom extensions
- Share learnings with team

## Customization

### Extending Skills

1. **Add new patterns** to existing skills
2. **Create new skills** for specific domains
3. **Customize standards** to match your organization
4. **Share updates** with the team

### Example: Custom Skill

```markdown
---
name: my-custom-skill
description: Custom patterns for my domain
---

# My Custom Skill

Custom patterns and standards...
```

## Support

### Resources

- **Documentation**: Each skill has comprehensive `SKILL.md` and `README.md`
- **Examples**: Working code examples in `examples/` folders
- **Templates**: Reusable templates in `templates/` folders
- **Scripts**: Automation scripts for deployment and validation

### Getting Help

1. **Databricks Assistant**: Ask questions directly
2. **Documentation**: Read skill documentation
3. **Examples**: Review working examples
4. **Team**: Share with your data engineering team

## Version History

- **v1.0.0** (January 2026)
  - Initial release
  - 4 comprehensive skills
  - 25 files, 8,550+ lines
  - Production-ready

## Contributing

To add or modify skills:

1. Follow the SKILL.md format
2. Include comprehensive examples
3. Add validation functions
4. Document thoroughly
5. Test with Databricks Assistant

## License

Internal use - Enterprise data engineering standards

---

**🚀 Ready to build world-class data pipelines with enterprise standards!**
