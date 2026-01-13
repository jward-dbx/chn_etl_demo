---
name: metadata-driven-framework
description: Patterns and best practices for building metadata-driven ETL frameworks in Databricks. Enables configuration-driven pipelines, dynamic processing, and centralized control through metadata tables.
---

# Metadata-Driven Framework Skill

This skill provides patterns for building metadata-driven ETL frameworks where pipeline behavior, transformations, and data quality rules are controlled through configuration metadata rather than hardcoded logic.

## Core Concepts

### What is a Metadata-Driven Framework?

A metadata-driven framework separates **configuration** from **execution logic**:

- **Metadata Tables**: Store configuration, rules, mappings, and parameters
- **Generic Engines**: Read metadata and execute accordingly
- **Dynamic Behavior**: Change pipeline behavior without code changes
- **Centralized Control**: Single source of truth for all pipelines

### Benefits

✅ **Consistency**: All pipelines follow same patterns  
✅ **Maintainability**: Configuration changes don't require code deploys  
✅ **Scalability**: Add new pipelines by adding metadata  
✅ **Auditability**: All changes tracked in metadata tables  
✅ **Reusability**: Generic engines work across all pipelines  

## Metadata Table Schemas

### 1. Pipeline Registry

Centralized registry of all ETL pipelines:

```sql
CREATE TABLE IF NOT EXISTS metadata.pipeline_registry (
  -- Pipeline Identity
  pipeline_id STRING NOT NULL,
  pipeline_name STRING NOT NULL,
  pipeline_description STRING,
  pipeline_type STRING NOT NULL,      -- batch, streaming, dlt, sql, notebook
  
  -- Source Configuration
  source_type STRING NOT NULL,        -- table, file, api, kafka, event_hub
  source_catalog STRING,
  source_schema STRING,
  source_table STRING,
  source_path STRING,
  source_format STRING,              -- delta, parquet, json, csv, avro
  
  -- Target Configuration
  target_catalog STRING NOT NULL,
  target_schema STRING NOT NULL,
  target_table STRING NOT NULL,
  target_path STRING,
  target_format STRING DEFAULT 'delta',
  
  -- Processing Configuration
  processing_mode STRING NOT NULL,    -- append, overwrite, merge, scd2
  partition_columns ARRAY<STRING>,
  z_order_columns ARRAY<STRING>,
  incremental_column STRING,         -- Column for incremental loads
  watermark_column STRING,           -- For streaming
  
  -- Dependencies
  depends_on ARRAY<STRING>,          -- Pipeline IDs this depends on
  dependency_type STRING,            -- sequential, parallel
  
  -- Schedule
  schedule_type STRING,              -- cron, event, manual, continuous
  schedule_expression STRING,        -- Cron expression if applicable
  
  -- Quality & Validation
  enable_data_quality BOOLEAN DEFAULT true,
  enable_schema_validation BOOLEAN DEFAULT true,
  quality_rules_id STRING,           -- FK to quality_rules table
  
  -- Ownership & Governance
  owner STRING NOT NULL,
  domain STRING NOT NULL,
  cost_center STRING,
  data_classification STRING,
  
  -- Status
  status STRING NOT NULL DEFAULT 'active',  -- active, inactive, deprecated
  enabled BOOLEAN NOT NULL DEFAULT true,
  
  -- Audit
  created_by STRING NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  updated_by STRING NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  
  CONSTRAINT pk_pipeline_registry PRIMARY KEY (pipeline_id)
)
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true'
);
```

### 2. Transformation Rules

Store transformation logic as metadata:

