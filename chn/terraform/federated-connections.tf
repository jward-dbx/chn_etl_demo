# Unity Catalog Federated Connections and Catalogs
# Defines SQL Server connections and their associated foreign catalogs

# SQL Server Connection: Adventure Works Database
resource "databricks_connection" "sqlserver_awa" {
  name            = var.sqlserver_connection_name
  connection_type = "SQLSERVER"
  comment         = var.sqlserver_connection_comment

  options = merge(
    {
      host     = var.sqlserver_host
      port     = var.sqlserver_port
      user     = var.sqlserver_user
      password = var.sqlserver_password
    },
    var.sqlserver_additional_options
  )

  properties = merge(
    {
      environment = var.environment
      managed_by  = "terraform"
      purpose     = "Federated queries to Adventure Works SQL Server database"
    },
    var.sqlserver_properties
  )
}

# Foreign Catalog: Adventure Works A Database
resource "databricks_catalog" "sqlserver_awa" {
  name            = var.sqlserver_catalog_name
  comment         = var.sqlserver_catalog_comment
  connection_name = databricks_connection.sqlserver_awa.name

  options = {
    database = var.sqlserver_database_name
  }

  isolation_mode = var.catalog_isolation_mode
  owner          = var.catalog_owner

  depends_on = [databricks_connection.sqlserver_awa]
}

# Foreign Catalog: Adventure Works B Database
resource "databricks_catalog" "sqlserver_awb" {
  name            = var.sqlserver_catalog_name_b
  comment         = var.sqlserver_catalog_comment_b
  connection_name = databricks_connection.sqlserver_awa.name

  options = {
    database = var.sqlserver_database_name_b
  }

  isolation_mode = var.catalog_isolation_mode
  owner          = var.catalog_owner

  depends_on = [databricks_connection.sqlserver_awa]
}
