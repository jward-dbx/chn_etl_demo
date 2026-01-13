# Spark Declarative Pipelines - Table Naming Conventions

## Critical Rule: No Multi-Part Table Names in CREATE Statements

When creating tables in Spark Declarative Pipelines (DLT), **DO NOT** use schema-qualified table names in your `CREATE TABLE` statements.

### ❌ WRONG - Will cause error

```sql
CREATE OR REFRESH STREAMING TABLE cursor.customer
AS SELECT * FROM ...
```

**Error**: `[UNSUPPORTED_SQL_STATEMENT] Multipart table names is not supported.`

### ✅ CORRECT - Use table name only

```sql
CREATE OR REFRESH STREAMING TABLE customer
AS SELECT * FROM ...
```

## Why?

The target schema is already specified in the pipeline configuration (`databricks.yml`):

```yaml
resources:
  pipelines:
    my_pipeline:
      catalog: dbx_chn_ward_demo
      target: cursor  # <-- Target schema defined here
```

When you specify `target: cursor` in the pipeline config, all tables created in your SQL files will automatically be created in the `cursor` schema. Adding the schema prefix in the SQL causes a conflict.

## Source Tables

You **DO** need to use fully-qualified names for source tables:

```sql
-- ✅ CORRECT - Source tables need full qualification
CREATE OR REFRESH STREAMING TABLE customer
AS SELECT * 
FROM STREAM(dbx_chn_ward_demo.landing_ss_aw.customer)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
           Fully qualified source table
```

## Summary

| Location | Naming Convention | Example |
|----------|------------------|---------|
| **Target table in CREATE** | Table name only | `CREATE TABLE customer` |
| **Source tables in FROM** | Fully qualified | `FROM catalog.schema.table` |
| **Pipeline config (target)** | Schema name only | `target: cursor` |

## Complete Example

**databricks.yml**:
```yaml
resources:
  pipelines:
    landing_to_cursor:
      catalog: dbx_chn_ward_demo
      target: cursor
      libraries:
        - file:
            path: ./customer.sql
```

**customer.sql**:
```sql
-- Target table: name only (no schema prefix)
CREATE OR REFRESH STREAMING TABLE customer
AS SELECT * 
FROM STREAM(dbx_chn_ward_demo.landing_ss_aw.customer)
--          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
--          Source table: fully qualified
```

**Result**: Creates table at `dbx_chn_ward_demo.cursor.customer`

## Additional Notes

### Views and Temporary Tables

The same rule applies to views and temporary tables:

```sql
-- ✅ CORRECT
CREATE OR REFRESH TEMPORARY VIEW temp_customer
AS SELECT * FROM ...

-- ❌ WRONG
CREATE OR REFRESH TEMPORARY VIEW cursor.temp_customer
AS SELECT * FROM ...
```

### Streaming vs Live Tables

This applies to both STREAMING and LIVE tables:

```sql
-- ✅ Both correct
CREATE OR REFRESH STREAMING TABLE orders
CREATE OR REFRESH LIVE TABLE customers
```

### Cross-Schema References

If you need to reference tables from different schemas in your queries, use fully qualified names:

```sql
CREATE OR REFRESH STREAMING TABLE enriched_customer
AS SELECT 
  c.*,
  r.region_name
FROM STREAM(dbx_chn_ward_demo.landing_ss_aw.customer) c
LEFT JOIN dbx_chn_ward_demo.reference.regions r
  ON c.region_id = r.region_id
```

## References

- [Databricks Delta Live Tables Documentation](https://docs.databricks.com/en/delta-live-tables/index.html)
- [DLT SQL Reference](https://docs.databricks.com/en/delta-live-tables/sql-ref.html)
