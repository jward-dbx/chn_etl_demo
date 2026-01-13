# demo_ward_patient_readmission - Databricks Asset Bundle

## Overview
COO of SummitCare Health Network needs real-time monitoring to align ER staffing with patient volume during September 2025 weekend surges and elevated sick leave. Beginning 2025-09-05 and peaking 2025-09-20–2025-09-21, ER arrivals spiked 25–35% on weekends, triage queues lengthened, median triage wait rose from ~12 to ~19 minutes, door-to-provider extended ~18%, and LWBS rate increased by ~15% vs baseline. Concurrently, ER nurse sick leave doubled (from ~3.2% to ~6.5%) with overtime up ~22%. The dashboard ties volume surge -> staffing gaps (effective coverage/N:P ratio) -> dated HR change log -> quality and reimbursement risk.

## Deployment

This bundle can be deployed to any Databricks workspace using Databricks Asset Bundles (DAB):

### Prerequisites
1. **Databricks CLI**: Install the latest version
   ```bash
   pip install databricks-cli
   ```
2. **Authentication**: Configure your workspace credentials
   ```bash
   databricks configure
   ```
3. **Workspace Access**: Ensure you have permissions for:
   - Unity Catalog catalog/schema creation
   - SQL Warehouse access
   - Workspace file storage

### Deploy the Bundle
```bash
# Navigate to the dab directory
cd dab/

# Validate the bundle configuration
databricks bundle validate

# Deploy to your workspace (--force-lock to override any existing locks)
databricks bundle deploy --force-lock

# Run the data generation workflow
databricks bundle run demo_workflow
```

The deployment will:
1. Create Unity Catalog resources (schema and volume)
2. Upload PDF files to workspace (if applicable)
3. Deploy job and dashboard resources

The workflow will:
1. Create Unity Catalog catalog if it doesn't exist (DAB doesn't support catalog creation)
2. Generate synthetic data using Faker and write to Unity Catalog Volume
3. Execute SQL transformations (bronze → silver → gold)
4. Deploy agent bricks (Genie spaces, Knowledge Assistants, Multi-Agent Supervisors) if configured

## Bundle Contents

### Core Files
- `databricks.yml` - Asset bundle configuration defining jobs, dashboards, and deployment settings
- `bricks_conf.json` - Agent brick configurations (Genie/KA/MAS) if applicable
- `agent_bricks_service.py` - Service for managing agent brick resources (includes type definitions)
- `deploy_resources.py` - Script to recreate agent bricks in the target workspace

### Data Generation
- Python scripts using Faker library for realistic synthetic data
- Configurable row counts, schemas, and business logic
- Automatic Delta table creation in Unity Catalog

### SQL Transformations
- `transformations.sql` - SQL transformations for data processing
- Bronze (raw) → Silver (cleaned) → Gold (aggregated) medallion architecture
- Views and tables for business analytics

### Agent Bricks
This bundle includes AI agent resources:

- **Genie Space** (ID: `01f0c1746d3d1e30b3a973bf791a08fb`)
  - Natural language interface for data exploration
  - Configured with table identifiers from your catalog/schema
  - Sample questions and instructions included

### Dashboards
This bundle includes Lakeview dashboards:
- **Lakeview ER Staffing, Access, Quality, and Financial Risk** - Business intelligence dashboard with visualizations

### PDF Documents
No PDF documents are included in this demo.

## Configuration

### Unity Catalog
- **Catalog**: `demo_generator`
- **Schema**: `justin_ward_demo_ward_patient_readmission`
- **Workspace Path**: `/Users/justin.ward@databricks.com/demo_ward_patient_readmission`

### Customization
You can modify the bundle by editing `databricks.yml`:
- Change target catalog/schema in the `variables` section
- Adjust cluster specifications for data generation
- Add additional tasks or resources

## Key Questions This Demo Answers
1. Which weekends in Sep-2025 had the highest LWBS and what staffing coverage gaps contributed?
2. How would adding 2 triage nurses on weekend evening shifts affect LWBS and door-to-provider time?
3. Which sites show persistent sick leave spikes among ER nurses, and during which shifts?
4. What acuity mix shifts occurred during surge weekends, and how did they influence throughput and waits?
5. What is the estimated reimbursement at risk by week, and how much did overtime spending offset service recovery?
6. Did readmission rates increase for LWBS or long-wait cohorts, and which segments were most exposed?

## Deployment to New Workspaces

This bundle is **portable** and can be deployed to any Databricks workspace:

1. The bundle will recreate all resources in the target workspace
2. Agent bricks (Genie/KA/MAS) are recreated from saved configurations in `bricks_conf.json`
3. SQL transformations and data generation scripts are environment-agnostic
4. Dashboards are deployed as Lakeview dashboard definitions

Simply run `databricks bundle deploy` in any workspace where you have the required permissions.

## Troubleshooting

### Common Issues

**Bundle validation fails:**
- Ensure `databricks.yml` has valid YAML syntax
- Check that catalog and schema names are valid
- Verify warehouse lookup matches an existing warehouse

**Agent brick deployment fails:**
- Check that `bricks_conf.json` exists and contains valid configurations
- Ensure you have permissions to create Genie spaces, KA tiles, and MAS tiles
- Verify vector search endpoint exists for Knowledge Assistants

**SQL transformations fail:**
- Ensure the catalog and schema exist in the target workspace
- Check warehouse permissions and availability
- Review SQL syntax for Unity Catalog compatibility (3-level namespace: `catalog.schema.table`)

### Getting Help
- Review Databricks Asset Bundles documentation: https://docs.databricks.com/dev-tools/bundles/
- Check the generated code in this bundle for implementation details
- Contact your Databricks workspace administrator for permissions issues

## Generated with AI Demo Generator
🤖 This bundle was automatically created using the Databricks AI Demo Generator.

**Created**: 2025-11-14 15:53:25
**User**: justin.ward@databricks.com
