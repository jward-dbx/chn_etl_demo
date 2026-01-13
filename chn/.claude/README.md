# Claude Skills for Databricks Development

This directory contains Claude AI agent skills for Databricks development, focusing on modern data engineering patterns and best practices.

## Available Skills

### 1. **databricks-dev**
Core Databricks development patterns and tools.

**Capabilities:**
- Databricks SDK usage and authentication
- Databricks CLI commands and workflows
- Databricks Connect for local development
- REST API patterns and best practices
- Configuration management

**Use When:**
- Setting up Databricks authentication
- Working with WorkspaceClient
- Executing CLI commands
- Making API calls

### 2. **sdp-writer** (Spark Declarative Pipelines)
Create and configure Lakeflow Spark Declarative Pipelines (formerly Delta Live Tables).

**Capabilities:**
- Pipeline creation in SQL or Python
- Ingestion patterns (Auto Loader, Kafka, Event Hub)
- Streaming patterns (deduplication, windowing)
- SCD (Slowly Changing Dimension) patterns
- Performance tuning with Liquid Clustering
- DLT migration guidance

**Use When:**
- Creating new data pipelines
- Building medallion architecture (bronze/silver/gold)
- Implementing streaming data flows
- Migrating from legacy DLT

### 3. **dabs-writer** (Databricks Asset Bundles)
Configure Databricks Asset Bundles for multi-environment deployments.

**Capabilities:**
- Bundle structure and configuration
- Pipeline resource definitions
- Dashboard deployments
- Job configurations
- Multi-environment setup (dev/staging/prod)
- Permissions management

**Use When:**
- Setting up CI/CD for Databricks
- Deploying pipelines across environments
- Managing Databricks resources as code
- Configuring alerts and dashboards

## How Skills Work

Claude automatically selects and applies relevant skills based on your requests. You don't need to explicitly reference them.

**Examples:**

- *"Create a Delta Live Tables pipeline"* → Uses `sdp-writer`
- *"Set up Databricks authentication"* → Uses `databricks-dev`
- *"Configure a DAB for deployment"* → Uses `dabs-writer`

## Project Structure

```
.claude/
├── README.md (this file)
└── skills/
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
    └── dabs-writer/
        ├── SKILL.md
        ├── SDP_guidance.md
        └── alerts_guidance.md
```

## Best Practices

### 1. **Modern Patterns (2025)**
- Use serverless compute for auto-scaling
- Use `CLUSTER BY` (Liquid Clustering) instead of `PARTITION BY`
- Implement proper data lineage with `LIVE` keyword
- Organize pipelines with `root_path` pattern

### 2. **Development Workflow**
- Use development mode for testing
- Implement data quality checks
- Follow medallion architecture
- Version control all configurations

### 3. **Deployment**
- Use Databricks Asset Bundles (DABs)
- Separate dev/staging/prod environments
- Implement proper permissions
- Automate with CI/CD

## Related Documentation

- **SDP Guidance**: `/docs/sdp-guidance/` - Comprehensive guides for Spark Declarative Pipelines
- **Setup**: `/docs/setup/` - Workspace and MCP configuration
- **Examples**: `/sdp_test/` - Working pipeline example

## Skill Maintenance

These skills are maintained as part of this project. To update:

1. Edit skill files in `.claude/skills/<skill-name>/`
2. Test changes with Claude
3. Commit and push updates

## References

- [Databricks Documentation](https://docs.databricks.com/)
- [Delta Live Tables](https://docs.databricks.com/delta-live-tables/)
- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/)
- [Databricks SDK](https://docs.databricks.com/dev-tools/sdk-python.html)
