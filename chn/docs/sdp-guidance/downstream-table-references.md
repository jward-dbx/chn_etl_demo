# Downstream Table References in SDP

## Overview

When creating tables that read from other tables within the **same DLT pipeline**, you must use the `LIVE` keyword to reference those tables. This creates proper data lineage in the DAG.

## The Problem

**Symptom**: `[TABLE_OR_VIEW_NOT_FOUND] The table or view table_name cannot be found`

**Cause**: Trying to reference pipeline tables without the `LIVE` keyword.

## The Solution

### ✅ Correct Syntax for Downstream Tables

**For STREAMING TABLES reading from pipeline tables:**

```sql
CREATE OR REFRESH STREAMING TABLE downstream_table
AS SELECT 
  t1.col1,
  t2.col2
FROM STREAM(LIVE.upstream_table1) t1
INNER JOIN STREAM(LIVE.upstream_table2) t2
  ON t1.id = t2.id
```

**For LIVE TABLES reading from pipeline tables:**

```sql
CREATE OR REFRESH LIVE TABLE downstream_table
AS SELECT 
  t1.col1,
  t2.col2
FROM LIVE.upstream_table1 t1
INNER JOIN LIVE.upstream_table2 t2
  ON t1.id = t2.id
```

### ❌ Incorrect Approaches

**Don't use unqualified table names:**
```sql
-- ❌ WRONG - Will fail with TABLE_OR_VIEW_NOT_FOUND
FROM STREAM(salesorderdetail) sod
```

**Don't use source table paths:**
```sql
-- ❌ WRONG - Bypasses pipeline lineage
FROM STREAM(dbx_chn_ward_demo.landing_ss_aw.salesorderdetail) sod
```

**Don't use schema-qualified names:**
```sql
-- ❌ WRONG - Multipart names not supported
FROM STREAM(cursor.salesorderdetail) sod
```

## Pattern Overview

### Source → Intermediate → Downstream

```sql
-- STEP 1: Ingest from source (external table)
CREATE OR REFRESH STREAMING TABLE customer
AS SELECT * 
FROM STREAM(dbx_chn_ward_demo.landing_ss_aw.customer)

-- STEP 2: Ingest from source (external table)
CREATE OR REFRESH STREAMING TABLE product  
AS SELECT * 
FROM STREAM(dbx_chn_ward_demo.landing_ss_aw.product)

-- STEP 3: Downstream table (reads from pipeline tables)
CREATE OR REFRESH STREAMING TABLE customer_product_flat
AS SELECT 
  c.CustomerID,
  c.FirstName,
  c.LastName,
  p.ProductID,
  p.ProductName
FROM STREAM(LIVE.customer) c
CROSS JOIN STREAM(LIVE.product) p  -- Using LIVE keyword!
```

### DAG Visualization

```
[External Source]     [Pipeline Ingestion]      [Downstream Transform]
landing_ss_aw.       →    customer           ↘
  customer                                    → customer_product_flat
landing_ss_aw.       →    product            ↗
  product
```

The `LIVE` keyword tells DLT:
1. This table is defined in the current pipeline
2. Create a dependency relationship
3. Show proper lineage in the DAG

## Complete Example: Our Landing to Cursor Pipeline

### File: customer.sql
```sql
CREATE OR REFRESH STREAMING TABLE customer
AS SELECT * FROM STREAM(dbx_chn_ward_demo.landing_ss_aw.customer)
```

### File: product.sql
```sql
CREATE OR REFRESH STREAMING TABLE product
AS SELECT * FROM STREAM(dbx_chn_ward_demo.landing_ss_aw.product)
```

### File: salesorderdetail.sql
```sql
CREATE OR REFRESH STREAMING TABLE salesorderdetail
AS SELECT * FROM STREAM(dbx_chn_ward_demo.landing_ss_aw.salesorderdetail)
```

### File: sales_orders_flat.sql (Downstream)
```sql
-- Downstream table reading from pipeline tables
CREATE OR REFRESH STREAMING TABLE sales_orders_flat
AS SELECT 
  sod.SalesOrderID,
  sod.OrderQty,
  sod.UnitPrice,
  p.ProductName,
  p.ListPrice
FROM STREAM(LIVE.salesorderdetail) sod    -- ✅ LIVE keyword!
INNER JOIN STREAM(LIVE.product) p         -- ✅ LIVE keyword!
  ON sod.ProductID = p.ProductID
```

## Rules Summary

| Table Type | Reading From | Syntax |
|------------|-------------|--------|
| **STREAMING TABLE** | External source | `FROM STREAM(catalog.schema.table)` |
| **STREAMING TABLE** | Pipeline table | `FROM STREAM(LIVE.table)` |
| **LIVE TABLE** | External source | `FROM catalog.schema.table` |
| **LIVE TABLE** | Pipeline table | `FROM LIVE.table` |

## Why This Matters

### 1. **Proper Data Lineage**
The DAG correctly shows dependencies and execution order.

### 2. **Dependency Resolution**
DLT knows to execute upstream tables before downstream tables.

### 3. **Change Propagation**
When upstream tables update, downstream tables automatically detect changes.

### 4. **Optimization**
DLT can optimize execution plans based on the dependency graph.

## Troubleshooting

### Error: `TABLE_OR_VIEW_NOT_FOUND`

**Check:**
1. ✅ Did you use `LIVE.table_name` for pipeline tables?
2. ✅ Did you use `STREAM(LIVE.table_name)` for streaming tables?
3. ✅ Is the upstream table defined in the same pipeline?
4. ✅ Did you spell the table name correctly?

### Error: `Multipart table names is not supported`

**Problem**: Using schema qualification like `cursor.table_name`

**Solution**: Remove schema prefix. Use just `LIVE.table_name`

### Tables Not Appearing in DAG

**Problem**: Using fully-qualified source paths bypasses pipeline lineage

**Solution**: Reference pipeline tables with `LIVE` keyword

## Best Practices

1. **Clear Naming**: Use descriptive names that indicate table purpose
   - Source ingestion: `customer`, `product`
   - Downstream: `customer_product_flat`, `sales_summary`

2. **File Organization**: Group by layer
   ```
   transformations/
   ├── 01_customer.sql        # Ingest
   ├── 02_product.sql         # Ingest
   ├── 10_sales_flat.sql      # Downstream
   ```

3. **Comments**: Document dependencies
   ```sql
   -- Downstream table
   -- Depends on: customer, product (pipeline tables)
   CREATE OR REFRESH STREAMING TABLE ...
   ```

4. **Testing**: Verify DAG shows proper lineage in UI

## References

- [Delta Live Tables - Table Dependencies](https://docs.databricks.com/delta-live-tables/index.html)
- [DLT SQL Reference - LIVE Keyword](https://docs.databricks.com/delta-live-tables/sql-ref.html)
- External Skills: `chn/.claude/skills/sdp-writer/streaming-patterns.md`
