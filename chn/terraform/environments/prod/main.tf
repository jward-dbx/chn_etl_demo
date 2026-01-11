# Production Environment - CHN ETL Demo
# Databricks Unity Catalog Configuration

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0"
    }
  }
}

# Databricks Provider Configuration
provider "databricks" {
  # host and token configured via environment variables
  # DATABRICKS_HOST and DATABRICKS_TOKEN
}

# SQL Server Connection: Adventure Works Azure SQL Database
module "sqlserver_awa" {
  source = "../../modules/connections"

  # Connection configuration
  connection_name    = var.sqlserver_connection_name
  connection_type    = "SQLSERVER"
  connection_comment = "SQL Server federation connection to Adventure Works database (Production)"

  # Database connection details
  host     = var.sqlserver_host
  port     = var.sqlserver_port
  user     = var.sqlserver_user
  password = var.sqlserver_password

  # SQL Server specific options
  additional_options = {
    applicationIntent       = "ReadOnly"
    trustServerCertificate = "true"
  }

  # Metadata
  properties = {
    environment = "prod"
    purpose     = "Federated queries to Adventure Works SQL Server database"
    managed_by  = "terraform"
  }

  # Foreign catalog configuration
  catalog_name    = var.sqlserver_catalog_name
  catalog_comment = "Foreign catalog mirroring Adventure Works SQL Server database (Production)"
  database_name   = var.sqlserver_database_name
  isolation_mode  = "OPEN"
  owner           = var.catalog_owner
}
