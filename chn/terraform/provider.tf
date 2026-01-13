# Terraform and Provider Configuration
# Authentication via environment variables: DATABRICKS_HOST and DATABRICKS_TOKEN

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0"
    }
  }
}

provider "databricks" {
  # Credentials configured via environment variables:
  # - DATABRICKS_HOST
  # - DATABRICKS_TOKEN
}
