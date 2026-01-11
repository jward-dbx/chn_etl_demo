# API Example: List and Get Databricks Connections

This example demonstrates how to use the Databricks API to list and retrieve connection details.

## Prerequisites

- Databricks workspace URL
- Databricks personal access token or service principal token
- `curl` or equivalent HTTP client

## Authentication

All API calls require a bearer token in the Authorization header:

```bash
export DATABRICKS_HOST="https://fe-sandbox-serverless-rde85f.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."
```

## List All Connections

### Request

```bash
curl -s -H "Authorization: Bearer ${DATABRICKS_TOKEN}" \
  "${DATABRICKS_HOST}/api/2.1/unity-catalog/connections" | jq
```

### Response (Sample)

```json
{
  "connections": [
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
      "full_name": "conn_sf_ward",
      "url": "jdbc://rea76172.east-us-2.azure.snowflakecomputing.com:443/",
      "credential_type": "USERNAME_PASSWORD",
      "connection_id": "fdda8412-8981-45be-a928-c5d9bb7f3a83",
      "securable_type": "CONNECTION",
      "securable_kind": "CONNECTION_SNOWFLAKE",
      "provisioning_info": {
        "state": "ACTIVE"
      }
    }
  ]
}
```

## Get Specific Connection

### Request

```bash
curl -s -H "Authorization: Bearer ${DATABRICKS_TOKEN}" \
  "${DATABRICKS_HOST}/api/2.1/unity-catalog/connections/conn_sf_ward" | jq
```

### Response

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
  "full_name": "conn_sf_ward",
  "url": "jdbc://rea76172.east-us-2.azure.snowflakecomputing.com:443/",
  "credential_type": "USERNAME_PASSWORD",
  "connection_id": "fdda8412-8981-45be-a928-c5d9bb7f3a83",
  "metastore_id": "1af69e89-b18f-46d2-ac9d-b74259f9cadb",
  "created_at": 1767010976937,
  "created_by": "justin.ward@databricks.com",
  "updated_at": 1767783311744,
  "updated_by": "justin.ward@databricks.com",
  "securable_type": "CONNECTION",
  "securable_kind": "CONNECTION_SNOWFLAKE",
  "provisioning_info": {
    "state": "ACTIVE"
  }
}
```

## Filter Connections by Type

### Using jq to filter Snowflake connections only:

```bash
curl -s -H "Authorization: Bearer ${DATABRICKS_TOKEN}" \
  "${DATABRICKS_HOST}/api/2.1/unity-catalog/connections" | \
  jq '.connections[] | select(.connection_type == "SNOWFLAKE")'
```

## Python Example

```python
import requests
import json
import os

# Configuration
DATABRICKS_HOST = os.getenv('DATABRICKS_HOST')
DATABRICKS_TOKEN = os.getenv('DATABRICKS_TOKEN')

headers = {
    'Authorization': f'Bearer {DATABRICKS_TOKEN}',
    'Content-Type': 'application/json'
}

# List all connections
response = requests.get(
    f'{DATABRICKS_HOST}/api/2.1/unity-catalog/connections',
    headers=headers
)

if response.status_code == 200:
    connections = response.json()['connections']
    print(f"Found {len(connections)} connections")
    
    # Find Snowflake connections
    sf_connections = [
        c for c in connections 
        if c['connection_type'] == 'SNOWFLAKE'
    ]
    
    for conn in sf_connections:
        print(f"\nConnection: {conn['name']}")
        print(f"  Host: {conn['options']['host']}")
        print(f"  Warehouse: {conn['options']['sfWarehouse']}")
        print(f"  Role: {conn['options'].get('sfRole', 'N/A')}")
        print(f"  Status: {conn['provisioning_info']['state']}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

## Extract Connection Configuration for Terraform

This script extracts a connection and generates Terraform variable values:

```bash
#!/bin/bash

CONNECTION_NAME="conn_sf_ward"

# Get connection details
CONNECTION_JSON=$(curl -s -H "Authorization: Bearer ${DATABRICKS_TOKEN}" \
  "${DATABRICKS_HOST}/api/2.1/unity-catalog/connections/${CONNECTION_NAME}")

# Extract values using jq
echo "# Terraform Variables for ${CONNECTION_NAME}"
echo ""
echo "connection_name     = \"$(echo $CONNECTION_JSON | jq -r '.name')\""
echo "snowflake_host      = \"$(echo $CONNECTION_JSON | jq -r '.options.host')\""
echo "snowflake_port      = \"$(echo $CONNECTION_JSON | jq -r '.options.port')\""
echo "snowflake_warehouse = \"$(echo $CONNECTION_JSON | jq -r '.options.sfWarehouse')\""
echo "snowflake_role      = \"$(echo $CONNECTION_JSON | jq -r '.options.sfRole')\""
echo "use_proxy           = \"$(echo $CONNECTION_JSON | jq -r '.options.use_proxy')\""
```

## Notes

- **Credentials are not returned** by the API for security reasons
- The API returns metadata and configuration, not secrets
- Use secret scopes or environment variables to manage credentials
- Connection IDs are unique across the metastore

## API Reference

- **Endpoint:** `/api/2.1/unity-catalog/connections`
- **Methods:** GET (list), GET (specific), POST (create), PATCH (update), DELETE (delete)
- **Authentication:** Bearer token required
- **Documentation:** https://docs.databricks.com/api/workspace/connections

---

**Created:** January 11, 2026  
**Purpose:** Extract connection configuration for Terraform deployment
