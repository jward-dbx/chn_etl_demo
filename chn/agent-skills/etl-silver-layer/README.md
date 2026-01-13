# Silver Layer ETL Development - Agent Skill

## Purpose

This agent skill provides comprehensive guidance, templates, and examples for developing production-grade silver layer ETL pipelines in Databricks following enterprise best practices.

## What's Included

### 1. **SKILL.md** - Main Skill Definition
The core skill file that Databricks Assistant loads automatically when ETL development is needed.

### 2. **Examples** (`examples/`)
- Complete working examples of Databricks Asset Bundles
- SQL and PySpark transformation patterns
- End-to-end pipeline implementations

### 3. **Templates** (`templates/`)
- Reusable code templates for common patterns
- Data quality frameworks
- Unit testing scaffolds
- Schema definitions

### 4. **Scripts** (`scripts/`)
- Deployment automation
- Testing utilities
- Schema validation tools

## Installation for Databricks Assistant

To make this skill available to Databricks Assistant:

1. Copy the entire `etl-silver-layer` folder to your Databricks workspace:
```bash
databricks workspace import-dir \
  /Users/justin.ward/chn/agent-skills/etl-silver-layer \
  /Users/<your-email>/.assistant/skills/etl-silver-layer
```

2. The skill will automatically be loaded by Databricks Assistant when you're working on ETL tasks

3. You can reference it explicitly by mentioning "silver layer ETL" or "ETL development" in your prompts

## Usage Examples

### With Databricks Assistant

Simply ask questions like:
- "Help me create a silver layer pipeline for customer data"
- "What are the standard column naming conventions for silver tables?"
- "Generate unit tests for my transformation logic"
- "Set up data quality rules for my pipeline"

### Manual Usage

You can also use the templates and examples directly:

```bash
# Copy a template to your project
cp templates/data_quality_rules.py my_project/

# Run the deployment script
./scripts/deploy_pipeline.sh --target dev --pipeline customer_silver
```

## Key Features

### ✅ Standards Enforcement
- Standardized column naming (snake_case, entity prefixes)
- Required metadata columns (timestamps, source tracking, lineage)
- Consistent data types and formats

### ✅ Data Quality Framework
- Built-in quality rules (completeness, validity, consistency, accuracy, uniqueness, timeliness)
- Automated quality checks with Great Expectations integration
- Quality metrics logging and alerting

### ✅ Testing Infrastructure
- Unit test templates using pytest
- Integration test patterns
- Data validation assertions
- Edge case handling

### ✅ Databricks Asset Bundles
- Complete DAB configurations
- Multi-environment deployment (dev, staging, prod)
- Resource definitions (jobs, pipelines, tables)
- Configuration management

### ✅ Performance Optimization
- Partitioning strategies
- Z-ordering recommendations
- Liquid clustering examples
- Optimized write patterns

## Architecture

This skill follows the **Medallion Architecture** pattern:

```
Bronze (Raw)  →  Silver (Refined)  →  Gold (Aggregated)
                      ↑
                 This Skill
```

### Silver Layer Characteristics:
- **Cleaned**: Deduplicated, validated, standardized
- **Conformed**: Consistent naming, types, formats
- **Enriched**: Business logic applied, lookups joined
- **Tracked**: Lineage, quality metrics, audit fields
- **Tested**: Unit tests, integration tests, quality checks

## Directory Structure

```
etl-silver-layer/
├── SKILL.md                          # Main skill definition
├── README.md                         # This file
├── examples/
│   ├── databricks.yml                # Asset bundle example
│   ├── silver_pipeline_example.py    # Complete pipeline
│   ├── transformations.sql           # SQL transformations
│   └── customer_silver_dlt.py        # Delta Live Tables example
├── templates/
│   ├── data_quality_rules.py         # DQ framework
│   ├── test_transformations.py       # Unit test template
│   ├── silver_table_schema.py        # Schema template
│   ├── config_template.yml           # Config template
│   └── scd_type2_merge.sql          # SCD Type 2 template
├── scripts/
│   ├── deploy_pipeline.sh            # Deployment script
│   ├── run_tests.sh                  # Test runner
│   ├── validate_schema.py            # Schema validator
│   └── generate_dq_report.py         # DQ reporting
└── docs/
    ├── standards.md                  # Detailed standards
    ├── best_practices.md             # Best practices guide
    └── troubleshooting.md            # Common issues
```

## Requirements

- Databricks Runtime 13.3 LTS or higher
- Unity Catalog enabled
- Databricks CLI configured
- Python 3.10+
- pytest (for unit testing)
- great-expectations (for data quality)

## Contributing

This skill is designed to evolve with your organization's needs. Customize:
- Column naming standards to match your conventions
- Data quality rules based on your requirements
- Templates to fit your specific use cases
- Scripts to automate your workflows

## Support

For questions or issues:
1. Check the `docs/troubleshooting.md` file
2. Review examples in `examples/` folder
3. Consult Databricks documentation
4. Ask Databricks Assistant with this skill loaded

## Version

- **Version**: 1.0.0
- **Last Updated**: January 2026
- **Compatible With**: Databricks Runtime 13.3+, Agent Skills Open Standard
