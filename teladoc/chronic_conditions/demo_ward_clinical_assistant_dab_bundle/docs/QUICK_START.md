# Quick Start Guide

## Prerequisites Setup

Since this is a new workspace, you need to create the catalog manually first.

### Step 1: Create Catalog and Schema

**Option A: Via Databricks UI (Easiest)**

1. Go to your workspace: https://fe-vm-vdm-serverless-exom73.cloud.databricks.com
2. Click **SQL** → **SQL Editor**
3. Make sure **Clinical Assistant Warehouse** is selected
4. Run these commands:

```sql
CREATE CATALOG ward_demo
COMMENT 'Catalog for clinical assistant demo';

USE CATALOG ward_demo;

CREATE SCHEMA justin_ward_demo_ward_clinical_assistant
COMMENT 'Schema for clinical assistant demo';
```

**Option B: Via Python Script**

```bash
python3 scripts/create_catalog.py
```

### Step 2: Deploy the Bundle

Once the catalog and schema exist:

```bash
databricks bundle deploy
```

### Step 3: Generate Data

After deployment, run the data generation workflow:

```bash
./scripts/run_data_generation.sh
```

Or manually:

```bash
databricks bundle run demo_workflow
```

## What Gets Created

- **Catalog**: `ward_demo`
- **Schema**: `justin_ward_demo_ward_clinical_assistant`
- **Volume**: `ward_demo.justin_ward_demo_ward_clinical_assistant.raw_data`
- **Tables**: Raw → Silver → Gold tables
- **Dashboard**: Chronic Care Ops & Risk Monitoring
- **App**: Clinical Assistant (Streamlit)
- **Agent Bricks**: Genie Space, Knowledge Assistant, Multi-Agent Supervisor

## Troubleshooting

### "Catalog does not exist" error

The catalog must be created before deploying. Use the SQL commands above or run `scripts/create_catalog.py`.

### Warehouse not found

Make sure "Clinical Assistant Warehouse" exists. If not, the bundle will try to use "Serverless Starter Warehouse".

### Data generation fails

Check that:
1. Catalog and schema exist
2. Volume was created successfully
3. Warehouse is running
4. You have proper permissions

