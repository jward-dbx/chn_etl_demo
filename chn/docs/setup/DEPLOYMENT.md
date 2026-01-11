# OMOP Semantic Layer - Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the complete OMOP Semantic Layer infrastructure to Databricks.

## Architecture

The OMOP Semantic Layer consists of three main components:

```
┌─────────────────────────────────────────────────────────────┐
│                  OMOP SEMANTIC LAYER                        │
└─────────────────────────────────────────────────────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
    ┌──────────┐      ┌──────────────┐    ┌──────────┐
    │ Snowflake│      │    Metric    │    │  Genie   │
    │Connection│ ───▶ │    Views     │───▶│  Space   │
    │& Catalog │      │  (7 views)   │    │   (NL)   │
    └──────────┘      └──────────────┘    └──────────┘
    Terraform         DABs / SQL          Python API
```

### Component 1: Snowflake Connection
- **Technology**: Terraform
- **Purpose**: Unity Catalog connection to Snowflake OMOP database
- **Output**: Foreign catalog with OMOP CDM tables

### Component 2: Semantic Layer Metric Views
- **Technology**: Databricks Asset Bundles (DABs) or SQL
- **Purpose**: 7 metric views for analytics over OMOP data
- **Output**: Views in Unity Catalog schema

### Component 3: Genie Space
- **Technology**: Python + Databricks API
- **Purpose**: Natural language interface to query metric views
- **Output**: Genie Space with sample questions and instructions

## Prerequisites

### Required Tools

```bash
# 1. Terraform
brew install terraform
# or
curl -fsSL https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_darwin_amd64.zip -o terraform.zip
unzip terraform.zip && sudo mv terraform /usr/local/bin/

# 2. Databricks CLI
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh

# 3. Python 3 with requests
pip3 install requests
```

### Required Credentials

1. **Databricks Workspace**
   - Workspace URL
   - Personal Access Token

2. **Snowflake**
   - Account URL
   - Username
   - Password
   - Warehouse name
   - Role

3. **SQL Warehouse**
   - SQL Warehouse ID (for Genie Space)

## Quick Start

### One-Command Deployment

```bash
# Deploy everything to dev environment
./deploy.sh --env dev --component all
```

### Component-by-Component Deployment

```bash
# 1. Deploy Snowflake connection only
./deploy.sh --env dev --component connection

# 2. Deploy metric views only
./deploy.sh --env dev --component views

# 3. Deploy Genie Space only
./deploy.sh --env dev --component genie
```

## Detailed Deployment Steps

### Step 1: Configure Environment

Create environment-specific configuration:

```bash
# Create dev environment config
mkdir -p config/dev
cat > config/dev/.env << 'EOF'
# Databricks
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."

# Snowflake Connection
export SNOWFLAKE_HOST="account.region.snowflakecomputing.com"
export SNOWFLAKE_USERNAME="your_username"
export SNOWFLAKE_PASSWORD="your_password"
export SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
export SNOWFLAKE_ROLE="ICEBERG_READER"

# Target Catalogs
export SOURCE_CATALOG="conn_sf_cursor_ward_catalog"
export TARGET_CATALOG="serverless_rde85f_catalog"
export TARGET_SCHEMA="semantic_omop_cursor"

# Genie Space
export GENIE_WAREHOUSE_ID="your_warehouse_id"
EOF
```

### Step 2: Deploy Snowflake Connection

**Using Terraform:**

```bash
cd deployment/terraform/connections

# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Apply configuration
terraform apply

# Verify
terraform show
```

**What Gets Created:**
- Unity Catalog connection: `conn_sf_cursor_ward`
- Foreign catalog: `conn_sf_cursor_ward_catalog`
- Access to Snowflake OMOP database

### Step 3: Deploy Metric Views

**Option A: Databricks Asset Bundles (Recommended)**

