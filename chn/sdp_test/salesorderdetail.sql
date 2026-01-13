-- Sales Order Detail table from landing to cursor
CREATE OR REFRESH STREAMING TABLE cursor.salesorderdetail
AS SELECT * FROM STREAM(dbx_chn_ward_demo.landing_ss_aw.salesorderdetail)
