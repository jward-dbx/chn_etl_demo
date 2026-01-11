# Backend configuration for Terraform state
# Uncomment and configure when ready to use remote state

# terraform {
#   backend "s3" {
#     bucket         = "chn-terraform-state"
#     key            = "prod/databricks/terraform.tfstate"
#     region         = "us-east-1"
#     encrypt        = true
#     dynamodb_table = "terraform-state-lock"
#   }
# }

# For local development, state is stored locally in terraform.tfstate
