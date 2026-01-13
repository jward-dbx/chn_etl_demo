# Terraform Quick Start Guide

## Setup

1. **Install Terraform**
   ```bash
   brew install terraform  # macOS
   # or download from https://www.terraform.io/downloads
   ```

2. **Set Databricks credentials**
   ```bash
   export DATABRICKS_HOST="https://adb-7405607609261208.8.azuredatabricks.net"
   export DATABRICKS_TOKEN="your-token-here"
   ```

3. **Navigate to environment**
   ```bash
   cd terraform/environments/dev
   ```

4. **Create terraform.tfvars from example**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with actual values
   ```

5. **Initialize Terraform**
   ```bash
   terraform init
   ```

6. **Plan and apply**
   ```bash
   terraform plan
   terraform apply
   ```

## Current Resources

- SQL Server connection: `conn_asqldb_awa`
- Foreign catalog: `conn_asqldb_awa_catalog`
- Database: `adventure-works-a`

See full documentation in `terraform/README.md`
