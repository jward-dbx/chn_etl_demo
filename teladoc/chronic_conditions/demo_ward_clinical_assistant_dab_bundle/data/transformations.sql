-- =============================================================
-- demo_ward_clinical_assistant - SILVER and GOLD Transformations
-- Catalog/Schema: ward_demo.justin_ward_demo_ward_clinical_assistant
-- Purpose: Build cleaned silver tables and gold aggregates to power the
--          Chronic Care Ops & Risk Monitoring dashboard and questions.
-- Notes:
-- - Inputs: raw tables named raw_<datasource> as per demo_story.json
-- - Outputs: silver_* (atomic cleaned), gold_* (aggregated, reusable)
-- - Spark SQL compatible (Databricks)
-- =============================================================

USE CATALOG ward_demo;
USE SCHEMA justin_ward_demo_ward_clinical_assistant;

-- ================================
-- === SILVER TABLES (CLEANED) ===
-- ================================

-- 1) silver_patient_master
CREATE OR REPLACE TABLE silver_patient_master AS
SELECT
  CAST(patient_id AS STRING) AS patient_id,
  CASE UPPER(TRIM(region))
    WHEN 'EAST' THEN 'East'
    WHEN 'CENTRAL' THEN 'Central'
    WHEN 'WEST' THEN 'West'
    ELSE COALESCE(region, 'East')
  END AS region,
  CASE LOWER(TRIM(condition))
    WHEN 'diabetes' THEN 'diabetes'
    WHEN 'hypertension' THEN 'hypertension'
    ELSE 'diabetes'
  END AS condition,
  CASE LOWER(TRIM(risk_tier))
    WHEN 'low' THEN 'low'
    WHEN 'medium' THEN 'medium'
    WHEN 'high' THEN 'high'
    ELSE 'medium'
  END AS risk_tier,
  CASE
    WHEN program IN ('CCM', 'CCM+Nutrition') THEN program
    WHEN UPPER(program) LIKE '%NUTR%' THEN 'CCM+Nutrition'
    ELSE 'CCM'
  END AS program,
  CAST(enrollment_date AS DATE) AS enrollment_date,
  CAST(active_flag AS BOOLEAN) AS active_flag
FROM raw_patient_master;

ALTER TABLE silver_patient_master SET TBLPROPERTIES('comment' = 'Clean patient registry with standardized enums: region {East, Central, West}, condition {diabetes, hypertension}, risk_tier {low, medium, high}, program {CCM, CCM+Nutrition}. Used for counts and grouping by patient segment.');

-- 2) silver_device_readings
CREATE OR REPLACE TABLE silver_device_readings AS
SELECT
  CAST(reading_id AS STRING) AS reading_id,
  CAST(patient_id AS STRING) AS patient_id,
  CASE UPPER(TRIM(region))
    WHEN 'EAST' THEN 'East'
    WHEN 'CENTRAL' THEN 'Central'
    WHEN 'WEST' THEN 'West'
    ELSE COALESCE(region, 'East')
  END AS region,
  CASE LOWER(TRIM(device_type))
    WHEN 'glucose' THEN 'glucose'
    WHEN 'bp' THEN 'bp'
    WHEN 'weight' THEN 'weight'
    ELSE 'glucose'
  END AS device_type,
  CASE UPPER(TRIM(vendor))
    WHEN 'DEVCO-GM' THEN 'DEVCO-GM'
    WHEN 'DEVCO-BP' THEN 'DEVCO-BP'
    WHEN 'DEVCO-SC' THEN 'DEVCO-SC'
    ELSE 'DEVCO-GM'
  END AS vendor,
  firmware_version,
  CAST(reading_time AS TIMESTAMP) AS reading_time,
  CAST(reading_time AS DATE) AS date,
  DATE_TRUNC('WEEK', reading_time) AS week_start,
  CAST(glucose_mg_dl AS DOUBLE) AS glucose_mg_dl,
  CAST(bp_systolic_mm_hg AS DOUBLE) AS bp_systolic_mm_hg,
  CAST(bp_diastolic_mm_hg AS DOUBLE) AS bp_diastolic_mm_hg,
  CAST(weight_kg AS DOUBLE) AS weight_kg,
  CAST(valid_flag AS BOOLEAN) AS valid_flag,
  COALESCE(error_code, 'NONE') AS error_code,
  CASE WHEN LOWER(TRIM(device_type)) = 'bp' AND bp_diastolic_mm_hg IS NULL THEN TRUE ELSE FALSE END AS bp_missing_diastolic
