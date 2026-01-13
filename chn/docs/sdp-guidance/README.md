# Spark Declarative Pipelines (SDP) Guidance

This directory contains guidance and best practices for creating Spark Declarative Pipelines (formerly Delta Live Tables) in Databricks.

## Available Guides

### [Root Path Pattern](./root-path-pattern.md) ⭐ **Recommended**
**Modern pipeline organization using root_path and glob patterns**

- Old vs new pattern comparison
- Benefits of root path approach
- Recommended folder structures
- Migration guide

**TL;DR**: Use `root_path` with organized folders instead of listing individual files:
- ❌ Old: List every file in `libraries`
- ✅ New: Set `root_path` + use `glob` patterns

### [Table Naming Conventions](./table-naming-conventions.md)
**Critical guidance on table naming in SDP SQL files**

- Why multipart table names fail in CREATE statements
- Correct syntax for target and source tables
- Complete examples and common pitfalls

**TL;DR**: When `target` schema is defined in pipeline config, use table name only (no schema prefix) in CREATE statements:
- ❌ `CREATE TABLE cursor.customer`
- ✅ `CREATE TABLE customer`

## External Skills

For comprehensive SDP development patterns, refer to the external skills repository:
- **Location**: `chn/.claude/skills/sdp-writer/`
- **Topics**: Ingestion patterns, streaming patterns, SCD patterns, performance tuning, DLT migration

## Quick Reference

### Pipeline Configuration Pattern

```yaml
# databricks.yml
resources:
  pipelines:
    my_pipeline:
      catalog: my_catalog
      target: my_schema      # Target schema for all tables
      serverless: true       # Use serverless compute (2025 best practice)
      continuous: false      # Manual trigger only
      development: true      # Development mode
      libraries:
        - file:
            path: ./table1.sql
        - file:
            path: ./table2.sql
```

### SQL File Pattern

```sql
-- table1.sql
-- Use table name only (target schema comes from pipeline config)
CREATE OR REFRESH STREAMING TABLE table1
AS SELECT * 
FROM STREAM(source_catalog.source_schema.source_table)
```

## Common Issues

### Issue: Multipart Table Name Error

**Error Message**:
```
[UNSUPPORTED_SQL_STATEMENT] Multipart table names is not supported.
```

**Cause**: Using schema-qualified table name in CREATE statement

**Solution**: Remove schema prefix from table name in CREATE statement

See [Table Naming Conventions](./table-naming-conventions.md) for detailed explanation.

## Best Practices Summary

1. **Use serverless compute** - Auto-scaling, cost-efficient
2. **Streaming tables** - For real-time incremental processing
3. **Development mode** - For testing and validation
4. **No schedules for testing** - Use manual triggers
5. **Table names only** - No schema prefix in CREATE statements
6. **Fully qualified sources** - Always use `catalog.schema.table` for source tables
7. **Liquid Clustering** - Use `CLUSTER BY` instead of `PARTITION BY` (2025+)

## Resources

- [Databricks Delta Live Tables Documentation](https://docs.databricks.com/en/delta-live-tables/index.html)
- [DLT SQL Reference](https://docs.databricks.com/en/delta-live-tables/sql-ref.html)
- [External SDP Skills](../../.claude/skills/sdp-writer/)
- [Example Pipeline](../../sdp_test/)

## Contributing

When you discover new patterns or issues:
1. Document them in this directory
2. Add examples to demonstrate correct usage
3. Reference official Databricks documentation
4. Keep examples simple and focused
