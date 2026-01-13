# SDP Root Path Pattern - Modern Organization

## Overview

The **root path pattern** is the modern way to organize Spark Declarative Pipelines, replacing the older method of listing individual file paths.

## Old vs New Pattern

### ❌ Old Pattern (Individual Files)

```yaml
resources:
  pipelines:
    my_pipeline:
      libraries:
        - file:
            path: ./customer.sql
        - file:
            path: ./product.sql
        - file:
            path: ./salesorderdetail.sql
        # Need to add every new file manually
```

**Problems**:
- Must update config for every new file
- No clear organization structure
- Files scattered at project root
- Hard to manage as pipeline grows

### ✅ New Pattern (Root Path + Glob)

```yaml
resources:
  pipelines:
    my_pipeline:
      root_path: ./src/pipelines/my_pipeline
      libraries:
        - glob:
            include: ./src/pipelines/my_pipeline/transformations/**
```

**Benefits**:
- 🎯 **Auto-discovery**: New files automatically included
- 📁 **Better organization**: Clear folder structure
- 🔧 **Easier maintenance**: No config updates for new files
- 📦 **Scalability**: Supports growing pipelines
- 🎨 **Clean separation**: Code separated from config

## Recommended Folder Structure

```
project/
├── databricks.yml
├── src/
│   └── pipelines/
│       └── <pipeline_name>/
│           ├── transformations/
│           │   ├── bronze/
│           │   │   ├── ingest_*.sql
│           │   ├── silver/
│           │   │   ├── clean_*.sql
│           │   └── gold/
│           │       ├── aggregate_*.sql
│           └── utils/
│               └── helper_functions.sql
├── README.md
└── DEPLOYMENT.md
```

## Root Path Benefits

### 1. **Automatic File Discovery**

When you add a new SQL file to the `transformations/` directory, it's automatically included in the pipeline - no YAML updates needed!

### 2. **Medallion Architecture Support**

Easily organize files by layer:
```
transformations/
├── bronze/      # Raw ingestion
├── silver/      # Cleaned, validated
└── gold/        # Business aggregates
```

### 3. **Relative Paths in SQL**

With `root_path` set, SQL files can reference each other more cleanly:
- Pipeline knows the base directory
- Files are relative to root, not scattered
- Easier to move/reorganize

### 4. **Better Version Control**

```bash
git add src/pipelines/my_pipeline/transformations/new_table.sql
# That's it! No YAML changes needed
```

### 5. **Multi-Pipeline Projects**

Easy to manage multiple pipelines in one project:
```
src/
├── pipelines/
│   ├── landing_to_silver/
│   │   └── transformations/
│   ├── silver_to_gold/
│   │   └── transformations/
│   └── metrics/
│       └── transformations/
```

## Migration Guide

### Step 1: Create New Structure

```bash
mkdir -p src/pipelines/<pipeline_name>/transformations
mv *.sql src/pipelines/<pipeline_name>/transformations/
```

### Step 2: Update databricks.yml

Replace individual file entries with root_path + glob:

```yaml
resources:
  pipelines:
    my_pipeline:
      # Add root_path
      root_path: ./src/pipelines/<pipeline_name>
      
      # Replace libraries section
      libraries:
        - glob:
            include: ./src/pipelines/<pipeline_name>/transformations/**
```

### Step 3: Update Workspace Files

Upload files to workspace in new structure:
```bash
# Create workspace directory
databricks workspace mkdirs \
  /Users/your.email@company.com/project/src/pipelines/<pipeline_name>/transformations

# Upload files
databricks workspace import-dir \
  src/pipelines/<pipeline_name>/transformations \
  /Users/your.email@company.com/project/src/pipelines/<pipeline_name>/transformations
```

### Step 4: Update Pipeline via API

```python
import requests

# Update pipeline with root_path
response = requests.put(
    f"{databricks_host}/api/2.0/pipelines/{pipeline_id}",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "root_path": "/Users/your.email@company.com/project/src/pipelines/<pipeline_name>",
        "libraries": [
            {"file": {"path": "transformations/file1.sql"}},
            {"file": {"path": "transformations/file2.sql"}},
        ]
    }
)
```

**Note**: When using API directly, you may still need to list files. The glob pattern works best with DABs deployment.

## Glob Patterns

When using Databricks Asset Bundles (DABs), you can use glob patterns:

```yaml
libraries:
  - glob:
      include: ./src/pipelines/<pipeline_name>/transformations/**
  - glob:
      include: ./src/pipelines/<pipeline_name>/utils/*.sql
```

### Common Glob Patterns

| Pattern | Matches |
|---------|---------|
| `**` | All files in directory and subdirectories |
| `*.sql` | All SQL files in current directory |
| `bronze/*.sql` | All SQL files in bronze subdirectory |
| `**/*.sql` | All SQL files recursively |

## Best Practices

### 1. Consistent Naming

```
transformations/
├── 01_ingest_customers.sql
├── 02_ingest_orders.sql
├── 10_clean_customers.sql
├── 11_clean_orders.sql
├── 20_aggregate_sales.sql
```

Number prefixes help control execution order (though DLT determines DAG automatically).

### 2. Layer Separation

Keep bronze, silver, and gold transformations in separate folders for clarity.

### 3. Descriptive Names

Use descriptive file names that indicate what the transformation does:
- ✅ `clean_customer_emails.sql`
- ❌ `transform1.sql`

### 4. Documentation

Add a README in each pipeline folder:
```
src/pipelines/my_pipeline/
├── README.md          # Pipeline purpose and logic
├── transformations/
└── utils/
```

## Example: Our Landing to Cursor Pipeline

**Before (Old Pattern)**:
```
sdp_test/
├── databricks.yml
├── customer.sql
├── product.sql
├── salesorderdetail.sql
└── sales_orders_flat.sql
```

**After (Root Path Pattern)**:
```
sdp_test/
├── databricks.yml
└── src/
    └── pipelines/
        └── landing_to_cursor/
            └── transformations/
                ├── customer.sql
                ├── product.sql
                ├── salesorderdetail.sql
                └── sales_orders_flat.sql
```

**Benefits Realized**:
- Clear pipeline isolation
- Can add more pipelines easily
- Files organized by purpose
- Scalable for future growth

## References

- [Databricks Asset Bundles - Pipeline Configuration](https://docs.databricks.com/dev-tools/bundles/resources.html)
- [Delta Live Tables - Best Practices](https://docs.databricks.com/delta-live-tables/index.html)
- External Skills: `chn/.claude/skills/dabs-writer/SDP_guidance.md`
