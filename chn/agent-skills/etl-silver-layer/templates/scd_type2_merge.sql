-- SCD Type 2 Merge Template for Silver Layer Tables
-- --------------------------------------------------
-- This template provides reusable SQL patterns for implementing
-- Slowly Changing Dimension (SCD) Type 2 logic in silver layer tables.
--
-- SCD Type 2 maintains historical records by:
-- 1. Closing out existing records when changes occur (set is_current=false, effective_end_date)
-- 2. Inserting new versions of changed records
-- 3. Keeping effective date ranges for each version
--
-- Usage: Replace placeholder values with actual table/column names

-- ============================================================================
-- BASIC SCD TYPE 2 MERGE (Simple)
-- ============================================================================

MERGE INTO ${catalog}.${schema}.${target_table} AS target
USING ${catalog}.${schema}.${staging_table} AS source
ON target.${business_key} = source.${business_key}
  AND target.is_current = TRUE

-- When matched and data has changed: Close out the current record
WHEN MATCHED AND (
  target.${tracked_column_1} <> source.${tracked_column_1} OR
  target.${tracked_column_2} <> source.${tracked_column_2} OR
  target.${tracked_column_3} <> source.${tracked_column_3}
)
THEN UPDATE SET
  is_current = FALSE,
  effective_end_date = current_timestamp(),
  record_updated_at = current_timestamp()

-- When not matched: Insert new record
WHEN NOT MATCHED
THEN INSERT *;

-- After merge: Insert new versions of changed records
INSERT INTO ${catalog}.${schema}.${target_table}
SELECT 
  source.*,
  current_timestamp() AS effective_start_date,
  CAST(NULL AS TIMESTAMP) AS effective_end_date,
  TRUE AS is_current
FROM ${catalog}.${schema}.${staging_table} AS source
INNER JOIN ${catalog}.${schema}.${target_table} AS target
  ON source.${business_key} = target.${business_key}
WHERE target.is_current = FALSE
  AND target.effective_end_date = (
    SELECT MAX(effective_end_date)
    FROM ${catalog}.${schema}.${target_table}
    WHERE ${business_key} = source.${business_key}
  );

-- ============================================================================
-- CUSTOMER TABLE - SCD TYPE 2 MERGE (Complete Example)
-- ============================================================================

-- Step 1: Stage the incoming data in a temporary view
CREATE OR REPLACE TEMPORARY VIEW customers_staging AS
SELECT 
  customer_id,
  customer_first_name,
  customer_last_name,
  customer_email,
  customer_phone,
  customer_address_line1,
  customer_city,
  customer_state,
  customer_zip_code,
  customer_country,
  is_active,
  is_email_verified,
  customer_created_at,
  customer_updated_at
FROM dev_catalog.bronze.customers
WHERE load_date = current_date();

-- Step 2: Perform SCD Type 2 merge
MERGE INTO dev_catalog.silver.customers_silver AS target
USING customers_staging AS source
ON target.customer_id = source.customer_id
  AND target.is_current = TRUE

-- When matched and tracking columns changed: Close current record
WHEN MATCHED AND (
  -- Compare tracked columns for changes
  COALESCE(target.customer_email, '') <> COALESCE(source.customer_email, '') OR
  COALESCE(target.customer_phone, '') <> COALESCE(source.customer_phone, '') OR
  COALESCE(target.customer_address_line1, '') <> COALESCE(source.customer_address_line1, '') OR
  COALESCE(target.customer_city, '') <> COALESCE(source.customer_city, '') OR
  COALESCE(target.customer_state, '') <> COALESCE(source.customer_state, '') OR
  COALESCE(target.customer_zip_code, '') <> COALESCE(source.customer_zip_code, '')
)
THEN UPDATE SET
  is_current = FALSE,
  effective_end_date = current_timestamp(),
  record_updated_at = current_timestamp()

-- When matched but no changes: Update the record timestamp only
WHEN MATCHED AND (
  COALESCE(target.customer_email, '') = COALESCE(source.customer_email, '') AND
  COALESCE(target.customer_phone, '') = COALESCE(source.customer_phone, '') AND
  COALESCE(target.customer_address_line1, '') = COALESCE(source.customer_address_line1, '') AND
  COALESCE(target.customer_city, '') = COALESCE(source.customer_city, '') AND
  COALESCE(target.customer_state, '') = COALESCE(source.customer_state, '') AND
  COALESCE(target.customer_zip_code, '') = COALESCE(source.customer_zip_code, '')
)
THEN UPDATE SET
  record_updated_at = current_timestamp()

