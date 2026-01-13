-- Customer table from landing to cursor
-- Note: Table name only (no schema prefix) because target schema is set in pipeline config
CREATE OR REFRESH STREAMING TABLE customer
AS SELECT * FROM STREAM(dbx_chn_ward_demo.landing_ss_aw.customer)
