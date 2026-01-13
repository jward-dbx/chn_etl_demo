# Metadata-Driven Framework - Agent Skill

## Overview

This agent skill provides patterns for building metadata-driven ETL frameworks where pipeline behavior, transformations, and data quality rules are controlled through configuration metadata rather than hardcoded logic.

## Core Concept

Separate **configuration** from **execution logic**:

- Configuration stored in metadata tables
- Generic engines execute based on metadata
- Change behavior without code changes
- Single source of truth for all pipelines

## Metadata Tables

This skill provides schemas for:

1. **Pipeline Registry** - Central catalog of all ETL pipelines
2. **Transformation Rules** - Column mappings and transformation logic
3. **Data Quality Rules** - Quality expectations and validation rules
4. **Execution Log** - Complete audit trail of all runs
5. **Schema Registry** - Centralized schema definitions

## Usage with Databricks Assistant

Upload this skill to your workspace:

```bash
databricks workspace import-dir \
  ./agent-skills/metadata-framework \
  /Users/<your-email>/.assistant/skills/metadata-framework
```

Then ask questions like:
- "Help me create a metadata-driven pipeline"
- "How do I register a new pipeline in the metadata?"
- "Show me how to add transformation rules"
- "How do I execute a pipeline from metadata?"
- "Create a generic pipeline engine"

## Key Features

- ✅ Configuration-driven pipelines
- ✅ Dynamic transformation execution
- ✅ Centralized metadata management
- ✅ Complete execution tracking
- ✅ Schema evolution support
- ✅ Data quality integration

## Quick Example

```python
# Register a pipeline
register_pipeline({
    "pipeline_id": "customer_silver_etl",
    "pipeline_name": "Customer Silver Layer ETL",
    "source_type": "table",
    "source_table": "bronze.customers",
    "target_table": "silver.customers",
    "processing_mode": "merge",
    "owner": "data-eng@company.com",
    "domain": "customer"
})

# Execute pipeline from metadata
pipeline = MetadataDrivenPipeline(spark, "customer_silver_etl")
pipeline.execute()
```

See `SKILL.md` for complete documentation and patterns.
