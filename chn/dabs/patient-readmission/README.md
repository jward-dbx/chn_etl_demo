# Patient Readmission Analysis - Databricks Asset Bundle

**Enterprise-grade data pipeline for ER patient readmission analysis and risk monitoring**

## Overview

This Databricks Asset Bundle (DAB) implements an end-to-end data pipeline for analyzing emergency room patient readmissions, staffing patterns, quality metrics, and financial risk. The pipeline follows medallion architecture (Bronze → Silver → Gold) and includes:

- **Synthetic data generation** using Faker for realistic ER visit scenarios
- **SQL transformations** creating silver (cleaned) and gold (aggregated) layers
- **AI resources** including Genie spaces for natural language queries
- **Lakeview dashboards** for executive monitoring

## Architecture

### Directory Structure

```
dabs/patient-readmission/
├── databricks.yml              # Main DAB configuration
├── config/                     # Environment-specific configs
├── src/                        # Source code
│   ├── generate_data.py       # Synthetic data generation
│   ├── transformations.sql    # Medallion SQL transformations
│   ├── deploy_resources.py    # Deploy Genie/dashboards
│   ├── agent_bricks_service.py # Agent management utilities
│   ├── utils.py               # Helper functions
│   ├── bricks_conf.json       # Agent brick configurations
│   └── dashboard_*.lvdash.json # Dashboard definitions
├── resources/                  # Additional resources
└── README.md                   # This file
```

### Data Model

**Bronze Layer (Raw):**
- `raw_emr_er_visits` - ER visit records
- `raw_hr_shifts_and_sickleave` - Staffing schedules
- `raw_patient_flow_metrics` - Flow telemetry
- `raw_patient_satisfaction_surveys` - Survey responses
- `raw_readmission_risk_feed` - ML predictions

**Silver Layer (Cleaned):**
- `silver_emr_er_visits` - Cleaned visits with derived fields
- `silver_hr_shifts_and_sickleave` - Processed staffing data
- `silver_patient_flow_metrics` - Telemetry with smoothing
- `silver_patient_satisfaction_surveys` - Aligned surveys
- `silver_readmission_risk_feed` - Risk scores with lags

**Gold Layer (Aggregated):**
- `gold_er_operational_hourly` - Hourly operations KPIs
- `gold_er_quality_daily` - Daily quality metrics
- `gold_er_staffing_daily` - Daily staffing analysis
- `gold_er_finance_daily` - Financial impact tracking
- `gold_er_readmission_risk_daily` - Risk aggregations
- `gold_global_filters_bridge` - Dashboard filters

## Prerequisites

1. **Databricks Workspace** with Unity Catalog enabled
2. **Databricks CLI** installed (`pip install databricks-cli`)
3. **Permissions:**
   - Unity Catalog: CREATE CATALOG, CREATE SCHEMA
   - Compute: CREATE CLUSTER
   - Workspace: CREATE JOB, CREATE DASHBOARD

## Configuration

### Environment Variables

The bundle uses environment-aware configuration:

| Variable | Description | Dev Default | Prod Default |
|----------|-------------|-------------|--------------|
| `CATALOG` | Unity Catalog name | `chn_etl_demo_catalog` | `chn_etl_demo_catalog` |
| `SCHEMA` | Schema name | `patient_readmission_dev` | `patient_readmission_prod` |
| `VOLUME` | Volume name for raw data | `raw_data` | `raw_data` |
| `ENVIRONMENT` | Deployment environment | `dev` | `prod` |

### Workspace Configuration

Update `databricks.yml` with your workspace details:

```yaml
targets:
  dev:
    workspace:
      host: https://your-workspace.cloud.databricks.com
```

## Deployment

### Quick Start

```bash
# Navigate to the DAB directory
cd dabs/patient-readmission

# Validate configuration
databricks bundle validate

# Deploy to development
databricks bundle deploy -t dev

# Run the pipeline
databricks bundle run patient_readmission_pipeline -t dev
```

### Step-by-Step Deployment

#### 1. Validate Bundle

```bash
databricks bundle validate -t dev
```

This checks:
- YAML syntax
- Resource dependencies
- Variable substitutions
- Workspace connectivity

#### 2. Deploy Resources

```bash
databricks bundle deploy -t dev
```