FROM raw_device_readings;

ALTER TABLE silver_device_readings SET TBLPROPERTIES('comment' = 'Atomic device ingestion with date and week_start helpers. Includes bp_missing_diastolic flag and preserves vendor/firmware/error_code for root-cause.');

-- 3) silver_encounter_notes
CREATE OR REPLACE TABLE silver_encounter_notes AS
SELECT
  CAST(note_id AS STRING) AS note_id,
  CAST(patient_id AS STRING) AS patient_id,
  CASE UPPER(TRIM(region))
    WHEN 'EAST' THEN 'East'
    WHEN 'CENTRAL' THEN 'Central'
    WHEN 'WEST' THEN 'West'
    ELSE COALESCE(region, 'East')
  END AS region,
  CAST(note_time AS TIMESTAMP) AS note_time,
  CAST(note_time AS DATE) AS date,
  DATE_TRUNC('WEEK', note_time) AS week_start,
  CAST(diet_non_adherence_flag AS BOOLEAN) AS diet_non_adherence_flag,
  CAST(med_adherence_flag AS BOOLEAN) AS med_adherence_flag
FROM raw_encounter_notes;

ALTER TABLE silver_encounter_notes SET TBLPROPERTIES('comment' = 'Clinician notes with summarization flags: diet_non_adherence_flag, med_adherence_flag. Daily and weekly helpers for timeseries.');

-- 4) silver_medication_lists
CREATE OR REPLACE TABLE silver_medication_lists AS
SELECT
  CAST(list_id AS STRING) AS list_id,
  CAST(patient_id AS STRING) AS patient_id,
  CASE UPPER(TRIM(region))
    WHEN 'EAST' THEN 'East'
    WHEN 'CENTRAL' THEN 'Central'
    WHEN 'WEST' THEN 'West'
    ELSE COALESCE(region, 'East')
  END AS region,
  CAST(snapshot_time AS TIMESTAMP) AS snapshot_time,
  CAST(snapshot_time AS DATE) AS date,
  DATE_TRUNC('WEEK', snapshot_time) AS week_start,
  CASE med_class
    WHEN 'Metformin' THEN 'Metformin'
    WHEN 'Insulin' THEN 'Insulin'
    WHEN 'GLP-1' THEN 'GLP-1'
    WHEN 'ACE_inhibitor' THEN 'ACE_inhibitor'
    WHEN 'ARB' THEN 'ARB'
    WHEN 'Beta_blocker' THEN 'Beta_blocker'
    WHEN 'Diuretic' THEN 'Diuretic'
    ELSE 'Other'
  END AS med_class,
  CASE change_type
    WHEN 'new' THEN 'new'
    WHEN 'stop' THEN 'stop'
    WHEN 'dose_change' THEN 'dose_change'
    WHEN 'no_change' THEN 'no_change'
    ELSE 'no_change'
  END AS change_type
FROM raw_medication_lists;

ALTER TABLE silver_medication_lists SET TBLPROPERTIES('comment' = 'Medication snapshots with class and change type normalized.');

-- 5) silver_device_change_log
CREATE OR REPLACE TABLE silver_device_change_log AS
SELECT
  CAST(change_id AS STRING) AS change_id,
  CAST(change_date AS TIMESTAMP) AS change_date,
  CAST(change_date AS DATE) AS date,
  CASE UPPER(TRIM(vendor))
    WHEN 'DEVCO-GM' THEN 'DEVCO-GM'
    WHEN 'DEVCO-BP' THEN 'DEVCO-BP'
    WHEN 'DEVCO-SC' THEN 'DEVCO-SC'
    ELSE COALESCE(vendor, 'DEVCO-GM')
  END AS vendor,
  CASE LOWER(TRIM(device_type))
    WHEN 'glucose' THEN 'glucose'
    WHEN 'bp' THEN 'bp'
    WHEN 'weight' THEN 'weight'
    ELSE 'glucose'
  END AS device_type,
  version,
  TRIM(regions_scope) AS regions_scope,
  CASE LOWER(TRIM(change_type))
    WHEN 'rollout' THEN 'rollout'
    WHEN 'config_push' THEN 'config_push'
    WHEN 'hotfix' THEN 'hotfix'
    ELSE LOWER(TRIM(change_type))
  END AS change_type,
  COALESCE(error_codes, 'NONE') AS error_codes,
  notes
