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

- **Latest Update ID**: `70a2684e-ec9c-47f0-bbf1-7727fae9e893`
- **Status**: Running (fixed table naming issue)
- **Previous Update ID**: `ce08400d-2824-40a2-8e61-60f429886a40` (failed due to multipart table name error)

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
