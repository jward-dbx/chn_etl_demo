# Getting Started with Silver Layer ETL Development Skills

## Overview

This comprehensive **Agent Skill** for Databricks provides everything you need to build production-grade silver layer ETL pipelines following enterprise best practices. It's designed to work with both Databricks Assistant (powered by Claude's Agent Skills framework) and as standalone development resources.

## What's Included

### 📚 Complete Skill Package

```
etl-silver-layer/
├── SKILL.md                      # Main skill definition (loaded by Databricks Assistant)
├── README.md                     # Skill documentation
├── GETTING_STARTED.md           # This file
│
├── examples/                     # Working code examples
│   ├── databricks.yml           # Complete DAB configuration
│   ├── silver_pipeline_example.py    # Full PySpark pipeline
│   ├── transformations.sql      # SQL transformation patterns
│   └── customer_silver_dlt.py   # Delta Live Tables example
│
├── templates/                    # Reusable templates
│   ├── data_quality_rules.py    # DQ framework with Great Expectations
│   ├── test_transformations.py  # Unit test template with pytest
│   ├── silver_table_schema.py   # Schema builder and validators
│   ├── config_template.yml      # Pipeline configuration
│   └── scd_type2_merge.sql     # SCD Type 2 SQL patterns
│
├── scripts/                      # Automation scripts
│   ├── deploy_pipeline.sh       # Deployment automation
│   ├── run_tests.sh            # Test runner
│   ├── validate_schema.py      # Schema validation
│   └── generate_dq_report.py   # DQ reporting
│
└── docs/                        # Documentation
    ├── standards.md            # Naming conventions and standards
    ├── best_practices.md       # Development best practices
    └── troubleshooting.md      # Common issues and solutions
```

## Quick Start

### Option 1: Use with Databricks Assistant (Recommended)

1. **Upload to Databricks Workspace:**
   ```bash
   databricks workspace import-dir \
     ./agent-skills/etl-silver-layer \
     /Users/<your-email>/.assistant/skills/etl-silver-layer
   ```

2. **Start using in Databricks:**
   - Open any Databricks notebook
   - Click on the Assistant icon
   - The skill will automatically load when you ask ETL-related questions

3. **Example prompts:**
   ```
   "Help me create a silver layer pipeline for customer data"
   "What are the standard column naming conventions?"
   "Generate unit tests for my customer transformation"
   "Set up data quality rules for the orders table"
   "Show me how to implement SCD Type 2 for products"
   ```

### Option 2: Use as Development Reference

1. **Browse examples:** 
   - Check `examples/` for complete working code
   - Copy and adapt to your use case

2. **Use templates:**
   - Copy templates from `templates/` directory
   - Customize for your specific tables

3. **Run scripts:**
   ```bash
   # Deploy a pipeline
   cd agent-skills/etl-silver-layer
   ./scripts/deploy_pipeline.sh --target dev
   
   # Run tests
   ./scripts/run_tests.sh --coverage
   
   # Validate schemas
   python scripts/validate_schema.py --env dev
   ```

## Key Features

### ✅ Enforced Standards

All silver layer tables must follow these standards:

- **Column Naming:** snake_case, entity-prefixed (`customer_first_name`)
- **Boolean Columns:** `is_*`, `has_*`, `needs_*` prefix
- **Timestamps:** `*_at`, `*_date` suffix  
- **Amounts:** `*_amount` suffix with DecimalType(18, 2)
- **Required Metadata:** 6 mandatory columns on every table

### ✅ Data Quality Framework

Built-in data quality checks:
- **Completeness:** Null value validation
- **Validity:** Format and range checks
- **Uniqueness:** Primary key constraints
- **Consistency:** Cross-field validation
- **Timeliness:** Data freshness checks
- **Accuracy:** Business rule validation

### ✅ Testing Infrastructure

Comprehensive testing approach:
- Unit tests with pytest and pytest-spark
- Integration test patterns
- Schema validation tests
- Data quality assertion tests
- Mock data fixtures

### ✅ SCD Type 2 Support

Full Slowly Changing Dimension Type 2 implementation:
- Historical tracking with effective dates
- Merge patterns for updates
- Query patterns for point-in-time analysis
- Automated version management

### ✅ Performance Optimization

Best practices for scale:
- Partitioning strategies
- Z-ordering recommendations
- Liquid clustering examples
- Optimized write patterns
- Skew handling

## Usage Examples

### Example 1: Create a New Silver Table

```python
# 1. Define schema using builder
from templates.silver_table_schema import SilverSchemaBuilder

schema = SilverSchemaBuilder() \
    .add_business_key("order_id", StringType(), nullable=False) \
    .add_business_key("customer_id", StringType(), nullable=False) \
    .add_timestamp("order_date", nullable=False) \
    .add_amount("order_total_amount") \
    .add_boolean_flag("is_completed") \
    .add_metadata_columns() \
    .build()

# 2. Create transformation
def transform_orders(bronze_df):
    return bronze_df.select(
        F.col("order_id"),
        F.col("customer_id"),
        F.to_timestamp("order_date").alias("order_date"),
        F.col("total").cast(DecimalType(18,2)).alias("order_total_amount"),
        F.when(F.col("status") == "COMPLETED", True).otherwise(False).alias("is_completed"),
        # ... add metadata columns
    )

# 3. Write with quality checks
validator = DataQualityValidator(spark, catalog, schema)
result = validator.validate_table("orders_silver")

if result["is_valid"]:
    transformed_df.write.saveAsTable("orders_silver")
```

### Example 2: Implement SCD Type 2

