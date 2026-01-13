# Deployment Details

## Pipeline Information

- **Pipeline Name**: Landing to Cursor Pipeline
- **Pipeline ID**: `249c1f9a-0171-48cc-a8f5-9ef2c41533f9`
- **Catalog**: `dbx_chn_ward_demo`
- **Target Schema**: `cursor`
- **Compute**: Serverless
- **Mode**: Development
- **Schedule**: Manual trigger only (no continuous processing)

## Current Run

- **Latest Update ID**: `fc326672-9303-49be-8b20-fa9890c662fb`
- **Status**: COMPLETED ✓ (migrated to root_path pattern)
- **Previous Updates**: 
  - `23bcc2c3-b319-4591-ae1d-751250dab45d` (completed - added sales_orders_flat table)
  - `70a2684e-ec9c-47f0-bbf1-7727fae9e893` (completed - fixed table naming issue)
  - `ce08400d-2824-40a2-8e61-60f429886a40` (failed - multipart table name error)

### Modern Root Path Pattern

**Migration**: Reorganized from individual file paths to modern root_path pattern.

**Old Structure** (flat files):
```
sdp_test/
├── customer.sql
├── product.sql
├── salesorderdetail.sql
└── sales_orders_flat.sql
```

**New Structure** (organized):
```
sdp_test/
└── src/
    └── pipelines/
        └── landing_to_cursor/
            └── transformations/
                ├── customer.sql
                ├── product.sql
                ├── salesorderdetail.sql
                └── sales_orders_flat.sql
```

**Benefits**:
- ✅ Auto-discovery of new files (with DABs glob patterns)
- ✅ Better organization and scalability
- ✅ Clear separation of concerns
- ✅ Supports multiple pipelines in one project

See `docs/sdp-guidance/root-path-pattern.md` for complete guide.

### Issue Fixed

The initial deployment failed with error:
```
[UNSUPPORTED_SQL_STATEMENT] Multipart table names is not supported.
```

**Root Cause**: Used schema-qualified table names (e.g., `cursor.customer`) in CREATE statements.

**Solution**: In SDP, when `target` schema is specified in pipeline config, use table name only in SQL:
- ❌ `CREATE TABLE cursor.customer`
- ✅ `CREATE TABLE customer`

See `docs/sdp-guidance/table-naming-conventions.md` for full guidance.

## Pipeline URL

View the pipeline in the Databricks UI:

https://adb-7405607609261208.8.azuredatabricks.net/#joblist/pipelines/249c1f9a-0171-48cc-a8f5-9ef2c41533f9/updates/ce08400d-2824-40a2-8e61-60f429886a40

## Source Tables

- `dbx_chn_ward_demo.landing_ss_aw.customer`
- `dbx_chn_ward_demo.landing_ss_aw.product`
- `dbx_chn_ward_demo.landing_ss_aw.salesorderdetail`

## Target Tables

- `dbx_chn_ward_demo.cursor.customer`
- `dbx_chn_ward_demo.cursor.product`
- `dbx_chn_ward_demo.cursor.salesorderdetail`
- `dbx_chn_ward_demo.cursor.sales_orders_flat` (joined table: 542 records)

## Manual Trigger

To trigger subsequent runs:

```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  "https://adb-7405607609261208.8.azuredatabricks.net/api/2.0/pipelines/249c1f9a-0171-48cc-a8f5-9ef2c41533f9/updates" \
  -d '{"full_refresh": false}'
```

## Check Status

```bash
curl -X GET \
  -H "Authorization: Bearer <token>" \
  "https://adb-7405607609261208.8.azuredatabricks.net/api/2.0/pipelines/249c1f9a-0171-48cc-a8f5-9ef2c41533f9"
```

## Workspace Files

SQL files uploaded to:
- `/Users/justin.ward@databricks.com/sdp_test/customer.sql`
- `/Users/justin.ward@databricks.com/sdp_test/product.sql`
- `/Users/justin.ward@databricks.com/sdp_test/salesorderdetail.sql`
- `/Users/justin.ward@databricks.com/sdp_test/sales_orders_flat.sql`

## Sales Orders Flat Table

The `sales_orders_flat` table is a denormalized view combining:
- Sales order details (quantities, prices, discounts)
- Product information (name, specifications, pricing)
- Calculated fields (ExtendedPrice, TotalDiscount)

**Join Logic**: `salesorderdetail` INNER JOIN `product` ON `ProductID`

**Record Count**: 542 records

**Key Fields**:
- Order information: SalesOrderID, SalesOrderDetailID, OrderQty
- Pricing: UnitPrice, UnitPriceDiscount, LineTotal
- Product details: ProductName, ProductNumber, ProductColor, StandardCost, ListPrice
- Calculated: ExtendedPrice (Qty × UnitPrice), TotalDiscount (ExtendedPrice - LineTotal)
