# Audit Columns Standard - Agent Skill

## Overview

This agent skill enforces standardized audit columns across all data tables in your Databricks environment. It ensures every table includes proper tracking for data lineage, changes, ownership, and compliance.

## Required Audit Columns

Every table must include:

- `created_at` - Record creation timestamp
- `updated_at` - Last modification timestamp
- `created_by` - User/service that created the record
- `updated_by` - User/service that last modified the record
- `load_id` - Unique batch/job identifier
- `pipeline_name` - Name of the processing pipeline
- `source_system` - Origin system identifier

## Usage with Databricks Assistant

Upload this skill to your workspace:

```bash
databricks workspace import-dir \
  ./agent-skills/audit-columns-standard \
  /Users/<your-email>/.assistant/skills/audit-columns-standard
```

Then ask questions like:
- "What audit columns do I need to add to my table?"
- "Help me add audit columns to this DataFrame"
- "How do I update audit columns when merging data?"
- "Validate that my table has all required audit columns"

## Key Features

- ✅ Standardized column names and types
- ✅ PySpark and SQL implementation patterns
- ✅ Automatic validation functions
- ✅ Merge/update patterns with audit tracking
- ✅ Audit history table patterns
- ✅ Compliance tracking

## Quick Example

```python
from pyspark.sql import functions as F

def add_audit_columns(df, load_id, pipeline_name, source_system):
    return df.withColumn("created_at", F.current_timestamp()) \
             .withColumn("updated_at", F.current_timestamp()) \
             .withColumn("created_by", F.lit(F.current_user())) \
             .withColumn("updated_by", F.lit(F.current_user())) \
             .withColumn("load_id", F.lit(load_id)) \
             .withColumn("pipeline_name", F.lit(pipeline_name)) \
             .withColumn("source_system", F.lit(source_system))
```

See `SKILL.md` for complete documentation and patterns.