```bash
cd deployment/dabs/semantic_layer

# Validate bundle
databricks bundle validate --target dev

# Deploy resources (creates job and warehouse)
databricks bundle deploy --target dev

# Run deployment job
databricks bundle run deploy_metric_views --target dev
```

**Option B: Manual SQL Deployment**

1. Open Databricks SQL Editor
2. Copy contents of `sql/ddl/deploy_metric_views.sql`
3. Update variables at the top:
   ```sql
   CREATE WIDGET TEXT source_catalog DEFAULT 'conn_sf_cursor_ward_catalog';
   CREATE WIDGET TEXT target_catalog DEFAULT 'serverless_rde85f_catalog';
   CREATE WIDGET TEXT target_schema DEFAULT 'semantic_omop_cursor';
   ```
4. Execute the SQL

**What Gets Created:**
- 7 metric views in `serverless_rde85f_catalog.semantic_omop_cursor`:
  - `patient_population_metrics`
  - `clinical_encounter_metrics`
  - `condition_metrics`
  - `lab_vitals_metrics`
  - `medication_utilization_metrics`
  - `procedure_utilization_metrics`
  - `provider_performance_metrics`

### Step 4: Deploy Genie Space

```bash
cd resources/genie

# Set credentials
export DATABRICKS_TOKEN="dapi..."

# Deploy
python3 deploy_genie_space.py \
  --name "OMOP Semantic Layer" \
  --warehouse-id "your_warehouse_id"
```

**What Gets Created:**
- Genie Space with:
  - 7 metric views configured
  - 13 sample questions
  - 8 example SQL queries
  - Healthcare terminology instructions

## Verification

### 1. Verify Snowflake Connection

```sql
-- List catalogs
SHOW CATALOGS LIKE 'conn_sf_cursor_ward_catalog';

-- List schemas
SHOW SCHEMAS IN conn_sf_cursor_ward_catalog;

-- List tables
SHOW TABLES IN conn_sf_cursor_ward_catalog.OMOP;
```

### 2. Verify Metric Views

```sql
-- List views
SHOW VIEWS IN serverless_rde85f_catalog.semantic_omop_cursor;

-- Test a view (remember: use MEASURE() for aggregations)
SELECT 
  Gender,
  MEASURE(`Total Patients`) as patient_count
FROM serverless_rde85f_catalog.semantic_omop_cursor.patient_population_metrics
GROUP BY Gender;
```

### 3. Verify Genie Space

1. Navigate to the Genie Space URL (provided in deployment output)
2. Try a sample question: "How many patients do we have by age group?"
3. Verify SQL is generated correctly
4. Check results are returned

## Troubleshooting

### Common Issues

#### 1. Terraform: Connection Failed

**Error**: `Incorrect username or password was specified`

**Solution**:
- Verify credentials in `terraform.tfvars`
- Ensure password includes special characters (e.g., `!`)
- Test Snowflake login directly

#### 2. Metric Views: Cannot Create via API

**Error**: `table_type must be EXTERNAL`

**Solution**:
- Metric views require Unity Catalog compute
- Use DABs or SQL Editor (not API)
- Cannot be created via `curl` or Python requests

#### 3. Genie Space: Metric Views Not Found

**Error**: `Table does not exist`

**Solution**:
- Ensure metric views are created first (Step 3)
- Verify catalog/schema names match in Genie config
- Check warehouse has access to the views

#### 4. DABs: Warehouse ID Required

**Error**: `warehouse_id is required`

**Solution**:
- Get warehouse ID: `databricks sql warehouses list`
- Update `databricks.yml` with the ID
- Or let bundle create serverless warehouse

### Debugging Commands

```bash
# Check Terraform state
cd deployment/terraform/connections
terraform state list
terraform state show databricks_connection.snowflake

# Check DABs deployment
cd deployment/dabs/semantic_layer
databricks bundle summary --target dev

# Check Genie Space
curl -H "Authorization: Bearer $DATABRICKS_TOKEN" \
  "https://[workspace]/api/2.0/genie/spaces"

# Check metric views via API
curl -H "Authorization: Bearer $DATABRICKS_TOKEN" \
  "https://[workspace]/api/2.1/unity-catalog/tables?catalog_name=serverless_rde85f_catalog&schema_name=semantic_omop_cursor"
```

