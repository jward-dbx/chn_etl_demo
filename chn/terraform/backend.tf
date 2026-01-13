# Terraform Backend Configuration
# Stores Terraform state file

# Uncomment and configure for remote state storage
# For local development, state is stored in terraform.tfstate

# Example: Azure Storage Account Backend
# terraform {
#   backend "azurerm" {
#     resource_group_name  = "terraform-state-rg"
#     storage_account_name = "tfstatechn"
#     container_name       = "terraform-state"
#     key                  = "chn-etl-demo.tfstate"
#   }
# }

# Example: AWS S3 Backend
# terraform {
#   backend "s3" {
#     bucket = "terraform-state-chn"
#     key    = "chn-etl-demo/terraform.tfstate"
#     region = "us-east-1"
#   }
# }

# Example: Databricks Unity Catalog Volume (if supported)
# terraform {
#   backend "local" {
#     path = "terraform.tfstate"
#   }
# }

# For now, using local state
# Run terraform init -reconfigure when switching backends
