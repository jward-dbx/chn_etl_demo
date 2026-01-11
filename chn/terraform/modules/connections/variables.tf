variable "connection_name" {
  description = "Name of the Unity Catalog connection"
  type        = string
}

variable "connection_type" {
  description = "Type of database connection (SQLSERVER, MYSQL, POSTGRESQL, etc.)"
  type        = string
  default     = "SQLSERVER"
}

variable "connection_comment" {
  description = "Description of the connection"
  type        = string
  default     = ""
}

variable "host" {
  description = "Database host address"
  type        = string
}

variable "port" {
  description = "Database port"
  type        = string
  default     = "1433"
}

variable "user" {
  description = "Database username"
  type        = string
  sensitive   = true
}

variable "password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "additional_options" {
  description = "Additional connection options (e.g., applicationIntent, trustServerCertificate)"
  type        = map(string)
  default     = {}
}

variable "properties" {
  description = "Additional metadata properties"
  type        = map(string)
  default     = {}
}

variable "catalog_name" {
  description = "Name of the foreign catalog"
  type        = string
}

variable "catalog_comment" {
  description = "Description of the catalog"
  type        = string
  default     = ""
}

variable "database_name" {
  description = "External database name to mirror in Unity Catalog"
  type        = string
}

variable "isolation_mode" {
  description = "Catalog isolation mode (OPEN, ISOLATED)"
  type        = string
  default     = "OPEN"
}

variable "owner" {
  description = "Owner of the catalog (user or group)"
  type        = string
  default     = null
}
