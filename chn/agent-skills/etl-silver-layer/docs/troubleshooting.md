# Troubleshooting Guide

## Common Issues and Solutions

### Table and Schema Issues

#### Issue: "Table or view not found"

**Symptoms:**
```
AnalysisException: Table or view 'customers_silver' not found
```

**Solutions:**
1. Check if table exists:
   ```sql
   SHOW TABLES IN catalog.schema;
   ```

2. Verify catalog and schema:
   ```python
   print(spark.catalog.currentCatalog())
   print(spark.catalog.currentDatabase())
   ```

3. Use fully qualified name:
   ```python
   df = spark.table("catalog.schema.table_name")
   ```

#### Issue: Schema mismatch errors

**Symptoms:**
```
AnalysisException: Cannot write incompatible data to table
Column 'customer_age' expected to be IntegerType but is StringType
```

**Solutions:**
1. Verify schema before writing:
   ```python
   expected_schema = get_customer_silver_schema()
   if df.schema != expected_schema:
       print("Schema mismatch!")
       df.printSchema()
   ```

2. Cast columns to correct types:
   ```python
   df = df.withColumn("customer_age", F.col("customer_age").cast(IntegerType()))
   ```

3. Use schema evolution (with caution):
   ```python
   df.write \
       .option("mergeSchema", "true") \
       .mode("append") \
       .saveAsTable(table_name)
   ```

### Data Quality Issues

#### Issue: Null values in required columns

**Symptoms:**
```
Data quality check failed: 1,234 null values in customer_id
```

**Solutions:**
1. Filter out nulls before processing:
   ```python
   df_clean = df.filter(F.col("customer_id").isNotNull())
   df_bad = df.filter(F.col("customer_id").isNull())
   
   # Quarantine bad records
   df_bad.write.mode("append").saveAsTable("quarantine_table")
   ```

2. Fill nulls with defaults:
   ```python
   df = df.fillna({
       "customer_email": "unknown@company.com",
       "customer_phone": "0000000000"
   })
   ```

3. Investigate source data:
   ```sql
   SELECT COUNT(*) as null_count
   FROM bronze.customers
   WHERE customer_id IS NULL;
   ```

#### Issue: Duplicate records

**Symptoms:**
```
Multiple current records found for customer_id: C12345
```

**Solutions:**
1. Deduplicate before processing:
   ```python
   # Keep most recent record
   from pyspark.sql.window import Window
   
   window = Window.partitionBy("customer_id").orderBy(F.desc("updated_at"))
   df_deduped = df.withColumn("row_num", F.row_number().over(window)) \
                  .filter("row_num = 1") \
                  .drop("row_num")
   ```

2. Find duplicates:
   ```sql
   SELECT customer_id, COUNT(*) as count
   FROM customers_silver
   WHERE is_current = TRUE
   GROUP BY customer_id
   HAVING COUNT(*) > 1;
   ```

3. Fix existing duplicates:
   ```sql
   -- Close out all but the latest
   MERGE INTO customers_silver AS target
   USING (
       SELECT customer_id, MAX(effective_start_date) as latest_date
       FROM customers_silver
       WHERE is_current = TRUE
       GROUP BY customer_id
       HAVING COUNT(*) > 1
   ) AS dupes
   ON target.customer_id = dupes.customer_id
      AND target.is_current = TRUE
      AND target.effective_start_date < dupes.latest_date
   WHEN MATCHED THEN UPDATE SET
       is_current = FALSE,
       effective_end_date = current_timestamp();
   ```

### Performance Issues

#### Issue: Slow queries / Pipeline timeouts

**Symptoms:**
- Queries taking > 5 minutes
- Pipeline jobs timing out
- Spark UI showing data skew

**Solutions:**
1. Check for data skew:
   ```python
   # Check partition sizes
   df.groupBy(spark_partition_id()).count().show()
   ```

2. Optimize table:
   ```sql
   OPTIMIZE customers_silver
   ZORDER BY (customer_id);
   ```

