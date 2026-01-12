# Unity Catalog Schemas
# Defines schemas within Unity Catalog catalogs

# Schema: SQL Server with Change Tracking Enabled
resource "databricks_schema" "sqlserver_ct_enabled" {
  catalog_name = var.schema_catalog_name
  name         = var.schema_ct_enabled_name
  comment      = var.schema_ct_enabled_comment
  owner        = var.catalog_owner

  properties = {
    change_tracking = "enabled"
    purpose         = "SQL Server data with change tracking enabled"
  }
}

# Schema: SQL Server with Change Tracking Disabled
resource "databricks_schema" "sqlserver_ct_disabled" {
  catalog_name = var.schema_catalog_name
  name         = var.schema_ct_disabled_name
  comment      = var.schema_ct_disabled_comment
  owner        = var.catalog_owner

  properties = {
    change_tracking = "disabled"
    purpose         = "SQL Server data with change tracking disabled"
  }
}