```sql
CREATE TABLE IF NOT EXISTS metadata.transformation_rules (
  -- Rule Identity
  rule_id STRING NOT NULL,
  pipeline_id STRING NOT NULL,       -- FK to pipeline_registry
  rule_sequence INT NOT NULL,        -- Execution order
  rule_name STRING NOT NULL,
  rule_description STRING,
  
  -- Transformation Type
  transformation_type STRING NOT NULL, -- select, filter, aggregate, join, pivot, custom
  
  -- Column Mappings
  source_columns ARRAY<STRING>,      -- Input columns
  target_column STRING,              -- Output column
  column_expression STRING,          -- SQL expression or transformation logic
  column_type STRING,                -- Data type for target column
  
  -- Transformation Logic
  sql_expression STRING,             -- SQL expression
  python_function STRING,            -- Python function name (if custom)
  transformation_params MAP<STRING, STRING>, -- Additional parameters
  
  -- Conditions
  apply_when STRING,                 -- SQL condition for conditional transformation
  
  -- Validation
  validation_rules ARRAY<STRING>,    -- Validation rules for this column
  nullable BOOLEAN DEFAULT true,
  
  -- Status
  enabled BOOLEAN NOT NULL DEFAULT true,
  
  -- Audit
  created_by STRING NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  updated_by STRING NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  
  CONSTRAINT pk_transformation_rules PRIMARY KEY (rule_id),
  CONSTRAINT fk_transformation_pipeline FOREIGN KEY (pipeline_id) 
    REFERENCES metadata.pipeline_registry(pipeline_id)
)
USING DELTA
PARTITIONED BY (pipeline_id);
```

### 3. Data Quality Rules

Store quality expectations as metadata:

```sql
CREATE TABLE IF NOT EXISTS metadata.data_quality_rules (
  -- Rule Identity
  quality_rule_id STRING NOT NULL,
  pipeline_id STRING NOT NULL,
  rule_name STRING NOT NULL,
  rule_description STRING,
  
  -- Rule Type
  rule_type STRING NOT NULL,         -- completeness, validity, uniqueness, consistency, timeliness
  rule_category STRING,              -- error, warning, info
  
  -- Rule Configuration
  table_name STRING,                 -- Table to validate
  column_name STRING,                -- Column to validate (NULL for table-level)
  validation_expression STRING NOT NULL, -- SQL expression that should be true
  
  -- Thresholds
  threshold_type STRING,             -- percentage, absolute
  threshold_value DECIMAL(10,2),     -- Max acceptable failures
  
  -- Action on Failure
  failure_action STRING NOT NULL,    -- fail, warn, quarantine, skip
  quarantine_table STRING,           -- Table for quarantined records
  
  -- Notification
  notify_on_failure BOOLEAN DEFAULT false,
  notification_recipients ARRAY<STRING>,
  
  -- Status
  enabled BOOLEAN NOT NULL DEFAULT true,
  severity STRING NOT NULL DEFAULT 'medium', -- critical, high, medium, low
  
  -- Audit
  created_by STRING NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  updated_by STRING NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  
  CONSTRAINT pk_data_quality_rules PRIMARY KEY (quality_rule_id)
)
USING DELTA
PARTITIONED BY (pipeline_id);
```

### 4. Pipeline Execution Log

Track all pipeline executions:

```sql
CREATE TABLE IF NOT EXISTS metadata.pipeline_execution_log (
  -- Execution Identity
  execution_id STRING NOT NULL,
  pipeline_id STRING NOT NULL,
  pipeline_run_id STRING,            -- Databricks job run ID
  
  -- Execution Details
  execution_start_time TIMESTAMP NOT NULL,
  execution_end_time TIMESTAMP,
  execution_duration_seconds INT,
  execution_status STRING NOT NULL,  -- running, succeeded, failed, cancelled
  
  -- Data Metrics
  records_read BIGINT,
  records_written BIGINT,
  records_updated BIGINT,
  records_deleted BIGINT,
  records_failed BIGINT,
  
  -- Quality Metrics
  quality_checks_passed INT DEFAULT 0,
  quality_checks_failed INT DEFAULT 0,
  quality_score DECIMAL(5,2),
  
  -- Error Details
  error_message STRING,
  error_stack_trace STRING,
  failed_stage STRING,
  
  -- Resource Usage
  compute_time_seconds INT,
  dbu_consumed DECIMAL(10,2),
  
  -- Execution Context
  executed_by STRING NOT NULL,
  execution_trigger STRING,          -- scheduled, manual, event, dependency
  configuration_snapshot MAP<STRING, STRING>, -- Config at execution time
  
  -- Audit
  load_id STRING NOT NULL,
  
  -- Partition
  execution_date DATE GENERATED ALWAYS AS (CAST(execution_start_time AS DATE)),
  
  CONSTRAINT pk_pipeline_execution_log PRIMARY KEY (execution_id)
)
USING DELTA
PARTITIONED BY (execution_date, pipeline_id);
```

### 5. Schema Registry

Centralized schema definitions:

