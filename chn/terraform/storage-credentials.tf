# Unity Catalog Storage Credentials and External Locations
# Defines Azure storage access for Unity Catalog

# Storage Credential: CHN Demo Storage Account
resource "databricks_storage_credential" "chn_demo" {
  name    = var.storage_credential_name
  comment = var.storage_credential_comment

  azure_managed_identity {
    access_connector_id = var.azure_access_connector_id
  }

  # Optional: Set owner
  owner = var.catalog_owner
}

# External Location: CHN Demo Unity Catalog Container
resource "databricks_external_location" "chn_demo_unity_catalog" {
  name            = var.external_location_name
  comment         = var.external_location_comment
  credential_name = databricks_storage_credential.chn_demo.name
  url             = var.external_location_url

  # Optional: Set owner
  owner = var.catalog_owner

  depends_on = [databricks_storage_credential.chn_demo]
}