FROM raw_device_change_log;

ALTER TABLE silver_device_change_log SET TBLPROPERTIES('comment' = 'Dated vendor/device change log with regions scope and error codes. Key anchors: 2025-10-02 rollout, 2025-10-12 config_push, 2025-10-21 hotfix.');

-- 6) silver_care_actions (join to patient master for consistent condition if needed)
CREATE OR REPLACE TABLE silver_care_actions AS
SELECT
  ca.action_id,
  ca.patient_id,
  CASE UPPER(TRIM(ca.region))
    WHEN 'EAST' THEN 'East'
    WHEN 'CENTRAL' THEN 'Central'
    WHEN 'WEST' THEN 'West'
    ELSE COALESCE(ca.region, 'East')
  END AS region,
  CASE LOWER(TRIM(ca.condition))
    WHEN 'diabetes' THEN 'diabetes'
    WHEN 'hypertension' THEN 'hypertension'
    ELSE pm.condition
  END AS condition,
  ca.action_time,
  CAST(ca.action_time AS DATE) AS date,
  DATE_TRUNC('WEEK', ca.action_time) AS week_start,
  CASE LOWER(TRIM(ca.action_type))
    WHEN 'nurse_outreach' THEN 'nurse_outreach'
    WHEN 'medication_review' THEN 'medication_review'
    WHEN 'nutrition_check_in' THEN 'nutrition_check_in'
    WHEN 'device_troubleshoot' THEN 'device_troubleshoot'
    ELSE 'nurse_outreach'
  END AS action_type,
  CAST(ca.executed_flag AS BOOLEAN) AS executed_flag,
  CAST(ca.estimated_cost_usd AS DOUBLE) AS estimated_cost_usd
FROM raw_care_actions ca
LEFT JOIN silver_patient_master pm ON pm.patient_id = ca.patient_id;

ALTER TABLE silver_care_actions SET TBLPROPERTIES('comment' = 'Operational actions from Next Best Action. Standardized enums and temporal helpers.');

-- =============================
-- === GOLD TABLES (BUSINESS) ===
-- =============================

-- A) gold_date_spine (continuous calendar 2025-08-01..2025-11-10)
CREATE OR REPLACE TABLE gold_date_spine AS
SELECT
  d AS date,
  DAYOFWEEK(d) AS dow,
  CASE WHEN DAYOFWEEK(d) IN (1,7) THEN TRUE ELSE FALSE END AS is_weekend,
  DATE_TRUNC('WEEK', d) AS week_start,
  DATE_TRUNC('MONTH', d) AS month
FROM (
  SELECT EXPLODE(SEQUENCE(
           DATE('2025-08-01'),
           DATE('2025-11-10'),
           INTERVAL 1 DAY
         )) AS d
) s;

ALTER TABLE gold_date_spine SET TBLPROPERTIES('comment' = 'Continuous daily calendar for 2025-08-01..2025-11-10 with weekend flag and week/month buckets.');

-- B) gold_device_ingestion_timeseries
-- Metrics by {date, region, device_type}: total readings, valid readings, valid_rate
CREATE OR REPLACE TABLE gold_device_ingestion_timeseries AS
WITH base AS (
  SELECT date, region, device_type,
         COUNT(*) AS readings_total,
         COUNT_IF(valid_flag) AS readings_valid
  FROM silver_device_readings
  GROUP BY date, region, device_type
),
scaffold AS (
  SELECT ds.date, r.region, dt.device_type
  FROM gold_date_spine ds
  CROSS JOIN (SELECT DISTINCT region FROM silver_patient_master) r
  CROSS JOIN (SELECT 'glucose' AS device_type UNION ALL SELECT 'bp' UNION ALL SELECT 'weight') dt
)
SELECT
  s.date,
  s.region,
  s.device_type,
  COALESCE(b.readings_total, 0) AS readings_total,
  COALESCE(b.readings_valid, 0) AS readings_valid,
  CASE WHEN COALESCE(b.readings_total,0) = 0 THEN NULL ELSE COALESCE(b.readings_valid,0) * 1.0 / b.readings_total END AS valid_rate