```sql
CREATE TABLE IF NOT EXISTS metadata.schema_registry (
  -- Schema Identity
  schema_id STRING NOT NULL,
  schema_name STRING NOT NULL,
  schema_version STRING NOT NULL,
  
  -- Schema Definition
  catalog_name STRING NOT NULL,
  schema_name_logical STRING NOT NULL,
  table_name STRING NOT NULL,
  
  -- Column Definitions
  column_definitions ARRAY<STRUCT<
    column_name: STRING,
    column_type: STRING,
    column_description: STRING,
    is_nullable: BOOLEAN,
    is_primary_key: BOOLEAN,
    is_partition_key: BOOLEAN,
    default_value: STRING,
    validation_rules: ARRAY<STRING>
  >>,
  
  -- Schema Metadata
  schema_description STRING,
  schema_owner STRING,
  schema_classification STRING,
  
  -- Evolution
  parent_schema_id STRING,           -- Previous version
  breaking_change BOOLEAN DEFAULT false,
  change_description STRING,
  
  -- Status
  status STRING NOT NULL DEFAULT 'active', -- draft, active, deprecated
  effective_date DATE,
  deprecation_date DATE,
  
  -- Audit
  created_by STRING NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  updated_by STRING NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  
  CONSTRAINT pk_schema_registry PRIMARY KEY (schema_id),
  CONSTRAINT uk_schema_version UNIQUE (schema_name, schema_version)
)
USING DELTA;
```

## Implementation Patterns

### Pattern 1: Generic Pipeline Engine

