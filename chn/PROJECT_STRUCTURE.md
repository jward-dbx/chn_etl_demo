# Project Structure

## Clean, Customer-Ready Demo

This project has been organized for maximum clarity and impact when demonstrating AI-assisted Databricks development.

## Directory Tree

```
chn/
├── README.md                         # Project overview and quick start
├── PROJECT_STRUCTURE.md              # This file
│
├── .claude/                          # Claude AI Skills
│   ├── README.md                     # Skills documentation
│   └── skills/
│       ├── databricks-dev/           # Core Databricks patterns
│       │   └── SKILL.md
│       ├── sdp-writer/               # Spark Declarative Pipelines
│       │   ├── SKILL.md
│       │   ├── ingestion-patterns.md
│       │   ├── streaming-patterns.md
│       │   ├── scd-query-patterns.md
│       │   ├── dlt-migration-guide.md
│       │   ├── performance-tuning.md
│       │   └── python-api-versions.md
│       └── dabs-writer/              # Databricks Asset Bundles
│           ├── SKILL.md
│           ├── SDP_guidance.md
│           └── alerts_guidance.md
│
├── sdp_test/                         # Working Pipeline Example
│   ├── README.md                     # Pipeline documentation
│   ├── DEPLOYMENT.md                 # Deployment history
│   ├── databricks.yml                # DAB configuration
│   └── src/
│       └── pipelines/
│           └── landing_to_cursor/
│               └── transformations/
│                   ├── customer.sql
│                   ├── product.sql
│                   ├── salesorderdetail.sql
│                   └── sales_orders_flat.sql
│
├── docs/                             # Documentation
│   ├── sdp-guidance/                 # SDP Best Practices
│   │   ├── README.md
│   │   ├── table-naming-conventions.md
│   │   ├── root-path-pattern.md
│   │   └── downstream-table-references.md
│   └── setup/                        # Configuration Guides
│       ├── MCP_SETUP.md              # Model Context Protocol
│       ├── WORKSPACE_SETUP.md        # Databricks workspace
│       ├── DEPLOYMENT.md
│       └── GENIE.md
│
└── config/                           # Configuration Templates
    ├── README.md
    ├── dev/
    │   └── env.example
    └── prod/
```

## What Was Removed

To create a focused demo, we removed:

- ❌ `terraform/` - Infrastructure code (not needed for demo)
- ❌ `dabs/patient-readmission/` - Old example project
- ❌ `app_ui_design/` - UI mockups
- ❌ `external-skills/` - External submodule (skills now owned)
- ❌ `docs/api-examples/` - Unnecessary documentation
- ❌ `docs/architecture/` - Unnecessary documentation
- ❌ `docs/connections/` - Unnecessary documentation
- ❌ `docs/recipes/` - Unnecessary documentation

## What We Kept

Essential components for the demo:

### ✅ Claude Skills (.claude/skills/)
- **databricks-dev**: SDK, CLI, API patterns
- **sdp-writer**: Spark Declarative Pipelines expertise
- **dabs-writer**: Databricks Asset Bundles configuration

### ✅ Working Example (sdp_test/)
- Complete SDP pipeline
- Modern patterns (serverless, root_path, LIVE keyword)
- Proper DAG lineage
- Deployment ready

### ✅ Essential Documentation (docs/)
- **sdp-guidance/**: Critical SDP patterns and troubleshooting
- **setup/**: MCP and workspace configuration

### ✅ Configuration (config/)
- Environment templates
- Setup instructions

## File Count Summary

| Category | Files | Purpose |
|----------|-------|---------|
| **Skills** | 11 | Claude AI expertise |
| **Pipeline** | 5 | Working SDP example |
| **Documentation** | 9 | Guides and setup |
| **Config** | 2 | Templates |
| **Total** | ~27 | Clean, focused demo |

## Key Features Demonstrated

1. **AI-Assisted Development**
   - Claude automatically applies relevant skills
   - Generates production-ready code
   - Follows best practices

2. **Modern Patterns (2025)**
   - Serverless compute
   - Liquid Clustering
   - Root path organization
   - Proper data lineage

3. **Complete Workflow**
   - Skills → Code Generation → Deployment
   - Multi-environment support
   - Version-controlled infrastructure

## Authentication Files

Located in project root (not in git):
- `.databrickscfg.chn` - Databricks CLI config
- `.databricks-workspaces.json` - Workspace definitions

MCP configuration:
- `~/.cursor/mcp.json` - Model Context Protocol setup

## Quick Navigation

| Want to... | Go to... |
|------------|----------|
| Understand the project | `README.md` |
| Learn about skills | `.claude/README.md` |
| See working pipeline | `sdp_test/README.md` |
| Learn SDP patterns | `docs/sdp-guidance/README.md` |
| Configure workspace | `docs/setup/MCP_SETUP.md` |

## Demo Flow

1. **Show Skills** → `.claude/skills/`
2. **Explain Concept** → `README.md`
3. **Run Example** → `sdp_test/`
4. **Show Results** → Databricks UI
5. **Discuss Patterns** → `docs/sdp-guidance/`

---

**Result**: Clean, professional demo showcasing AI-assisted Databricks development with real working examples and comprehensive guidance.
