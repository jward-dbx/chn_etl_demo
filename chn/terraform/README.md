# Terraform Configuration for CHN ETL Demo
# Databricks Unity Catalog Connections and Catalogs

This directory contains Terraform configurations for managing Databricks resources in the CHN ETL Demo workspace.

## Directory Structure

```
terraform/
├── modules/
│   └── connections/          # Reusable module for connections and catalogs
│       ├── main.tf          # Main resource definitions
│       ├── variables.tf     # Input variables
│       └── outputs.tf       # Output values
├── environments/
│   ├── dev/                 # Development environment
│   │   ├── main.tf         # Dev environment configuration
│   │   ├── variables.tf    # Dev-specific variables
│   │   ├── terraform.tfvars # Dev variable values (gitignored)
│   │   └── backend.tf      # State backend configuration
│   └── prod/                # Production environment
│       ├── main.tf
│       ├── variables.tf
│       ├── terraform.tfvars
│       └── backend.tf
└── README.md                # This file
```

## Usage

### Prerequisites

1. Install [Terraform](https://www.terraform.io/downloads) (>= 1.0)
2. Set up Databricks authentication:
   ```bash
   export DATABRICKS_HOST="https://fe-sandbox-chn-etl-demo.cloud.databricks.com"
   export DATABRICKS_TOKEN="your-token-here"
   ```

### Initialize and Apply

```bash
# Navigate to the environment
cd environments/dev

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply the configuration
terraform apply
```

### Creating New Connections

1. Add connection details to `terraform.tfvars`
2. Run `terraform plan` to review changes
3. Run `terraform apply` to create resources

## Module: connections

Creates Databricks Unity Catalog connections and foreign catalogs for federated queries.

### Inputs

| Name | Description | Type | Required |
|------|-------------|------|----------|
| `connection_name` | Name of the connection | string | yes |
| `connection_type` | Type of connection (SQLSERVER, MYSQL, etc.) | string | yes |
| `host` | Database host | string | yes |
| `port` | Database port | string | yes |
| `user` | Database user | string | yes |
| `password` | Database password (use secrets in production) | string | yes |
| `catalog_name` | Name of the foreign catalog | string | yes |
| `database_name` | External database to mirror | string | yes |

### Outputs

| Name | Description |
|------|-------------|
| `connection_id` | ID of the created connection |
| `catalog_id` | ID of the created catalog |

## Security Best Practices

1. **Never commit secrets**: Use `.gitignore` for `terraform.tfvars`
2. **Use Databricks secrets**: Store credentials in Databricks secrets and reference them
3. **State management**: Use remote state (S3, Azure Blob, etc.) for team collaboration
4. **Least privilege**: Grant minimal required permissions

## Resources

- [Databricks Terraform Provider](https://registry.terraform.io/providers/databricks/databricks/latest/docs)
- [Unity Catalog Connections](https://registry.terraform.io/providers/databricks/databricks/latest/docs/resources/connection)
- [Foreign Catalogs](https://registry.terraform.io/providers/databricks/databricks/latest/docs/resources/catalog)
