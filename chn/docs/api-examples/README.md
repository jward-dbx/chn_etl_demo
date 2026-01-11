# API Examples

This directory contains practical examples of using the Databricks API for operations not covered by MCP servers.

## Organization

Examples are organized by API category:
- `workspace/` - Workspace operations (notebooks, folders)
- `jobs/` - Job creation and management
- `clusters/` - Cluster operations
- `unity-catalog/` - Unity Catalog operations
- `sql/` - SQL warehouse and query operations

## Example Format

Each example includes:
- **Purpose**: What the example demonstrates
- **Prerequisites**: Required permissions, resources
- **Code**: Complete working example (curl, Python, or both)
- **Expected Output**: Sample response
- **Notes**: Important considerations

## Authentication

All examples assume authentication via bearer token:
```bash
export DATABRICKS_HOST="https://fe-sandbox-serverless-rde85f.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."
```

---

*Examples will be added as we use the Databricks API*
