# Healthcare AI ETL Platform UI - Databricks Deployment

Interactive demonstration UI for an AI-driven ETL platform on Databricks Lakehouse.

## 🎯 What This Is

This is a fully interactive UI mockup/"art of the possible" demonstration showing:

- **AI Agents** for intelligent data orchestration
- **Skills Library** with reusable Databricks capabilities
- **Lakehouse Federation** monitoring and optimization
- **Governance & Compliance** controls (HIPAA-focused)
- **Pipeline Visualization** with AI recommendations
- **Natural Language** pipeline creation interface

## 📁 Files Deployed

All files have been uploaded to the Databricks workspace at:
```
/Users/justin.ward@databricks.com/apps/healthcare-ai-etl-ui/
```

Files include:
- `index.html` - Complete interactive UI
- `app.py` - Flask application server
- `app.yaml` - Databricks App configuration
- `requirements.txt` - Python dependencies
- `Healthcare_AI_ETL_UI` - Databricks notebook

## 🚀 How to Access

### Option 1: Databricks Notebook (Simplest)

1. Navigate to: `https://adb-7405607609261208.8.azuredatabricks.net/#notebook/3669470726009207`
2. Or go to Workspace → Users → justin.ward@databricks.com → apps → Healthcare_AI_ETL_UI
3. Run the notebook to display the interactive UI

### Option 2: Local Testing

Open the `index.html` file directly in your browser:
```bash
open /Users/justin.ward/chn/app_ui_design/index.html
```

### Option 3: Databricks App (If Available)

If Databricks Apps is enabled in your workspace:
1. Use Databricks CLI to deploy: `databricks bundle deploy`
2. Access via the Apps section in the workspace

## ✨ Features You Can Interact With

- ✅ **Dashboard**: View stats, create pipelines with natural language
- ✅ **Agents Page**: Click agent cards to see detailed modals
- ✅ **Skills Library**: Browse 9 healthcare-specific skills
- ✅ **Federation**: Click sources for performance analysis and recommendations
- ✅ **Governance**: View HIPAA compliance policies
- ✅ **Pipelines**: See visual pipeline flow with metrics

## 🏥 Healthcare Use Case

This demo focuses on a healthcare analytics scenario:
- Epic EHR and FHIR data ingestion
- OMOP Common Data Model transformation
- Clinical quality measures (HEDIS/CMS)
- Patient monitoring and alerts
- Claims processing
- HIPAA compliance throughout

## 🔧 Technical Stack

- **Frontend**: React (via Babel), Tailwind CSS, Lucide Icons
- **Backend** (for deployment): Flask (Python)
- **Databricks Features Highlighted**:
  - Auto Loader & Delta Lake
  - Lakehouse Federation
  - Unity Catalog
  - Databricks Workflows
  - Lakehouse Monitoring
  - Spark Declarative Pipelines

## ⚠️ Important Notes

- This is a **UI mockup/wireframe** - no backend functionality
- All data shown is mock data for demonstration
- Fully interactive - click through all pages and modals
- Ready for customer demos and discussions

## 📝 Next Steps

To make this functional:
1. Connect to real Databricks APIs for live data
2. Implement actual AI agent orchestration
3. Add authentication and access controls
4. Connect to Unity Catalog for real metadata
5. Integrate with Databricks Workflows for pipeline management

## 🔗 Workspace URL

https://adb-7405607609261208.8.azuredatabricks.net/
