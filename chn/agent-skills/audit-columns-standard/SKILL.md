---
name: audit-columns-standard
description: Enforces standardized audit columns on all data tables for tracking data lineage, changes, and compliance. Provides templates and validation for created_at, updated_at, created_by, updated_by, and other audit fields.
---

# Audit Columns Standard Skill

This skill ensures all data tables include standardized audit columns for tracking data lineage, changes, ownership, and compliance across your Databricks environment.

## Core Audit Column Standards

### Required Audit Columns (ALL Tables)

Every table in bronze, silver, and gold layers MUST include these audit columns:

```sql
-- Temporal Audit Columns
created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
updated_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()

-- Identity Audit Columns  
created_by           STRING NOT NULL DEFAULT current_user()
updated_by           STRING NOT NULL DEFAULT current_user()

-- Process Audit Columns
load_id              STRING NOT NULL       -- Unique identifier for the batch/job
pipeline_name        STRING NOT NULL       -- Name of the pipeline that processed the record
pipeline_run_id      STRING                -- Unique run ID from the pipeline execution

-- Data Lineage Columns
source_system        STRING NOT NULL       -- Origin system (e.g., 'salesforce', 'sap', 'api')
source_table         STRING                -- Source table/object name
source_record_id     STRING                -- Original record ID from source

-- Version Control Columns
record_version       INTEGER DEFAULT 1     -- Version number for the record
record_hash          STRING                -- Hash of record content for change detection
```

### Extended Audit Columns (Recommended for Critical Tables)

For tables requiring enhanced auditability (PII, financial, compliance):

```sql
-- Compliance Audit Columns
data_classification  STRING                -- PII, CONFIDENTIAL, INTERNAL, PUBLIC
compliance_tags      ARRAY<STRING>         -- Compliance frameworks: GDPR, HIPAA, SOX, etc.
retention_date       TIMESTAMP             -- Date when record should be purged

-- Change Tracking Columns
change_type          STRING                -- INSERT, UPDATE, DELETE, MERGE
change_reason        STRING                -- Business reason for the change
previous_values      STRING                -- JSON of changed fields (for history)

-- Quality Audit Columns
quality_score        DECIMAL(5,2)          -- Data quality score (0-100)
validation_status    STRING                -- PASSED, FAILED, WARNING, PENDING
validation_errors    ARRAY<STRING>         -- List of validation errors if any

-- Access Audit Columns
last_accessed_at     TIMESTAMP             -- Last time record was queried
accessed_by          STRING                -- User who last accessed the record
access_count         INTEGER DEFAULT 0     -- Number of times accessed
```

## Naming Conventions

### Timestamp Columns
- **Pattern**: `*_at` or `*_date` or `*_timestamp`
- **Type**: `TIMESTAMP` (not STRING or BIGINT)
- **Examples**: `created_at`, `updated_at`, `deleted_at`, `archived_at`

### User/Identity Columns
- **Pattern**: `*_by` or `*_user` or `*_identity`
- **Type**: `STRING` (email, username, or service principal)
- **Examples**: `created_by`, `updated_by`, `approved_by`, `deleted_by`

### Process/Job Columns
- **Pattern**: `*_id` or `*_name` or `*_run_*`
- **Type**: `STRING` for IDs, `STRING` for names
- **Examples**: `load_id`, `job_id`, `pipeline_name`, `pipeline_run_id`

## Implementation Patterns

### Pattern 1: Add Audit Columns to DataFrame (PySpark)

