---
name: tagging-standards
description: Enforces standardized tagging taxonomy for all Databricks artifacts including tables, volumes, models, jobs, and pipelines. Provides tag registry, validation, and governance frameworks for metadata management.
---

# Tagging Standards Skill

This skill enforces a comprehensive tagging taxonomy for all Databricks artifacts, enabling effective governance, cost management, data discovery, and compliance tracking.

## Core Tagging Taxonomy

### Required Tags (ALL Artifacts)

Every artifact (table, job, pipeline, model, volume) MUST have these tags:

```python
REQUIRED_TAGS = {
    # Organizational Tags
    "domain": str,              # Business domain: customer, product, finance, marketing, operations
    "owner": str,               # Team/individual owner email
    "cost_center": str,         # Cost center or department code
    
    # Technical Tags
    "environment": str,         # dev, staging, prod
    "layer": str,               # bronze, silver, gold, raw, curated
    "data_classification": str, # public, internal, confidential, restricted, pii
    
    # Lifecycle Tags
    "created_date": str,        # ISO 8601 format: YYYY-MM-DD
    "last_modified": str,       # ISO 8601 format: YYYY-MM-DD
    "status": str,              # active, deprecated, archived, in_development
}
```

### Extended Tags (Recommended)

```python
RECOMMENDED_TAGS = {
    # Data Governance
    "data_steward": str,        # Data steward email
    "data_quality_tier": str,   # gold, silver, bronze (different from layer)
    "retention_policy": str,    # 30d, 90d, 1y, 7y, permanent
    "backup_policy": str,       # daily, weekly, monthly, none
    
    # Compliance & Security
    "compliance_framework": str, # gdpr, hipaa, sox, pci, ccpa
    "encryption_required": str,  # true, false
    "access_level": str,         # restricted, team, company, public
    "pii_fields": str,          # Comma-separated list of PII columns
    
    # Business Context
    "project": str,              # Project or initiative name
    "use_case": str,             # analytics, ml, reporting, operational
    "criticality": str,          # critical, high, medium, low
    "sla_tier": str,             # p0, p1, p2, p3
    
    # Technical Metadata
    "source_system": str,        # Origin system
    "update_frequency": str,     # real_time, hourly, daily, weekly, monthly
    "data_format": str,          # delta, parquet, csv, json, avro
    "schema_version": str,       # v1.0.0, v2.1.3
    
    # Cost Management
    "budget_code": str,          # Budget allocation code
    "charge_back": str,          # Department to charge
    "cost_optimization": str,    # enabled, disabled
}
```

### Specialized Tags by Artifact Type

#### Tables/Views
```python
TABLE_SPECIFIC_TAGS = {
    "table_type": str,           # fact, dimension, bridge, accumulating_snapshot
    "partition_strategy": str,   # date, region, category
    "z_order_columns": str,      # Comma-separated
    "row_count_est": str,        # Estimated row count tier: <1M, 1M-10M, 10M-100M, >100M
    "update_pattern": str,       # append, upsert, overwrite, scd2
}
```

#### Jobs/Pipelines
```python
JOB_SPECIFIC_TAGS = {
    "job_type": str,             # etl, ml_training, reporting, data_quality
    "schedule": str,             # cron expression or frequency
    "max_runtime": str,          # Expected max runtime: 5m, 1h, 4h
    "dependencies": str,         # Comma-separated list of dependent jobs
    "notification_group": str,   # Email group for alerts
}
```

#### ML Models
```python
MODEL_SPECIFIC_TAGS = {
    "model_type": str,           # classification, regression, clustering, forecasting
    "framework": str,            # sklearn, tensorflow, pytorch, xgboost
    "training_data": str,        # Source table for training
    "model_version": str,        # v1.0.0
    "performance_metric": str,   # accuracy:0.95, rmse:0.23
}
```

## Tag Registry (Metadata Store)

### Create Tag Registry Table

