output "connection_id" {
  description = "The ID of the created connection"
  value       = databricks_connection.this.id
}

output "connection_name" {
  description = "The name of the created connection"
  value       = databricks_connection.this.name
}

output "connection_url" {
  description = "The JDBC URL of the connection"
  value       = databricks_connection.this.url
}

output "catalog_id" {
  description = "The ID of the created catalog"
  value       = databricks_catalog.this.id
}

output "catalog_name" {
  description = "The name of the created catalog"
  value       = databricks_catalog.this.name
}

output "catalog_full_name" {
  description = "The full name of the catalog"
  value       = databricks_catalog.this.full_name
}
