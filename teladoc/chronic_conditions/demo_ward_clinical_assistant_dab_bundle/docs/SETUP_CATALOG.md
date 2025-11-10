# Catalog Setup Instructions

Since this is a new workspace, you need to create the catalog manually before deploying the bundle.

## Option 1: Via Databricks UI (Recommended)

1. **Open Databricks SQL Editor**:
   - Go to your workspace: https://fe-vm-vdm-serverless-exom73.cloud.databricks.com
   - Click on **SQL** in the sidebar
   - Click **SQL Editor**

2. **Create the Catalog**:
   ```sql
   CREATE CATALOG ward_demo
   COMMENT 'Catalog for clinical assistant demo';
   ```

3. **Create the Schema**:
   ```sql
   USE CATALOG ward_demo;
   
   CREATE SCHEMA justin_ward_demo_ward_clinical_assistant
   COMMENT 'Schema for clinical assistant demo';
   ```

4. **Verify**:
   ```sql
   SHOW CATALOGS;
   SHOW SCHEMAS IN ward_demo;
   ```

## Option 2: Via SQL File

Run the provided SQL file:

1. **Upload `scripts/setup_catalog.sql`** to your workspace
2. **Open it in a Databricks notebook**
3. **Run the cells** to create catalog and schema

## Option 3: Via Python Script

You can also run this in a Databricks notebook:

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

# Create catalog (may require storage location)
w.catalogs.create(name="ward_demo", comment="Catalog for clinical assistant demo")

# Create schema
w.schemas.create(
    name="justin_ward_demo_ward_clinical_assistant",
    catalog_name="ward_demo",
    comment="Schema for clinical assistant demo"
)
```

## After Catalog Creation

Once the catalog and schema are created, you can:

1. **Deploy the bundle**:
   ```bash
   databricks bundle deploy
   ```

2. **Run data generation**:
   ```bash
   ./scripts/run_data_generation.sh
   # or
   databricks bundle run demo_workflow
   ```

## Troubleshooting

### "Metastore storage root URL does not exist"

This means you need to provide a storage location. Use:

```sql
CREATE CATALOG ward_demo
MANAGED LOCATION 's3://your-bucket/ward_demo'
COMMENT 'Catalog for clinical assistant demo';
```

Or create it via the UI which will handle storage automatically.

### "Catalog already exists"

Great! The catalog is already created. Just proceed with schema creation or deployment.