FROM scaffold s
LEFT JOIN base b
  ON b.date = s.date AND b.region = s.region AND b.device_type = s.device_type;

ALTER TABLE gold_device_ingestion_timeseries SET TBLPROPERTIES('comment' = 'Daily ingestion by device_type and region with valid_rate. Shows the ~28% drop in glucose valid readings and BP signal issues post 2025-10-02 in Central/West, partial recovery on 2025-10-12, normalization after 2025-10-21.');

-- C) gold_bp_quality_timeseries
CREATE OR REPLACE TABLE gold_bp_quality_timeseries AS
WITH daily AS (
  SELECT date, region,
         COUNT_IF(device_type = 'bp') AS bp_readings,
         COUNT_IF(device_type = 'bp' AND bp_missing_diastolic) AS diastolic_missing
  FROM silver_device_readings
  GROUP BY date, region
)
SELECT
  d.date,
  d.region,
  COALESCE(bp_readings, 0) AS bp_readings,
  COALESCE(diastolic_missing, 0) AS diastolic_missing,
  CASE WHEN COALESCE(bp_readings,0) = 0 THEN NULL ELSE diastolic_missing * 1.0 / bp_readings END AS missing_rate_diastolic
FROM daily d;

ALTER TABLE gold_bp_quality_timeseries SET TBLPROPERTIES('comment' = 'Daily BP quality: diastolic missing rate by region. Spike in Central/West after 2025-10-02, improves after 2025-10-12, residual weekend gaps until 2025-10-21.');

-- D) gold_encounter_signal_timeseries
CREATE OR REPLACE TABLE gold_encounter_signal_timeseries AS
SELECT
  date,
  region,
  AVG(CASE WHEN diet_non_adherence_flag THEN 1.0 ELSE 0.0 END) AS pct_notes_with_diet_non_adherence,
  AVG(CASE WHEN med_adherence_flag THEN 1.0 ELSE 0.0 END) AS pct_notes_with_med_adherence_issues,
  COUNT(*) AS notes_count
FROM silver_encounter_notes
GROUP BY date, region;

ALTER TABLE gold_encounter_signal_timeseries SET TBLPROPERTIES('comment' = 'Daily encounter summarization signals by region: diet non-adherence and medication adherence issues. Expected uptick to ~27-31% during incident window.');

