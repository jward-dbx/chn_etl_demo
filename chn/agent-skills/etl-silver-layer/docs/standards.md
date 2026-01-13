# Silver Layer Standards and Conventions

## Overview

This document defines the enterprise standards for silver layer data tables in Databricks. All silver layer implementations must adhere to these standards to ensure consistency, quality, and maintainability.

## Table of Contents

- [Column Naming Conventions](#column-naming-conventions)
- [Required Metadata Columns](#required-metadata-columns)
- [Data Types](#data-types)
- [SCD Type 2 Implementation](#scd-type-2-implementation)
- [Data Quality Requirements](#data-quality-requirements)
- [Table Properties](#table-properties)

## Column Naming Conventions

### General Rules

1. **Use snake_case**: All column names must be in snake_case (lowercase with underscores)
   - ✅ `customer_first_name`
   - ❌ `CustomerFirstName`, `customerFirstName`, `customer-first-name`

2. **No special characters**: Only alphanumeric and underscores allowed
   - ✅ `order_total_amount`
   - ❌ `order$total`, `order.total`, `order-total`

3. **No leading/trailing underscores**
   - ✅ `customer_id`
   - ❌ `_customer_id`, `customer_id_`

4. **No consecutive underscores**
   - ✅ `customer_address_line1`
   - ❌ `customer__address`

### Entity-Specific Naming

Prefix column names with the entity they describe:

```
Customer entity:
- customer_id
- customer_first_name
- customer_email
- customer_created_at

Order entity:
- order_id
- order_date
- order_total_amount
- order_status
```

### Boolean Columns

Boolean columns must use one of these prefixes:

- `is_`: State or status (`is_active`, `is_deleted`, `is_verified`)
- `has_`: Possession or presence (`has_address`, `has_discount`, `has_children`)
- `needs_`: Requirement (`needs_approval`, `needs_reorder`)

### Timestamp Columns

Timestamp columns must use one of these suffixes:

- `_at`: Specific point in time (`created_at`, `updated_at`, `shipped_at`)
- `_date`: Date value (`order_date`, `birth_date`, `effective_start_date`)
- `_time`: Time value (`processing_time`, `delivery_time`)

### Numeric Columns

#### Amounts (Monetary Values)

Use `_amount` suffix with DecimalType(18, 2):
- `order_total_amount`
- `customer_balance_amount`
- `product_cost_amount`

#### Counts

Use `_count` suffix with IntegerType:
- `order_item_count`
- `customer_purchase_count`
- `product_quantity_count`

#### Rates/Percentages

Use `_rate` or `_percent` suffix with DecimalType(10, 4):
- `tax_rate`
- `discount_rate`
- `conversion_rate`

## Required Metadata Columns

Every silver layer table MUST include these metadata columns:

### Standard Metadata

```python
record_created_at    TIMESTAMP NOT NULL   # When record was created in silver
record_updated_at    TIMESTAMP NOT NULL   # Last update timestamp
source_system        STRING NOT NULL      # Origin system identifier
load_id              STRING NOT NULL      # Batch/job identifier for lineage
is_current           BOOLEAN NOT NULL     # Current version flag (for SCD Type 2)
is_deleted           BOOLEAN NOT NULL     # Soft delete flag
```

### SCD Type 2 Columns (Recommended)

For tables tracking historical changes:

```python
effective_start_date TIMESTAMP NOT NULL   # When this version became active
effective_end_date   TIMESTAMP NULL       # When this version ended (NULL for current)
```

## Data Types

### Standard Type Mapping

| Use Case | Data Type | Example |
|----------|-----------|---------|
| Primary Keys | StringType | `customer_id STRING` |
| Names/Text | StringType | `customer_first_name STRING` |
| Descriptions | StringType | `product_description STRING` |
| Monetary Amounts | DecimalType(18, 2) | `order_total_amount DECIMAL(18,2)` |
| Quantities/Counts | IntegerType | `order_quantity INT` |
| Rates/Percentages | DecimalType(10, 4) | `tax_rate DECIMAL(10,4)` |
| Dates | DateType | `birth_date DATE` |
| Timestamps | TimestampType | `created_at TIMESTAMP` |
| Flags | BooleanType | `is_active BOOLEAN` |

### Decimal Precision Guidelines

- **Monetary amounts**: DecimalType(18, 2) - supports up to 999,999,999,999,999.99
- **Rates/percentages**: DecimalType(10, 4) - supports 0.0000 to 999999.9999
- **Weights/measures**: DecimalType(10, 2) - supports up to 99,999,999.99

## SCD Type 2 Implementation

### When to Use SCD Type 2

Use SCD Type 2 for tables where historical changes are important:

- ✅ Customer information (address changes, contact info)
- ✅ Product prices and attributes
- ✅ Employee records
- ✅ Account information
- ❌ Transactional data (orders, payments) - these are immutable
- ❌ Event data (logs, clicks) - already historical

### Implementation Pattern

```sql
-- Table structure
CREATE TABLE customers_silver (
  customer_id STRING NOT NULL,
  customer_email STRING,
  customer_phone STRING,
  -- ... other attributes ...
  
  -- SCD Type 2 columns
  effective_start_date TIMESTAMP NOT NULL,
  effective_end_date TIMESTAMP,
  
  -- Standard metadata
  record_created_at TIMESTAMP NOT NULL,
  record_updated_at TIMESTAMP NOT NULL,
  source_system STRING NOT NULL,
  load_id STRING NOT NULL,
  is_current BOOLEAN NOT NULL,
  is_deleted BOOLEAN NOT NULL
)
USING DELTA
PARTITIONED BY (customer_state);
```

### Querying SCD Type 2 Tables

```sql
-- Get current records only
SELECT * FROM customers_silver
WHERE is_current = TRUE AND is_deleted = FALSE;

-- Get record as of specific date
SELECT * FROM customers_silver
WHERE customer_id = 'C12345'
  AND effective_start_date <= '2023-06-15'
  AND (effective_end_date IS NULL OR effective_end_date > '2023-06-15');

-- Get all versions of a record
SELECT * FROM customers_silver
WHERE customer_id = 'C12345'
ORDER BY effective_start_date DESC;
```

## Data Quality Requirements

### Completeness

Critical columns must have 100% completeness (no nulls):
- Business keys (IDs)
- Required business attributes
- All metadata columns

### Validity

Data must meet format and range requirements:
- Email addresses: Valid email format
- Phone numbers: Minimum length (e.g., 10 digits)
- Dates: Valid date ranges
- Amounts: Positive values where applicable

### Uniqueness

Business keys must be unique within current records:
- One current record per business key
- Composite keys must be unique together

### Consistency

Cross-field validations must pass:
- `updated_at >= created_at`
- `total = subtotal + tax - discount`
- `effective_end_date > effective_start_date` (when not null)

### Timeliness

Data freshness requirements:
- Record_created_at within acceptable lag (e.g., 24 hours)
- Source timestamps within expected ranges

## Table Properties

### Required Properties

```sql
ALTER TABLE customers_silver SET TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'quality' = 'silver',
  'layer' = 'silver',
  'domain' = 'customer',
  'owner' = 'data-engineering'
);
```

### Recommended Properties

```sql
-- Enable optimized writes
'delta.autoOptimize.optimizeWrite' = 'true'

-- Enable auto compaction
'delta.autoOptimize.autoCompact' = 'true'

-- Set retention period (7 days minimum for time travel)
'delta.deletedFileRetentionDuration' = 'interval 7 days'

-- Enable liquid clustering (for high cardinality)
'delta.enableLiquidClustering' = 'true'
```

### Partitioning Strategy

Partition tables by columns that:
- Are frequently used in WHERE clauses
- Have reasonable cardinality (10-10,000 distinct values)
- Are immutable or rarely change

Common partition columns:
- Date columns: `order_date`, `created_date`
- Geographic: `state`, `country`, `region`
- Status: `status`, `category` (if low cardinality)

### Z-Ordering

Z-order by columns used in:
- JOIN conditions
- WHERE filters
- ORDER BY clauses

```sql
OPTIMIZE customers_silver
ZORDER BY (customer_id, customer_email, customer_state);
```

## Validation Checklist

Use this checklist before deploying a new silver table:

- [ ] All column names follow snake_case convention
- [ ] Boolean columns use is_/has_/needs_ prefix
- [ ] Timestamp columns use _at/_date suffix
- [ ] Amount columns use _amount suffix with DecimalType(18,2)
- [ ] All required metadata columns present
- [ ] SCD Type 2 columns included (if applicable)
- [ ] Primary key(s) defined and documented
- [ ] Table properties set (change data feed, quality tags)
- [ ] Partitioning strategy defined
- [ ] Z-ordering columns identified
- [ ] Data quality rules defined and tested
- [ ] Unit tests written and passing
- [ ] Documentation updated

## Examples

### ✅ Good Example: Customer Table

```sql
CREATE TABLE customers_silver (
  -- Business Key
  customer_id STRING NOT NULL,
  
  -- Customer Attributes
  customer_first_name STRING,
  customer_last_name STRING,
  customer_email STRING,
  customer_phone STRING,
  customer_date_of_birth TIMESTAMP,
  customer_age INT,
  
  -- Address
  customer_address_line1 STRING,
  customer_city STRING,
  customer_state STRING,
  customer_zip_code STRING,
  
  -- Flags
  is_active BOOLEAN,
  is_email_verified BOOLEAN,
  has_address BOOLEAN,
  
  -- Business Timestamps
  customer_created_at TIMESTAMP,
  customer_updated_at TIMESTAMP,
  
  -- SCD Type 2
  effective_start_date TIMESTAMP NOT NULL,
  effective_end_date TIMESTAMP,
  
  -- Metadata
  record_created_at TIMESTAMP NOT NULL,
  record_updated_at TIMESTAMP NOT NULL,
  source_system STRING NOT NULL,
  load_id STRING NOT NULL,
  is_current BOOLEAN NOT NULL,
  is_deleted BOOLEAN NOT NULL
)
USING DELTA
PARTITIONED BY (customer_state)
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'quality' = 'silver',
  'domain' = 'customer'
);
```

### ❌ Bad Example: Non-Standard Table

```sql
CREATE TABLE Customer (  -- ❌ Table name not snake_case
  CustomerId INT,        -- ❌ Column not snake_case, wrong type for ID
  FirstName VARCHAR(50), -- ❌ Column not prefixed with entity
  eMail STRING,          -- ❌ Mixed case
  Phone# STRING,         -- ❌ Special character in name
  Active BIT,            -- ❌ Should be is_active BOOLEAN
  _internal_flag BOOLEAN,-- ❌ Leading underscore
  created TIMESTAMP      -- ❌ Should be customer_created_at
  -- ❌ Missing all metadata columns
);
```

## Compliance

All silver layer tables must pass the schema validation script:

```bash
python scripts/validate_schema.py --table customers_silver
```

Non-compliant tables will not be promoted to production.