```python
from pyspark.sql import functions as F
from datetime import datetime

def add_audit_columns(df, load_id, pipeline_name, source_system, 
                     pipeline_run_id=None, source_table=None):
    """
    Add standardized audit columns to any DataFrame.
    
    Args:
        df: Input DataFrame
        load_id: Unique batch/load identifier
        pipeline_name: Name of the processing pipeline
        source_system: Source system identifier
        pipeline_run_id: Optional pipeline run ID
        source_table: Optional source table name
        
    Returns:
        DataFrame with audit columns added
    """
    return df.withColumn("created_at", F.current_timestamp()) \
             .withColumn("updated_at", F.current_timestamp()) \
             .withColumn("created_by", F.lit(F.current_user())) \
             .withColumn("updated_by", F.lit(F.current_user())) \
             .withColumn("load_id", F.lit(load_id)) \
             .withColumn("pipeline_name", F.lit(pipeline_name)) \
             .withColumn("pipeline_run_id", F.lit(pipeline_run_id)) \
             .withColumn("source_system", F.lit(source_system)) \
             .withColumn("source_table", F.lit(source_table)) \
             .withColumn("source_record_id", F.col("id").cast("string")) \
             .withColumn("record_version", F.lit(1)) \
             .withColumn("record_hash", F.md5(F.concat_ws("||", *df.columns)))

# Usage Example
bronze_df = spark.table("bronze.customers")
audited_df = add_audit_columns(
    df=bronze_df,
    load_id=f"load_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    pipeline_name="customers_silver_etl",
    source_system="salesforce_crm",
    pipeline_run_id=dbutils.widgets.get("run_id"),
    source_table="sf_customers"
)
```

### Pattern 2: Add Audit Columns in SQL

```sql
-- Create table with audit columns
CREATE TABLE IF NOT EXISTS silver.customers (
  -- Business columns
  customer_id STRING NOT NULL,
  customer_name STRING,
  customer_email STRING,
  
  -- Required audit columns
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  created_by STRING NOT NULL DEFAULT current_user(),
  updated_by STRING NOT NULL DEFAULT current_user(),
  load_id STRING NOT NULL,
  pipeline_name STRING NOT NULL,
  pipeline_run_id STRING,
  source_system STRING NOT NULL,
  source_table STRING,
  source_record_id STRING,
  record_version INT DEFAULT 1,
  record_hash STRING
)
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'audit.enabled' = 'true',
  'audit.columns' = 'created_at,updated_at,created_by,updated_by'
);

-- Insert with audit columns
INSERT INTO silver.customers
SELECT 
  customer_id,
  customer_name,
  customer_email,
  -- Audit columns
  CURRENT_TIMESTAMP() AS created_at,
  CURRENT_TIMESTAMP() AS updated_at,
  current_user() AS created_by,
  current_user() AS updated_by,
  '${load_id}' AS load_id,
  'customers_silver_etl' AS pipeline_name,
  '${pipeline_run_id}' AS pipeline_run_id,
  'salesforce_crm' AS source_system,
  'sf_customers' AS source_table,
  CAST(id AS STRING) AS source_record_id,
  1 AS record_version,
  md5(concat_ws('||', customer_id, customer_name, customer_email)) AS record_hash
FROM bronze.customers;
```

### Pattern 3: Update Audit Columns on Change

```python
def update_audit_columns(df, change_type="UPDATE"):
    """
    Update audit columns when modifying existing records.
    
    Args:
        df: DataFrame with changes
        change_type: Type of change (UPDATE, DELETE, MERGE)
        
    Returns:
        DataFrame with updated audit columns
    """
    return df.withColumn("updated_at", F.current_timestamp()) \
             .withColumn("updated_by", F.lit(F.current_user())) \
             .withColumn("record_version", F.col("record_version") + 1) \
             .withColumn("change_type", F.lit(change_type)) \
             .withColumn("record_hash", F.md5(F.concat_ws("||", *[c for c in df.columns if not c.startswith("record_")])))

# Usage in merge
from delta.tables import DeltaTable

target_table = DeltaTable.forName(spark, "silver.customers")

target_table.alias("target").merge(
    update_audit_columns(source_df).alias("source"),
    "target.customer_id = source.customer_id"
).whenMatchedUpdate(set={
    # Business columns
    "customer_name": "source.customer_name",
    "customer_email": "source.customer_email",
    # Audit columns
    "updated_at": "source.updated_at",
    "updated_by": "source.updated_by",
    "record_version": "source.record_version",
    "record_hash": "source.record_hash",
    "change_type": "source.change_type"
}).whenNotMatchedInsert(values={
    "customer_id": "source.customer_id",
    "customer_name": "source.customer_name",
    "customer_email": "source.customer_email",
    # All audit columns from source
    "created_at": "source.created_at",
    "updated_at": "source.updated_at",
    "created_by": "source.created_by",
    "updated_by": "source.updated_by",
    "load_id": "source.load_id",
    "pipeline_name": "source.pipeline_name",
    "source_system": "source.source_system",
    "record_version": "source.record_version",
    "record_hash": "source.record_hash"
}).execute()
```