## Environment Management

### Development Environment

```bash
./deploy.sh --env dev --component all
```

- Uses `config/dev/.env`
- Deploys to dev workspace
- Names include `[dev]` prefix

### Production Environment

```bash
./deploy.sh --env prod --component all
```

- Uses `config/prod/.env`
- Deploys to prod workspace
- Names include `[prod]` prefix
- Requires additional approvals

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy OMOP Semantic Layer

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        default: 'dev'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
      
      - name: Setup Databricks CLI
        run: |
          curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
      
      - name: Configure Credentials
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: |
          databricks configure --host "$DATABRICKS_HOST" --token "$DATABRICKS_TOKEN"
      
      - name: Deploy
        env:
          TF_VAR_databricks_token: ${{ secrets.DATABRICKS_TOKEN }}
          TF_VAR_snowflake_password: ${{ secrets.SNOWFLAKE_PASSWORD }}
        run: |
          ./deploy.sh --env ${{ github.event.inputs.environment || 'dev' }} --component all
```

## Rollback Procedures

### Rollback Connection

```bash
cd deployment/terraform/connections
terraform destroy
```

### Rollback Metric Views

```sql
USE CATALOG serverless_rde85f_catalog;
USE SCHEMA semantic_omop_cursor;

-- Drop all views
DROP VIEW IF EXISTS patient_population_metrics;
DROP VIEW IF EXISTS clinical_encounter_metrics;
DROP VIEW IF EXISTS condition_metrics;
DROP VIEW IF EXISTS lab_vitals_metrics;
DROP VIEW IF EXISTS medication_utilization_metrics;
DROP VIEW IF EXISTS procedure_utilization_metrics;
DROP VIEW IF EXISTS provider_performance_metrics;
```

### Rollback Genie Space

```bash
# Get space ID
databricks api GET /api/2.0/genie/spaces

# Delete space
databricks api DELETE /api/2.0/genie/spaces/[SPACE_ID]
```

## Security Best Practices

1. **Never commit credentials**
   - Use `.env` files (git-ignored)
   - Use environment variables
   - Use secret management systems

2. **Use service principals for prod**
   - Create dedicated service principal
   - Grant minimal permissions
   - Rotate credentials regularly

3. **Encrypt sensitive data**
   - Use Databricks secrets for tokens
   - Terraform backend encryption
   - Transit encryption for Snowflake

4. **Audit deployments**
   - Log all deployments
   - Track who deployed what
   - Review changes before applying

## Cost Optimization

### Serverless SQL Warehouse

- Auto-stops after 10 minutes
- Pay-per-query pricing
- No idle costs

### Metric Views

- No storage cost (views, not tables)
- Query cost only when accessed
- Cache results when possible

### Terraform State

- Use remote backend
- Enable state locking
- Regular state cleanup

## Next Steps

After successful deployment:

1. **Test Queries**
   - Run sample queries on metric views
   - Verify data accuracy
   - Check performance

2. **Configure Alerts**
   - Set up failure notifications
   - Monitor query performance
   - Track usage metrics

3. **Documentation**
   - Document custom configurations
   - Create runbooks for common tasks
   - Train team on Genie Space usage

4. **Iterate**
   - Add more metric views as needed
   - Enhance Genie Space instructions
   - Optimize query performance

## Support

For issues or questions:

- **Documentation**: See `docs/` directory
- **Recipes**: See `docs/recipes/` for specific tasks
- **API Examples**: See `docs/api-examples/`
- **GitHub Issues**: Submit bug reports/feature requests

---

**Last Updated**: January 11, 2026  
**Version**: 1.0.0  
**Maintainer**: OMOP Semantic Layer Team