-- When not matched: Insert new customer
WHEN NOT MATCHED
THEN INSERT (
  customer_id,
  customer_first_name,
  customer_last_name,
  customer_email,
  customer_phone,
  customer_address_line1,
  customer_city,
  customer_state,
  customer_zip_code,
  customer_country,
  is_active,
  is_email_verified,
  customer_created_at,
  customer_updated_at,
  effective_start_date,
  effective_end_date,
  record_created_at,
  record_updated_at,
  source_system,
  load_id,
  is_current,
  is_deleted
) VALUES (
  source.customer_id,
  source.customer_first_name,
  source.customer_last_name,
  source.customer_email,
  source.customer_phone,
  source.customer_address_line1,
  source.customer_city,
  source.customer_state,
  source.customer_zip_code,
  source.customer_country,
  source.is_active,
  source.is_email_verified,
  source.customer_created_at,
  source.customer_updated_at,
  current_timestamp(),
  CAST(NULL AS TIMESTAMP),
  current_timestamp(),
  current_timestamp(),
  'source_crm',
  '${load_id}',
  TRUE,
  FALSE
);

-- Step 3: Insert new versions of changed records
INSERT INTO dev_catalog.silver.customers_silver
SELECT 
  source.customer_id,
  source.customer_first_name,
  source.customer_last_name,
  source.customer_email,
  source.customer_phone,
  source.customer_address_line1,
  source.customer_city,
  source.customer_state,
  source.customer_zip_code,
  source.customer_country,
  source.is_active,
  source.is_email_verified,
  source.customer_created_at,
  source.customer_updated_at,
  current_timestamp() AS effective_start_date,
  CAST(NULL AS TIMESTAMP) AS effective_end_date,
  current_timestamp() AS record_created_at,
  current_timestamp() AS record_updated_at,
  'source_crm' AS source_system,
  '${load_id}' AS load_id,
  TRUE AS is_current,
  FALSE AS is_deleted
FROM customers_staging AS source
WHERE EXISTS (
  SELECT 1
  FROM dev_catalog.silver.customers_silver AS target
  WHERE target.customer_id = source.customer_id
    AND target.is_current = FALSE
    AND target.effective_end_date >= date_sub(current_timestamp(), INTERVAL 1 MINUTE)
);

-- ============================================================================
-- PRODUCTS TABLE - SCD TYPE 2 MERGE (With Price History)
-- ============================================================================

MERGE INTO dev_catalog.silver.products_silver AS target
USING (
  SELECT 
    product_id,
    product_name,
    product_sku,
    product_category,
    product_subcategory,
    product_brand,
    product_cost_amount,
    product_list_price_amount,
    is_active
  FROM dev_catalog.bronze.products
  WHERE load_date = current_date()
) AS source
ON target.product_id = source.product_id
  AND target.is_current = TRUE

-- When matched and prices changed: Close current record (track price history)
WHEN MATCHED AND (
  target.product_list_price_amount <> source.product_list_price_amount OR
  target.product_cost_amount <> source.product_cost_amount OR
  COALESCE(target.product_name, '') <> COALESCE(source.product_name, '')
)
THEN UPDATE SET
  is_current = FALSE,
  effective_end_date = current_timestamp(),
  record_updated_at = current_timestamp()

-- When not matched: Insert new product
WHEN NOT MATCHED
THEN INSERT (
  product_id,
  product_name,
  product_sku,
  product_category,
  product_subcategory,
  product_brand,
  product_cost_amount,
  product_list_price_amount,
  product_margin_amount,
  product_margin_rate,
  is_active,
  effective_start_date,
  effective_end_date,
  record_created_at,
  record_updated_at,
  source_system,
  load_id,
  is_current,
  is_deleted
) VALUES (
  source.product_id,
  source.product_name,
  source.product_sku,
  source.product_category,
  source.product_subcategory,
  source.product_brand,
  source.product_cost_amount,
  source.product_list_price_amount,
  source.product_list_price_amount - source.product_cost_amount,
  (source.product_list_price_amount - source.product_cost_amount) / NULLIF(source.product_list_price_amount, 0),
  source.is_active,
  current_timestamp(),
  CAST(NULL AS TIMESTAMP),
  current_timestamp(),
  current_timestamp(),
  'source_inventory',
  '${load_id}',
  TRUE,
  FALSE
);

-- ============================================================================
-- ADVANCED: SCD TYPE 2 WITH SOFT DELETES
-- ============================================================================

-- This pattern handles records that are deleted in the source system
-- by setting is_deleted = TRUE and closing the effective date

