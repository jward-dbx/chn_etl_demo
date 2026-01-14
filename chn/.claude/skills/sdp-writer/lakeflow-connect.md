# Lakeflow Connect - Managed Database Ingestion

## Overview

**Lakeflow Connect** enables managed ingestion from database and application sources into Databricks using pre-built connectors. It simplifies CDC (Change Data Capture) ingestion with a two-stage architecture:

1. **Ingestion Gateway**: Extracts snapshot and change data from source databases
2. **Ingestion Pipeline**: Applies changes to destination Unity Catalog tables

**When to use Lakeflow Connect vs Traditional Ingestion**:

| Source Type | Use | Pattern |
|------------|-----|---------|
| **Database sources** (SQL Server, Oracle, PostgreSQL, MySQL, etc.) | **Lakeflow Connect** | Managed connectors with CDC |
| **Cloud storage files** (S3, ADLS, GCS) | **Auto Loader** | `read_files()` pattern (see [ingestion-patterns.md](ingestion-patterns.md)) |
| **Streaming sources** (Kafka, Event Hub, Kinesis) | **Native streaming** | `read_stream()` pattern (see [ingestion-patterns.md](ingestion-patterns.md)) |
| **SaaS applications** (Salesforce, ServiceNow) | **Lakeflow Connect** | Managed connectors |

---

## Supported Connectors

Lakeflow Connect supports managed ingestion from:

- **Relational Databases**: SQL Server (Azure SQL, Amazon RDS), Oracle, PostgreSQL, MySQL, Amazon Aurora
- **Data Warehouses**: Snowflake, Google BigQuery
- **SaaS Applications**: Salesforce, ServiceNow, Workday
- **Others**: MongoDB, SAP (via connections)