-- E) gold_patient_risk_timeseries (patient-day risk modeling proxy)
-- Proxy risk model: combine device validity + note flags; amplify impact during 2025-10-02..2025-10-21 per narrative.
-- Steps:
--  - Build per-patient-day features from device and notes
--  - Join to patient segmentation
--  - Compute risk_score with elevation for high-risk diabetics during incident
CREATE OR REPLACE TABLE gold_patient_risk_timeseries AS
WITH date_bounds AS (
  SELECT DATE('2025-10-02') AS start_dt, DATE('2025-10-21') AS end_dt
),
patient_days AS (
  SELECT
    d.date,
    pm.patient_id,
    pm.region,
    pm.condition,
    pm.risk_tier
  FROM gold_date_spine d
  INNER JOIN silver_patient_master pm ON pm.active_flag = TRUE
),
features AS (
  SELECT
    sdr.patient_id,
    sdr.date,
    MAX(CASE WHEN sdr.device_type = 'glucose' AND sdr.valid_flag THEN 1 ELSE 0 END) AS has_valid_glucose,
    MAX(CASE WHEN sdr.device_type = 'bp' AND sdr.valid_flag THEN 1 ELSE 0 END) AS has_valid_bp,
    AVG(CASE WHEN sdr.device_type = 'bp' AND sdr.bp_missing_diastolic THEN 1.0 ELSE 0.0 END) AS bp_diastolic_missing_rate
  FROM silver_device_readings sdr
  GROUP BY sdr.patient_id, sdr.date
),
notes AS (
  SELECT
    sen.patient_id,
    sen.date,
    MAX(CASE WHEN sen.diet_non_adherence_flag THEN 1 ELSE 0 END) AS any_diet_non_adherence,
    MAX(CASE WHEN sen.med_adherence_flag THEN 1 ELSE 0 END) AS any_med_adherence_issue
  FROM silver_encounter_notes sen
  GROUP BY sen.patient_id, sen.date
),
joined AS (
  SELECT
    pd.date,
    pd.patient_id,
    pd.region,
    pd.condition,
    pd.risk_tier,
    COALESCE(f.has_valid_glucose, 0) AS has_valid_glucose,
    COALESCE(f.has_valid_bp, 0) AS has_valid_bp,
    COALESCE(f.bp_diastolic_missing_rate, 0.0) AS bp_diastolic_missing_rate,
    COALESCE(n.any_diet_non_adherence, 0) AS any_diet_non_adherence,
    COALESCE(n.any_med_adherence_issue, 0) AS any_med_adherence_issue
  FROM patient_days pd
  LEFT JOIN features f ON f.patient_id = pd.patient_id AND f.date = pd.date
  LEFT JOIN notes n ON n.patient_id = pd.patient_id AND n.date = pd.date
),
scored AS (
  SELECT
    j.*,
    -- Base risk from tier
    CASE j.risk_tier WHEN 'high' THEN 0.5 WHEN 'medium' THEN 0.25 ELSE 0.1 END AS base_risk,
    -- Penalties for missing valid readings
    (CASE WHEN j.has_valid_glucose = 0 AND j.condition = 'diabetes' THEN 0.2 ELSE 0.0 END
     + CASE WHEN j.has_valid_bp = 0 AND j.condition = 'hypertension' THEN 0.15 ELSE 0.0 END) AS ingestion_penalty,
    -- Quality issue penalty (bp diastolic missing)
    LEAST(j.bp_diastolic_missing_rate * 0.3, 0.3) AS quality_penalty,
    -- Note signals
    (CASE WHEN j.any_diet_non_adherence = 1 THEN 0.1 ELSE 0.0 END
     + CASE WHEN j.any_med_adherence_issue = 1 THEN 0.1 ELSE 0.0 END) AS notes_penalty
  FROM joined j
),
incident_adj AS (
  SELECT s.*, db.start_dt, db.end_dt,
         CASE WHEN s.date BETWEEN db.start_dt AND db.end_dt AND s.risk_tier = 'high' AND s.condition = 'diabetes' THEN 1.6 ELSE 1.0 END AS incident_multiplier
  FROM scored s CROSS JOIN date_bounds db
)
SELECT
  date,
  region,
  risk_tier,
  condition,
  AVG(
    LEAST(
      (base_risk + ingestion_penalty + quality_penalty + notes_penalty) * incident_multiplier,
      1.0
    )
  ) AS avg_risk_score,
  COUNT(*) AS patient_days
FROM incident_adj
GROUP BY date, region, risk_tier, condition;

ALTER TABLE gold_patient_risk_timeseries SET TBLPROPERTIES('comment' = 'Patient-day risk proxy aggregated by date, region, risk_tier, condition. Incorporates ingestion gaps, BP quality, and encounter signals with a 1.6x multiplier for high-risk diabetics during 2025-10-02..2025-10-21 to reflect narrative risk elevation.');

-- F) gold_patient_risk_weekly
CREATE OR REPLACE TABLE gold_patient_risk_weekly AS
SELECT
  DATE_TRUNC('WEEK', date) AS week_start,
  region,
  risk_tier,
  condition,
  AVG(avg_risk_score) AS avg_risk_score,
  SUM(patient_days) AS patient_days
FROM gold_patient_risk_timeseries
GROUP BY DATE_TRUNC('WEEK', date), region, risk_tier, condition;

ALTER TABLE gold_patient_risk_weekly SET TBLPROPERTIES('comment' = 'Weekly risk aggregation for distribution by risk tier and condition. Shows elevation during incident window and normalization post 2025-10-21.');

