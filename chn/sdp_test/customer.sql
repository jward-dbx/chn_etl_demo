-- Customer table from landing to cursor
CREATE OR REFRESH STREAMING TABLE cursor.customer
AS SELECT * FROM STREAM(dbx_chn_ward_demo.landing_ss_aw.customer)
