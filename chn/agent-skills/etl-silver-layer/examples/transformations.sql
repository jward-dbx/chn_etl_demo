-- Silver Layer SQL Transformations Example
-- This file demonstrates SQL-based transformations following silver layer standards
-- These can be used in Delta Live Tables or standalone SQL pipelines

-- ============================================================================
-- CUSTOMERS SILVER TABLE
-- ============================================================================

-- Create or refresh the silver customers table with standardized transformations
CREATE OR REFRESH STREAMING LIVE TABLE customers_silver (
  CONSTRAINT valid_customer_id EXPECT (customer_id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_email EXPECT (customer_email IS NOT NULL AND customer_email RLIKE '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$') ON VIOLATION DROP ROW,
  CONSTRAINT valid_phone EXPECT (LENGTH(customer_phone) >= 10) ON VIOLATION FAIL
)
COMMENT 'Silver layer customer data with standardized column names and data quality checks'
TBLPROPERTIES (
  'quality' = 'silver',
  'layer' = 'silver',
  'domain' = 'customer',
  'delta.enableChangeDataFeed' = 'true'
)
PARTITIONED BY (customer_state)
AS SELECT
  -- Business Key
  customer_id,
  
  -- Customer Name (standardized to uppercase, trimmed)
  UPPER(TRIM(first_name)) AS customer_first_name,
  UPPER(TRIM(last_name)) AS customer_last_name,
  CONCAT(UPPER(TRIM(first_name)), ' ', UPPER(TRIM(last_name))) AS customer_full_name,
  
  -- Contact Information (standardized formats)
  LOWER(TRIM(email)) AS customer_email,
  REGEXP_REPLACE(phone, '[^0-9]', '') AS customer_phone,
  
  -- Personal Information
  TO_TIMESTAMP(date_of_birth, 'yyyy-MM-dd') AS customer_date_of_birth,
  YEAR(CURRENT_DATE()) - YEAR(TO_TIMESTAMP(date_of_birth, 'yyyy-MM-dd')) AS customer_age,
  
  -- Address Information (standardized)
  TRIM(address_line1) AS customer_address_line1,
  TRIM(address_line2) AS customer_address_line2,
  TRIM(city) AS customer_city,
  UPPER(TRIM(state)) AS customer_state,
  zip_code AS customer_zip_code,
  UPPER(TRIM(country)) AS customer_country,
  
  -- Boolean Flags (following is_/has_ convention)
  CAST(active AS BOOLEAN) AS is_active,
  CAST(email_verified AS BOOLEAN) AS is_email_verified,
  CASE WHEN address_line1 IS NOT NULL THEN TRUE ELSE FALSE END AS has_address,
  CASE WHEN phone IS NOT NULL AND LENGTH(REGEXP_REPLACE(phone, '[^0-9]', '')) >= 10 THEN TRUE ELSE FALSE END AS has_valid_phone,
  
  -- Business Timestamps
  TO_TIMESTAMP(created_at) AS customer_created_at,
  TO_TIMESTAMP(updated_at) AS customer_updated_at,
  
  -- SCD Type 2 Columns
  CURRENT_TIMESTAMP() AS effective_start_date,
  CAST(NULL AS TIMESTAMP) AS effective_end_date,
  
  -- Standard Metadata Columns (REQUIRED for all silver tables)
  CURRENT_TIMESTAMP() AS record_created_at,
  CURRENT_TIMESTAMP() AS record_updated_at,
  'source_crm' AS source_system,
  '${load_id}' AS load_id,
  TRUE AS is_current,
  FALSE AS is_deleted
FROM STREAM(bronze.customers);

-- ============================================================================
-- ORDERS SILVER TABLE
-- ============================================================================

CREATE OR REFRESH STREAMING LIVE TABLE orders_silver (
  CONSTRAINT valid_order_id EXPECT (order_id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_customer_id EXPECT (customer_id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_order_amount EXPECT (order_total_amount > 0) ON VIOLATION FAIL,
  CONSTRAINT valid_order_date EXPECT (order_date IS NOT NULL) ON VIOLATION DROP ROW
)
COMMENT 'Silver layer orders data with standardized calculations and enrichments'
TBLPROPERTIES (
  'quality' = 'silver',
  'layer' = 'silver',
  'domain' = 'orders',
  'delta.enableChangeDataFeed' = 'true'
)
PARTITIONED BY (order_year, order_month)
AS SELECT
  -- Business Keys
  order_id,
  customer_id,
  
  -- Order Details (standardized naming)
  TO_TIMESTAMP(order_date, 'yyyy-MM-dd HH:mm:ss') AS order_date,
  YEAR(TO_TIMESTAMP(order_date, 'yyyy-MM-dd HH:mm:ss')) AS order_year,
  MONTH(TO_TIMESTAMP(order_date, 'yyyy-MM-dd HH:mm:ss')) AS order_month,
  DATE(TO_TIMESTAMP(order_date, 'yyyy-MM-dd HH:mm:ss')) AS order_date_only,
  
  -- Financial Amounts (standardized decimal precision)
  CAST(subtotal AS DECIMAL(18,2)) AS order_subtotal_amount,
  CAST(tax AS DECIMAL(18,2)) AS order_tax_amount,
  CAST(shipping AS DECIMAL(18,2)) AS order_shipping_amount,
  CAST(discount AS DECIMAL(18,2)) AS order_discount_amount,
  CAST(total AS DECIMAL(18,2)) AS order_total_amount,
  
  -- Order Attributes
  UPPER(TRIM(status)) AS order_status,
  UPPER(TRIM(payment_method)) AS order_payment_method,
  UPPER(TRIM(shipping_method)) AS order_shipping_method,
  
  -- Derived Metrics
  CAST(total AS DECIMAL(18,2)) - CAST(discount AS DECIMAL(18,2)) AS order_net_amount,
  CAST(tax AS DECIMAL(18,2)) / NULLIF(CAST(subtotal AS DECIMAL(18,2)), 0) AS order_tax_rate,
  
  -- Boolean Flags
  CASE WHEN UPPER(status) = 'COMPLETED' THEN TRUE ELSE FALSE END AS is_completed,
  CASE WHEN CAST(discount AS DECIMAL(18,2)) > 0 THEN TRUE ELSE FALSE END AS has_discount,
  CASE WHEN UPPER(status) = 'CANCELLED' THEN TRUE ELSE FALSE END AS is_cancelled,
  
  -- Shipping Information
  TRIM(shipping_address_line1) AS order_shipping_address_line1,
  TRIM(shipping_address_line2) AS order_shipping_address_line2,
  TRIM(shipping_city) AS order_shipping_city,
  UPPER(TRIM(shipping_state)) AS order_shipping_state,
  shipping_zip_code AS order_shipping_zip_code,
  
  -- Business Timestamps
  TO_TIMESTAMP(created_at) AS order_created_at,
  TO_TIMESTAMP(updated_at) AS order_updated_at,
  TO_TIMESTAMP(shipped_at) AS order_shipped_at,
  TO_TIMESTAMP(delivered_at) AS order_delivered_at,
  
  -- Standard Metadata Columns (REQUIRED)
  CURRENT_TIMESTAMP() AS record_created_at,
  CURRENT_TIMESTAMP() AS record_updated_at,
  'source_ecommerce' AS source_system,
  '${load_id}' AS load_id,
  TRUE AS is_current,
  FALSE AS is_deleted
FROM STREAM(bronze.orders);

-- ============================================================================
-- ORDER ITEMS SILVER TABLE WITH ENRICHMENT
-- ============================================================================

CREATE OR REFRESH STREAMING LIVE TABLE order_items_silver (
  CONSTRAINT valid_order_item_id EXPECT (order_item_id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_order_id EXPECT (order_id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_product_id EXPECT (product_id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_quantity EXPECT (order_item_quantity > 0) ON VIOLATION FAIL,
  CONSTRAINT valid_unit_price EXPECT (order_item_unit_price >= 0) ON VIOLATION FAIL
)
COMMENT 'Silver layer order items with product enrichment'
TBLPROPERTIES (
  'quality' = 'silver',
  'layer' = 'silver',
  'domain' = 'orders',
  'delta.enableChangeDataFeed' = 'true'
)
AS SELECT
  -- Business Keys
  oi.order_item_id,
  oi.order_id,
  oi.product_id,
  
  -- Order Item Details
  CAST(oi.quantity AS INTEGER) AS order_item_quantity,
  CAST(oi.unit_price AS DECIMAL(18,2)) AS order_item_unit_price,
  CAST(oi.discount AS DECIMAL(18,2)) AS order_item_discount_amount,
  CAST(oi.tax AS DECIMAL(18,2)) AS order_item_tax_amount,
  
  -- Calculated Amounts
  CAST(oi.quantity AS INTEGER) * CAST(oi.unit_price AS DECIMAL(18,2)) AS order_item_subtotal_amount,
  (CAST(oi.quantity AS INTEGER) * CAST(oi.unit_price AS DECIMAL(18,2))) - CAST(oi.discount AS DECIMAL(18,2)) AS order_item_total_amount,
  
  -- Product Information (enriched from products table)
  p.product_name,
  p.product_category,
  p.product_subcategory,
  p.product_brand,
  p.product_sku,
  
  -- Product Attributes
  CAST(p.cost AS DECIMAL(18,2)) AS product_cost_amount,
  CAST(p.list_price AS DECIMAL(18,2)) AS product_list_price_amount,
  
  -- Margin Calculation
  (CAST(oi.unit_price AS DECIMAL(18,2)) - CAST(p.cost AS DECIMAL(18,2))) / NULLIF(CAST(oi.unit_price AS DECIMAL(18,2)), 0) AS order_item_margin_rate,
  (CAST(oi.unit_price AS DECIMAL(18,2)) - CAST(p.cost AS DECIMAL(18,2))) * CAST(oi.quantity AS INTEGER) AS order_item_margin_amount,
  
  -- Boolean Flags
  CASE WHEN CAST(oi.discount AS DECIMAL(18,2)) > 0 THEN TRUE ELSE FALSE END AS has_discount,
  CASE WHEN CAST(oi.unit_price AS DECIMAL(18,2)) < CAST(p.list_price AS DECIMAL(18,2)) THEN TRUE ELSE FALSE END AS is_discounted_from_list,
  
  -- Standard Metadata Columns (REQUIRED)
  CURRENT_TIMESTAMP() AS record_created_at,
  CURRENT_TIMESTAMP() AS record_updated_at,
  'source_ecommerce' AS source_system,
  '${load_id}' AS load_id,
  TRUE AS is_current,
  FALSE AS is_deleted
FROM STREAM(bronze.order_items) oi
LEFT JOIN LIVE.products_silver p ON oi.product_id = p.product_id AND p.is_current = TRUE;

-- ============================================================================
-- PRODUCTS SILVER TABLE
-- ============================================================================

CREATE OR REFRESH LIVE TABLE products_silver (
  CONSTRAINT valid_product_id EXPECT (product_id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_product_name EXPECT (product_name IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_prices EXPECT (product_list_price_amount >= product_cost_amount) ON VIOLATION FAIL
)
COMMENT 'Silver layer products with standardized attributes and classifications'
TBLPROPERTIES (
  'quality' = 'silver',
  'layer' = 'silver',
  'domain' = 'products',
  'delta.enableChangeDataFeed' = 'true'
)
AS SELECT
  -- Business Key
  product_id,
  
  -- Product Identity
  TRIM(name) AS product_name,
  TRIM(sku) AS product_sku,
  TRIM(description) AS product_description,
  
  -- Product Classification (standardized)
  UPPER(TRIM(category)) AS product_category,
  UPPER(TRIM(subcategory)) AS product_subcategory,
  UPPER(TRIM(brand)) AS product_brand,
  
  -- Pricing (standardized decimal precision)
  CAST(cost AS DECIMAL(18,2)) AS product_cost_amount,
  CAST(list_price AS DECIMAL(18,2)) AS product_list_price_amount,
  CAST(list_price AS DECIMAL(18,2)) - CAST(cost AS DECIMAL(18,2)) AS product_margin_amount,
  (CAST(list_price AS DECIMAL(18,2)) - CAST(cost AS DECIMAL(18,2))) / NULLIF(CAST(list_price AS DECIMAL(18,2)), 0) AS product_margin_rate,
  
  -- Product Attributes
  CAST(weight AS DECIMAL(10,2)) AS product_weight_amount,
  TRIM(weight_unit) AS product_weight_unit,
  CAST(quantity_in_stock AS INTEGER) AS product_quantity_in_stock_count,
  CAST(reorder_level AS INTEGER) AS product_reorder_level_count,
  
  -- Boolean Flags
  CAST(is_active AS BOOLEAN) AS is_active,
  CAST(is_featured AS BOOLEAN) AS is_featured,
  CASE WHEN CAST(quantity_in_stock AS INTEGER) > 0 THEN TRUE ELSE FALSE END AS is_in_stock,
  CASE WHEN CAST(quantity_in_stock AS INTEGER) <= CAST(reorder_level AS INTEGER) THEN TRUE ELSE FALSE END AS needs_reorder,
  
  -- Business Timestamps
  TO_TIMESTAMP(created_at) AS product_created_at,
  TO_TIMESTAMP(updated_at) AS product_updated_at,
  TO_TIMESTAMP(discontinued_at) AS product_discontinued_at,
  
  -- SCD Type 2 Columns
  CURRENT_TIMESTAMP() AS effective_start_date,
  CAST(NULL AS TIMESTAMP) AS effective_end_date,
  
  -- Standard Metadata Columns (REQUIRED)
  CURRENT_TIMESTAMP() AS record_created_at,
  CURRENT_TIMESTAMP() AS record_updated_at,
  'source_inventory' AS source_system,
  '${load_id}' AS load_id,
  TRUE AS is_current,
  FALSE AS is_deleted
FROM bronze.products;

-- ============================================================================
-- DATA QUALITY MONITORING VIEW
-- ============================================================================

-- Create a view to monitor data quality metrics across all silver tables
CREATE OR REFRESH LIVE TABLE data_quality_metrics
COMMENT 'Data quality metrics for all silver layer tables'
AS
WITH customer_quality AS (
  SELECT
    'customers_silver' AS table_name,
    COUNT(*) AS total_records,
    COUNT(DISTINCT customer_id) AS unique_keys,
    SUM(CASE WHEN customer_email IS NULL THEN 1 ELSE 0 END) AS null_emails,
    SUM(CASE WHEN customer_phone IS NULL THEN 1 ELSE 0 END) AS null_phones,
    CURRENT_TIMESTAMP() AS checked_at
  FROM LIVE.customers_silver
),
order_quality AS (
  SELECT
    'orders_silver' AS table_name,
    COUNT(*) AS total_records,
    COUNT(DISTINCT order_id) AS unique_keys,
    SUM(CASE WHEN order_total_amount <= 0 THEN 1 ELSE 0 END) AS invalid_amounts,
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_customer_refs,
    CURRENT_TIMESTAMP() AS checked_at
  FROM LIVE.orders_silver
)
SELECT * FROM customer_quality
UNION ALL
SELECT 
  table_name,
  total_records,
  unique_keys,
  invalid_amounts AS quality_issue_count_1,
  null_customer_refs AS quality_issue_count_2,
  checked_at
FROM order_quality;