3. Enable AQE:
   ```python
   spark.conf.set("spark.sql.adaptive.enabled", "true")
   spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
   ```

4. Repartition before write:
   ```python
   df.repartition(100, "customer_state").write.saveAsTable(...)
   ```

#### Issue: Out of memory errors

**Symptoms:**
```
java.lang.OutOfMemoryError: Java heap space
```

**Solutions:**
1. Increase executor memory:
   ```python
   spark.conf.set("spark.executor.memory", "16g")
   spark.conf.set("spark.driver.memory", "8g")
   ```

2. Process data in batches:
   ```python
   # Process by partition
   partitions = df.select("customer_state").distinct().collect()
   for partition in partitions:
       state = partition.customer_state
       df_partition = df.filter(f"customer_state = '{state}'")
       process_partition(df_partition)
   ```

3. Avoid collect() on large datasets:
   ```python
   # Bad
   data = df.collect()  # Pulls all data to driver
   
   # Good
   df.write.saveAsTable(...)  # Distributed write
   ```

### Delta Lake Issues

#### Issue: Concurrent write conflicts

**Symptoms:**
```
ConcurrentAppendException: Files were added to the table during the write
```

**Solutions:**
1. Use merge instead of append:
   ```python
   delta_table.alias("target").merge(
       source_df.alias("source"),
       "target.id = source.id"
   ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
   ```

2. Enable optimistic concurrency:
   ```python
   df.write \
       .option("txnVersion", "version") \
       .option("txnAppId", "app_id") \
       .mode("append") \
       .saveAsTable(table_name)
   ```

#### Issue: Table version too old

**Symptoms:**
```
The transaction attempted to write to a table that has already been updated
```

**Solutions:**
1. Increase file retention:
   ```sql
   ALTER TABLE customers_silver 
   SET TBLPROPERTIES (
       'delta.deletedFileRetentionDuration' = 'interval 7 days'
   );
   ```

2. Use time travel to restore:
   ```sql
   SELECT * FROM customers_silver VERSION AS OF 10;
   ```

3. Run vacuum less frequently:
   ```sql
   -- Only vacuum after retention period
   VACUUM customers_silver RETAIN 168 HOURS;  -- 7 days
   ```

### SCD Type 2 Issues

#### Issue: Multiple current records

**Symptoms:**
```
Data integrity error: Customer C12345 has 3 current records
```

**Solutions:**
1. Find problematic records:
   ```sql
   SELECT customer_id, COUNT(*) as current_count
   FROM customers_silver
   WHERE is_current = TRUE
   GROUP BY customer_id
   HAVING COUNT(*) > 1;
   ```

2. Close all but the latest:
   ```sql
   WITH latest_records AS (
       SELECT 
           customer_id,
           MAX(effective_start_date) as max_date
       FROM customers_silver
       WHERE is_current = TRUE
       GROUP BY customer_id
       HAVING COUNT(*) > 1
   )
   UPDATE customers_silver
   SET is_current = FALSE,
       effective_end_date = current_timestamp()
   WHERE customer_id IN (SELECT customer_id FROM latest_records)
     AND is_current = TRUE
     AND effective_start_date < (
         SELECT max_date FROM latest_records l 
         WHERE l.customer_id = customers_silver.customer_id
     );
   ```

#### Issue: No current record for customer

**Symptoms:**
```
Warning: Customer C12345 has no current record
```

**Solutions:**
1. Find orphaned records:
   ```sql
   SELECT DISTINCT a.customer_id
   FROM customers_silver a
   WHERE NOT EXISTS (
       SELECT 1 FROM customers_silver b
       WHERE b.customer_id = a.customer_id
         AND b.is_current = TRUE
   );
   ```

2. Reopen most recent record:
   ```sql
   WITH latest_records AS (
       SELECT 
           customer_id,
           MAX(effective_start_date) as max_date
       FROM customers_silver
       GROUP BY customer_id
   )
   UPDATE customers_silver
   SET is_current = TRUE,
       effective_end_date = NULL
   WHERE (customer_id, effective_start_date) IN (
       SELECT customer_id, max_date FROM latest_records
   );
   ```

