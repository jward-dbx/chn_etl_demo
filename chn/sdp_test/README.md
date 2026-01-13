# SDP Landing to Cursor Pipeline

This Spark Declarative Pipeline (SDP) copies tables from the `landing_ss_aw` schema to the `cursor` schema in the `dbx_chn_ward_demo` catalog.

## Tables Included

- `customer`
- `product`
- `salesorderdetail`

## Architecture

- **Source**: `dbx_chn_ward_demo.landing_ss_aw.*`
- **Target**: `dbx_chn_ward_demo.cursor.*`
- **Compute**: Serverless (2025 best practice)
- **Processing**: Streaming tables for real-time updates
- **Organization**: Modern root_path pattern with structured folders

## Project Structure

```
sdp_test/
├── databricks.yml                 # Pipeline configuration
├── src/
│   └── pipelines/
│       └── landing_to_cursor/
│           └── transformations/   # All SQL transformation files
│               ├── customer.sql
│               ├── product.sql
│               ├── salesorderdetail.sql
│               └── sales_orders_flat.sql
├── README.md
└── DEPLOYMENT.md
```

**Note**: This project uses the modern **root_path pattern** for better organization and scalability. See `docs/sdp-guidance/root-path-pattern.md` for details.

## Deployment

### Prerequisites

```bash
# Ensure Databricks CLI is installed and configured
databricks --version

# Authenticate to the CHN workspace
databricks auth login --host https://adb-7405607609261208.8.azuredatabricks.net
```

### Deploy the Pipeline

```bash
# Navigate to the project directory
cd /Users/justin.ward/chn/sdp_test

# Validate the bundle
databricks bundle validate

# Deploy to development
databricks bundle deploy --target dev

# Run the pipeline
databricks bundle run landing_to_cursor_pipeline
```

### Alternative: Deploy via API

You can also create the pipeline directly via the Databricks UI:
1. Go to **Workflows** > **Delta Live Tables**
2. Click **Create Pipeline**
3. Add the SQL files: `customer.sql`, `product.sql`, `salesorderdetail.sql`
4. Configure:
   - **Catalog**: `dbx_chn_ward_demo`
   - **Target Schema**: `cursor`
   - **Serverless**: Enabled
   - **Development Mode**: Enabled

## Pipeline Logic

Each SQL file creates a streaming table that reads from the source landing table and writes to the target cursor schema:

```sql
CREATE OR REFRESH STREAMING TABLE {table_name}
AS SELECT * FROM STREAM(dbx_chn_ward_demo.landing_ss_aw.{table_name})
```

**Important**: Do NOT use schema-qualified names (e.g., `cursor.table_name`) in the CREATE statement. The `target` schema is specified in `databricks.yml`. See `docs/sdp-guidance/table-naming-conventions.md` for details.

This creates a continuous streaming pipeline that:
- Processes changes incrementally
- Maintains data freshness
- Handles schema evolution
- Provides data quality monitoring

## Monitoring

After deployment, monitor the pipeline:

```bash
# Check pipeline status
databricks pipelines get landing_to_cursor_pipeline

# View pipeline logs
databricks pipelines get-update landing_to_cursor_pipeline --update-id <update-id>
```

Or via the UI:
1. Navigate to **Workflows** > **Delta Live Tables**
2. Find your pipeline: `[username] Landing to Cursor Pipeline`
3. View the DAG and execution details

## Customization

To modify the pipeline:

1. **Add/Remove Tables**: Edit `databricks.yml` to include/exclude SQL files
2. **Change Schemas**: Update variables in `databricks.yml`:
   ```yaml
   variables:
     source_schema:
       default: your_source_schema
     target_schema:
       default: your_target_schema
   ```
3. **Add Transformations**: Modify the SQL files to include transformations, filters, or data quality checks

## Clean Up

To remove the pipeline:

```bash
databricks bundle destroy --target dev
```
