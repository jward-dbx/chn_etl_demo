# Databricks AI-Assisted Development Demo

This project demonstrates AI-assisted Databricks development using Claude with specialized skills for modern data engineering patterns.

## 🎯 Purpose

Showcase how AI can accelerate Databricks development by:
- Providing expert guidance on Databricks best practices
- Generating production-ready pipeline code
- Following 2025 modern patterns (serverless, Liquid Clustering, etc.)
- Automating deployment with Databricks Asset Bundles

## 📁 Project Structure

```
chn/
├── .claude/                          # Claude AI skills
│   ├── skills/
│   │   ├── databricks-dev/          # SDK, CLI, API patterns
│   │   ├── sdp-writer/              # Spark Declarative Pipelines
│   │   └── dabs-writer/             # Databricks Asset Bundles
│   └── README.md
│
├── sdp_test/                         # Example SDP Pipeline
│   ├── databricks.yml               # DAB configuration
│   ├── src/pipelines/               # Pipeline SQL files
│   ├── DEPLOYMENT.md                # Deployment details
│   └── README.md
│
├── docs/                             # Documentation
│   ├── sdp-guidance/                # SDP best practices
│   │   ├── table-naming-conventions.md
│   │   ├── root-path-pattern.md
│   │   └── downstream-table-references.md
│   └── setup/                       # Configuration guides
│       ├── MCP_SETUP.md
│       └── WORKSPACE_SETUP.md
│
└── config/                           # Configuration templates
    └── dev/
        └── env.example
```

## 🚀 Quick Start

### Prerequisites

- Databricks workspace with Unity Catalog
- Databricks CLI installed
- Python 3.8+
- Claude AI access (via Cursor or API)

### 1. Configure Databricks Access

```bash
# Copy environment template
cp config/dev/env.example config/dev/.env

# Edit with your workspace details
# DATABRICKS_HOST=https://your-workspace.azuredatabricks.net
# DATABRICKS_TOKEN=your-token
```

### 2. Review Example Pipeline

The `sdp_test/` directory contains a working Spark Declarative Pipeline that:
- Ingests data from source tables
- Creates streaming tables in Unity Catalog
- Implements downstream transformations
- Follows modern best practices

```bash
cd sdp_test
cat README.md  # Read pipeline documentation
```

### 3. Use Claude Skills

Claude automatically applies skills based on your requests:

**Example Prompts:**
- *"Create a Delta Live Tables pipeline for customer data"*
- *"Set up a DAB for multi-environment deployment"*
- *"Show me how to use Auto Loader for JSON files"*
- *"Configure serverless compute for my pipeline"*

## 🎓 Key Concepts Demonstrated

### 1. **Spark Declarative Pipelines (SDP)**
Modern approach to building data pipelines:
- SQL-first declarative syntax
- Automatic dependency resolution
- Built-in data quality
- Streaming and batch support

### 2. **Modern Patterns (2025)**
- **Serverless compute**: Auto-scaling, cost-efficient
- **Liquid Clustering**: `CLUSTER BY` instead of `PARTITION BY`
- **Root path pattern**: Organized folder structure
- **LIVE keyword**: Proper table dependencies

### 3. **Databricks Asset Bundles (DABs)**
Infrastructure-as-code for Databricks:
- Version-controlled configurations
- Multi-environment deployments
- Automated CI/CD
- Resource management

## 📚 Documentation

### SDP Guidance (`docs/sdp-guidance/`)

Comprehensive guides for building Spark Declarative Pipelines:

1. **Table Naming Conventions**
   - Why multipart names fail
   - Correct syntax patterns
   - Common pitfalls

2. **Root Path Pattern**
   - Modern folder organization
   - Auto-discovery with glob patterns
   - Migration from old patterns

3. **Downstream Table References**
   - Using `LIVE` keyword
   - Creating proper DAG lineage
   - Troubleshooting errors

### Setup Guides (`docs/setup/`)

- **MCP_SETUP.md**: Configure Model Context Protocol for Databricks
- **WORKSPACE_SETUP.md**: Initial workspace configuration

## 🔧 Example: SDP Pipeline

The included pipeline (`sdp_test/`) demonstrates:

**Source**: `dbx_chn_ward_demo.landing_ss_aw`
- customer
- product  
- salesorderdetail

**Target**: `dbx_chn_ward_demo.cursor`
- customer (ingested)
- product (ingested)
- salesorderdetail (ingested)
- sales_orders_flat (downstream join)

**Key Features**:
- Streaming ingestion from source
- Downstream transformation with proper lineage
- Modern root_path organization
- Serverless compute
- Development mode for testing

## 🎯 Skills Overview

### databricks-dev
Core Databricks development patterns:
- SDK authentication and usage
- CLI commands and workflows
- REST API patterns
- Configuration management

### sdp-writer
Spark Declarative Pipeline creation:
- SQL and Python syntax
- Ingestion patterns (Auto Loader, Kafka)
- Streaming patterns (deduplication, windowing)
- SCD patterns
- Performance tuning

### dabs-writer
Databricks Asset Bundle configuration:
- Multi-environment setup
- Pipeline resources
- Dashboard deployments
- Job configurations
- Permissions management

## 🔐 Authentication

This project uses Databricks Personal Access Tokens (PAT) for authentication.

**Setup**:
1. Generate PAT in Databricks workspace
2. Configure in `~/.databrickscfg` or environment variables
3. See `docs/setup/WORKSPACE_SETUP.md` for details

**MCP Integration**:
- Model Context Protocol (MCP) enables Claude to interact directly with Databricks
- Configuration in `~/.cursor/mcp.json`
- See `docs/setup/MCP_SETUP.md` for setup

## 📊 Use Cases

This demo shows how to:
- ✅ Build production-ready data pipelines with AI assistance
- ✅ Follow Databricks best practices automatically
- ✅ Generate deployment configurations
- ✅ Implement modern patterns (serverless, Liquid Clustering)
- ✅ Create proper data lineage
- ✅ Deploy across multiple environments

## 🤝 Contributing

This is a demonstration project. To extend:

1. Add new skills in `.claude/skills/`
2. Create additional pipeline examples
3. Enhance documentation
4. Share learnings and patterns

## 📝 License

This project is for demonstration purposes.

## 🔗 Resources

- [Databricks Documentation](https://docs.databricks.com/)
- [Delta Live Tables](https://docs.databricks.com/delta-live-tables/)
- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/)
- [Claude AI](https://www.anthropic.com/claude)

---

**Built with Claude AI** • Demonstrating AI-assisted Databricks development