```sql
CREATE TABLE IF NOT EXISTS metadata.tag_registry (
  -- Tag Definition
  tag_key STRING NOT NULL,
  tag_category STRING NOT NULL,        -- organizational, technical, governance, cost
  tag_description STRING NOT NULL,
  
  -- Tag Constraints
  is_required BOOLEAN NOT NULL DEFAULT false,
  allowed_values ARRAY<STRING>,        -- Controlled vocabulary (NULL = freeform)
  validation_regex STRING,             -- Regex pattern for validation
  
  -- Applicability
  applies_to ARRAY<STRING> NOT NULL,   -- table, job, pipeline, model, volume, cluster
  environment_scope ARRAY<STRING>,     -- dev, staging, prod, all
  
  -- Ownership
  tag_owner STRING NOT NULL,
  created_by STRING NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  
  -- Status
  status STRING NOT NULL DEFAULT 'active',  -- active, deprecated, retired
  deprecation_date TIMESTAMP,
  replacement_tag STRING,
  
  -- Documentation
  usage_examples STRING,
  related_tags ARRAY<STRING>,
  
  CONSTRAINT pk_tag_registry PRIMARY KEY (tag_key)
)
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true'
);

-- Insert standard tags
INSERT INTO metadata.tag_registry VALUES
  -- Organizational Tags
  ('domain', 'organizational', 'Business domain for the artifact', true, 
   ARRAY('customer', 'product', 'finance', 'marketing', 'operations', 'engineering'),
   NULL, ARRAY('table', 'job', 'pipeline', 'model', 'volume'), ARRAY('all'),
   'data-governance@company.com', current_user(), current_timestamp(), current_timestamp(),
   'active', NULL, NULL, 'domain=customer for customer-related tables', ARRAY('owner', 'cost_center')),
   
  ('owner', 'organizational', 'Email of the owning team or individual', true,
   NULL, '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
   ARRAY('table', 'job', 'pipeline', 'model', 'volume'), ARRAY('all'),
   'data-governance@company.com', current_user(), current_timestamp(), current_timestamp(),
   'active', NULL, NULL, 'owner=data-eng@company.com', ARRAY('data_steward', 'domain')),
   
  ('environment', 'technical', 'Deployment environment', true,
   ARRAY('dev', 'staging', 'prod'), NULL,
   ARRAY('table', 'job', 'pipeline', 'model', 'volume', 'cluster'), ARRAY('all'),
   'platform-eng@company.com', current_user(), current_timestamp(), current_timestamp(),
   'active', NULL, NULL, 'environment=prod', ARRAY('layer', 'status')),
   
  ('layer', 'technical', 'Data layer in medallion architecture', true,
   ARRAY('bronze', 'silver', 'gold', 'raw', 'curated'), NULL,
   ARRAY('table'), ARRAY('all'),
   'data-architecture@company.com', current_user(), current_timestamp(), current_timestamp(),
   'active', NULL, NULL, 'layer=silver', ARRAY('environment', 'domain')),
   
  ('data_classification', 'governance', 'Data sensitivity classification', true,
   ARRAY('public', 'internal', 'confidential', 'restricted', 'pii'), NULL,
   ARRAY('table', 'volume'), ARRAY('all'),
   'security@company.com', current_user(), current_timestamp(), current_timestamp(),
   'active', NULL, NULL, 'data_classification=pii for tables with personal data', ARRAY('pii_fields', 'encryption_required'));
```

### Tag Compliance Tracking Table

```sql
CREATE TABLE IF NOT EXISTS metadata.tag_compliance (
  -- Artifact Information
  artifact_type STRING NOT NULL,       -- table, job, pipeline, model, volume
  artifact_catalog STRING,
  artifact_schema STRING,
  artifact_name STRING NOT NULL,
  artifact_id STRING,
  
  -- Compliance Status
  compliance_status STRING NOT NULL,   -- compliant, non_compliant, partially_compliant
  missing_required_tags ARRAY<STRING>,
  invalid_tag_values MAP<STRING, STRING>,
  
  -- Metrics
  total_tags_count INT,
  required_tags_count INT,
  recommended_tags_count INT,
  compliance_score DECIMAL(5,2),      -- Percentage (0-100)
  
  -- Temporal
  checked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  last_modified_at TIMESTAMP,
  
  -- Ownership
  owner STRING,
  notified_at TIMESTAMP,
  
  -- Partition
  check_date DATE GENERATED ALWAYS AS (CAST(checked_at AS DATE))
)
USING DELTA
PARTITIONED BY (check_date, artifact_type, compliance_status)
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true'
);
```