-- G) gold_care_actions_weekly
CREATE OR REPLACE TABLE gold_care_actions_weekly AS
SELECT
  week_start,
  region,
  condition,
  action_type,
  COUNT(*) AS actions_total,
  COUNT_IF(executed_flag) AS actions_executed,
  CASE WHEN COUNT(*) = 0 THEN NULL ELSE COUNT_IF(executed_flag) * 1.0 / COUNT(*) END AS execute_rate,
  AVG(estimated_cost_usd) AS avg_cost_usd
FROM silver_care_actions
GROUP BY week_start, region, condition, action_type;

ALTER TABLE gold_care_actions_weekly SET TBLPROPERTIES('comment' = 'Weekly action mix by region/condition/action_type with execution and cost. Event shows pivot to nurse_outreach and medication_review and ~22-28% volume increase.');

-- H) gold_cumulative_care_cost
CREATE OR REPLACE TABLE gold_cumulative_care_cost AS
WITH daily AS (
  SELECT
    date,
    region,
    condition,
    SUM(CASE WHEN executed_flag THEN estimated_cost_usd ELSE 0.0 END) AS executed_cost_usd
  FROM silver_care_actions
  GROUP BY date, region, condition
),
with_running AS (
  SELECT
    date,
    region,
    condition,
    executed_cost_usd,
    SUM(executed_cost_usd) OVER (PARTITION BY region, condition ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total_cost_usd
  FROM daily
)
SELECT * FROM with_running;

ALTER TABLE gold_cumulative_care_cost SET TBLPROPERTIES('comment' = 'Daily executed cost and running cumulative total by region and condition to visualize incremental exposure rising during incident and flattening post 2025-10-21.');

-- I) gold_root_cause_alignment
-- Join ingestion anomalies with dated change log by exact date to align markers.
-- Also expose counts of error codes in readings on those dates for context.
CREATE OR REPLACE TABLE gold_root_cause_alignment AS
WITH anomalies AS (
  SELECT
    date,
    region,
    device_type,
    readings_total,
    readings_valid,
    valid_rate,
    LAG(valid_rate, 7) OVER (PARTITION BY region, device_type ORDER BY date) AS valid_rate_lag7,
    (valid_rate - LAG(valid_rate, 7) OVER (PARTITION BY region, device_type ORDER BY date)) AS delta_vs_7d
  FROM gold_device_ingestion_timeseries
),
change_expanded AS (
  -- explode regions_scope list to rows
  SELECT
    s.date,
    TRIM(r) AS region,
    s.vendor,
    s.device_type,
    s.version,
    s.change_type,
    s.error_codes,
    s.notes
  FROM (
    SELECT date, vendor, device_type, version, change_type, error_codes, notes, SPLIT(regions_scope, ',') AS regions
    FROM silver_device_change_log
  ) s LATERAL VIEW EXPLODE(s.regions) e AS r
),
error_counts AS (
  SELECT
    date,
    region,
    vendor,
    device_type,
    COUNT_IF(error_code IS NOT NULL AND error_code <> 'NONE') AS error_events
  FROM silver_device_readings
  GROUP BY date, region, vendor, device_type
)
SELECT
  a.date,
  a.region,
  a.device_type,
  a.readings_total,
  a.readings_valid,
  a.valid_rate,
  a.valid_rate_lag7,
  a.delta_vs_7d,
  c.vendor,
  c.version,
  c.change_type,
  c.error_codes,
  c.notes,
  ec.error_events
FROM anomalies a
LEFT JOIN change_expanded c
  ON c.date = a.date AND c.region = a.region AND c.device_type = a.device_type
LEFT JOIN error_counts ec
  ON ec.date = a.date AND ec.region = a.region AND ec.device_type = a.device_type
WHERE a.device_type IN ('glucose','bp');

ALTER TABLE gold_root_cause_alignment SET TBLPROPERTIES('comment' = 'Alignment table linking ingestion valid_rate shifts to dated change log entries (regions exploded) and error event counts. Validates 2025-10-02 rollout, 2025-10-12 config push, 2025-10-21 hotfix against observed anomalies.');