## Audit Column Validation

### Validation Rules

```python
def validate_audit_columns(df, table_name):
    """
    Validate that all required audit columns are present and valid.
    
    Args:
        df: DataFrame to validate
        table_name: Name of the table for error messages
        
    Returns:
        Tuple of (is_valid, errors)
    """
    errors = []
    
    # Required columns
    required_columns = [
        "created_at", "updated_at", "created_by", "updated_by",
        "load_id", "pipeline_name", "source_system"
    ]
    
    # Check presence
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing required audit column: {col}")
    
    # Check for nulls in required columns
    for col in required_columns:
        if col in df.columns:
            null_count = df.filter(F.col(col).isNull()).count()
            if null_count > 0:
                errors.append(f"Audit column '{col}' has {null_count} null values")
    
    # Validate timestamps
    timestamp_cols = ["created_at", "updated_at"]
    for col in timestamp_cols:
        if col in df.columns:
            # Check if updated_at >= created_at
            if col == "updated_at" and "created_at" in df.columns:
                invalid_dates = df.filter(F.col("updated_at") < F.col("created_at")).count()
                if invalid_dates > 0:
                    errors.append(f"Found {invalid_dates} records where updated_at < created_at")
    
    # Validate load_id format (should not be empty)
    if "load_id" in df.columns:
        empty_load_ids = df.filter(F.trim(F.col("load_id")) == "").count()
        if empty_load_ids > 0:
            errors.append(f"Found {empty_load_ids} records with empty load_id")
    
    is_valid = len(errors) == 0
    
    if not is_valid:
        print(f"Audit column validation failed for {table_name}:")
        for error in errors:
            print(f"  - {error}")
    
    return is_valid, errors

# Usage
is_valid, errors = validate_audit_columns(df, "silver.customers")
if not is_valid:
    raise ValueError(f"Audit column validation failed: {errors}")
```

### Validation SQL Query

```sql
-- Check for missing or invalid audit columns
SELECT 
  '${table_name}' AS table_name,
  COUNT(*) AS total_records,
  
  -- Check for nulls
  SUM(CASE WHEN created_at IS NULL THEN 1 ELSE 0 END) AS null_created_at,
  SUM(CASE WHEN updated_at IS NULL THEN 1 ELSE 0 END) AS null_updated_at,
  SUM(CASE WHEN created_by IS NULL THEN 1 ELSE 0 END) AS null_created_by,
  SUM(CASE WHEN load_id IS NULL THEN 1 ELSE 0 END) AS null_load_id,
  
  -- Check for invalid timestamps
  SUM(CASE WHEN updated_at < created_at THEN 1 ELSE 0 END) AS invalid_timestamps,
  
  -- Check for empty values
  SUM(CASE WHEN TRIM(load_id) = '' THEN 1 ELSE 0 END) AS empty_load_id,
  SUM(CASE WHEN TRIM(pipeline_name) = '' THEN 1 ELSE 0 END) AS empty_pipeline_name,
  
  -- Summary
  CASE 
    WHEN SUM(CASE WHEN created_at IS NULL THEN 1 ELSE 0 END) = 0
     AND SUM(CASE WHEN updated_at IS NULL THEN 1 ELSE 0 END) = 0
     AND SUM(CASE WHEN updated_at < created_at THEN 1 ELSE 0 END) = 0
    THEN 'PASSED'
    ELSE 'FAILED'
  END AS validation_status
FROM ${catalog}.${schema}.${table_name};
```