## Implementation Patterns

### Pattern 1: Apply Tags to Tables (SQL)

```sql
-- Apply required tags to a table
ALTER TABLE ${catalog}.${schema}.${table_name} SET TAGS (
  'domain' = 'customer',
  'owner' = 'data-eng@company.com',
  'cost_center' = 'CC-1234',
  'environment' = 'prod',
  'layer' = 'silver',
  'data_classification' = 'pii',
  'created_date' = '2024-01-15',
  'last_modified' = '2024-01-15',
  'status' = 'active'
);

-- Apply column-level tags for PII
ALTER TABLE ${catalog}.${schema}.${table_name} 
ALTER COLUMN customer_email SET TAGS (
  'pii' = 'true',
  'pii_type' = 'email',
  'encryption_required' = 'true'
);

ALTER TABLE ${catalog}.${schema}.${table_name}
ALTER COLUMN customer_phone SET TAGS (
  'pii' = 'true',
  'pii_type' = 'phone',
  'encryption_required' = 'true'
);
```

### Pattern 2: Apply Tags Programmatically (Python)

```python
from databricks.sdk import WorkspaceClient
from datetime import datetime

def apply_standard_tags(catalog, schema, table_name, **additional_tags):
    """
    Apply standard required tags plus any additional tags to a table.
    
    Args:
        catalog: Catalog name
        schema: Schema name
        table_name: Table name
        **additional_tags: Additional tags as keyword arguments
        
    Example:
        apply_standard_tags(
            catalog="main",
            schema="silver",
            table_name="customers",
            domain="customer",
            owner="data-eng@company.com",
            cost_center="CC-1234",
            compliance_framework="gdpr",
            pii_fields="email,phone,ssn"
        )
    """
    w = WorkspaceClient()
    
    # Required tags with defaults
    tags = {
        "created_date": datetime.now().strftime("%Y-%m-%d"),
        "last_modified": datetime.now().strftime("%Y-%m-%d"),
        "status": "active",
    }
    
    # Merge with provided tags
    tags.update(additional_tags)
    
    # Validate required tags
    required_tags = ["domain", "owner", "cost_center", "environment", 
                    "layer", "data_classification"]
    missing_tags = [tag for tag in required_tags if tag not in tags]
    
    if missing_tags:
        raise ValueError(f"Missing required tags: {missing_tags}")
    
    # Apply tags
    full_table_name = f"{catalog}.{schema}.{table_name}"
    
    # Build ALTER TABLE statement
    tag_pairs = [f"'{k}' = '{v}'" for k, v in tags.items()]
    sql = f"ALTER TABLE {full_table_name} SET TAGS ({', '.join(tag_pairs)})"
    
    spark.sql(sql)
    
    print(f"✅ Applied {len(tags)} tags to {full_table_name}")
    
    # Log to compliance table
    log_tagging_action(full_table_name, tags)
    
    return tags

def apply_tags_to_job(job_id, tags):
    """
    Apply tags to a Databricks job.
    
    Args:
        job_id: Databricks job ID
        tags: Dictionary of tag key-value pairs
    """
    w = WorkspaceClient()
    
    # Get current job configuration
    job = w.jobs.get(job_id)
    
    # Update tags
    existing_tags = job.settings.tags or {}
    existing_tags.update(tags)
    
    # Update job
    w.jobs.update(
        job_id=job_id,
        new_settings={
            "tags": existing_tags
        }
    )
    
    print(f"✅ Applied tags to job {job_id}")
```

