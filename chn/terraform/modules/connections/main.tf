# Unity Catalog Connection Module
# Creates a database connection and foreign catalog for federated queries

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0"
    }
  }
}

# SQL Server Connection
resource "databricks_connection" "this" {
  name            = var.connection_name
  connection_type = var.connection_type
  comment         = var.connection_comment

  options = merge(
    {
      host = var.host
      port = var.port
      user = var.user
      password = var.password
    },
    var.additional_options
  )

  properties = var.properties
}

# Foreign Catalog
resource "databricks_catalog" "this" {
  name            = var.catalog_name
  comment         = var.catalog_comment
  connection_name = databricks_connection.this.name

  options = {
    database = var.database_name
  }

  isolation_mode = var.isolation_mode
  
  # Optional: Set owner
  owner = var.owner

  depends_on = [databricks_connection.this]
}
