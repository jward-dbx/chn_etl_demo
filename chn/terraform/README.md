# CHN ETL Demo - Terraform Infrastructure

Infrastructure as Code for CHN ETL Demo project using Terraform and Databricks.

## 📁 Project Structure

```
terraform/
├── provider.tf                    # Provider and Terraform configuration
├── federated-connections.tf       # SQL Server connections and catalogs
├── variables.tf                   # Variable definitions
├── outputs.tf                     # Output definitions
├── backend.tf                     # State backend configuration
├── environments/
│   ├── dev/
│   │   └── terraform.tfvars       # Development environment values
│   └── prod/
│       └── terraform.tfvars.example  # Production environment template
├── modules/                       # [DEPRECATED] Old module structure
└── README.md                      # This file
```

## 🏗️ Architecture

### Infrastructure Defined Once
Following Terraform best practices, infrastructure is defined **once** in the root `terraform/` directory. Environment-specific values are provided via `terraform.tfvars` files in the `environments/` subdirectories.

### File Organization by Purpose

- **`provider.tf`**: Terraform and provider configuration
- **`federated-connections.tf`**: Resources for Unity Catalog connections and foreign catalogs
- **`variables.tf`**: Input variable definitions with validation
- **`outputs.tf`**: Output values after deployment
- **`backend.tf`**: State storage configuration

This organization makes it clear what each file does and scales well as the project grows.

## 🚀 Quick Start

### Prerequisites

1. **Terraform** >= 1.0 installed
2. **Databricks workspace** with Unity Catalog enabled
3. **Databricks token** with appropriate permissions

### Deploy to Development

```bash
# Navigate to terraform directory
cd /Users/justin.ward/chn/terraform

# Set Databricks credentials
export DATABRICKS_HOST="https://adb-7405607609261208.8.azuredatabricks.net"
export DATABRICKS_TOKEN="your-token-here"

# Initialize Terraform (first time only)
terraform init

# Review planned changes
terraform plan -var-file=environments/dev/terraform.tfvars

# Apply changes
terraform apply -var-file=environments/dev/terraform.tfvars

# View outputs
terraform output
```

### Deploy to Production

```bash
# Copy and customize production variables
cp environments/prod/terraform.tfvars.example environments/prod/terraform.tfvars
# Edit environments/prod/terraform.tfvars with production values

# Set production credentials
export DATABRICKS_HOST="https://your-prod-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-prod-token"

# Deploy
terraform plan -var-file=environments/prod/terraform.tfvars
terraform apply -var-file=environments/prod/terraform.tfvars
```

## 📝 What Gets Created

### SQL Server Connection
- **Name**: `conn_asqldb_awa` (dev) / `conn_asqldb_awa_prod` (prod)
- **Type**: SQL Server (read-only)
- **Purpose**: Federated queries to Adventure Works database

### Foreign Catalog
- **Name**: `conn_asqldb_awa_catalog` (dev) / `conn_asqldb_awa_catalog_prod` (prod)
- **Type**: FOREIGN_CATALOG
- **Mirrors**: Adventure Works SQL Server database

## 🔧 Configuration

### Environment Variables

All configurations support environment-specific customization through `terraform.tfvars`:

| Variable | Description | Required |
|----------|-------------|----------|
| `environment` | Deployment environment (dev/staging/prod) | Yes |
| `sqlserver_connection_name` | Connection name | Yes |
| `sqlserver_host` | SQL Server hostname | Yes |
| `sqlserver_user` | Database username | Yes |
| `sqlserver_password` | Database password | Yes |
| `sqlserver_database_name` | Database to federate | Yes |
| `sqlserver_catalog_name` | Foreign catalog name | Yes |
| `catalog_owner` | Catalog owner email | No |

### Example terraform.tfvars

```hcl
environment = "dev"

sqlserver_connection_name = "conn_asqldb_awa"
sqlserver_host            = "myserver.database.windows.net"
sqlserver_user            = "admin_user"
sqlserver_password        = "SecurePassword123!"
sqlserver_database_name   = "adventure-works-a"

sqlserver_catalog_name = "conn_asqldb_awa_catalog"
catalog_owner          = "user@company.com"
```

## 🎯 Usage After Deployment

Once deployed, query the SQL Server database through Unity Catalog:

```sql
-- List available schemas
SHOW SCHEMAS IN conn_asqldb_awa_catalog;

-- Query federated data
SELECT * FROM conn_asqldb_awa_catalog.dbo.Customers LIMIT 10;

-- Join with local data
SELECT 
  local.customer_id,
  local.order_count,
  remote.customer_name
FROM my_catalog.my_schema.local_orders local
JOIN conn_asqldb_awa_catalog.dbo.Customers remote
  ON local.customer_id = remote.customer_id;
```

## 🔄 State Management

### Local State (Default)
State is stored locally in `terraform.tfstate`. **Do not commit this file to git.**

### Remote State (Recommended for Production)
Update `backend.tf` to use remote state:

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "tfstatechn"
    container_name       = "terraform-state"
    key                  = "chn-etl-demo.tfstate"
  }
}
```

Then reinitialize:
```bash
terraform init -reconfigure
```

## 🛡️ Security Best Practices

1. **Never commit secrets**: `terraform.tfvars` is gitignored
2. **Use environment variables** for sensitive data when possible
3. **Enable encryption** for remote state storage
4. **Restrict IAM permissions** to least privilege
5. **Review plans** before applying changes
6. **Use remote state** with state locking in production

## 📊 Outputs

After deployment, Terraform provides useful outputs:

```bash
terraform output sqlserver_connection_id
terraform output sqlserver_catalog_name
terraform output deployment_summary  # Full summary in JSON format
```

## 🧹 Cleanup

To destroy all managed resources:

```bash
# Review what will be destroyed
terraform plan -destroy -var-file=environments/dev/terraform.tfvars

# Destroy resources
terraform destroy -var-file=environments/dev/terraform.tfvars
```

## 📚 Additional Documentation

- [Terraform Quickstart](./QUICKSTART.md) - Step-by-step deployment guide
- [Configuration Summary](./CONFIGURATION_SUMMARY.md) - Detailed configuration reference
- [Databricks Unity Catalog Docs](https://docs.databricks.com/data-governance/unity-catalog/index.html)
- [Databricks Terraform Provider](https://registry.terraform.io/providers/databricks/databricks/latest/docs)

## 🆘 Troubleshooting

### Connection Test Fails
- Verify SQL Server is running (Azure SQL Serverless may need to spin up)
- Check firewall rules allow Databricks IP ranges
- Confirm credentials are correct

### State Lock Issues
- Ensure no other Terraform operations are running
- If using remote state, verify backend configuration

### Import Existing Resources
```bash
terraform import databricks_connection.sqlserver_awa "metastore_id|connection_name"
terraform import databricks_catalog.sqlserver_awa "catalog_name"
```

---

**Maintained by**: Data Engineering Team  
**Last Updated**: January 2026  
**Terraform Version**: >= 1.0  
**Provider Version**: databricks ~> 1.0