### Pattern 3: Bulk Tag Application

```python
def bulk_apply_tags_to_schema(catalog, schema, default_tags):
    """
    Apply default tags to all tables in a schema.
    
    Args:
        catalog: Catalog name
        schema: Schema name
        default_tags: Dictionary of tags to apply to all tables
    """
    # Get all tables in schema
    tables = spark.sql(f"SHOW TABLES IN {catalog}.{schema}").collect()
    
    results = []
    for table_row in tables:
        table_name = table_row.tableName
        
        try:
            # Get existing tags
            existing_tags = get_table_tags(catalog, schema, table_name)
            
            # Merge with defaults (existing tags take precedence)
            merged_tags = {**default_tags, **existing_tags}
            
            # Apply tags
            apply_standard_tags(catalog, schema, table_name, **merged_tags)
            
            results.append({
                "table": f"{catalog}.{schema}.{table_name}",
                "status": "success",
                "tags_applied": len(merged_tags)
            })
        except Exception as e:
            results.append({
                "table": f"{catalog}.{schema}.{table_name}",
                "status": "failed",
                "error": str(e)
            })
    
    # Create summary
    success_count = len([r for r in results if r["status"] == "success"])
    failed_count = len([r for r in results if r["status"] == "failed"])
    
    print(f"\n📊 Bulk Tagging Summary:")
    print(f"   Total tables: {len(results)}")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    
    return results

# Usage
default_tags = {
    "domain": "customer",
    "environment": "prod",
    "layer": "silver",
    "owner": "data-eng@company.com",
    "cost_center": "CC-1234",
    "data_classification": "internal",
    "created_date": "2024-01-15",
    "status": "active"
}

results = bulk_apply_tags_to_schema("main", "silver", default_tags)
```

### Pattern 4: Tag Validation

```python
def validate_table_tags(catalog, schema, table_name):
    """
    Validate that a table has all required tags with valid values.
    
    Returns:
        Tuple of (is_compliant, issues)
    """
    issues = []
    
    # Get table tags
    tags = get_table_tags(catalog, schema, table_name)
    
    # Load tag registry
    tag_registry = spark.table("metadata.tag_registry") \
        .filter("status = 'active' AND 'table' IN applies_to") \
        .collect()
    
    # Check required tags
    for tag_def in tag_registry:
        tag_key = tag_def.tag_key
        is_required = tag_def.is_required
        allowed_values = tag_def.allowed_values
        validation_regex = tag_def.validation_regex
        
        # Check if required tag exists
        if is_required and tag_key not in tags:
            issues.append(f"Missing required tag: {tag_key}")
            continue
        
        if tag_key in tags:
            tag_value = tags[tag_key]
            
            # Validate against allowed values
            if allowed_values and tag_value not in allowed_values:
                issues.append(
                    f"Invalid value for tag '{tag_key}': '{tag_value}'. "
                    f"Allowed values: {allowed_values}"
                )
            
            # Validate against regex
            if validation_regex:
                import re
                if not re.match(validation_regex, tag_value):
                    issues.append(
                        f"Tag '{tag_key}' value '{tag_value}' does not match "
                        f"required pattern: {validation_regex}"
                    )
    
    is_compliant = len(issues) == 0
    
    # Calculate compliance score
    required_tags_in_registry = [t for t in tag_registry if t.is_required]
    tags_present = len([t for t in required_tags_in_registry if t.tag_key in tags])
    compliance_score = (tags_present / len(required_tags_in_registry) * 100) if required_tags_in_registry else 100
    
    # Log to compliance table
    log_compliance_check(
        artifact_type="table",
        artifact_name=f"{catalog}.{schema}.{table_name}",
        compliance_status="compliant" if is_compliant else "non_compliant",
        missing_tags=[i.split(": ")[1] for i in issues if i.startswith("Missing")],
        compliance_score=compliance_score
    )
    
    return is_compliant, issues, compliance_score

# Usage
is_compliant, issues, score = validate_table_tags("main", "silver", "customers")

if not is_compliant:
    print(f"❌ Tag validation failed (Score: {score}%):")
    for issue in issues:
        print(f"   - {issue}")
else:
    print(f"✅ All tags are compliant (Score: {score}%)")
```

