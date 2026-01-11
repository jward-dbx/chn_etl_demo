# Databricks Development Resources Reference

This document provides quick access to key resources for developing and deploying OMOP Semantic artifacts.

## 📋 Quick Reference

### When to Use Each Tool

| Task | Tool | Reference |
|------|------|-----------|
| Query Databricks tables/data | MCP Server (DBSQL) | Already configured (`vending-machine-dbsql`) |
| Execute Python in Databricks | MCP Server (System AI) | Already configured (`vending-machine-system-ai`) |
| Workspace operations (create jobs, clusters, etc.) | Databricks API | [API Documentation](#databricks-api) |
| Deploy cross-workspace artifacts | Databricks Asset Bundles | [DAB Documentation](#databricks-asset-bundles-dabs) |
| Infrastructure as Code | Terraform | [Terraform Provider](#terraform-provider) |

---

## 🔌 MCP Servers (Already Configured)

### vending-machine-dbsql
- **Purpose**: Execute SQL queries against Unity Catalog
- **Use for**: Data exploration, querying tables, running analytics
- **Example**: `SHOW CATALOGS`, `SELECT * FROM catalog.schema.table`

### vending-machine-system-ai
- **Purpose**: Execute Python code in Databricks environment
- **Use for**: Data transformations, calculations, system AI functions

---

## 🌐 Databricks API

**URL**: https://docs.databricks.com/api/workspace/introduction

### When to Use
Use the Databricks API when MCP servers cannot perform the required operation:
- Creating/managing jobs and workflows
- Managing clusters and compute resources
- Workspace file operations (import/export notebooks)
- Managing secrets and permissions
- Creating/managing Unity Catalog objects
- Model serving endpoints

### Common API Endpoints
- **Workspace API**: `/api/2.0/workspace/*` - Import/export notebooks, manage folders
- **Jobs API**: `/api/2.1/jobs/*` - Create, run, manage jobs
- **Clusters API**: `/api/2.0/clusters/*` - Manage compute resources
- **DBFS API**: `/api/2.0/dbfs/*` - File system operations
- **Unity Catalog API**: `/api/2.1/unity-catalog/*` - Manage catalogs, schemas, tables
- **SQL API**: `/api/2.0/sql/*` - Manage warehouses, queries, dashboards

### Authentication
Uses the same token configured for MCP servers:
```bash
curl -H "Authorization: Bearer dapi..." \
  https://fe-sandbox-serverless-rde85f.cloud.databricks.com/api/2.0/workspace/list?path=/
```

---

## 🏗️ Databricks Asset Bundles (DABs)

**Documentation**: https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/  
**Examples**: https://github.com/databricks/bundle-examples

### When to Use
Use DABs for **cross-workspace deployable artifacts**:
- ✅ Deploying OMOP ETL pipelines to dev/prod
- ✅ Managing jobs and workflows as code
- ✅ Deploying notebooks, Python code, SQL scripts
- ✅ Creating repeatable deployments
- ✅ CI/CD pipelines

### Key Concepts
- **Bundle**: Collection of Databricks resources defined in YAML
- **Target**: Environment (dev/prod) with specific configurations
- **Resources**: Jobs, pipelines, dashboards, models, etc.
- **Artifacts**: Python wheels, notebooks, SQL files

### Bundle Structure
```yaml
# databricks.yml
bundle:
  name: omop_semantic
  
resources:
  jobs:
    omop_etl:
      name: "OMOP ETL Pipeline"
      tasks:
        - task_key: bronze_ingestion
          notebook_task:
            notebook_path: ./notebooks/etl/bronze_ingestion.py
```

### Common Commands
```bash
# Validate bundle
databricks bundle validate

# Deploy to dev
databricks bundle deploy -t dev

# Deploy to prod
databricks bundle deploy -t prod

# Run a job
databricks bundle run my_job_name
```

### Example Templates
The [bundle-examples repo](https://github.com/databricks/bundle-examples) includes:
- `default_python` - Basic Python project
- `default_sql` - SQL-based project
- `lakeflow_pipelines_python` - Delta Live Tables with Python
- `lakeflow_pipelines_sql` - Delta Live Tables with SQL
- `mlops_stacks` - ML workflows

---

## 🔧 Terraform Provider

**URL**: https://registry.terraform.io/providers/databricks/databricks/latest/docs

### When to Use
Use Terraform for **infrastructure-level management**:
- ✅ Creating catalogs, schemas, tables
- ✅ Managing workspace-level resources
- ✅ Setting up permissions and service principals
- ✅ Creating clusters, instance pools
- ✅ Complex multi-resource dependencies

### Key Resources
- **databricks_catalog** - Create Unity Catalog catalogs
- **databricks_schema** - Create schemas
- **databricks_table** - Define tables
- **databricks_job** - Define jobs
- **databricks_notebook** - Deploy notebooks
- **databricks_cluster** - Create clusters
- **databricks_sql_warehouse** - SQL warehouses
- **databricks_secret_scope** - Manage secrets

### Example Terraform
```hcl
# Create OMOP catalog
resource "databricks_catalog" "omop" {
  name    = "dev_omop"
  comment = "OMOP CDM v5.4 catalog"
}

# Create schema
resource "databricks_schema" "gold_omop" {
  catalog_name = databricks_catalog.omop.name
  name         = "gold_omop"
  comment      = "OMOP CDM standardized tables"
}

# Create table
resource "databricks_table" "person" {
  catalog_name = databricks_catalog.omop.name
  schema_name  = databricks_schema.gold_omop.name
  name         = "person"
  table_type   = "MANAGED"
  data_source_format = "DELTA"
  
  column {
    name = "person_id"
    type = "BIGINT"
  }
  # ... more columns
}
```

---

## 🎯 Decision Tree: Which Tool to Use?

```
Need to query data?
├─→ YES: Use MCP Server (vending-machine-dbsql)
└─→ NO: Continue...

Need to execute Python code?
├─→ YES: Use MCP Server (vending-machine-system-ai)
└─→ NO: Continue...

Need to deploy artifacts across workspaces?
├─→ YES: Use Databricks Asset Bundles (DABs)
└─→ NO: Continue...

Need to manage infrastructure/resources?
├─→ Prefer declarative IaC: Use Terraform
└─→ One-off operations: Use Databricks API
```

---

## 📝 Usage Patterns

### Pattern 1: Extract Semantic Layer from Workspace
1. **Query tables** using MCP DBSQL to identify semantic layer objects
2. **Export definitions** using Databricks API (workspace/export)
3. **Convert to DAB format** for cross-workspace deployment
4. **Commit to git** on feature branch

### Pattern 2: Deploy OMOP Artifacts
1. **Define resources** in `databricks.yml` (DAB config)
2. **Write ETL code** in src/ directory
3. **Test locally** with unit tests
4. **Deploy to dev** using `databricks bundle deploy -t dev`
5. **Validate** and test in dev workspace
6. **Deploy to prod** using `databricks bundle deploy -t prod`

### Pattern 3: Create Infrastructure
1. **Define Terraform resources** in `.tf` files
2. **Plan changes** with `terraform plan`
3. **Apply infrastructure** with `terraform apply`
4. **Deploy application code** using DABs

---

## 💾 Saving Instructions

As we use these resources, instructions will be added to:
- **`docs/recipes/`** - Step-by-step guides for specific tasks
- **`docs/api-examples/`** - API call examples with curl/Python
- **`deployment/terraform/`** - Terraform configurations
- **`deployment/dabs/`** - DAB configurations

---

## 🔗 Quick Links

| Resource | URL |
|----------|-----|
| Databricks API Docs | https://docs.databricks.com/api/workspace/introduction |
| Terraform Provider | https://registry.terraform.io/providers/databricks/databricks/latest/docs |
| DAB Documentation | https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/ |
| DAB Examples (GitHub) | https://github.com/databricks/bundle-examples |
| OMOP CDM Specification | https://ohdsi.github.io/CommonDataModel/ |
| Athena Vocabulary Browser | https://athena.ohdsi.org/ |

---

*Last updated: January 11, 2026*
