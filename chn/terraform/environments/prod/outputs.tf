output "sqlserver_connection_id" {
  description = "ID of the SQL Server connection"
  value       = module.sqlserver_awa.connection_id
}

output "sqlserver_connection_url" {
  description = "JDBC URL of the SQL Server connection"
  value       = module.sqlserver_awa.connection_url
}

output "sqlserver_catalog_id" {
  description = "ID of the Adventure Works catalog"
  value       = module.sqlserver_awa.catalog_id
}

output "sqlserver_catalog_name" {
  description = "Name of the Adventure Works catalog"
  value       = module.sqlserver_awa.catalog_name
}
