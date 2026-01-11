# Patient Readmission DAB - Manual Deployment Instructions

## ✅ What I've Already Done

I've successfully created the Unity Catalog structures via API:

```
✓ Schema: chn_etl_demo_catalog.patient_readmission_dev
✓ Volume: chn_etl_demo_catalog.patient_readmission_dev.raw_data
```

## 🚀 Complete the Deployment (2 Options)

### Option 1: Install Databricks CLI and Deploy (Recommended)

This is the cleanest approach using the Databricks Asset Bundle:

```bash
# 1. Install Databricks CLI
pip install databricks-cli

# 2. Configure with your workspace
databricks configure --host https://fe-sandbox-chn-etl-demo.cloud.databricks.com
# When prompted, enter your Databricks token

# 3. Navigate to the DAB directory
cd /Users/justin.ward/chn/dabs/patient-readmission

# 4. Deploy the bundle
databricks bundle deploy -t dev --force-lock

# 5. Run the pipeline
databricks bundle run patient_readmission_pipeline -t dev
```

**Timeline:** ~15-20 minutes total (10-16 min for pipeline execution)

### Option 2: Manual Deployment via Databricks UI

If you prefer not to install the CLI, you can deploy manually:

#### Step 1: Import Source Files to Workspace

1. Navigate to https://fe-sandbox-chn-etl-demo.cloud.databricks.com
2. Go to **Workspace** → Create folder `/Users/justin.ward@databricks.com/chn_etl_demo/patient_readmission`
3. Upload these files from `/Users/justin.ward/chn/dabs/patient-readmission/src/`:
   - `generate_data.py`
   - `transformations.sql`
   - `deploy_resources.py`
   - `agent_bricks_service.py`
   - `utils.py`
   - `bricks_conf.json`
   - `dashboard_lakeview_er_staffing_quality.lvdash.json`

#### Step 2: Create and Run Workflow

1. Go to **Workflows** → **Create Job**
2. Name: `[dev] Patient Readmission Pipeline`

**Task 1 - Generate Data:**
- Type: Python script
- Source file: `/Users/justin.ward@databricks.com/chn_etl_demo/patient_readmission/generate_data.py`
- Cluster:
  - Spark Version: 14.3.x LTS
  - Node type: i3.xlarge (or similar)
  - Workers: 2
- Libraries: `faker>=19.0.0`, `pandas>=2.0.0`, `numpy>=1.24.0`
- Environment variables:
  ```
  CATALOG=chn_etl_demo_catalog
  SCHEMA=patient_readmission_dev
  VOLUME=raw_data
  ```

**Task 2 - SQL Transformations:**
- Type: SQL
- Warehouse: Serverless Starter Warehouse
- Source file: `/Users/justin.ward@databricks.com/chn_etl_demo/patient_readmission/transformations.sql`
- **Important:** Before running, replace all `${catalog}` with `chn_etl_demo_catalog` and `${schema}` with `patient_readmission_dev` in the SQL file

**Task 3 - Deploy Resources:**
- Type: Python script
- Source file: `/Users/justin.ward@databricks.com/chn_etl_demo/patient_readmission/deploy_resources.py`
- Cluster: Same as Task 1
- Libraries: `databricks-sdk>=0.18.0`
- Environment variables: Same as Task 1

3. Set dependencies: Task 1 → Task 2 → Task 3
4. Click **Run now**

## 📊 What Gets Created

Once deployed, you'll have:

**Data Assets:**
- 5 Bronze tables (raw data) - ~312K ER visit records
- 5 Silver tables (cleaned)
- 6 Gold tables (aggregated KPIs)

**AI Resources:**
- Genie AI Space: "ER Staffing, Access, Quality & Financial Risk"
- Lakeview Dashboard with executive metrics

**Tables Created:**
```
chn_etl_demo_catalog.patient_readmission_dev.raw_emr_er_visits
chn_etl_demo_catalog.patient_readmission_dev.raw_hr_shifts_and_sickleave
chn_etl_demo_catalog.patient_readmission_dev.raw_patient_flow_metrics
chn_etl_demo_catalog.patient_readmission_dev.raw_patient_satisfaction_surveys
chn_etl_demo_catalog.patient_readmission_dev.raw_readmission_risk_feed
chn_etl_demo_catalog.patient_readmission_dev.silver_emr_er_visits
chn_etl_demo_catalog.patient_readmission_dev.silver_hr_shifts_and_sickleave
chn_etl_demo_catalog.patient_readmission_dev.silver_patient_flow_metrics
chn_etl_demo_catalog.patient_readmission_dev.silver_patient_satisfaction_surveys
chn_etl_demo_catalog.patient_readmission_dev.silver_readmission_risk_feed
chn_etl_demo_catalog.patient_readmission_dev.gold_er_operational_hourly
chn_etl_demo_catalog.patient_readmission_dev.gold_er_quality_daily
chn_etl_demo_catalog.patient_readmission_dev.gold_er_staffing_daily
chn_etl_demo_catalog.patient_readmission_dev.gold_er_finance_daily
chn_etl_demo_catalog.patient_readmission_dev.gold_er_readmission_risk_daily
chn_etl_demo_catalog.patient_readmission_dev.gold_global_filters_bridge
```

## ✅ Verify Deployment

After the workflow completes, run this query:

```sql
-- Check schema and tables
SHOW TABLES IN chn_etl_demo_catalog.patient_readmission_dev;

-- View sample data
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

## 💡 Recommendation

I **strongly recommend Option 1** (Databricks CLI) because:
- ✅ One command deployment
- ✅ Automatic variable substitution
- ✅ Proper dependency management
- ✅ Easier to redeploy/update
- ✅ Version controlled

The CLI install takes ~2 minutes and makes future deployments trivial.

## 🆘 Need Help?

If you encounter issues:
1. Check the job run logs in Databricks UI
2. Verify environment variables are set correctly
3. Ensure the warehouse is available
4. See `DEPLOYMENT.md` for troubleshooting

---

**All code and configurations are ready in:** `/Users/justin.ward/chn/dabs/patient-readmission/`