### Testing Issues

#### Issue: Tests fail locally but pass in CI

**Symptoms:**
- Tests pass on local machine
- Tests fail in Databricks / CI environment

**Solutions:**
1. Check Spark version consistency:
   ```python
   print(spark.version)
   # Ensure same version in all environments
   ```

2. Use absolute paths:
   ```python
   # Bad
   df = spark.read.parquet("data/customers.parquet")
   
   # Good
   import os
   base_path = os.path.dirname(__file__)
   df = spark.read.parquet(f"{base_path}/data/customers.parquet")
   ```

3. Mock external dependencies:
   ```python
   from unittest.mock import patch
   
   @patch('module.external_api_call')
   def test_transformation(mock_api):
       mock_api.return_value = expected_response
       result = transform_data(df)
       assert result.count() == expected_count
   ```

### Deployment Issues

#### Issue: Bundle validation fails

**Symptoms:**
```
Error: Invalid databricks.yml configuration
```

**Solutions:**
1. Validate YAML syntax:
   ```bash
   # Use YAML linter
   yamllint databricks.yml
   ```

2. Check bundle structure:
   ```bash
   databricks bundle validate --target dev
   ```

3. Verify target configuration:
   ```yaml
   targets:
     dev:
       mode: development
       workspace:
         host: https://your-workspace.cloud.databricks.com
   ```

#### Issue: Permission denied errors

**Symptoms:**
```
PermissionDenied: User does not have permission to create table in schema
```

**Solutions:**
1. Check Unity Catalog permissions:
   ```sql
   SHOW GRANTS ON SCHEMA catalog.schema;
   ```

2. Request necessary permissions:
   - CREATE TABLE on schema
   - SELECT, MODIFY on existing tables
   - USAGE on catalog and schema

3. Use service principal for deployment:
   ```bash
   export DATABRICKS_CLIENT_ID=<client_id>
   export DATABRICKS_CLIENT_SECRET=<client_secret>
   ```

## Debugging Tools

### Spark UI

Access Spark UI to investigate performance:
1. Find Spark UI URL in cluster details
2. Check:
   - Stage duration and task distribution
   - Data skew in task metrics
   - Shuffle read/write sizes
   - GC time

### Query History

Review query history:
```sql
-- In Databricks SQL
SELECT * FROM system.query.history
WHERE statement_text LIKE '%customers_silver%'
ORDER BY start_time DESC
LIMIT 10;
```

### Delta Lake Transaction Log

Inspect Delta transaction log:
```python
# Read transaction log
log_df = spark.read.json("dbfs:/path/to/table/_delta_log/*.json")
log_df.select("commitInfo", "add", "remove").show(truncate=False)
```

### Enable Debug Logging

Turn on debug logging:
```python
spark.sparkContext.setLogLevel("DEBUG")

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

## Getting Help

If you're still stuck:

1. **Check documentation**: Review examples and templates in this repository
2. **Search logs**: Look for specific error messages in Spark/cluster logs
3. **Ask team**: Post in #data-engineering Slack channel
4. **Contact support**: Open ticket with Databricks support
5. **Community**: Search Stack Overflow and Databricks Community forums

## Useful Commands Reference

```bash
# Validate bundle
databricks bundle validate --target dev

# Deploy bundle
databricks bundle deploy --target dev

# Run tests
pytest tests/ -v --cov=src

# Validate schema
python scripts/validate_schema.py --env dev --table customers_silver

# Generate DQ report
python scripts/generate_dq_report.py --env dev --table customers_silver

# Check table details
databricks tables describe catalog.schema.table_name

# View job runs
databricks jobs list-runs --job-id <job_id> --limit 10
```

## Prevention Tips

1. **Test early and often**: Run tests before deploying
2. **Monitor proactively**: Set up alerts before issues occur
3. **Document changes**: Keep README and docs updated
4. **Code review**: Have peers review changes
5. **Gradual rollouts**: Deploy to dev/staging before prod
6. **Backup data**: Use Delta time travel before risky operations
