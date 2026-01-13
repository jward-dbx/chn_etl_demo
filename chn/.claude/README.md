# Claude Skills Configuration

This directory contains Claude AI agent skills for the CHN ETL Demo project.

## Skills Available

The skills are sourced from the `ssa-projects` repository (Databricks Field Engineering) and include:

### 1. **databricks-dev**
Guide for Databricks development using CLI, Databricks Connect, SDK and REST API.
- WorkspaceClient authentication patterns
- SDK usage best practices
- CLI configuration and usage
- REST API patterns

### 2. **sdp-writer** (Spark Declarative Pipelines)
Create and configure Databricks Lakeflow Spark Declarative Pipelines (formerly Delta Live Tables).
- Ingestion patterns (Auto Loader, Kafka, Event Hub)
- Streaming patterns (deduplication, windowing, stateful operations)
- SCD query patterns
- DLT migration guide
- Performance tuning with Liquid Clustering
- 2025 best practices (serverless compute, CLUSTER BY)

### 3. **dabs-writer** (Databricks Asset Bundles)
Create and configure Databricks Asset Bundles for deployment.
- SDP guidance
- Alerts configuration
- Multi-environment deployment patterns

### 4. **python-dev**
Python development best practices for Databricks projects.

## How It Works

- **Location**: `/Users/justin.ward/chn/.claude/skills/` (symlink to `external-skills/ssa-projects/.claude/skills/`)
- **Source**: Git submodule at `external-skills/ssa-projects/`
- **Auto-discovery**: Claude automatically discovers and uses skills based on your prompts
- **No explicit reference needed**: Just describe what you want to do, and Claude will select the appropriate skill

## Usage

You don't need to explicitly reference skills. Simply provide prompts like:

- "Create a Delta Live Tables pipeline for customer data"
- "Set up a Databricks Asset Bundle for this project"
- "Show me how to use WorkspaceClient to list clusters"
- "Create an Auto Loader ingestion pattern for JSON files"

Claude will automatically select and apply the relevant skills.

## Updating Skills

To get the latest skills from the upstream repository:

```bash
cd /Users/justin.ward
git submodule update --remote chn/external-skills/ssa-projects
cd chn
git add external-skills/ssa-projects
git commit -m "Update ssa-projects skills"
git push
```

## Structure

```
.claude/
├── README.md (this file)
└── skills/ -> ../external-skills/ssa-projects/.claude/skills/
    ├── databricks-dev/
    │   └── SKILL.md
    ├── sdp-writer/
    │   ├── SKILL.md
    │   ├── ingestion-patterns.md
    │   ├── streaming-patterns.md
    │   ├── scd-query-patterns.md
    │   ├── dlt-migration-guide.md
    │   ├── performance-tuning.md
    │   └── python-api-versions.md
    ├── dabs-writer/
    │   ├── SKILL.md
    │   ├── SDP_guidance.md
    │   └── alerts_guidance.md
    └── python-dev/
        └── SKILL.md
```

## Notes

- Skills are read-only (sourced from external submodule)
- Do not modify skills directly; contribute changes upstream to `databricks-field-eng/ssa-projects`
- The symlink ensures Claude can discover skills in the standard `.claude/skills/` location