## Tag Governance Dashboard

### Compliance Summary Query

```sql
-- Generate compliance summary across all artifacts
CREATE OR REPLACE VIEW metadata.v_tagging_compliance_summary AS
SELECT 
  artifact_type,
  compliance_status,
  COUNT(*) AS artifact_count,
  AVG(compliance_score) AS avg_compliance_score,
  SUM(CASE WHEN compliance_score = 100 THEN 1 ELSE 0 END) AS fully_compliant_count,
  SUM(CASE WHEN compliance_score < 50 THEN 1 ELSE 0 END) AS critically_non_compliant_count,
  MAX(checked_at) AS last_check_time
FROM metadata.tag_compliance
WHERE check_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY artifact_type, compliance_status
ORDER BY artifact_type, compliance_status;

-- Find artifacts missing required tags
CREATE OR REPLACE VIEW metadata.v_missing_required_tags AS
SELECT 
  artifact_type,
  artifact_name,
  owner,
  missing_required_tags,
  DATEDIFF(CURRENT_DATE(), CAST(checked_at AS DATE)) AS days_non_compliant,
  checked_at
FROM metadata.tag_compliance
WHERE compliance_status = 'non_compliant'
  AND SIZE(missing_required_tags) > 0
  AND check_date >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY days_non_compliant DESC, artifact_type;

-- Cost center tagging for chargeback
CREATE OR REPLACE VIEW metadata.v_cost_center_tagging AS
SELECT 
  cost_center,
  COUNT(DISTINCT artifact_name) AS artifact_count,
  SUM(CASE WHEN artifact_type = 'table' THEN 1 ELSE 0 END) AS table_count,
  SUM(CASE WHEN artifact_type = 'job' THEN 1 ELSE 0 END) AS job_count,
  SUM(CASE WHEN artifact_type = 'pipeline' THEN 1 ELSE 0 END) AS pipeline_count
FROM (
  SELECT 
    artifact_name,
    artifact_type,
    COALESCE(invalid_tag_values['cost_center'], 'UNTAGGED') AS cost_center
  FROM metadata.tag_compliance
  WHERE check_date = CURRENT_DATE()
)
GROUP BY cost_center
ORDER BY artifact_count DESC;
```

## Best Practices

### 1. Tag at Creation Time
- Apply tags when creating artifacts, not retroactively
- Include tagging in templates and DABs
- Make tagging part of CI/CD validation

### 2. Use Controlled Vocabularies
- Define allowed values for categorical tags
- Maintain tag registry with valid values
- Enforce validation before applying tags

### 3. Automate Tag Management
- Use default tags for bulk operations
- Inherit tags from parent resources
- Propagate tags through lineage

### 4. Monitor Compliance
- Run daily compliance checks
- Alert on non-compliant artifacts
- Dashboard for tag coverage

### 5. Governance Process
- Require tag approval for new tag keys
- Document tag usage and examples
- Review and deprecate unused tags

## Quick Reference

### Apply Tags to Table
```sql
ALTER TABLE catalog.schema.table SET TAGS (
  'domain' = 'customer',
  'owner' = 'team@company.com',
  'environment' = 'prod'
);
```

### View Table Tags
```sql
DESCRIBE TABLE EXTENDED catalog.schema.table;
-- or
SHOW TBLPROPERTIES catalog.schema.table;
```

### Remove Tags
```sql
ALTER TABLE catalog.schema.table UNSET TAGS ('old_tag_key');
```

### Query by Tags
```sql
-- Find all tables with specific tag
SELECT table_catalog, table_schema, table_name
FROM system.information_schema.tables
WHERE table_tags['domain'] = 'customer';
```

### Validate Compliance
```python
validate_table_tags("main", "silver", "customers")
```
