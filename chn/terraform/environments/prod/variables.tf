variable "sqlserver_connection_name" {
  description = "Name of the SQL Server connection"
  type        = string
  default     = "conn_asqldb_awa_prod"
}

variable "sqlserver_host" {
  description = "SQL Server host address"
  type        = string
}

variable "sqlserver_port" {
  description = "SQL Server port"
  type        = string
  default     = "1433"
}

variable "sqlserver_user" {
  description = "SQL Server username"
  type        = string
  sensitive   = true
}

variable "sqlserver_password" {
  description = "SQL Server password"
  type        = string
  sensitive   = true
}

variable "sqlserver_catalog_name" {
  description = "Name of the foreign catalog for SQL Server"
  type        = string
  default     = "conn_asqldb_awa_catalog_prod"
}

variable "sqlserver_database_name" {
  description = "SQL Server database name to mirror"
  type        = string
}

variable "catalog_owner" {
  description = "Owner email for catalogs"
  type        = string
  default     = null
}
