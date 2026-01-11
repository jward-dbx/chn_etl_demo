# Recipe: Deploy Snowflake Connection Using Terraform

This recipe provides step-by-step instructions for deploying a Snowflake connection to a Databricks workspace using Terraform.

## Prerequisites

- Terraform installed (v1.0 or later)
- Databricks CLI configured (optional but recommended)
- Databricks workspace access with permission to create connections
- Snowflake credentials (username and password)
- Access to create Databricks secret scopes

## Overview

The Snowflake connection configuration uses Terraform to create a reusable, version-controlled deployment that can be applied to multiple workspaces.

**Connection Details:**
- **Source:** `conn_sf_ward` from vending-machine workspace
- **Type:** Snowflake (USERNAME_PASSWORD authentication)
- **Purpose:** Federated queries to Iceberg tables in Snowflake

## Step 1: Set Up Databricks Secrets

Before deploying, you must create a secret scope and store Snowflake credentials.

### Option A: Using Databricks CLI

```bash
# Create secret scope
databricks secrets create-scope --scope snowflake_creds

# Add Snowflake username
databricks secrets put --scope snowflake_creds --key sf_username
# (Enter username when prompted)

# Add Snowflake password
databricks secrets put --scope snowflake_creds --key sf_password
# (Enter password when prompted)

# Verify secrets
databricks secrets list --scope snowflake_creds
```

### Option B: Using Databricks UI

1. Navigate to your Databricks workspace
2. Go to **Settings** → **Secrets**
3. Click **Create Scope**
4. Name: `snowflake_creds`
5. Add secrets:
   - Key: `sf_username`, Value: `<your_snowflake_username>`
   - Key: `sf_password`, Value: `<your_snowflake_password>`

## Step 2: Configure Terraform Variables

Create a `terraform.tfvars` file (git-ignored) with your workspace-specific values:

```bash
cd deployment/terraform/connections

# Copy the example file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

### Required Variables

```hcl
# Databricks Configuration
databricks_host  = "https://your-workspace.cloud.databricks.com"
databricks_token = "dapi..."  # Your Databricks token

# Connection Configuration
connection_name    = "conn_sf_ward"
connection_comment = "Snowflake connection for federated queries"

# Snowflake Configuration
snowflake_host      = "your-account.snowflakecomputing.com"
snowflake_port      = "443"
snowflake_warehouse = "COMPUTE_WH"
snowflake_role      = "ICEBERG_READER"

# Secrets Configuration
secret_scope        = "snowflake_creds"
secret_key_username = "sf_username"
secret_key_password = "sf_password"
```

### Alternative: Use Environment Variables

Instead of `terraform.tfvars`, you can set environment variables:

```bash
export TF_VAR_databricks_host="https://your-workspace.cloud.databricks.com"
export TF_VAR_databricks_token="dapi..."
export TF_VAR_snowflake_host="your-account.snowflakecomputing.com"
# ... etc
```

## Step 3: Initialize Terraform

```bash
cd deployment/terraform/connections

# Download required providers
terraform init
```

**Expected output:**
```
Initializing the backend...
Initializing provider plugins...
- Finding databricks/databricks versions matching "~> 1.0"...
...
Terraform has been successfully initialized!
```

## Step 4: Validate Configuration

```bash
# Check configuration syntax
terraform validate

# Format configuration files
terraform fmt
```

## Step 5: Preview Changes

```bash
# Generate and show execution plan
terraform plan
```

Review the output carefully. You should see:
```
Terraform will perform the following actions:

  # databricks_connection.snowflake will be created
  + resource "databricks_connection" "snowflake" {
      + connection_type = "SNOWFLAKE"
      + name            = "conn_sf_ward"
      + options         = {
          + host        = "REA76172.east-us-2.azure.snowflakecomputing.com"
          + port        = "443"
          + sfWarehouse = "COMPUTE_WH"
          + sfRole      = "ICEBERG_READER"
        }
      ...
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

## Step 6: Apply Configuration

```bash
# Create the connection
terraform apply

# Review the plan and type 'yes' to confirm
```

**Expected output:**
```
databricks_connection.snowflake: Creating...
databricks_connection.snowflake: Creation complete after 3s [id=...]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:
connection_name = "conn_sf_ward"
connection_id   = "fdda8412-8981-45be-a928-c5d9bb7f3a83"
connection_url  = "jdbc://rea76172.east-us-2.azure.snowflakecomputing.com:443/"
```

## Step 7: Verify Connection

### Using Databricks UI

1. Navigate to **Data** → **Connections**
2. Verify `conn_sf_ward` appears in the list
3. Check status is **ACTIVE**

### Using Databricks CLI

```bash
databricks connections list | grep conn_sf_ward
```

### Using SQL

```sql
-- Test the connection
SELECT * FROM SNOWFLAKE_CONNECTION(
  `conn_sf_ward`,
  'SELECT CURRENT_TIMESTAMP() AS test_time'
);
```

## Step 8: Managing the Connection

### Update Connection

1. Modify values in `terraform.tfvars`
2. Run `terraform plan` to preview changes
3. Run `terraform apply` to apply changes

### Destroy Connection

```bash
# ⚠️  WARNING: This will delete the connection
terraform destroy
```

## Deploying to Additional Workspaces

To deploy the same connection to another workspace:

1. **Create new tfvars file:**
   ```bash
   cp terraform.tfvars terraform-prod.tfvars
   ```

2. **Update values** for the new workspace

3. **Apply with specific tfvars:**
   ```bash
   terraform apply -var-file="terraform-prod.tfvars"
   ```

4. **Use Terraform workspaces** (optional):
   ```bash
   terraform workspace new prod
   terraform workspace select prod
   terraform apply -var-file="terraform-prod.tfvars"
   ```

## Troubleshooting

### Issue: "Secret scope not found"
**Solution:** Create the secret scope first (Step 1)

### Issue: "Permission denied"
**Solution:** Ensure your Databricks token has `CREATE CONNECTION` permission

### Issue: "Connection test failed"
**Solution:** 
- Verify Snowflake credentials are correct
- Check Snowflake warehouse is running
- Verify network connectivity between Databricks and Snowflake

### Issue: "Snowflake role doesn't exist"
**Solution:** Verify the role name in Snowflake: `SHOW ROLES;`

## Best Practices

1. **Never commit secrets** - Use secret scopes or environment variables
2. **Use Terraform workspaces** for multi-environment deployments
3. **Store state remotely** (S3, Azure Blob, Terraform Cloud)
4. **Version control everything** except tfvars with secrets
5. **Test in dev first** before applying to production
6. **Document custom configurations** for your team

## Related Resources

- [Terraform Databricks Provider Docs](https://registry.terraform.io/providers/databricks/databricks/latest/docs)
- [Databricks Connections Documentation](https://docs.databricks.com/data-governance/unity-catalog/lakehouse-federation.html)
- [Snowflake Connection Guide](https://docs.databricks.com/data-governance/unity-catalog/external-data-source/snowflake.html)

---

**Created:** January 11, 2026  
**Connection Source:** `conn_sf_ward` (vending-machine workspace)  
**Tool:** Terraform
