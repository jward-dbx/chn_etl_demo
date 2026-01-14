# SDP Pipeline Configuration for DABs

## Key Decisions (prompt if unclear)
1. Streaming or batch oriented?
2. Continuous or triggered execution?
3. Serverless (default) or classic compute?

## Pipeline Resource Pattern

```yaml
resources:
  pipelines:
    pipeline_name:
      name: "[${bundle.target}] Pipeline Name"

      # Target catalog and schema
      catalog: ${var.catalog}
      target: ${var.schema}

      # Pipeline libraries
      libraries:
        - glob:
            include: ../src/pipelines/<pipeline_folder>/transformations/**
      
      root_path: ../src/pipelines/<pipeline_folder>

      serverless: true

      # Pipeline configuration
      configuration:
        source_catalog: ${var.source_catalog}
        source_schema: ${var.source_schema}

      continuous: false
      development: true
      photon: true

      channel: current

      permissions:
        - level: CAN_VIEW
          group_name: "users"
```

**Permission levels**: `CAN_VIEW`, `CAN_RUN`, `CAN_MANAGE`

## Best Practices

1. **Use `root_path` and `libraries.glob`** for newer organization structure
2. **Default to serverless** unless user specifies otherwise
3. **Use variables** for catalog/schema parameterization
4. **Set `development: true`** for dev/staging targets

---

## Lakeflow Connect Pipelines

**Use Case**: Managed ingestion from database sources (SQL Server, PostgreSQL, MySQL, Oracle, etc.)

**See**: `.claude/skills/sdp-writer/lakeflow-connect.md` for comprehensive Lakeflow Connect guidance

### Gateway + Ingestion Pipeline Pattern

Lakeflow Connect uses a two-stage architecture:
1. **Gateway**: Extracts CDC from source database (runs continuously)
2. **Ingestion Pipeline**: Applies changes to target tables (scheduled)

```yaml
variables:
  gateway_name:
    default: sqlserver-gateway
  pipeline_name:
    default: sqlserver-ingestion-pipeline
  connection_name:
    default: sqlserver_source
  staging_catalog:
    default: main
  staging_schema:
    default: ingestion_staging

resources:
  pipelines:
    # Ingestion Gateway - extracts CDC from source
    database_gateway:
      name: "[${bundle.target}] ${var.gateway_name}"
      gateway_definition:
        connection_name: ${var.connection_name}
        gateway_storage_catalog: ${var.staging_catalog}
        gateway_storage_schema: ${var.staging_schema}
        gateway_storage_name: ${var.gateway_name}
      target: ${var.staging_schema}
      catalog: ${var.staging_catalog}
      continuous: true  # Gateway MUST run continuously
      
    # Ingestion Pipeline - applies changes to target
    database_ingestion:
      name: "[${bundle.target}] ${var.pipeline_name}"
      ingestion_definition:
        ingestion_gateway_id: ${resources.pipelines.database_gateway.id}
        objects:
          # Option 1: Ingest specific tables
          - table:
              source_catalog: source_db
              source_schema: sales
              source_table: orders
              destination_catalog: ${var.catalog}
              destination_schema: ${var.schema}
              destination_table: orders
              table_configuration:
                scd_type: "2"  # Enable SCD Type 2 history tracking
          
          # Option 2: Ingest entire schema
          - schema:
              source_catalog: source_db
              source_schema: production
              destination_catalog: ${var.catalog}
              destination_schema: ${var.schema}
              schema_configuration:
                scd_type: "2"  # Apply SCD Type 2 to all tables
      target: ${var.schema}
      catalog: ${var.catalog}
      
  jobs:
    # Schedule ingestion pipeline refresh
    database_ingestion_job:
      name: "[${bundle.target}] Database Ingestion Job"
      schedule:
        quartz_cron_expression: "0 */4 * * * ?"  # Every 4 hours
        timezone_id: "UTC"
      email_notifications:
        on_failure:
          - data-team@company.com
      tasks:
        - task_key: refresh_pipeline
          pipeline_task:
            pipeline_id: ${resources.pipelines.database_ingestion.id}
```

### Multi-Environment Connection Variables

```yaml
# databricks.yml
variables:
  connection_name:
    default: "sqlserver_dev"

targets:
  dev:
    default: true
    variables:
      catalog: "dev_catalog"
      schema: "dev_schema"
      connection_name: "sqlserver_dev"
  
  prod:
    mode: production
    variables:
      catalog: "prod_catalog"
      schema: "prod_schema"
      connection_name: "sqlserver_prod"
```

### Deployment Commands

```bash
# Deploy gateway and pipeline
databricks bundle deploy -t dev

# Start gateway (continuous) - leave running
databricks bundle run database_gateway -t dev

# Pipeline runs on schedule via job
# Or manually trigger:
databricks bundle run database_ingestion -t dev
```

### Key Differences from Traditional SDP

| Aspect | Traditional SDP | Lakeflow Connect |
|--------|----------------|------------------|
| **Definition** | `libraries` with .sql/.py files | `gateway_definition` + `ingestion_definition` |
| **Source** | Cloud storage, Kafka, streaming | Database connections (SQL Server, PostgreSQL, etc.) |
| **Code** | SQL/Python transformation logic | No code - declarative table selection |
| **CDC** | Manual AUTO CDC implementation | Automatic CDC via gateway |
| **Execution** | Gateway continuous, pipeline scheduled | Both components required |

### Important Notes

1. **Gateway must run continuously** - Don't schedule the gateway, only the ingestion pipeline
2. **Connection required** - Create Unity Catalog connection before deploying bundle
3. **Staging separate from destination** - Use different catalogs/schemas for staging vs final tables
4. **SCD Type 2** - Configure via `table_configuration.scd_type: "2"` for history tracking