## Audit Table Pattern

### Create Audit History Table

For tracking all changes to sensitive tables:

```sql
CREATE TABLE IF NOT EXISTS audit.table_changes (
  -- Audit metadata
  audit_id STRING NOT NULL,
  audit_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  audit_user STRING NOT NULL DEFAULT current_user(),
  
  -- Target table information
  table_catalog STRING NOT NULL,
  table_schema STRING NOT NULL,
  table_name STRING NOT NULL,
  
  -- Record information
  record_id STRING NOT NULL,
  change_type STRING NOT NULL,  -- INSERT, UPDATE, DELETE
  
  -- Change details
  changed_columns ARRAY<STRING>,
  old_values MAP<STRING, STRING>,
  new_values MAP<STRING, STRING>,
  
  -- Process information
  pipeline_name STRING,
  load_id STRING,
  
  -- Additional context
  change_reason STRING,
  approved_by STRING,
  
  -- Partition column
  audit_date DATE GENERATED ALWAYS AS (CAST(audit_timestamp AS DATE))
)
USING DELTA
PARTITIONED BY (audit_date, table_name)
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);
```

### Log Changes to Audit Table

```python
def log_change_to_audit(table_name, record_id, change_type, 
                        changed_columns, old_values, new_values,
                        pipeline_name, load_id, change_reason=None):
    """
    Log a change to the audit history table.
    """
    audit_record = spark.createDataFrame([{
        "audit_id": f"{uuid.uuid4()}",
        "audit_timestamp": datetime.now(),
        "audit_user": spark.sparkContext.sparkUser(),
        "table_catalog": "main",
        "table_schema": "silver",
        "table_name": table_name,
        "record_id": record_id,
        "change_type": change_type,
        "changed_columns": changed_columns,
        "old_values": old_values,
        "new_values": new_values,
        "pipeline_name": pipeline_name,
        "load_id": load_id,
        "change_reason": change_reason
    }])
    
    audit_record.write.mode("append").saveAsTable("audit.table_changes")
```

## Best Practices

### 1. Always Set Audit Columns
- Never allow null values in required audit columns
- Use DEFAULT values in table definitions where possible
- Validate audit columns before writing to tables

### 2. Use Consistent Formats
- Timestamps: Always use TIMESTAMP type, never STRING or BIGINT
- User identity: Use email or service principal name
- Load IDs: Use consistent format like `load_YYYYMMDD_HHMMSS` or UUID

### 3. Maintain Audit Trail
- Never delete audit columns
- Preserve audit history when archiving data
- Enable Change Data Feed on all tables

### 4. Document Lineage
- Always populate source_system, source_table, source_record_id
- Use pipeline_name and pipeline_run_id for traceability
- Store load_id for batch reconstruction

### 5. Validate Regularly
- Run audit column validation as part of CI/CD
- Monitor for missing or invalid audit data
- Alert on audit column violations

## Quick Reference

### Required Audit Columns Checklist
- [ ] `created_at` - Timestamp of record creation
- [ ] `updated_at` - Timestamp of last update
- [ ] `created_by` - User who created the record
- [ ] `updated_by` - User who last updated the record
- [ ] `load_id` - Batch/job identifier
- [ ] `pipeline_name` - Processing pipeline name
- [ ] `source_system` - Origin system identifier

### Common Patterns
- **New records**: Set created_at = updated_at, created_by = updated_by
- **Updates**: Increment record_version, update updated_at and updated_by
- **Deletes**: Add deleted_at timestamp, keep all audit history
- **Merges**: Update audit columns only for changed records

### Validation Commands
```bash
# Validate schema
python scripts/validate_audit_columns.py --table silver.customers

# Check for missing audit columns
databricks sql execute --query "SELECT * FROM audit.column_compliance"

# Generate audit report
python scripts/generate_audit_report.py --catalog main --schema silver
```