This creates:
- Unity Catalog schema: `chn_etl_demo_catalog.patient_readmission_dev`
- Managed volume: `raw_data`
- Workflow job: `[dev] Patient Readmission Pipeline`
- Dashboard: `[dev] ER Staffing, Access, Quality & Financial Risk`

#### 3. Run Pipeline

```bash
# Run the full pipeline
databricks bundle run patient_readmission_pipeline -t dev

# Or run via Databricks UI
# Navigate to Workflows → [dev] Patient Readmission Pipeline → Run Now
```

#### 4. Verify Deployment

```sql
-- Check catalog and schema
SHOW SCHEMAS IN chn_etl_demo_catalog;

-- Verify tables were created
SHOW TABLES IN chn_etl_demo_catalog.patient_readmission_dev;

-- Sample data
SELECT * FROM chn_etl_demo_catalog.patient_readmission_dev.gold_er_quality_daily
LIMIT 10;
```

## Production Deployment

### Differences from Development

Production deployments include:
- Separate schema: `patient_readmission_prod`
- Enhanced permissions and access controls
- Audit logging
- Scheduled job runs

### Deploy to Production

```bash
# Deploy production resources
databricks bundle deploy -t prod

# Schedule the pipeline (example: daily at 2 AM)
databricks jobs reset --json '{
  "job_id": <job_id>,
  "new_settings": {
    "schedule": {
      "quartz_cron_expression": "0 0 2 * * ?",
      "timezone_id": "America/New_York"
    }
  }
}'
```

## Pipeline Tasks

### Task 1: Generate Data

**File:** `src/generate_data.py`

Generates ~312,000 synthetic ER visit records with realistic patterns:
- Weekend surge scenarios (Sep 2025)
- Staffing patterns and sick leave
- Patient flow metrics
- Satisfaction surveys
- Readmission risk predictions

**Output:** Parquet files in Unity Catalog Volume, auto-created as Delta tables

### Task 2: SQL Transformations

**File:** `src/transformations.sql`

Executes medallion architecture transformations:
1. **Silver layer:** Clean and standardize raw data
2. **Gold layer:** Create aggregated KPIs and metrics

**Compute:** SQL Warehouse (serverless recommended)

### Task 3: Deploy Resources

**File:** `src/deploy_resources.py`

Deploys AI-powered resources:
- Genie spaces for natural language querying
- Sample questions and SQL instructions
- Dashboard links

## Monitoring & Troubleshooting

### Check Job Status

```bash
# List recent runs
databricks jobs list-runs --job-id <job_id> --limit 5

# Get run details
databricks jobs get-run --run-id <run_id>
```

### Common Issues

#### Issue: Schema doesn't exist
**Solution:** Ensure catalog was created (DAB doesn't create catalogs)
```sql
CREATE CATALOG IF NOT EXISTS chn_etl_demo_catalog;
```

#### Issue: Permission denied
**Solution:** Grant appropriate Unity Catalog permissions
```sql
GRANT CREATE SCHEMA ON CATALOG chn_etl_demo_catalog TO `your_user`;
```

#### Issue: SQL transformation fails
**Solution:** Check that data generation completed successfully
```sql
SELECT COUNT(*) FROM chn_etl_demo_catalog.patient_readmission_dev.raw_emr_er_visits;
```

## Scaling Best Practices

### For Multiple Projects

This DAB structure supports multiple parallel projects:

```
dabs/
├── patient-readmission/
├── claims-processing/
├── clinical-trials/
└── shared-utilities/
```

Each project:
- Has its own schema
- Shares the same catalog
- Uses consistent naming conventions
- Follows the same directory structure

### Environment Promotion

Promote changes through environments:

```bash
# 1. Develop and test in dev
databricks bundle deploy -t dev
databricks bundle run patient_readmission_pipeline -t dev

# 2. Deploy to production after validation
databricks bundle deploy -t prod
```

### CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Deploy DAB
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Production
        run: |
          databricks bundle deploy -t prod
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
```

## Resources

- [Databricks Asset Bundles Documentation](https://docs.databricks.com/dev-tools/bundles/)
- [Unity Catalog Best Practices](https://docs.databricks.com/data-governance/unity-catalog/best-practices.html)
- [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Databricks bundle logs
3. Contact your Databricks workspace administrator

---

**Generated by CHN ETL Demo Project**  
**Last Updated:** 2026-01-11