```python
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from delta.tables import DeltaTable
import uuid
from datetime import datetime

class MetadataDrivenPipeline:
    """Generic pipeline engine that executes based on metadata configuration."""
    
    def __init__(self, spark, pipeline_id):
        self.spark = spark
        self.pipeline_id = pipeline_id
        self.execution_id = str(uuid.uuid4())
        self.load_id = f"load_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Load pipeline configuration
        self.config = self._load_pipeline_config()
        self.transformations = self._load_transformations()
        self.quality_rules = self._load_quality_rules()
    
    def _load_pipeline_config(self):
        """Load pipeline configuration from metadata."""
        config_df = self.spark.table("metadata.pipeline_registry") \
            .filter(f"pipeline_id = '{self.pipeline_id}' AND enabled = true") \
            .first()
        
        if not config_df:
            raise ValueError(f"Pipeline {self.pipeline_id} not found or disabled")
        
        return config_df.asDict()
    
    def _load_transformations(self):
        """Load transformation rules ordered by sequence."""
        return self.spark.table("metadata.transformation_rules") \
            .filter(f"pipeline_id = '{self.pipeline_id}' AND enabled = true") \
            .orderBy("rule_sequence") \
            .collect()
    
    def _load_quality_rules(self):
        """Load data quality rules."""
        if not self.config.get("enable_data_quality"):
            return []
        
        return self.spark.table("metadata.data_quality_rules") \
            .filter(f"pipeline_id = '{self.pipeline_id}' AND enabled = true") \
            .collect()
    
    def extract(self) -> DataFrame:
        """Extract data from source based on metadata."""
        source_type = self.config["source_type"]
        
        if source_type == "table":
            source_table = f"{self.config['source_catalog']}.{self.config['source_schema']}.{self.config['source_table']}"
            df = self.spark.table(source_table)
            
            # Apply incremental load if configured
            incremental_col = self.config.get("incremental_column")
            if incremental_col:
                last_value = self._get_last_watermark()
                if last_value:
                    df = df.filter(F.col(incremental_col) > last_value)
        
        elif source_type == "file":
            df = self.spark.read.format(self.config["source_format"]) \
                .load(self.config["source_path"])
        
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
        
        self.records_read = df.count()
        print(f"📥 Extracted {self.records_read:,} records from {source_type}")
        
        return df
    
    def transform(self, df: DataFrame) -> DataFrame:
        """Apply transformations based on metadata rules."""
        print(f"🔄 Applying {len(self.transformations)} transformations...")
        
        for rule in self.transformations:
            rule_dict = rule.asDict()
            
            transformation_type = rule_dict["transformation_type"]
            
            if transformation_type == "select":
                # Column selection/renaming
                expr = rule_dict["column_expression"]
                target_col = rule_dict["target_column"]
                df = df.withColumn(target_col, F.expr(expr))
            
            elif transformation_type == "filter":
                # Row filtering
                filter_expr = rule_dict["sql_expression"]
                df = df.filter(filter_expr)
            
            elif transformation_type == "aggregate":
                # Aggregation
                group_cols = rule_dict["source_columns"]
                agg_expr = rule_dict["column_expression"]
                target_col = rule_dict["target_column"]
                df = df.groupBy(*group_cols).agg(F.expr(agg_expr).alias(target_col))
            
            elif transformation_type == "join":
                # Join with another table
                join_params = rule_dict["transformation_params"]
                right_table = join_params["right_table"]
                join_condition = join_params["join_condition"]
                join_type = join_params.get("join_type", "left")
                
                right_df = self.spark.table(right_table)
                df = df.join(right_df, F.expr(join_condition), join_type)
            
            print(f"  ✓ Applied: {rule_dict['rule_name']}")
        
        # Add audit columns
        df = self._add_audit_columns(df)
        
        return df
    
    def _add_audit_columns(self, df: DataFrame) -> DataFrame:
        """Add standard audit columns."""
        return df.withColumn("load_id", F.lit(self.load_id)) \
                 .withColumn("pipeline_name", F.lit(self.config["pipeline_name"])) \
                 .withColumn("pipeline_run_id", F.lit(self.execution_id)) \
                 .withColumn("source_system", F.lit(self.config["source_type"])) \
                 .withColumn("created_at", F.current_timestamp()) \
                 .withColumn("updated_at", F.current_timestamp())
    
    def validate(self, df: DataFrame) -> tuple[DataFrame, bool]:
        """
        Apply data quality rules.
        Returns: (validated_df, all_checks_passed)
        """
        if not self.quality_rules:
            return df, True
        
        print(f"✅ Running {len(self.quality_rules)} quality checks...")
        
        all_passed = True
        
        for rule in self.quality_rules:
            rule_dict = rule.asDict()
            rule_name = rule_dict["rule_name"]
            validation_expr = rule_dict["validation_expression"]
            failure_action = rule_dict["failure_action"]
            
            # Count violations
            violations = df.filter(~F.expr(validation_expr)).count()
            
            if violations > 0:
                print(f"  ⚠️  {rule_name}: {violations} violations")
                
                if failure_action == "fail":
                    all_passed = False
                    raise ValueError(f"Quality check failed: {rule_name}")
                
                elif failure_action == "quarantine":
                    # Move bad records to quarantine
                    bad_records = df.filter(~F.expr(validation_expr))
                    quarantine_table = rule_dict["quarantine_table"]
                    bad_records.write.mode("append").saveAsTable(quarantine_table)
                    
                    # Keep only good records
                    df = df.filter(F.expr(validation_expr))
                
                elif failure_action == "warn":
                    all_passed = False
                    # Continue processing
            else:
                print(f"  ✓ {rule_name}: PASSED")
        
        return df, all_passed
    
    def load(self, df: DataFrame):
        """Load data to target based on metadata."""
        target_table = f"{self.config['target_catalog']}.{self.config['target_schema']}.{self.config['target_table']}"
        processing_mode = self.config["processing_mode"]
        
        print(f"💾 Loading to {target_table} (mode: {processing_mode})...")
        
        if processing_mode == "overwrite":
            df.write.format("delta").mode("overwrite").saveAsTable(target_table)
        
        elif processing_mode == "append":
            df.write.format("delta").mode("append").saveAsTable(target_table)
        
        elif processing_mode == "merge":
            # Merge logic
            if not self.spark.catalog.tableExists(target_table):
                df.write.format("delta").saveAsTable(target_table)
            else:
                self._perform_merge(df, target_table)
        
        self.records_written = df.count()
        print(f"✓ Loaded {self.records_written:,} records")
    
    def _perform_merge(self, source_df: DataFrame, target_table: str):
        """Perform merge operation."""
        # This is simplified - would need merge keys from metadata
        target = DeltaTable.forName(self.spark, target_table)
        
        target.alias("target").merge(
            source_df.alias("source"),
            "target.id = source.id"  # Would come from metadata
        ).whenMatchedUpdateAll() \
         .whenNotMatchedInsertAll() \
         .execute()
    
    def _log_execution(self, status: str, error_message: str = None):
        """Log pipeline execution to metadata."""
        log_record = {
            "execution_id": self.execution_id,
            "pipeline_id": self.pipeline_id,
            "execution_start_time": self.start_time,
            "execution_end_time": datetime.now(),
            "execution_status": status,
            "records_read": self.records_read,
            "records_written": self.records_written,
            "executed_by": self.spark.sparkContext.sparkUser(),
            "load_id": self.load_id,
            "error_message": error_message
        }
        
        self.spark.createDataFrame([log_record]).write \
            .mode("append").saveAsTable("metadata.pipeline_execution_log")
    
    def execute(self):
        """Execute the full pipeline."""
        self.start_time = datetime.now()
        
        try:
            print(f"\n🚀 Starting pipeline: {self.config['pipeline_name']}")
            print(f"   Execution ID: {self.execution_id}")
            
            # Extract
            df = self.extract()
            
            # Transform
            df = self.transform(df)
            
            # Validate
            df, quality_passed = self.validate(df)
            
            # Load
            self.load(df)
            
            # Log success
            self._log_execution("succeeded")
            
            print(f"✅ Pipeline completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Pipeline failed: {str(e)}")
            self._log_execution("failed", str(e))
            raise

# Usage
pipeline = MetadataDrivenPipeline(spark, "customer_silver_etl")
pipeline.execute()
```