```python
# Use the provided CustomerSilverTransformer class
from examples.silver_pipeline_example import CustomerSilverTransformer

transformer = CustomerSilverTransformer(
    spark, 
    source_catalog="dev_catalog",
    source_schema="bronze",
    target_catalog="dev_catalog",
    target_schema="silver",
    load_id="20240112_001"
)

# Transform and upsert with SCD Type 2 logic
transformed_df = transformer.transform()
transformer.upsert_to_silver(transformed_df)
```

### Example 3: Run Data Quality Checks

```python
from templates.data_quality_rules import DataQualityValidator

# Initialize validator
validator = DataQualityValidator(
    spark=spark,
    catalog="dev_catalog",
    schema="silver"
)

# Validate a table
results = validator.validate_table("customers_silver")

# Print report
print(validator.generate_quality_report(results))

# Log issues if validation failed
if not results["is_valid"]:
    validator.log_quality_issues(results)
```

### Example 4: Deploy with Databricks Asset Bundles

```bash
# 1. Copy the example bundle configuration
cp examples/databricks.yml your_project/

# 2. Customize for your tables and pipelines
vim your_project/databricks.yml

# 3. Validate configuration
databricks bundle validate --target dev

# 4. Deploy
./scripts/deploy_pipeline.sh --target dev
```

## Standards Compliance

### Required Metadata Columns

Every silver table MUST include:

```python
record_created_at    TIMESTAMP NOT NULL   # When record created in silver
record_updated_at    TIMESTAMP NOT NULL   # Last update timestamp  
source_system        STRING NOT NULL      # Origin system identifier
load_id              STRING NOT NULL      # Batch/job identifier
is_current           BOOLEAN NOT NULL     # Current version flag
is_deleted           BOOLEAN NOT NULL     # Soft delete flag
```

### SCD Type 2 Columns (Recommended)

For historical tracking:

```python
effective_start_date TIMESTAMP NOT NULL   # Version start date
effective_end_date   TIMESTAMP NULL       # Version end date (NULL = current)
```

### Validation

Run schema validation before promoting to production:

```bash
python scripts/validate_schema.py --env dev --table your_table
```

## Best Practices Checklist

Before deploying a silver layer pipeline:

- [ ] All column names follow snake_case convention
- [ ] Boolean columns use `is_*`/`has_*`/`needs_*` prefix
- [ ] Timestamp columns use `*_at`/`*_date` suffix
- [ ] Amount columns use `*_amount` suffix with DecimalType(18,2)
- [ ] All 6 required metadata columns present
- [ ] SCD Type 2 implemented (if tracking history)
- [ ] Data quality rules defined and tested
- [ ] Unit tests written and passing (>80% coverage)
- [ ] Schema validation passes
- [ ] Table partitioned appropriately
- [ ] Z-ordering configured
- [ ] Change data feed enabled
- [ ] Documentation updated

## Learning Path

### Beginner (Day 1)

1. Read `docs/standards.md` - Understand naming conventions
2. Review `examples/silver_pipeline_example.py` - See complete example
3. Copy `templates/silver_table_schema.py` - Create your first table
4. Run `scripts/validate_schema.py` - Validate your table

### Intermediate (Week 1)

1. Implement data quality checks using `templates/data_quality_rules.py`
2. Write unit tests based on `templates/test_transformations.py`
3. Study `examples/transformations.sql` - Learn SQL patterns
4. Implement SCD Type 2 using `templates/scd_type2_merge.sql`

### Advanced (Month 1)

1. Create Databricks Asset Bundle using `examples/databricks.yml`
2. Set up Delta Live Tables pipeline with `examples/customer_silver_dlt.py`
3. Implement full CI/CD with `scripts/deploy_pipeline.sh`
4. Build custom data quality framework
5. Optimize for performance (partitioning, Z-ordering, clustering)

## Troubleshooting

Common issues and solutions are documented in `docs/troubleshooting.md`.

Quick tips:

- **Schema validation fails?** Check column naming conventions
- **Tests failing?** Verify test data matches production schema
- **Slow performance?** Review partitioning and Z-ordering
- **Data quality issues?** Check quarantine table for bad records
- **Deployment errors?** Validate bundle and check permissions

## Resources

### Documentation

- [Standards](docs/standards.md) - Detailed naming and schema standards
- [Best Practices](docs/best_practices.md) - Development best practices
- [Troubleshooting](docs/troubleshooting.md) - Common issues and fixes

### Examples

- [Full Pipeline Example](examples/silver_pipeline_example.py) - Complete working code
- [SQL Transformations](examples/transformations.sql) - Declarative SQL patterns
- [Delta Live Tables](examples/customer_silver_dlt.py) - DLT implementation
- [Asset Bundle](examples/databricks.yml) - DAB configuration

### Templates

- [Data Quality Rules](templates/data_quality_rules.py) - Reusable DQ framework
- [Unit Tests](templates/test_transformations.py) - Test templates
- [Schema Builder](templates/silver_table_schema.py) - Schema utilities
- [SCD Type 2](templates/scd_type2_merge.sql) - Historical tracking patterns

## Support

- **Databricks Assistant:** Ask questions directly in any notebook
- **Documentation:** Comprehensive docs in `docs/` folder
- **Examples:** Working code in `examples/` folder
- **Templates:** Reusable patterns in `templates/` folder

## Contributing

To extend this skill:

1. Add new examples to `examples/`
2. Create reusable templates in `templates/`
3. Update `SKILL.md` with new patterns
4. Add documentation to `docs/`
5. Share with the team!

## Version

- **Version:** 1.0.0
- **Created:** January 2026
- **Compatible:** Databricks Runtime 13.3+, Agent Skills Open Standard
- **License:** Internal use only

---

**Ready to build production-grade silver layer pipelines? Start with the examples or ask Databricks Assistant for help!** 🚀