**Note**: Connector availability and features may vary. Check [Databricks documentation](https://docs.databricks.com/ingestion/lakeflow-connect/) for the latest list.

---

## Architecture

### Two-Stage Ingestion

```
┌─────────────────┐
│ Source Database │
│  (SQL Server)   │
└────────┬────────┘
         │
         │ Extract CDC
         ↓
┌─────────────────┐
│ Ingestion       │ ← Runs continuously
│ Gateway         │   Stores in staging volume
└────────┬────────┘
         │
         │ Staged data
         ↓
┌─────────────────┐
│ Ingestion       │ ← Applies changes
│ Pipeline        │   to target tables
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Unity Catalog   │
│ Target Tables   │
└─────────────────┘
```

**Key Points**:
- Gateway must run **continuously** to capture CDC changes
- Pipeline processes staged data into target streaming tables
- Both use serverless compute for auto-scaling
- Gateway stores data in staging catalog/schema/volume

---

## Prerequisites

Before creating Lakeflow Connect pipelines, ensure:

1. **Workspace Configuration**:
   - Unity Catalog enabled
   - Serverless compute enabled
   - Target catalog and schema exist

2. **Permissions**:
   - `CREATE CONNECTION` or `USE CONNECTION` on the connection
   - `USE CATALOG` on target catalog
   - `USE SCHEMA`, `CREATE TABLE`, `CREATE VOLUME` on target schema (or `CREATE SCHEMA` on catalog)

3. **Source Database Setup**:
   - CDC enabled on source database (e.g., Change Tracking for SQL Server)
   - Network connectivity (VPN, ExpressRoute, or Direct Connect for on-premises)
   - Service account with read permissions

4. **Compute Policy** (if using custom policies):
   - Must allow DLT cluster type
   - Minimum 8 cores recommended for gateway driver node

---

## Creating Connections

Before creating pipelines, create a Unity Catalog connection to store source credentials.

### Option 1: Catalog Explorer UI

1. In Databricks workspace, go to **Catalog** → **External Data** → **Connections**
2. Click **Create connection**
3. Select connection type (e.g., SQL Server)
4. Provide:
   - **Connection name**: Unique identifier
   - **Host**: Database server address
   - **Port**: Default 1433 for SQL Server
   - **Username** and **Password**: Service account credentials
   - **Additional options**: SSL settings, authentication method
5. Test connection and click **Create**

### Option 2: Databricks CLI

```bash
export CONNECTION_NAME="sqlserver_source"
export DB_HOST="myserver.database.windows.net"
export DB_USER="dbuser"
export DB_PASSWORD="secure_password"

databricks connections create --json '{
  "name": "'"$CONNECTION_NAME"'",
  "connection_type": "SQLSERVER",
  "options": {
    "host": "'"$DB_HOST"'",
    "port": "1433",
    "user": "'"$DB_USER"'",
    "password": "'"$DB_PASSWORD"'",
    "trustServerCertificate": "false"
  }
}'
```

### Option 3: Python SDK

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

connection = w.connections.create(
    name="sqlserver_source",
    connection_type="SQLSERVER",
    options={
        "host": "myserver.database.windows.net",
        "port": "1433",
        "user": "dbuser",
        "password": "secure_password"
    }
)

print(f"Created connection: {connection.connection_id}")
```

**Security Best Practice**: Use Databricks Secrets for credentials:

```bash
# Store credentials in secrets
databricks secrets put-secret --scope my-scope --key db-password

# Reference in connection (CLI)
databricks connections create --json '{
  "name": "sqlserver_source",
  "connection_type": "SQLSERVER",
  "options": {
    "host": "myserver.database.windows.net",
    "port": "1433",
    "user": "dbuser",
    "password": "{{secrets/my-scope/db-password}}"
  }
}'
```

---

## Creating Ingestion Gateway and Pipeline

### Option 1: Databricks UI (Recommended for Getting Started)

**Best for**: Initial setup, exploratory work, admin users

1. In workspace sidebar, click **Data Ingestion**
2. Under **Databricks connectors**, select your source type (e.g., **SQL Server**)
3. **Ingestion Gateway page**:
   - Enter unique gateway name (e.g., `sqlserver_gateway`)
   - Select staging catalog and schema
   - Click **Next**
4. **Ingestion Pipeline page**:
   - Enter unique pipeline name (e.g., `sqlserver_ingestion_pipeline`)
   - Select destination catalog
   - Select or create Unity Catalog connection
   - Click **Create pipeline and continue**
5. **Source page**:
   - Select tables to ingest (individual tables or entire schemas)
   - Configure history tracking (SCD Type 2) if needed
   - Click **Next**
6. **Destination page**:
   - Select target catalog and schema
   - Map source tables to destination (optional custom names)
   - Click **Save and continue**
7. **Settings page** (optional):
   - Create schedule for pipeline refresh
   - Set email notifications
   - Click **Save and run pipeline**

### Option 2: Databricks Asset Bundles (DABs)

**Best for**: Production deployments, multi-environment, CI/CD

Create a DAB resource file with gateway and pipeline definitions:

**File**: `resources/lakeflow_sqlserver.yml`

```yaml
variables:
  gateway_name:
    default: sqlserver-gateway
  pipeline_name:
    default: sqlserver-ingestion-pipeline
  connection_name:
    default: sqlserver_source
  staging_catalog:
    default: main
  staging_schema:
    default: ingestion_staging
  dest_catalog:
    default: ${var.catalog}
  dest_schema:
    default: ${var.schema}