MERGE INTO dev_catalog.silver.customers_silver AS target
USING (
  -- Get current customers from bronze
  SELECT customer_id, customer_email, customer_phone, is_active
  FROM dev_catalog.bronze.customers
  WHERE load_date = current_date()
  
  UNION ALL
  
  -- Add deletes (customers that existed before but not in current load)
  SELECT DISTINCT 
    target.customer_id,
    target.customer_email,
    target.customer_phone,
    FALSE AS is_active
  FROM dev_catalog.silver.customers_silver AS target
  LEFT JOIN dev_catalog.bronze.customers AS source
    ON target.customer_id = source.customer_id
    AND source.load_date = current_date()
  WHERE target.is_current = TRUE
    AND target.is_deleted = FALSE
    AND source.customer_id IS NULL
) AS source
ON target.customer_id = source.customer_id
  AND target.is_current = TRUE

-- Handle deletes: Mark as deleted and close effective date
WHEN MATCHED AND source.is_active = FALSE AND target.is_deleted = FALSE
THEN UPDATE SET
  is_deleted = TRUE,
  is_current = FALSE,
  effective_end_date = current_timestamp(),
  record_updated_at = current_timestamp()

-- Handle updates (same as before)
WHEN MATCHED AND (
  COALESCE(target.customer_email, '') <> COALESCE(source.customer_email, '') OR
  COALESCE(target.customer_phone, '') <> COALESCE(source.customer_phone, '')
)
THEN UPDATE SET
  is_current = FALSE,
  effective_end_date = current_timestamp(),
  record_updated_at = current_timestamp()

-- Handle inserts
WHEN NOT MATCHED
THEN INSERT *;

-- ============================================================================
-- QUERY PATTERNS FOR SCD TYPE 2 TABLES
-- ============================================================================

-- Get current snapshot (most common query)
SELECT *
FROM dev_catalog.silver.customers_silver
WHERE is_current = TRUE
  AND is_deleted = FALSE;

-- Get historical versions of a specific customer
SELECT *
FROM dev_catalog.silver.customers_silver
WHERE customer_id = 'C12345'
ORDER BY effective_start_date DESC;

-- Get customer data as of a specific date
SELECT *
FROM dev_catalog.silver.customers_silver
WHERE customer_id = 'C12345'
  AND effective_start_date <= '2023-06-15'
  AND (effective_end_date IS NULL OR effective_end_date > '2023-06-15');

-- Get all changes that occurred in a date range
SELECT *
FROM dev_catalog.silver.customers_silver
WHERE effective_start_date BETWEEN '2023-06-01' AND '2023-06-30'
ORDER BY customer_id, effective_start_date;

-- Find customers with multiple versions (changed records)
SELECT customer_id, COUNT(*) AS version_count
FROM dev_catalog.silver.customers_silver
GROUP BY customer_id
HAVING COUNT(*) > 1
ORDER BY version_count DESC;

-- Get change velocity (how often records change)
SELECT 
  customer_id,
  COUNT(*) - 1 AS change_count,
  MIN(effective_start_date) AS first_seen,
  MAX(effective_start_date) AS last_changed,
  DATEDIFF(day, MIN(effective_start_date), MAX(effective_start_date)) AS days_tracked,
  (COUNT(*) - 1) / NULLIF(DATEDIFF(day, MIN(effective_start_date), MAX(effective_start_date)), 0) AS changes_per_day
FROM dev_catalog.silver.customers_silver
GROUP BY customer_id
HAVING COUNT(*) > 1
ORDER BY change_count DESC;

-- ============================================================================
-- MAINTENANCE QUERIES
-- ============================================================================

-- Check for data integrity issues (overlapping effective dates)
SELECT 
  customer_id,
  COUNT(*) AS current_count
FROM dev_catalog.silver.customers_silver
WHERE is_current = TRUE
GROUP BY customer_id
HAVING COUNT(*) > 1;

-- Check for orphaned records (no current version)
SELECT DISTINCT customer_id
FROM dev_catalog.silver.customers_silver AS a
WHERE NOT EXISTS (
  SELECT 1
  FROM dev_catalog.silver.customers_silver AS b
  WHERE b.customer_id = a.customer_id
    AND b.is_current = TRUE
);

-- Calculate table statistics
SELECT 
  COUNT(*) AS total_records,
  COUNT(DISTINCT customer_id) AS unique_customers,
  SUM(CASE WHEN is_current = TRUE THEN 1 ELSE 0 END) AS current_records,
  SUM(CASE WHEN is_current = FALSE THEN 1 ELSE 0 END) AS historical_records,
  SUM(CASE WHEN is_deleted = TRUE THEN 1 ELSE 0 END) AS deleted_records,
  AVG(CAST(DATEDIFF(day, effective_start_date, COALESCE(effective_end_date, current_timestamp())) AS DOUBLE)) AS avg_version_duration_days
FROM dev_catalog.silver.customers_silver;
