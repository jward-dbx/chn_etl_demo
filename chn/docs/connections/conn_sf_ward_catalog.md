# Foreign Catalog: conn_sf_ward_catalog

## Catalog Details (from Vending Machine Workspace)

**Extracted on:** January 11, 2026  
**Source API:** `/api/2.1/unity-catalog/catalogs/conn_sf_ward_catalog`

### Configuration
```json
{
  "name": "conn_sf_ward_catalog",
  "catalog_type": "FOREIGN_CATALOG",
  "connection_name": "conn_sf_ward",
  "options": {
    "database": "OMOP"
  },
  "owner": "justin.ward@databricks.com",
  "isolation_mode": "OPEN",
  "browse_only": false,
  "securable_kind": "CATALOG_FOREIGN_SNOWFLAKE"
}
```

### Key Parameters
- **Catalog Name:** `conn_sf_ward_catalog`
- **Type:** Foreign Catalog (Snowflake)
- **Connection:** `conn_sf_ward`
- **Snowflake Database:** `OMOP`
- **Isolation Mode:** OPEN
- **Browse Only:** false

### Purpose
This foreign catalog provides federated access to the Snowflake OMOP database through Databricks, allowing queries against Snowflake tables using Databricks SQL.

## Terraform Implementation

The catalog is created alongside the connection in a single deployment.

See `deployment/terraform/connections/snowflake_catalog.tf` for the Terraform configuration.

## Deployment

Both the connection and catalog are deployed together:

```bash
cd deployment/terraform/connections
terraform plan   # Preview both resources
terraform apply  # Create connection + catalog
```

## Dependencies

- **Connection:** Must be created before catalog
- **Snowflake Database:** Must exist in Snowflake (OMOP)
- **Permissions:** User must have CREATE CATALOG permission

---

**Related Files:**
- Connection: `conn_sf_ward.md`
- Terraform Config: `snowflake_catalog.tf`