resources:
  pipelines:
    # Ingestion Gateway - extracts CDC from source
    sqlserver_gateway:
      name: "[${bundle.target}] ${var.gateway_name}"
      gateway_definition:
        connection_name: ${var.connection_name}
        gateway_storage_catalog: ${var.staging_catalog}
        gateway_storage_schema: ${var.staging_schema}
        gateway_storage_name: ${var.gateway_name}
      target: ${var.staging_schema}
      catalog: ${var.staging_catalog}
      continuous: true  # Gateway must run continuously
      
    # Ingestion Pipeline - applies changes to target tables
    sqlserver_ingestion:
      name: "[${bundle.target}] ${var.pipeline_name}"
      ingestion_definition:
        ingestion_gateway_id: ${resources.pipelines.sqlserver_gateway.id}
        objects:
          # Ingest specific table
          - table:
              source_catalog: adventureworks
              source_schema: sales
              source_table: orders
              destination_catalog: ${var.dest_catalog}
              destination_schema: ${var.dest_schema}
              destination_table: orders
              # Optional: Enable SCD Type 2 history tracking
              table_configuration:
                scd_type: "2"
          
          # Ingest entire schema
          - schema:
              source_catalog: adventureworks
              source_schema: production
              destination_catalog: ${var.dest_catalog}
              destination_schema: ${var.dest_schema}
              # Optional: Apply SCD Type 2 to all tables in schema
              schema_configuration:
                scd_type: "2"
      target: ${var.dest_schema}
      catalog: ${var.dest_catalog}
      
  jobs:
    # Schedule the ingestion pipeline
    sqlserver_ingestion_job:
      name: "[${bundle.target}] SQL Server Ingestion Job"
      schedule:
        quartz_cron_expression: "0 0 * * * ?"  # Every hour
        timezone_id: "America/Los_Angeles"
      email_notifications:
        on_failure:
          - data-team@company.com
      tasks:
        - task_key: refresh_pipeline
          pipeline_task:
            pipeline_id: ${resources.pipelines.sqlserver_ingestion.id}
```

**Deploy**:

```bash
# Validate configuration
databricks bundle validate -t dev

# Deploy to dev
databricks bundle deploy -t dev

# Start the gateway (continuous)
databricks bundle run sqlserver_gateway -t dev

# Run the ingestion pipeline (scheduled by job)
databricks bundle run sqlserver_ingestion -t dev
```

### Option 3: Databricks CLI

**Best for**: Scripting, automation, one-off setups

```bash
# Set variables
export CONNECTION_NAME="sqlserver_source"
export GATEWAY_NAME="sqlserver_gateway"
export PIPELINE_NAME="sqlserver_ingestion_pipeline"
export STAGING_CATALOG="main"
export STAGING_SCHEMA="ingestion_staging"
export TARGET_CATALOG="analytics"
export TARGET_SCHEMA="sales"

# Get connection ID
CONNECTION_ID=$(databricks connections list --output json | \
  jq -r ".[] | select(.name==\"$CONNECTION_NAME\") | .connection_id")

# Create ingestion gateway
GATEWAY_OUTPUT=$(databricks pipelines create --json '{
  "name": "'"$GATEWAY_NAME"'",
  "gateway_definition": {
    "connection_id": "'"$CONNECTION_ID"'",
    "gateway_storage_catalog": "'"$STAGING_CATALOG"'",
    "gateway_storage_schema": "'"$STAGING_SCHEMA"'",
    "gateway_storage_name": "'"$GATEWAY_NAME"'"
  },
  "catalog": "'"$STAGING_CATALOG"'",
  "target": "'"$STAGING_SCHEMA"'",
  "continuous": true
}')

GATEWAY_ID=$(echo $GATEWAY_OUTPUT | jq -r '.pipeline_id')
echo "Created gateway: $GATEWAY_ID"

# Create ingestion pipeline
PIPELINE_OUTPUT=$(databricks pipelines create --json '{
  "name": "'"$PIPELINE_NAME"'",
  "ingestion_definition": {
    "ingestion_gateway_id": "'"$GATEWAY_ID"'",
    "objects": [
      {
        "table": {
          "source_catalog": "adventureworks",
          "source_schema": "sales",
          "source_table": "orders",
          "destination_catalog": "'"$TARGET_CATALOG"'",
          "destination_schema": "'"$TARGET_SCHEMA"'",
          "destination_table": "orders"
        }
      },
      {
        "schema": {
          "source_catalog": "adventureworks",
          "source_schema": "production",
          "destination_catalog": "'"$TARGET_CATALOG"'",
          "destination_schema": "'"$TARGET_SCHEMA"'"
        }
      }
    ]
  },
  "catalog": "'"$TARGET_CATALOG"'",
  "target": "'"$TARGET_SCHEMA"'"
}')

