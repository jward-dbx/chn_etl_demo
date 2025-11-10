# demo_ward_clinical_assistant - Databricks Asset Bundle

## Overview
The Chief Medical Officer at CareSphere Telehealth needs continuous monitoring of chronic care operations to see how an Oct 02–Oct 21, 2025 device firmware rollout for Bluetooth glucometers and BP cuffs created a measurable shift in patient vitals ingestion quality, elevated short-term risk scores, and forced care plan adjustments. Following the rollout (2025-10-02), valid glucose readings dropped ~28% for a subset of devices while BP readings showed increased missing diastolic values; encounter summarization flagged more diet non-adherence notes; hospitalization risk stratification rose 1.6x for high-risk Type 2 diabetics; and Next Best Action recommendations pivoted toward nurse check-ins and medication review. A corrective configuration push on 2025-10-12 restored most ingestion, but weekend gaps persisted until 2025-10-21. The dashboard ties ingestion anomaly -> patient segment mix -> change log -> care actions and workload -> clinical risk and potential cost exposure.

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

- **Genie Space** (ID: `01f0be2ba4821915846537ddfcb01861`)
  - Natural language interface for data exploration
  - Configured with table identifiers from your catalog/schema
  - Sample questions and instructions included

- **Knowledge Assistant** (ID: `01af0803-c222-4ee8-b01a-33af77099141`)
  - AI assistant with knowledge sources from Unity Catalog volumes
  - Vector search-powered retrieval augmented generation (RAG)
  - Example questions and guidelines included

- **Multi-Agent Supervisor** (ID: `6e11c42c-acc6-423e-a1cd-b2c6051da0f3`)
  - Orchestrates multiple specialized agents
  - Routes queries to appropriate sub-agents (Genie, KA, endpoints)
  - Complex multi-step workflows supported

### Dashboards
This bundle includes Lakeview dashboards:
- **Chronic Care Ops & Risk Monitoring** - Business intelligence dashboard with visualizations

### PDF Documents
This bundle includes PDF documents that will be uploaded to the workspace:
- PDF files are automatically uploaded during bundle deployment via DAB artifacts
- These PDFs are included in the bundle workspace path
- You can manually copy them to Unity Catalog Volumes if needed for RAG scenarios
- Example: Use Databricks Files API or `dbutils.fs.cp` to move files to a volume

## Configuration

### Unity Catalog
- **Catalog**: `ward_demo`
- **Schema**: `justin_ward_demo_ward_clinical_assistant`
- **Workspace Path**: `/Users/justin.ward@databricks.com/demo_ward_clinical_assistant`

### Customization
You can modify the bundle by editing `databricks.yml`:
- Change target catalog/schema in the `variables` section
- Adjust cluster specifications for data generation
- Add additional tasks or resources

## Key Questions This Demo Answers
1. When did the ingestion quality shift occur by device type and region, and how large was the drop vs baseline?
2. Which patient segments (risk tier, condition) were most affected, and how did their risk scores change during and after the event?
3. What dated change entries align with the onset and recovery, and which error codes were most prevalent?
4. How did Next Best Action recommendations and executed actions mix change week-over-week, and how long until they normalized?
5. What is the cumulative care cost exposure attributable to the incident, by region and condition?
6. Did encounter summarization show a significant increase in diet or medication non-adherence mentions, and did these correlate with risk elevation?
7. By 2025-10-21, which metrics returned to baseline and which still showed weekend residual gaps?

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

## Clinical Assistant Streamlit App

This bundle includes a Streamlit application (`clinical_assistant_app.py`) that provides a clinical assistant interface for chronic care management.

### Features

- **Chat Interface**: Interactive chat with the Multi-Agent Supervisor (MAS) that coordinates:
  - Genie Data Explorer for SQL/data queries
  - Knowledge Assistant for document Q&A from care playbooks and device firmware notes
- **Patient Information**: Displays patient details from the database including:
  - Patient ID, region, condition, risk tier
  - Enrollment information
- **Connected Device Vitals**: Real-time display of:
  - Glucose readings
  - Blood pressure measurements
  - Weight tracking
  - Status indicators and trends
- **Risk Stratification**: Shows:
  - Overall risk score
  - Hospitalization risk
  - Deterioration risk
- **Next Best Actions**: AI-recommended care steps (with placeholders for Nesbeth's actions component)
- **Recent Encounter Notes**: Display of recent clinical notes

### Deployment

The app is configured in `databricks.yml` and can be deployed using:

```bash
databricks bundle deploy
```

The app will be available in the Databricks Apps section of your workspace.

### Configuration

The app connects to:
- **MAS Endpoint**: `mas-6e11c42c-endpoint` (configured in `clinical_assistant_app.py`)
- **Database**: `ward_demo.justin_ward_demo_ward_clinical_assistant` schema
- **Default Patient**: `P-2847` (can be modified in the app)

### Usage

1. Deploy the bundle: `databricks bundle deploy`
2. Navigate to **Apps** in your Databricks workspace
3. Open the "Clinical Assistant" app
4. The app will display patient information and allow you to chat with the MAS

### Customization

To change the default patient or modify the app:
1. Edit `clinical_assistant_app.py`
2. Update `st.session_state.selected_patient_id` to use a different patient ID
3. Redeploy: `databricks bundle deploy`

### Notes

- The MAS endpoint call may need adjustment based on your endpoint's exact API format
- Patient data is queried directly from Unity Catalog tables
- The Next Best Actions component includes placeholders for future Nesbeth integration
- Risk stratification uses aggregated data from `gold_patient_risk_timeseries`

## Generated with AI Demo Generator
🤖 This bundle was automatically created using the Databricks AI Demo Generator.

**Created**: 2025-11-10 11:39:54
**User**: justin.ward@databricks.com
