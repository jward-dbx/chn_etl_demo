# Configuration Files

This directory contains environment-specific configuration files.

## Structure

- **dev/**: Development environment configurations
- **prod/**: Production environment configurations

## Usage

Configuration files should include:
- Database connection settings (catalog, schema)
- Compute resource specifications
- Feature flags
- Environment-specific parameters

## Security

⚠️ **IMPORTANT**: Never commit sensitive credentials to git!

- Use Databricks secrets for sensitive information
- Use environment variables for workspace-specific settings
- Reference secrets in configuration files, never hard-code

## Example

```yaml
# config/dev/database.yml
catalog: dev_omop
schema: cdm_54
warehouse_id: abc123def456
```