PIPELINE_ID=$(echo $PIPELINE_OUTPUT | jq -r '.pipeline_id')
echo "Created pipeline: $PIPELINE_ID"

# Start the gateway
databricks pipelines start --pipeline-id $GATEWAY_ID

# Run the ingestion pipeline
databricks pipelines start --pipeline-id $PIPELINE_ID
```

### Option 4: Python Notebook

**Best for**: Interactive development, experimentation

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Configuration
CONNECTION_NAME = "sqlserver_source"
GATEWAY_NAME = "sqlserver_gateway"
PIPELINE_NAME = "sqlserver_ingestion_pipeline"
STAGING_CATALOG = "main"
STAGING_SCHEMA = "ingestion_staging"
TARGET_CATALOG = "analytics"
TARGET_SCHEMA = "sales"

# Get connection
connections = [c for c in w.connections.list() if c.name == CONNECTION_NAME]
if not connections:
    raise ValueError(f"Connection '{CONNECTION_NAME}' not found")
connection_id = connections[0].connection_id

# Create gateway
gateway = w.pipelines.create(
    name=GATEWAY_NAME,
    gateway_definition={
        "connection_id": connection_id,
        "gateway_storage_catalog": STAGING_CATALOG,
        "gateway_storage_schema": STAGING_SCHEMA,
        "gateway_storage_name": GATEWAY_NAME
    },
    catalog=STAGING_CATALOG,
    target=STAGING_SCHEMA,
    continuous=True
)

print(f"Created gateway: {gateway.pipeline_id}")

# Create ingestion pipeline
pipeline = w.pipelines.create(
    name=PIPELINE_NAME,
    ingestion_definition={
        "ingestion_gateway_id": gateway.pipeline_id,
        "objects": [
            {
                "table": {
                    "source_catalog": "adventureworks",
                    "source_schema": "sales",
                    "source_table": "orders",
                    "destination_catalog": TARGET_CATALOG,
                    "destination_schema": TARGET_SCHEMA,
                    "destination_table": "orders"
                }
            },
            {
                "schema": {
                    "source_catalog": "adventureworks",
                    "source_schema": "production",
                    "destination_catalog": TARGET_CATALOG,
                    "destination_schema": TARGET_SCHEMA
                }
            }
        ]
    },
    catalog=TARGET_CATALOG,
    target=TARGET_SCHEMA
)

print(f"Created pipeline: {pipeline.pipeline_id}")

# Start gateway (continuous)
w.pipelines.start_update(pipeline_id=gateway.pipeline_id)

# Start ingestion pipeline
w.pipelines.start_update(pipeline_id=pipeline.pipeline_id)
```

---

## Common Patterns

### Pattern 1: Ingest Specific Tables

**Use case**: Select individual tables from source database

**DABs Configuration**:
```yaml
ingestion_definition:
  ingestion_gateway_id: ${resources.pipelines.gateway.id}
  objects:
    - table:
        source_catalog: source_db
        source_schema: schema1
        source_table: customers
        destination_catalog: ${var.catalog}
        destination_schema: ${var.schema}
        destination_table: customers
    
    - table:
        source_catalog: source_db
        source_schema: schema1
        source_table: orders
        destination_catalog: ${var.catalog}
        destination_schema: ${var.schema}
        destination_table: orders
```

### Pattern 2: Ingest Entire Schema

**Use case**: Replicate all tables in a source schema

**DABs Configuration**:
```yaml
ingestion_definition:
  ingestion_gateway_id: ${resources.pipelines.gateway.id}
  objects:
    - schema:
        source_catalog: source_db
        source_schema: analytics
        destination_catalog: ${var.catalog}
        destination_schema: ${var.schema}
        # Destination table names match source table names
```

### Pattern 3: Enable History Tracking (SCD Type 2)

**Use case**: Track historical changes for dimension tables

