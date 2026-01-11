# Patient Readmission DAB - Deployment Guide

## Pre-Deployment Checklist

- [ ] Databricks CLI installed and authenticated
- [ ] Unity Catalog `chn_etl_demo_catalog` exists
- [ ] User has appropriate permissions
- [ ] SQL Warehouse identified (or using serverless)

## Step 1: Create Catalog (if needed)

```sql
-- Run in Databricks SQL Editor or Notebook
CREATE CATALOG IF NOT EXISTS chn_etl_demo_catalog
COMMENT 'CHN ETL Demo - Main catalog for all projects';

-- Grant permissions
GRANT CREATE SCHEMA ON CATALOG chn_etl_demo_catalog TO `your_user@databricks.com`;
GRANT USE CATALOG ON CATALOG chn_etl_demo_catalog TO `your_user@databricks.com`;
```

## Step 2: Validate Bundle

```bash
cd /Users/justin.ward/chn/dabs/patient-readmission

# Check configuration
databricks bundle validate -t dev

# Expected output:
# ✓ Configuration valid
# ✓ All resources defined
# ✓ Dependencies resolved
```

## Step 3: Deploy to Development

```bash
# Deploy bundle (creates schema, volume, job, dashboard)
databricks bundle deploy -t dev --force-lock

# Expected resources created:
# - Schema: chn_etl_demo_catalog.patient_readmission_dev
# - Volume: chn_etl_demo_catalog.patient_readmission_dev.raw_data
# - Job: [dev] Patient Readmission Pipeline
# - Dashboard: [dev] ER Staffing, Access, Quality & Financial Risk
```

## Step 4: Run the Pipeline

```bash
# Option 1: Via CLI
databricks bundle run patient_readmission_pipeline -t dev

# Option 2: Via Databricks UI
# 1. Navigate to Workflows
# 2. Find "[dev] Patient Readmission Pipeline"
# 3. Click "Run Now"
```

## Step 5: Monitor Execution

### Check Job Status

```bash
# Get job ID from deployment output
export JOB_ID=<your_job_id>

# Monitor run
databricks jobs list-runs --job-id $JOB_ID --limit 1
```

### Expected Timeline

| Task | Duration | Status Indicators |
|------|----------|-------------------|
| Generate Data | 5-8 min | Creating ~312K records |
| SQL Transformations | 3-5 min | Creating 11 silver + 6 gold tables |
| Deploy Resources | 2-3 min | Creating Genie space |
| **Total** | **10-16 min** | |

## Step 6: Verify Deployment

### Check Tables

```sql
-- List all tables
SHOW TABLES IN chn_etl_demo_catalog.patient_readmission_dev;

-- Expected tables:
-- Bronze (5): raw_emr_er_visits, raw_hr_shifts_and_sickleave, raw_patient_flow_metrics, 
--             raw_patient_satisfaction_surveys, raw_readmission_risk_feed
-- Silver (5): silver_emr_er_visits, silver_hr_shifts_and_sickleave, silver_patient_flow_metrics,
--             silver_patient_satisfaction_surveys, silver_readmission_risk_feed  
-- Gold (6): gold_er_operational_hourly, gold_er_quality_daily, gold_er_staffing_daily,
--           gold_er_finance_daily, gold_er_readmission_risk_daily, gold_global_filters_bridge
```

### Sample Queries

```sql
-- Check data volume
SELECT 
  'raw_emr_er_visits' as table_name,
  COUNT(*) as row_count 
FROM chn_etl_demo_catalog.patient_readmission_dev.raw_emr_er_visits
UNION ALL
SELECT 
  'gold_er_quality_daily',
  COUNT(*) 
FROM chn_etl_demo_catalog.patient_readmission_dev.gold_er_quality_daily;

-- View quality metrics
SELECT 
  site,
  date,
  is_weekend,
  visits_total,
  lwbs_rate,
  median_triage_wait_minutes,
  median_door_to_provider_minutes
FROM chn_etl_demo_catalog.patient_readmission_dev.gold_er_quality_daily
WHERE date BETWEEN '2025-09-01' AND '2025-09-30'
ORDER BY lwbs_rate DESC
LIMIT 10;
```

### Check Genie Space

```sql
-- List Genie spaces
SELECT * FROM system.ai.genie_spaces
WHERE display_name LIKE '%ER Staffing%';

-- Navigate to Genie UI:
-- Databricks UI → Genie → Find "ER Staffing, Access, Quality & Financial Risk"
```

### Check Dashboard

```
Navigate to: Workspace → /Users/your_user/chn_etl_demo/dashboards/
Find: [dev] ER Staffing, Access, Quality & Financial Risk
```

## Troubleshooting

### Error: Catalog doesn't exist

```sql
-- Create catalog manually
CREATE CATALOG IF NOT EXISTS chn_etl_demo_catalog;
```

### Error: Permission denied

```sql
-- Grant appropriate permissions
GRANT USE CATALOG ON CATALOG chn_etl_demo_catalog TO `your_user`;
GRANT CREATE SCHEMA ON CATALOG chn_etl_demo_catalog TO `your_user`;
```

### Error: Warehouse not found

Update `databricks.yml`:
```yaml
variables:
  warehouse_name:
    default: "Your Warehouse Name"  # Update this
```

Or set the warehouse_id directly:
```yaml
variables:
  warehouse_id:
    default: "abc123def456"  # Your warehouse ID
```

### Error: Task fails with "Module not found"

Check library installation in job cluster configuration. The DAB should auto-install:
- `faker>=19.0.0`
- `databricks-sdk>=0.18.0`
- `pandas>=2.0.0`

## Production Deployment (After Dev Validation)

```bash
# Deploy to production
databricks bundle deploy -t prod

# This creates:
# - Schema: chn_etl_demo_catalog.patient_readmission_prod
# - Separate job and dashboard with [prod] prefix
```

## Next Steps

1. ✅ Explore the Lakeview dashboard
2. ✅ Try natural language queries in Genie
3. ✅ Review gold layer tables for business insights
4. ✅ Schedule the job for regular runs
5. ✅ Set up alerting on key metrics

## Rollback Procedure

If you need to rollback:

```bash
# Destroy deployed resources
databricks bundle destroy -t dev

# This will:
# - Delete the job
# - Delete the dashboard  
# - Keep the data (tables remain)

# To also delete data:
DROP SCHEMA IF EXISTS chn_etl_demo_catalog.patient_readmission_dev CASCADE;
```

## Support

- DAB Documentation: https://docs.databricks.com/dev-tools/bundles/
- Unity Catalog: https://docs.databricks.com/data-governance/unity-catalog/
- Project README: See `dabs/patient-readmission/README.md`
