# Terraform Outputs
# Provides information about created resources

# ============================================================================
# SQL SERVER CONNECTION OUTPUTS
# ============================================================================

output "sqlserver_connection_id" {
  description = "ID of the SQL Server connection"
  value       = databricks_connection.sqlserver_awa.id
}

output "sqlserver_connection_name" {
  description = "Name of the SQL Server connection"
  value       = databricks_connection.sqlserver_awa.name
}

output "sqlserver_connection_url" {
  description = "JDBC URL of the SQL Server connection"
  value       = databricks_connection.sqlserver_awa.url
}

output "sqlserver_connection_state" {
  description = "Provisioning state of the SQL Server connection"
  value       = databricks_connection.sqlserver_awa.provisioning_info
}

# ============================================================================
# FOREIGN CATALOG OUTPUTS
# ============================================================================

output "sqlserver_catalog_id" {
  description = "ID of the SQL Server foreign catalog"
  value       = databricks_catalog.sqlserver_awa.id
}

output "sqlserver_catalog_name" {
  description = "Name of the SQL Server foreign catalog"
  value       = databricks_catalog.sqlserver_awa.name
}

output "sqlserver_catalog_full_name" {
  description = "Full name of the SQL Server foreign catalog"
  value       = databricks_catalog.sqlserver_awa.full_name
}

output "sqlserver_catalog_type" {
  description = "Type of the catalog"
  value       = databricks_catalog.sqlserver_awa.catalog_type
}

# ============================================================================
# FOREIGN CATALOG B OUTPUTS
# ============================================================================

output "sqlserver_catalog_b_id" {
  description = "ID of the SQL Server foreign catalog B"
  value       = databricks_catalog.sqlserver_awb.id
}

output "sqlserver_catalog_b_name" {
  description = "Name of the SQL Server foreign catalog B"
  value       = databricks_catalog.sqlserver_awb.name
}

output "sqlserver_catalog_b_full_name" {
  description = "Full name of the SQL Server foreign catalog B"
  value       = databricks_catalog.sqlserver_awb.full_name
}

output "sqlserver_catalog_b_type" {
  description = "Type of the catalog B"
  value       = databricks_catalog.sqlserver_awb.catalog_type
}

# ============================================================================
# SUMMARY OUTPUT
# ============================================================================

output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    environment    = var.environment
    connection     = databricks_connection.sqlserver_awa.name
    catalogs       = [
      databricks_catalog.sqlserver_awa.name,
      databricks_catalog.sqlserver_awb.name
    ]
    databases      = [
      var.sqlserver_database_name,
      var.sqlserver_database_name_b
    ]
    connection_url = databricks_connection.sqlserver_awa.url
  }
}