**DABs Configuration**:
```yaml
ingestion_definition:
  ingestion_gateway_id: ${resources.pipelines.gateway.id}
  objects:
    - table:
        source_catalog: source_db
        source_schema: hr
        source_table: employees
        destination_catalog: ${var.catalog}
        destination_schema: ${var.schema}
        destination_table: employees_history
        table_configuration:
          scd_type: "2"  # Enable SCD Type 2 tracking
    
    # Apply SCD Type 2 to all tables in schema
    - schema:
        source_catalog: source_db
        source_schema: dimensions
        destination_catalog: ${var.catalog}
        destination_schema: ${var.schema}
        schema_configuration:
          scd_type: "2"
```

**Result**: Tables automatically include `__START_AT` and `__END_AT` columns

**Querying SCD Type 2 tables**: See [scd-query-patterns.md](scd-query-patterns.md) for patterns to query current and historical data.

### Pattern 4: Custom Destination Table Names

**Use case**: Rename tables during ingestion (e.g., add prefixes, change naming conventions)

**DABs Configuration**:
```yaml
ingestion_definition:
  ingestion_gateway_id: ${resources.pipelines.gateway.id}
  objects:
    - table:
        source_catalog: source_db
        source_schema: sales
        source_table: SalesOrder  # PascalCase in source
        destination_catalog: ${var.catalog}
        destination_schema: ${var.schema}
        destination_table: sales_orders  # snake_case in destination
```

### Pattern 5: Multi-Environment Deployment

**Use case**: Deploy same pipeline to dev/staging/prod with different configurations

**Main databricks.yml**:
```yaml
bundle:
  name: lakeflow-ingestion

include:
  - resources/*.yml

variables:
  catalog:
    default: "dev_catalog"
  schema:
    default: "dev_schema"
  connection_name:
    default: "sqlserver_dev"

targets:
  dev:
    default: true
    mode: development
    workspace:
      profile: dev
    variables:
      catalog: "dev_catalog"
      schema: "dev_schema"
      connection_name: "sqlserver_dev"
  
  prod:
    mode: production
    workspace:
      profile: prod
    variables:
      catalog: "prod_catalog"
      schema: "prod_schema"
      connection_name: "sqlserver_prod"
```

**Deploy to environments**:
```bash
# Deploy to dev
databricks bundle deploy -t dev

# Deploy to prod
databricks bundle deploy -t prod
```

### Pattern 6: Select Columns to Ingest

**Use case**: Ingest only specific columns from source tables (reduce data transfer and storage)

**Note**: Column selection must be configured through the UI or via API after pipeline creation. DABs doesn't support inline column selection.

**Via UI**:
1. Create pipeline in UI
2. On **Source** page, expand table
3. Uncheck columns to exclude
4. Save pipeline

**Via Python SDK** (after pipeline creation):
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Update pipeline with column selection
w.pipelines.update(
    pipeline_id="<pipeline-id>",
    ingestion_definition={
        "ingestion_gateway_id": "<gateway-id>",
        "objects": [
            {
                "table": {
                    "source_catalog": "source_db",
                    "source_schema": "sales",
                    "source_table": "customers",
                    "destination_catalog": "analytics",
                    "destination_schema": "sales",
                    "destination_table": "customers",
                    "table_configuration": {
                        "primary_keys": ["customer_id"],
                        "columns": [
                            {"name": "customer_id"},
                            {"name": "customer_name"},
                            {"name": "email"},
                            # Only these columns will be ingested
                        ]
                    }
                }
            }
        ]
    }
)
```

---

## Scheduling and Operations

### Gateway Management

**Critical**: The ingestion gateway **must run continuously** to capture CDC changes from the source.

**Start gateway (continuous mode)**:
```bash
# Via CLI
databricks pipelines start --pipeline-id <gateway-id>

# Gateway runs indefinitely until stopped
```

**Monitor gateway**:
```bash
databricks pipelines get --pipeline-id <gateway-id>
```

### Pipeline Scheduling

Schedule the ingestion pipeline to apply staged changes to target tables:

**Option 1: Pipeline UI**:
1. Go to pipeline details page
2. Click **Schedule**
3. Set frequency (hourly, daily, custom cron)
4. Save schedule

**Option 2: DABs with Job**:
```yaml
resources:
  jobs:
    ingestion_refresh:
      name: "Lakeflow Ingestion Refresh"
      schedule:
        quartz_cron_expression: "0 */4 * * * ?"  # Every 4 hours
        timezone_id: "UTC"
      tasks:
        - task_key: refresh_pipeline
          pipeline_task:
            pipeline_id: ${resources.pipelines.ingestion_pipeline.id}
