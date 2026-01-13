---
name: etl-silver-layer-development
description: Comprehensive ETL development skill for building standardized silver layer data pipelines in Databricks using Asset Bundles, declarative pipelines, with enforced data quality rules and unit testing.
---

# Silver Layer ETL Development Skill

This skill provides best practices, templates, and executable examples for developing production-grade silver layer data pipelines in Databricks.

## Overview

The silver layer (refined/conformed data) is a critical component of the medallion architecture, where data is:
- Cleaned and validated
- Standardized with consistent column naming
- Enriched with business logic
- Quality-checked and tested
- Ready for analytical consumption

## Core Principles

### 1. Standardized Column Naming
All silver layer tables must follow these conventions:
- **Snake case**: `customer_id`, `order_date`, `total_amount`
- **Prefix with entity**: `customer_first_name`, `customer_last_name`
- **Timestamps**: Use `_at` suffix (e.g., `created_at`, `updated_at`)
- **Boolean fields**: Use `is_` or `has_` prefix (e.g., `is_active`, `has_address`)
- **Amounts/Metrics**: Use `_amount`, `_count`, `_rate` suffix

### 2. Metadata Columns (Required in ALL Silver Tables)
Every silver table must include:
```python
- record_created_at: TIMESTAMP  # When record was created in silver
- record_updated_at: TIMESTAMP  # Last update timestamp
- source_system: STRING         # Origin system identifier
- load_id: STRING               # Batch/job identifier for lineage
- is_current: BOOLEAN           # For SCD Type 2 tracking
- is_deleted: BOOLEAN           # Soft delete flag
```

### 3. Data Quality Framework
Implement these quality checks at minimum:
- **Completeness**: Null checks on critical columns
- **Validity**: Data type and format validation
- **Consistency**: Cross-field logical checks
- **Accuracy**: Range and threshold validation
- **Uniqueness**: Primary key constraints
- **Timeliness**: Data freshness checks

### 4. Unit Testing Standards
Every transformation must have:
- **Input validation tests**: Verify data types and schemas
- **Transformation logic tests**: Assert business rules
- **Output validation tests**: Confirm schema and data quality
- **Edge case tests**: Handle nulls, duplicates, extremes

## Workflow

### Step 1: Set Up Databricks Asset Bundle
Use the provided `databricks.yml` template in the `examples/` folder to structure your pipeline project.

### Step 2: Define Source-to-Silver Transformations
Create declarative SQL transformations in `transformations/` folder following the template pattern.

### Step 3: Implement Data Quality Rules
Use the `data_quality_rules.py` template to define and enforce quality expectations.

### Step 4: Write Unit Tests
Follow the `test_transformations.py` template for pytest-based unit testing.

### Step 5: Deploy with Asset Bundle
Use `databricks bundle deploy` to deploy your pipeline to the target environment.

## File Structure
```
etl-silver-layer/
├── SKILL.md (this file)
├── examples/
│   ├── databricks.yml              # Asset bundle configuration
│   ├── silver_pipeline_example.py  # Complete pipeline example
│   └── transformations.sql         # SQL transformation examples
├── templates/
│   ├── data_quality_rules.py       # DQ framework template
│   ├── test_transformations.py     # Unit test template
│   ├── silver_table_schema.py      # Schema definition template
│   └── config_template.yml         # Pipeline configuration
├── scripts/
│   ├── deploy_pipeline.sh          # Deployment automation
│   ├── run_tests.sh                # Testing automation
│   └── validate_schema.py          # Schema validation utility
└── README.md                       # Usage documentation
```

## Quick Start Example

To create a new silver layer pipeline:

1. Copy the example asset bundle structure:
```bash
cp -r examples/databricks.yml your_pipeline/
```

2. Define your transformations using SQL or PySpark

3. Add data quality rules and unit tests

4. Deploy using:
```bash
databricks bundle deploy --target dev
```

## Best Practices

### Performance Optimization
- Use partitioning on date columns (`partition_date`)
- Implement Z-ordering on frequently filtered columns
- Use Delta Lake liquid clustering for high-cardinality columns
- Enable Delta optimized writes

### Change Data Capture (CDC)
- Implement SCD Type 2 for historical tracking
- Use merge operations for upserts
- Track lineage with `load_id`

### Security & Governance
- Apply Unity Catalog tags for PII identification
- Implement row-level and column-level security
- Document data lineage in Asset Bundle config

### Monitoring & Observability
- Log all data quality failures
- Track pipeline metrics (rows processed, duration, failures)
- Set up alerting for quality threshold breaches

## Examples and Templates

All examples and templates are provided in their respective folders. Each includes:
- Inline comments explaining the approach
- Configuration options and best practices
- Error handling patterns
- Performance optimization tips

## Resources
- See `examples/` for working code samples
- See `templates/` for reusable templates
- See `scripts/` for automation utilities
- See `README.md` for detailed usage guide