### Pattern 2: Configuration-Based Pipeline Registration

```python
def register_pipeline(config: dict):
    """
    Register a new pipeline in the metadata registry.
    
    Args:
        config: Pipeline configuration dictionary
    """
    # Validate required fields
    required_fields = [
        "pipeline_id", "pipeline_name", "pipeline_type",
        "source_type", "target_catalog", "target_schema", "target_table",
        "processing_mode", "owner", "domain"
    ]
    
    missing_fields = [f for f in required_fields if f not in config]
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")
    
    # Add audit fields
    config["created_by"] = spark.sparkContext.sparkUser()
    config["updated_by"] = spark.sparkContext.sparkUser()
    config["status"] = config.get("status", "active")
    config["enabled"] = config.get("enabled", True)
    
    # Insert into registry
    df = spark.createDataFrame([config])
    df.write.mode("append").saveAsTable("metadata.pipeline_registry")
    
    print(f"✅ Registered pipeline: {config['pipeline_id']}")

# Example registration
register_pipeline({
    "pipeline_id": "customer_silver_etl",
    "pipeline_name": "Customer Silver Layer ETL",
    "pipeline_description": "Transform bronze customer data to silver layer",
    "pipeline_type": "batch",
    "source_type": "table",
    "source_catalog": "main",
    "source_schema": "bronze",
    "source_table": "customers",
    "target_catalog": "main",
    "target_schema": "silver",
    "target_table": "customers",
    "processing_mode": "merge",
    "partition_columns": ["customer_state"],
    "z_order_columns": ["customer_id", "customer_email"],
    "incremental_column": "updated_at",
    "schedule_type": "cron",
    "schedule_expression": "0 2 * * *",
    "enable_data_quality": True,
    "enable_schema_validation": True,
    "owner": "data-eng@company.com",
    "domain": "customer",
    "cost_center": "CC-1234",
    "data_classification": "pii"
})
```

## Best Practices

### 1. Version Control for Metadata
- Track all metadata changes in source control
- Use migration scripts for metadata updates
- Maintain schema versions

### 2. Validation and Testing
- Validate metadata before pipeline execution
- Test generic engines with various configurations
- Unit test transformation rules

### 3. Error Handling
- Graceful degradation for missing metadata
- Detailed error messages referencing metadata
- Automatic retries for transient failures

### 4. Performance
- Cache frequently accessed metadata
- Index metadata tables appropriately
- Partition large metadata tables

### 5. Governance
- Audit all metadata changes
- Require approvals for production changes
- Document metadata schemas thoroughly

## Quick Reference

### Register New Pipeline
```python
register_pipeline({...})
```

### Execute Pipeline
```python
pipeline = MetadataDrivenPipeline(spark, "pipeline_id")
pipeline.execute()
```

### Query Pipeline Status
```sql
SELECT * FROM metadata.pipeline_execution_log
WHERE pipeline_id = 'customer_silver_etl'
ORDER BY execution_start_time DESC
LIMIT 10;
```

### Update Pipeline Configuration
```sql
UPDATE metadata.pipeline_registry
SET schedule_expression = '0 1 * * *'
WHERE pipeline_id = 'customer_silver_etl';
```
