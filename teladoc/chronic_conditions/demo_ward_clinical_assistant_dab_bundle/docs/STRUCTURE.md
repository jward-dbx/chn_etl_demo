# Project Structure

This document describes the organized folder structure of the Clinical Assistant Databricks Asset Bundle.

## Directory Layout

```
demo_ward_clinical_assistant_dab_bundle/
├── app/                          # Application code (Streamlit app)
│   ├── clinical_assistant_app.py # Main Streamlit application
│   ├── app.yaml                  # Databricks App configuration
│   └── app_ui_design/            # UI design files (React reference)
│       └── clinical-assistant-ui.jsx
│
├── bundle/                       # Databricks Asset Bundle files
│   ├── agent_bricks_service.py  # Service for managing Agent Bricks (KA/MAS/Genie)
│   ├── bricks_conf.json         # Agent Bricks configuration
│   ├── deploy_resources.py      # Script to deploy agent bricks
│   └── dashboard_clinical_ccm_monitoring.lvdash.json  # Lakeview dashboard
│
├── data/                         # Data generation and transformation
│   ├── generate_data.py          # Synthetic data generation script
│   ├── transformations.sql       # SQL transformations (bronze → silver → gold)
│   └── utils.py                  # Utility functions for data operations
│
├── docs/                         # Documentation and knowledge base
│   ├── pdf/                      # PDF documents for knowledge assistant
│   │   └── care_ops_playbooks_and_device_firmware_notes/
│   │       └── [9 PDF files]
│   ├── CONFIG.md                 # Configuration guide
│   ├── DEPLOYMENT.md             # Deployment instructions
│   ├── QUICK_START.md            # Quick start guide
│   ├── SETUP_CATALOG.md          # Catalog setup instructions
│   └── STRUCTURE.md              # This file
│
├── scripts/                      # Setup and utility scripts
│   ├── create_catalog.py         # Script to create catalog and schema
│   ├── setup_config.sh           # Interactive configuration setup
│   ├── setup_catalog.sql         # SQL script for catalog creation
│   └── run_data_generation.sh   # Script to run data generation workflow
│
├── config/                       # Configuration files
│   ├── config.template           # Configuration template (git tracked)
│   └── config.local              # Local configuration (gitignored)
│
├── databricks.yml               # Databricks Asset Bundle configuration (root)
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

## Folder Descriptions

### `app/`
Contains the Streamlit application code and configuration:
- **clinical_assistant_app.py**: Main Streamlit app with chat interface, patient info, vitals, risk scores, and next best actions
- **app.yaml**: Databricks App deployment configuration
- **app_ui_design/**: Reference UI design files (React/JSX) for the app interface

### `bundle/`
Contains Databricks Asset Bundle specific files:
- **agent_bricks_service.py**: Service wrapper for managing Knowledge Assistants, Multi-Agent Supervisors, and Genie spaces
- **bricks_conf.json**: Configuration for Agent Bricks (Genie, KA, MAS) with IDs, endpoints, and examples
- **deploy_resources.py**: Script that reads bricks_conf.json and deploys/updates agent bricks resources
- **dashboard_clinical_ccm_monitoring.lvdash.json**: Lakeview dashboard definition for monitoring chronic care operations

### `data/`
Contains data generation and transformation code:
- **generate_data.py**: Generates synthetic patient data, device readings, encounter notes, etc. using Faker
- **transformations.sql**: SQL transformations implementing medallion architecture (bronze → silver → gold)
- **utils.py**: Utility functions for data operations (Parquet saving, datetime handling)

### `docs/`
Contains documentation and knowledge base materials:
- **pdf/**: PDF documents used as knowledge sources for the Knowledge Assistant (care playbooks, device firmware notes, etc.)
- **CONFIG.md**: Guide for configuring workspace URL and authentication
- **DEPLOYMENT.md**: Detailed deployment instructions
- **QUICK_START.md**: Quick start guide for getting started
- **SETUP_CATALOG.md**: Instructions for creating the Unity Catalog catalog
- **STRUCTURE.md**: This file - project structure documentation

### `scripts/`
Contains setup and utility scripts:
- **create_catalog.py**: Python script to create Unity Catalog catalog and schema
- **setup_config.sh**: Interactive bash script to configure Databricks CLI and create config files
- **setup_catalog.sql**: SQL script for manual catalog creation
- **run_data_generation.sh**: Convenience script to run the data generation workflow

### `config/`
Contains configuration files:
- **config.template**: Template file showing configuration structure (git tracked)
- **config.local**: Local configuration with your credentials (gitignored, created by setup script)

## Root Files

- **databricks.yml**: Main Databricks Asset Bundle configuration file (must be at root)
- **requirements.txt**: Python package dependencies
- **README.md**: Project documentation and setup instructions

## Key Paths in Configuration

The `databricks.yml` file references these paths:
- Job tasks: `./data/generate_data.py`, `./data/transformations.sql`, `./bundle/deploy_resources.py`
- Dashboard: `./bundle/dashboard_clinical_ccm_monitoring.lvdash.json`
- App: `./app/clinical_assistant_app.py`, `./app/app.yaml`
- Artifacts: `./docs/pdf/**/*`

## Import Paths

- `bundle/deploy_resources.py` imports `agent_bricks_service` from the same folder
- `data/generate_data.py` imports `utils` from the same folder
- All imports are relative to their respective folders