```

**Option 3: CLI**:
```bash
# Manual run
databricks pipelines start --pipeline-id <pipeline-id>

# Via scheduled job
databricks jobs create --json '{
  "name": "Lakeflow Ingestion Job",
  "schedule": {
    "quartz_cron_expression": "0 0 * * * ?",
    "timezone_id": "UTC"
  },
  "tasks": [{
    "task_key": "refresh",
    "pipeline_task": {"pipeline_id": "<pipeline-id>"}
  }]
}'
```

### Monitoring and Alerts

**Set email notifications**:

Via DABs:
```yaml
resources:
  jobs:
    ingestion_job:
      name: "Ingestion Job"
      email_notifications:
        on_start: []
        on_success:
          - success@company.com
        on_failure:
          - alerts@company.com
        no_alert_for_skipped_runs: false
```

**Monitor pipeline status**:
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Get latest pipeline update
updates = w.pipelines.list_updates(pipeline_id="<pipeline-id>")
latest = list(updates)[0]

print(f"State: {latest.update.state}")
print(f"Records processed: {latest.update.num_records_processed}")
```

### Verify Data Ingestion

**Check destination tables**:
```sql
-- View ingested data
SELECT * FROM analytics.sales.orders LIMIT 100;

-- Check record counts
SELECT COUNT(*) FROM analytics.sales.orders;

-- Verify CDC captured changes
SELECT * FROM analytics.sales.orders 
WHERE _change_type IN ('INSERT', 'UPDATE', 'DELETE')
ORDER BY _commit_timestamp DESC
LIMIT 100;
```

**Monitor pipeline progress** in UI:
1. Navigate to **Pipelines** in workspace
2. Click pipeline name
3. View **Upserted records** and **Deleted records** columns (enable in column configuration if not visible)

---

## Best Practices

### 1. Gateway Must Run Continuously

**✅ Correct**:
- Start gateway and leave it running
- Gateway continuously extracts CDC changes
- Prevents missing changes due to source CDC retention policies

**❌ Incorrect**:
- Running gateway on schedule (will miss CDC changes)
- Stopping/starting gateway frequently

### 2. Separate Staging and Destination

**Recommended**:
```yaml
gateway_definition:
  gateway_storage_catalog: "ingestion_staging"  # Dedicated staging catalog
  gateway_storage_schema: "staging"

ingestion_definition:
  catalog: "analytics"  # Separate destination catalog
  target: "sales"
```

**Benefits**:
- Isolate staging data from business-facing tables
- Easier to manage permissions and lifecycle
- Can use same staging for multiple pipelines

### 3. Use DABs for Production

**Benefits**:
- Multi-environment deployment (dev/staging/prod)
- Version control with Git
- Automated CI/CD integration
- Consistent configuration across environments

### 4. Monitor Gateway Health

**Set up alerts** for gateway failures:
```yaml
resources:
  jobs:
    gateway_monitor:
      name: "Gateway Health Monitor"
      schedule:
        quartz_cron_expression: "0 */15 * * * ?"  # Every 15 min
      email_notifications:
        on_failure:
          - oncall@company.com
      tasks:
        - task_key: check_gateway
          notebook_task:
            notebook_path: ../src/monitoring/check_gateway_health.py
```

### 5. Use SCD Type 2 for Dimensions

**When to use**:
- Dimension tables that change over time
- Need to track historical values
- Reporting on data as it was at a point in time

**Configuration**:
```yaml
table_configuration:
  scd_type: "2"
```

**Querying**: See [scd-query-patterns.md](scd-query-patterns.md)

### 6. Source Database Configuration

**SQL Server requirements**:
- Enable Change Tracking on database and tables
- Grant `VIEW CHANGE TRACKING` permission to service account
- Set appropriate retention period (consider pipeline frequency)

