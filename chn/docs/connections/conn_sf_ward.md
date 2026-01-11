# Snowflake Connection: conn_sf_ward

## Connection Details (from Vending Machine Workspace)

**Extracted on:** January 11, 2026  
**Source API:** `/api/2.1/unity-catalog/connections`

### Configuration
```json
{
  "name": "conn_sf_ward",
  "connection_type": "SNOWFLAKE",
  "options": {
    "sfRole": "ICEBERG_READER",
    "host": "REA76172.east-us-2.azure.snowflakecomputing.com",
    "use_proxy": "false",
    "port": "443",
    "sfWarehouse": "COMPUTE_WH"
  },
  "owner": "justin.ward@databricks.com",
  "read_only": true,
  "url": "jdbc://rea76172.east-us-2.azure.snowflakecomputing.com:443/",
  "credential_type": "USERNAME_PASSWORD",
  "connection_id": "fdda8412-8981-45be-a928-c5d9bb7f3a83",
  "securable_type": "CONNECTION",
  "securable_kind": "CONNECTION_SNOWFLAKE",
  "provisioning_info": {
    "state": "ACTIVE"
  }
}
```

### Key Parameters
- **Connection Name:** `conn_sf_ward`
- **Type:** Snowflake
- **Host:** `REA76172.east-us-2.azure.snowflakecomputing.com`
- **Port:** 443
- **Snowflake Warehouse:** `COMPUTE_WH`
- **Snowflake Role:** `ICEBERG_READER`
- **Credential Type:** USERNAME_PASSWORD
- **Status:** ACTIVE

### Usage
This connection is used for federated queries to Snowflake from Databricks, specifically with the `ICEBERG_READER` role for accessing Iceberg tables.

## Terraform Implementation

See `deployment/terraform/connections/snowflake_connection.tf` for the deployable Terraform configuration.

## Deployment Instructions

1. **Set up Terraform variables** in `terraform.tfvars`
2. **Store credentials** in Databricks Secrets
3. **Apply Terraform** to create connection in target workspace

For detailed steps, see `docs/recipes/deploy_snowflake_connection.md`
