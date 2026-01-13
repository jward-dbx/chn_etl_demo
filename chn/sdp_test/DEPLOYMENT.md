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

- **Update ID**: `ce08400d-2824-40a2-8e61-60f429886a40`
- **Status**: WAITING_FOR_RESOURCES (serverless compute spinning up)

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
