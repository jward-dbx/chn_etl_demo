# Deploying Metric Views with Databricks Asset Bundles

This guide explains how to deploy OMOP semantic layer metric views using Databricks Asset Bundles (DABs).

## Overview

The metric views deployment uses:
- **SQL DDL**: Dynamic SQL script with embedded YAML definitions
- **DABs**: Orchestrates deployment across environments
- **SQL Job**: Executes the deployment script in Unity Catalog compute

## Prerequisites

1. **Databricks CLI** installed and configured
   ```bash
   databricks --version
   ```

2. **Source catalog** exists and is accessible
   - Snowflake connection and foreign catalog deployed
   - OMOP CDM tables available

3. **Target schema** exists
   ```sql
   CREATE SCHEMA IF NOT EXISTS <catalog>.<schema>;
   ```

4. **SQL Warehouse** available for execution
   - Get ID from Databricks UI or CLI:
     ```bash
     databricks warehouses list
     ```

## Configuration

### 1. Update Bundle Variables

Edit `deployment/dabs/semantic_layer/databricks.yml`:

```yaml
targets:
  dev:
    variables:
      source_catalog: "conn_sf_cursor_ward_catalog"  # Your Snowflake catalog
      target_catalog: "serverless_rde85f_catalog"     # Your Databricks catalog
      target_schema: "semantic_omop_cursor"           # Your target schema
      sql_warehouse_id: "abc123def456"                 # Your SQL warehouse ID
```

### 2. Get SQL Warehouse ID

```bash
# List available warehouses
databricks warehouses list --output json | jq -r '.warehouses[] | "\(.name): \(.id)"'

# Or use a specific warehouse name
databricks warehouses list --output json | jq -r '.warehouses[] | select(.name=="Serverless Starter Warehouse") | .id'
```

## Deployment

### Deploy to Development

```bash
cd deployment/dabs/semantic_layer

# Validate bundle
databricks bundle validate --target dev

# Deploy (creates/updates job definition)
databricks bundle deploy --target dev

# Run the deployment job
databricks bundle run deploy_metric_views --target dev
```

### Deploy to Production

```bash
# Set environment variables
export DATABRICKS_HOST="https://your-prod-workspace.cloud.databricks.com"
export PROD_SOURCE_CATALOG="prod_snowflake_catalog"
export PROD_TARGET_CATALOG="prod_databricks_catalog"
export PROD_TARGET_SCHEMA="semantic_omop"
export PROD_SQL_WAREHOUSE_ID="warehouse_id"

# Deploy and run
databricks bundle deploy --target prod
databricks bundle run deploy_metric_views --target prod
```

## Verification

### Check Job Status

```bash
# List recent runs
databricks jobs list-runs --job-name "Deploy OMOP Metric Views - semantic_omop_cursor" --limit 5

# Get specific run details
databricks jobs get-run <run_id>
```

### Verify Views in SQL

```sql
-- List all metric views
SHOW VIEWS IN serverless_rde85f_catalog.semantic_omop_cursor;

-- Describe a specific view
DESCRIBE EXTENDED serverless_rde85f_catalog.semantic_omop_cursor.patient_population_metrics;

-- Test a metric view (requires MEASURE() function)
SELECT 
  Gender,
  MEASURE(`Total Patients`),
  MEASURE(`Average Age`)
FROM serverless_rde85f_catalog.semantic_omop_cursor.patient_population_metrics
GROUP BY Gender;
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy Metric Views

on:
  push:
    branches: [main]
    paths:
      - 'semantic_layer/**'
      - 'sql/ddl/deploy_metric_views.sql'
      - 'deployment/dabs/semantic_layer/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Databricks CLI
        run: |
          curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
      
      - name: Configure Databricks
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: |
          databricks configure --host "$DATABRICKS_HOST" --token "$DATABRICKS_TOKEN"
      
      - name: Validate Bundle
        working-directory: deployment/dabs/semantic_layer
        run: databricks bundle validate --target prod
      
      - name: Deploy Bundle
        working-directory: deployment/dabs/semantic_layer
        run: databricks bundle deploy --target prod
      
      - name: Run Deployment
        working-directory: deployment/dabs/semantic_layer
        run: databricks bundle run deploy_metric_views --target prod --wait
```

## Troubleshooting

### Common Issues

1. **Catalog not found**
   - Ensure source and target catalogs exist and are accessible
   - Check Unity Catalog permissions

2. **SQL syntax errors**
   - Validate YAML files in `semantic_layer/metric_views/`
   - Test SQL script manually in SQL editor

3. **Permission denied**
   - Verify `CREATE VIEW` permission on target schema
   - Check warehouse permissions

4. **Source tables not found**
   - Ensure Snowflake connection is active
   - Verify OMOP tables exist in source catalog

### Manual Deployment

If DABs fails, deploy manually:

```sql
-- In Databricks SQL Editor or Notebook
SET VAR source_catalog = 'conn_sf_cursor_ward_catalog';
SET VAR target_catalog = 'serverless_rde85f_catalog';
SET VAR target_schema = 'semantic_omop_cursor';

-- Copy and paste contents of sql/ddl/deploy_metric_views.sql
-- Or upload file and execute
```

## Updating Metric Views

1. **Modify YAML files** in `semantic_layer/metric_views/`
2. **Regenerate SQL**: Run `generate_sql_deploy.py`
3. **Commit changes** to Git
4. **Deploy**: Run `databricks bundle run deploy_metric_views`

## Rollback

To rollback to a previous version:

```bash
# Checkout previous version
git checkout <previous_commit>

# Regenerate SQL
cd semantic_layer
python3 generate_sql_deploy.py

# Redeploy
cd ../deployment/dabs/semantic_layer
databricks bundle run deploy_metric_views --target prod
```

Or drop views and redeploy:

```sql
-- Drop all views
DROP VIEW IF EXISTS serverless_rde85f_catalog.semantic_omop_cursor.patient_population_metrics;
-- ... repeat for all views
```

## References

- [Databricks Asset Bundles Documentation](https://docs.databricks.com/dev-tools/bundles/)
- [Metric Views Documentation](https://docs.databricks.com/semantic-layer/metric-views.html)
- [Unity Catalog SQL Reference](https://docs.databricks.com/sql/language-manual/)
- [OMOP CDM v5.4](https://ohdsi.github.io/CommonDataModel/)

---

**Last Updated**: January 11, 2026  
**Bundle Version**: 1.0.0