**Example**:
```sql
-- Enable Change Tracking on database
ALTER DATABASE AdventureWorks
SET CHANGE_TRACKING = ON
(CHANGE_RETENTION = 7 DAYS, AUTO_CLEANUP = ON);

-- Enable Change Tracking on table
ALTER TABLE Sales.Orders
ENABLE CHANGE_TRACKING;

-- Grant permissions
GRANT VIEW CHANGE TRACKING ON DATABASE::AdventureWorks TO [service_account];
```

---

## Common Issues and Troubleshooting

### Issue: Gateway fails to start

**Causes**:
- Connection credentials invalid
- Source database unreachable
- CDC not enabled on source

**Solutions**:
1. Test connection in Catalog Explorer
2. Verify network connectivity (VPN, firewall rules)
3. Check CDC enabled on source database
4. Review gateway logs in pipeline UI

### Issue: Pipeline shows no data ingested

**Causes**:
- Gateway not running
- No changes in source since last run
- Table selection incorrect

**Solutions**:
1. Verify gateway is running continuously
2. Check gateway staging volume has data
3. Verify source table names match exactly (case-sensitive)

### Issue: Missing CDC changes

**Causes**:
- Gateway stopped for extended period
- Source CDC retention period expired
- Gateway checkpoint lost

**Solutions**:
1. Keep gateway running continuously
2. Increase source CDC retention period
3. If checkpoint lost, perform full refresh

### Issue: SCD Type 2 not creating history

**Causes**:
- `scd_type` not configured
- Source doesn't support CDC
- No changes detected

**Solutions**:
1. Verify `table_configuration.scd_type: "2"` is set
2. Check source has CDC enabled
3. Make test change in source and verify

### Issue: High latency in data ingestion

**Causes**:
- Gateway processing slow
- Pipeline refresh infrequent
- Large data volumes

**Solutions**:
1. Check gateway compute is running
2. Increase pipeline refresh frequency
3. Consider partitioning strategy
4. Review source query performance

---

## Integration with Other Skills

### Use with dabs-writer

**See**: `.claude/skills/dabs-writer/SDP_guidance.md` for Lakeflow Connect DABs patterns

Key integration points:
- Gateway and pipeline as bundle resources
- Multi-environment variable configuration
- Job scheduling for pipeline refresh

### Use with sdp-writer

After ingestion via Lakeflow Connect, apply downstream transformations:

**Bronze (Lakeflow Connect)** → **Silver (SDP Transformations)** → **Gold (Aggregations)**

Example:
```sql
-- Bronze: Ingested via Lakeflow Connect
-- (no code needed, managed by Lakeflow Connect)

-- Silver: Cleanse and enrich
CREATE OR REPLACE STREAMING TABLE silver_orders AS
SELECT
  order_id,
  customer_id,
  order_date,
  CAST(total_amount AS DECIMAL(18,2)) AS total_amount,
  CASE 
    WHEN status = 'C' THEN 'Completed'
    WHEN status = 'P' THEN 'Pending'
    ELSE 'Unknown'
  END AS status_description
FROM STREAM catalog.schema.orders  -- Bronze table from Lakeflow Connect
WHERE order_id IS NOT NULL;

-- Gold: Aggregate
CREATE OR REFRESH MATERIALIZED VIEW gold_daily_sales AS
SELECT
  DATE(order_date) AS sale_date,
  COUNT(DISTINCT order_id) AS order_count,
  SUM(total_amount) AS total_sales
FROM catalog.schema.silver_orders
GROUP BY DATE(order_date);
```

---

## Resources

- [Lakeflow Connect Documentation](https://docs.databricks.com/ingestion/lakeflow-connect/)
- [SQL Server Connector Guide](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sql-server-pipeline)
- [Unity Catalog Connections](https://docs.databricks.com/data-governance/unity-catalog/connect-to-data-sources.html)
- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/)
- [SCD Query Patterns](scd-query-patterns.md)
- [Traditional Ingestion Patterns](ingestion-patterns.md)
