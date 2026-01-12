# Terraform Variables for CHN ETL Demo Infrastructure
# Set values in environment-specific terraform.tfvars files

# ============================================================================
# ENVIRONMENT
# ============================================================================

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

# ============================================================================
# SQL SERVER CONNECTION
# ============================================================================

variable "sqlserver_connection_name" {
  description = "Name of the SQL Server Unity Catalog connection"
  type        = string
}

variable "sqlserver_connection_comment" {
  description = "Description of the SQL Server connection"
  type        = string
  default     = "SQL Server federation connection"
}

variable "sqlserver_host" {
  description = "SQL Server host address (e.g., server.database.windows.net)"
  type        = string
}

variable "sqlserver_port" {
  description = "SQL Server port number"
  type        = string
  default     = "1433"
}

variable "sqlserver_user" {
  description = "SQL Server authentication username"
  type        = string
  sensitive   = true
}

variable "sqlserver_password" {
  description = "SQL Server authentication password"
  type        = string
  sensitive   = true
}

variable "sqlserver_database_name" {
  description = "SQL Server database name to federate"
  type        = string
}

variable "sqlserver_additional_options" {
  description = "Additional SQL Server connection options"
  type        = map(string)
  default = {
    applicationIntent      = "ReadOnly"
    trustServerCertificate = "true"
  }
}

variable "sqlserver_properties" {
  description = "Additional metadata properties for the connection"
  type        = map(string)
  default     = {}
}

# ============================================================================
# FOREIGN CATALOG
# ============================================================================

variable "sqlserver_catalog_name" {
  description = "Name of the foreign catalog for SQL Server"
  type        = string
}

variable "sqlserver_catalog_comment" {
  description = "Description of the foreign catalog"
  type        = string
  default     = "Foreign catalog mirroring SQL Server database"
}

variable "catalog_isolation_mode" {
  description = "Catalog isolation mode (OPEN or ISOLATED)"
  type        = string
  default     = "OPEN"
  
  validation {
    condition     = contains(["OPEN", "ISOLATED"], var.catalog_isolation_mode)
    error_message = "Isolation mode must be OPEN or ISOLATED."
  }
}

variable "catalog_owner" {
  description = "Owner email address for the catalog"
  type        = string
  default     = null
}

# ============================================================================
# FOREIGN CATALOG - ADVENTURE WORKS B
# ============================================================================

variable "sqlserver_catalog_name_b" {
  description = "Name of the foreign catalog for SQL Server database B"
  type        = string
}

variable "sqlserver_catalog_comment_b" {
  description = "Description of the foreign catalog for database B"
  type        = string
  default     = "Foreign catalog mirroring SQL Server database B"
}

variable "sqlserver_database_name_b" {
  description = "SQL Server database B name to federate"
  type        = string
}

# ============================================================================
# STORAGE CREDENTIALS
# ============================================================================

variable "storage_credential_name" {
  description = "Name of the storage credential"
  type        = string
}

variable "storage_credential_comment" {
  description = "Description of the storage credential"
  type        = string
  default     = "Storage credential for CHN demo"
}

variable "azure_access_connector_id" {
  description = "Azure Databricks Access Connector resource ID"
  type        = string
}

# ============================================================================
# EXTERNAL LOCATIONS
# ============================================================================

variable "external_location_name" {
  description = "Name of the external location"
  type        = string
}

variable "external_location_comment" {
  description = "Description of the external location"
  type        = string
  default     = "External location for CHN demo Unity Catalog data"
}

variable "external_location_url" {
  description = "ABFSS URL for the external location (e.g., abfss://container@storage.dfs.core.windows.net/path)"
  type        = string
}
