# Tagging Standards - Agent Skill

## Overview

This agent skill enforces a comprehensive tagging taxonomy for all Databricks artifacts (tables, jobs, pipelines, models, volumes). It enables effective governance, cost management, data discovery, and compliance tracking.

## Required Tags

Every artifact must have:

- `domain` - Business domain (customer, product, finance, etc.)
- `owner` - Team/individual owner email
- `cost_center` - Cost center code
- `environment` - dev, staging, prod
- `layer` - bronze, silver, gold
- `data_classification` - public, internal, confidential, restricted, pii
- `created_date` - ISO 8601 format
- `status` - active, deprecated, archived

## Tag Registry

This skill includes a complete tag registry system:

- Central metadata table for tag definitions
- Controlled vocabularies for consistent values
- Validation rules and regex patterns
- Compliance tracking and reporting
- Automated validation

## Usage with Databricks Assistant

Upload this skill to your workspace:

```bash
databricks workspace import-dir \
  ./agent-skills/tagging-standards \
  /Users/<your-email>/.assistant/skills/tagging-standards
```

Then ask questions like:
- "What tags do I need to apply to my table?"
- "Help me tag all tables in this schema"
- "Validate tags on my tables"
- "Generate a tagging compliance report"
- "What's the tagging standard for PII data?"

## Key Features

- ✅ Comprehensive tag taxonomy
- ✅ Tag registry with controlled vocabularies
- ✅ Validation and compliance tracking
- ✅ Bulk tagging operations
- ✅ Governance dashboards
- ✅ Cost center tracking for chargeback

## Quick Example

```python
# Apply tags to a table
apply_standard_tags(
    catalog="main",
    schema="silver",
    table_name="customers",
    domain="customer",
    owner="data-eng@company.com",
    cost_center="CC-1234",
    environment="prod",
    layer="silver",
    data_classification="pii"
)

# Validate compliance
is_compliant, issues, score = validate_table_tags(
    "main", "silver", "customers"
)
```

See `SKILL.md` for complete documentation and patterns.