-- J) gold_global_filters_bridge (optional helper for UI filter counts)
CREATE OR REPLACE TABLE gold_global_filters_bridge AS
WITH regions AS (
  SELECT date, region, 'region' AS field_name, region AS field_value FROM gold_device_ingestion_timeseries
),
device_types AS (
  SELECT date, device_type AS field_value, 'device_type' AS field_name, NULL AS region FROM gold_device_ingestion_timeseries
),
risk_tiers AS (
  SELECT date, region, 'risk_tier' AS field_name, risk_tier AS field_value FROM gold_patient_risk_timeseries
),
conditions AS (
  SELECT date, region, 'condition' AS field_name, condition AS field_value FROM gold_patient_risk_timeseries
),
action_types AS (
  SELECT week_start AS date, NULL AS region, 'action_type' AS field_name, action_type AS field_value FROM gold_care_actions_weekly
)
SELECT date, region, field_name, field_value FROM regions
UNION ALL
SELECT date, region, field_name, field_value FROM device_types
UNION ALL
SELECT date, region, field_name, field_value FROM risk_tiers
UNION ALL
SELECT date, region, field_name, field_value FROM conditions
UNION ALL
SELECT date, region, field_name, field_value FROM action_types;

ALTER TABLE gold_global_filters_bridge SET TBLPROPERTIES('comment' = 'Helper bridge enumerating values observed in gold for global filters (region, device_type, risk_tier, condition, action_type).');

-- =======================
-- === COUNTER TABLES ===
-- =======================

-- Counter: Active CCM Patients (active with any device in last 30 days)
CREATE OR REPLACE TABLE gold_counter_active_patients AS
WITH last_date AS (SELECT MAX(date) AS max_date FROM gold_date_spine),
active_with_device AS (
  SELECT DISTINCT pm.patient_id
  FROM silver_patient_master pm
  INNER JOIN silver_device_readings dr ON dr.patient_id = pm.patient_id
  WHERE pm.active_flag = TRUE
    AND dr.date BETWEEN date_sub((SELECT max_date FROM last_date), 29) AND (SELECT max_date FROM last_date)
)
SELECT COUNT(*) AS active_ccm_patients
FROM active_with_device;

ALTER TABLE gold_counter_active_patients SET TBLPROPERTIES('comment' = 'Single-row KPI: count of active CCM patients with any device reading in trailing 30 days.');

-- Counter: Valid Device Readings (Last 7 Days)
CREATE OR REPLACE TABLE gold_counter_valid_readings_last7 AS
WITH last_date AS (SELECT MAX(date) AS max_date FROM gold_date_spine)
SELECT
  SUM(CASE WHEN valid_flag THEN 1 ELSE 0 END) AS valid_readings_last7
FROM silver_device_readings
WHERE date BETWEEN date_sub((SELECT max_date FROM last_date), 6) AND (SELECT max_date FROM last_date);

ALTER TABLE gold_counter_valid_readings_last7 SET TBLPROPERTIES('comment' = 'Single-row KPI: total valid readings across devices in the trailing 7 days anchored to dataset max date.');

-- Counter: Avg Daily Risk Score (High Tier) - last 7 days
CREATE OR REPLACE TABLE gold_counter_avg_daily_risk_high_last7 AS
WITH last_date AS (SELECT MAX(date) AS max_date FROM gold_patient_risk_timeseries)
SELECT
  AVG(avg_risk_score) AS avg_daily_risk_high_last7
FROM gold_patient_risk_timeseries
WHERE risk_tier = 'high'
  AND date BETWEEN date_sub((SELECT max_date FROM last_date), 6) AND (SELECT max_date FROM last_date);

ALTER TABLE gold_counter_avg_daily_risk_high_last7 SET TBLPROPERTIES('comment' = 'Single-row KPI: average daily risk score for high-risk tier across the last 7 days.');

-- Counter: Care Actions Executed (Last 14 Days)
CREATE OR REPLACE TABLE gold_counter_care_actions_executed_last14 AS
WITH last_date AS (SELECT MAX(date) AS max_date FROM gold_date_spine)
SELECT
  COUNT(*) AS actions_executed_last14
FROM silver_care_actions
WHERE executed_flag = TRUE
  AND date BETWEEN date_sub((SELECT max_date FROM last_date), 13) AND (SELECT max_date FROM last_date);

ALTER TABLE gold_counter_care_actions_executed_last14 SET TBLPROPERTIES('comment' = 'Single-row KPI: executed care actions over the trailing 14 days.');
