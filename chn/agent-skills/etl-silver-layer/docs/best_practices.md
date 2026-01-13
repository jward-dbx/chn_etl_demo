# Silver Layer ETL Best Practices

## Table of Contents

- [Pipeline Design](#pipeline-design)
- [Performance Optimization](#performance-optimization)
- [Data Quality](#data-quality)
- [Testing Strategy](#testing-strategy)
- [Error Handling](#error-handling)
- [Monitoring and Alerting](#monitoring-and-alerting)
- [Security and Governance](#security-and-governance)
- [Deployment](#deployment)

## Pipeline Design

### Separation of Concerns

**Do:** Separate extraction, transformation, and loading into distinct stages
```python
# Good: Clear separation
def extract_from_bronze(spark, source_table):
    return spark.table(source_table)

def transform_to_silver(df):
    return df.transform(clean_data) \
             .transform(standardize_names) \
             .transform(add_metadata)

def load_to_silver(df, target_table):
    df.write.format("delta").mode("append").saveAsTable(target_table)
```

**Don't:** Mix concerns in a single monolithic function

### Idempotency

**Do:** Design pipelines to be idempotent (safe to run multiple times)
```python
# Use merge for upserts instead of append
delta_table.alias("target").merge(
    source_df.alias("source"),
    "target.id = source.id AND target.is_current = true"
).whenMatchedUpdate(...).whenNotMatchedInsert(...).execute()
```

**Don't:** Use append mode for silver layer tables with updates

### Incremental Processing

**Do:** Process only new or changed data when possible
```python
# Filter by date or watermark
new_data = df.filter(
    F.col("load_date") >= F.lit(last_load_date)
)
```

**Don't:** Reprocess all historical data on every run

## Performance Optimization

### Partitioning

**Do:** Partition by frequently filtered columns with reasonable cardinality
```python
# Good: Date-based partitioning
df.write.partitionBy("order_year", "order_month").saveAsTable("orders_silver")

# Good: Geographic partitioning  
df.write.partitionBy("customer_state").saveAsTable("customers_silver")
```

**Don't:** Partition by high-cardinality columns (e.g., customer_id) or low-cardinality columns (e.g., is_active with 2 values)

### Z-Ordering

**Do:** Z-order by columns used in joins and filters
```sql
-- Optimize after initial load and regularly thereafter
OPTIMIZE customers_silver
ZORDER BY (customer_id, customer_email);
```

### Data Skew Handling

**Do:** Handle skewed data with salting or AQE
```python
# Enable Adaptive Query Execution
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")

# Salt for heavily skewed joins
df_salted = df.withColumn("salt", F.expr("floor(rand() * 10)"))
```

### Caching Strategy

**Do:** Cache DataFrames that are used multiple times
```python
# Cache intermediate results
staging_df = bronze_df.transform(initial_cleanup).cache()
customers = staging_df.filter("entity_type = 'customer'")
orders = staging_df.filter("entity_type = 'order'")
staging_df.unpersist()  # Clean up when done
```

**Don't:** Cache everything or forget to unpersist

### Broadcast Joins

**Do:** Broadcast small dimension tables in joins
```python
# Broadcast small lookup tables
from pyspark.sql.functions import broadcast

large_df.join(
    broadcast(small_lookup_df),
    "lookup_key"
)
```

## Data Quality

### Defensive Programming

**Do:** Validate inputs before processing
```python
# Check schema before processing
expected_columns = ["customer_id", "email", "phone"]
missing_columns = set(expected_columns) - set(df.columns)
if missing_columns:
    raise ValueError(f"Missing columns: {missing_columns}")

# Check for critical nulls
null_count = df.filter(F.col("customer_id").isNull()).count()
if null_count > 0:
    raise ValueError(f"Found {null_count} null customer_ids")
```

### Data Quality Checks

**Do:** Implement comprehensive quality checks
```python
from great_expectations.dataset import SparkDFDataset

# Use Great Expectations for data quality
ge_df = SparkDFDataset(df)
ge_df.expect_column_values_to_not_be_null("customer_id")
ge_df.expect_column_values_to_match_regex("customer_email", r"^[\w\.-]+@[\w\.-]+\.\w+$")
ge_df.expect_column_values_to_be_between("customer_age", 0, 120)
```

### Quarantine Bad Records

**Do:** Quarantine records that fail quality checks instead of dropping
```python
# Separate good and bad records
good_records = df.filter("customer_email IS NOT NULL AND customer_email RLIKE email_pattern")
bad_records = df.filter("customer_email IS NULL OR NOT customer_email RLIKE email_pattern")

# Save bad records for investigation
bad_records.withColumn("failure_reason", F.lit("Invalid email")) \
           .write.mode("append").saveAsTable("quarantine_table")

# Process only good records
process_to_silver(good_records)
```

## Testing Strategy

### Unit Testing Pyramid

**Do:** Follow testing pyramid (many unit tests, fewer integration tests)
```
         /\      Integration Tests (E2E)
        /  \     
       /    \    Integration Tests (Component)
      /      \   
     /________\  Unit Tests (Functions, Transformations)
```

### Test Fixtures

**Do:** Use reusable test fixtures
```python
@pytest.fixture
def sample_customer_data(spark):
    return spark.createDataFrame([
        ("C001", "john@example.com", "5551234567"),
        ("C002", "jane@example.com", "5559876543"),
    ], ["customer_id", "email", "phone"])

def test_email_standardization(sample_customer_data):
    result = standardize_email(sample_customer_data)
    assert result.filter(F.col("email").contains("@")).count() == 2
```

### Test Data Quality

**Do:** Test data quality rules in unit tests
```python
def test_no_null_customer_ids(transformed_df):
    null_count = transformed_df.filter(F.col("customer_id").isNull()).count()
    assert null_count == 0, "Found null customer IDs"

def test_email_format(transformed_df):
    invalid_emails = transformed_df.filter(
        ~F.col("customer_email").rlike(r"^[\w\.-]+@[\w\.-]+\.\w+$")
    ).count()
    assert invalid_emails == 0, f"Found {invalid_emails} invalid emails"
```

## Error Handling

### Graceful Failures

**Do:** Fail gracefully with clear error messages
```python
try:
    df = spark.table(source_table)
except AnalysisException as e:
    logger.error(f"Source table {source_table} not found: {e}")
    send_alert(f"Pipeline failed: source table missing")
    raise

# Log progress and metrics
logger.info(f"Processing {df.count()} records from {source_table}")
```

### Retry Logic

**Do:** Implement retry logic for transient failures
```python
from retry import retry

@retry(tries=3, delay=60, backoff=2)
def write_to_silver(df, table_path):
    df.write.format("delta").mode("overwrite").saveAsTable(table_path)
```

### Dead Letter Queue

**Do:** Store failed records for later processing
```python
try:
    process_records(df)
except Exception as e:
    df.withColumn("error_message", F.lit(str(e))) \
      .withColumn("failed_at", F.current_timestamp()) \
      .write.mode("append").saveAsTable("dead_letter_queue")
    raise
```

## Monitoring and Alerting

### Pipeline Metrics

**Do:** Track key pipeline metrics
```python
metrics = {
    "pipeline_name": "customers_silver",
    "start_time": start_time,
    "end_time": datetime.now(),
    "records_processed": df.count(),
    "records_failed": failed_count,
    "duration_seconds": (datetime.now() - start_time).total_seconds(),
    "load_id": load_id
}

# Write metrics to table
spark.createDataFrame([metrics]).write \
    .mode("append").saveAsTable("pipeline_metrics")
```

### Data Quality Monitoring

**Do:** Monitor data quality trends over time
```sql
-- Track completeness trends
SELECT 
    date_trunc('day', record_created_at) as load_date,
    COUNT(*) as total_records,
    SUM(CASE WHEN customer_email IS NULL THEN 1 ELSE 0 END) as null_emails,
    SUM(CASE WHEN customer_phone IS NULL THEN 1 ELSE 0 END) as null_phones
FROM customers_silver
WHERE record_created_at >= current_date - INTERVAL 30 DAYS
GROUP BY 1
ORDER BY 1 DESC;
```

### Alerting Thresholds

**Do:** Set up alerts for anomalies
```python
# Alert if record count drops significantly
current_count = df.count()
expected_count = get_average_count(table_name, days=7)

if current_count < expected_count * 0.5:
    send_alert(
        f"Low record count detected: {current_count} (expected ~{expected_count})"
    )
```

## Security and Governance

### Data Classification

**Do:** Tag sensitive columns
```sql
-- Tag PII columns
ALTER TABLE customers_silver 
ALTER COLUMN customer_email 
SET TAGS ('data_classification' = 'PII');

ALTER TABLE customers_silver 
ALTER COLUMN customer_phone 
SET TAGS ('data_classification' = 'PII');
```

### Row-Level Security

**Do:** Implement row-level security for sensitive data
```sql
-- Create row filter function
CREATE FUNCTION region_filter(user_region STRING, row_region STRING)
RETURNS BOOLEAN
RETURN user_region = row_region OR user_region = 'ALL';

-- Apply to table
ALTER TABLE customers_silver 
SET ROW FILTER region_filter(current_user(), customer_region);
```

### Audit Logging

**Do:** Log all data access and modifications
```python
# Log pipeline execution
audit_log = {
    "pipeline": "customers_silver",
    "user": spark.sparkContext.sparkUser(),
    "action": "write",
    "table": target_table,
    "records_modified": df.count(),
    "timestamp": datetime.now()
}

spark.createDataFrame([audit_log]).write \
    .mode("append").saveAsTable("audit_log")
```

## Deployment

### Environment Promotion

**Do:** Follow a promotion path: dev → staging → prod
```bash
# Deploy to dev first
databricks bundle deploy --target dev

# Run tests in dev
databricks jobs run-now --job-id <dev_job_id>

# After validation, promote to staging
databricks bundle deploy --target staging

# After staging validation, promote to prod
databricks bundle deploy --target prod
```

### Configuration Management

**Do:** Externalize configuration
```yaml
# config.yml
environments:
  dev:
    catalog: dev_catalog
    max_concurrent_runs: 1
  prod:
    catalog: prod_catalog
    max_concurrent_runs: 3
```

### Blue-Green Deployments

**Do:** Use blue-green deployments for zero-downtime updates
```python
# Write to new version
df.write.saveAsTable("customers_silver_v2")

# Validate new version
run_validation("customers_silver_v2")

# Swap: rename tables atomically
spark.sql("ALTER TABLE customers_silver RENAME TO customers_silver_backup")
spark.sql("ALTER TABLE customers_silver_v2 RENAME TO customers_silver")
```

### Rollback Strategy

**Do:** Have a rollback plan
```sql
-- Use Delta Lake time travel for rollback
RESTORE TABLE customers_silver TO VERSION AS OF 42;

-- Or restore to timestamp
RESTORE TABLE customers_silver TO TIMESTAMP AS OF '2023-06-15 10:00:00';
```

## Summary Checklist

Before deploying a silver layer pipeline, ensure:

- [ ] Pipeline is idempotent and can be safely re-run
- [ ] Incremental processing is implemented where applicable
- [ ] Tables are properly partitioned and optimized
- [ ] Comprehensive data quality checks are in place
- [ ] Unit tests cover all transformation logic
- [ ] Error handling and retry logic implemented
- [ ] Metrics and alerting configured
- [ ] PII is identified and protected
- [ ] Configuration is externalized
- [ ] Rollback strategy is documented
- [ ] Documentation is complete and up-to-date
