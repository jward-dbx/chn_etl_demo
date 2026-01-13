-- ======================================================
-- SummitCare Health Network ER Weekend Surge Demo
-- SILVER and GOLD transformations for Sept-2025 monitoring
-- Catalog/Schema: ${catalog}.${schema}
-- ======================================================

-- =============================
-- SILVER LAYER (cleaned data)
-- =============================

-- Silver EMR ER Visits
CREATE OR REPLACE TABLE ${catalog}.${schema}.silver_emr_er_visits AS
WITH base AS (
  SELECT
    TRIM(visit_id) AS visit_id,
    TRIM(patient_id) AS patient_id,
    CASE TRIM(site)
      WHEN 'Lakeview Central' THEN 'Lakeview Central'
      WHEN 'Lakeview East' THEN 'Lakeview East'
      WHEN 'North Ridge' THEN 'North Ridge'
      WHEN 'South Point' THEN 'South Point'
      WHEN 'Pine Valley' THEN 'Pine Valley'
      WHEN 'Riverbend' THEN 'Riverbend'
      ELSE 'Unknown Site'
    END AS site,
    COALESCE(TRIM(unit), 'ER') AS unit,
    CAST(arrival_time AS TIMESTAMP) AS arrival_time_utc,
    CAST(discharge_time AS TIMESTAMP) AS discharge_time_utc,
    CAST(provider_start_time AS TIMESTAMP) AS provider_start_time_utc,
    CAST(arrival_hour AS INT) AS arrival_hour,
    CAST(acuity_level AS INT) AS acuity_level,
    COALESCE(diagnosis_group, 'Other') AS diagnosis_group,
    CASE UPPER(TRIM(discharge_disposition))
      WHEN 'DISCHARGED' THEN 'Discharged'
      WHEN 'ADMITTED' THEN 'Admitted'
      WHEN 'TRANSFERRED' THEN 'Transferred'
      WHEN 'LWBS' THEN 'LWBS'
      ELSE 'Discharged'
    END AS discharge_disposition,
    COALESCE(readmission_30d_flag, FALSE) AS readmission_30d_flag,
    CAST(cost_per_visit_usd AS DOUBLE) AS cost_per_visit_usd
  FROM ${catalog}.${schema}.raw_emr_er_visits
)
SELECT
  visit_id,
  patient_id,
  site,
  unit,
  arrival_time_utc,
  discharge_time_utc,
  provider_start_time_utc,
  arrival_hour,
  acuity_level,
  diagnosis_group,
  discharge_disposition,
  readmission_30d_flag,
  cost_per_visit_usd,
  CAST(arrival_time_utc AS DATE) AS arrival_date,
  DATE_TRUNC('WEEK', arrival_time_utc) AS week_start,
  DATE_TRUNC('MONTH', arrival_time_utc) AS month_start,
  DAYOFWEEK(arrival_time_utc) AS day_of_week_num,
  CASE WHEN DAYOFWEEK(arrival_time_utc) IN (1,7) THEN TRUE ELSE FALSE END AS is_weekend,
  CASE WHEN provider_start_time_utc IS NULL THEN TRUE ELSE FALSE END AS provider_start_time_null_flag,
  CASE WHEN discharge_time_utc IS NOT NULL THEN ROUND((UNIX_TIMESTAMP(discharge_time_utc) - UNIX_TIMESTAMP(arrival_time_utc)) / 60.0, 2) ELSE NULL END AS visit_duration_minutes,
  CASE WHEN provider_start_time_utc IS NOT NULL THEN ROUND((UNIX_TIMESTAMP(provider_start_time_utc) - UNIX_TIMESTAMP(arrival_time_utc)) / 60.0, 2) ELSE NULL END AS door_to_provider_minutes_raw,
  CASE 
    WHEN site IN ('Lakeview Central','Lakeview East') THEN 'Urban'
    WHEN site IN ('North Ridge','South Point') THEN 'Suburban'
    WHEN site IN ('Pine Valley','Riverbend') THEN 'Rural'
    ELSE 'Unknown Region'
  END AS region,
  'ER' AS service_line
FROM base;

ALTER TABLE ${catalog}.${schema}.silver_emr_er_visits
  SET TBLPROPERTIES ('comment' = 'Clean EMR ER visit facts in UTC with derived dates, weekend flag, service_line, region, visit_duration and door-to-provider raw minutes. Supports arrival/throughput/LWBS and cost metrics.');

-- Silver HR Shifts & Sick Leave
CREATE OR REPLACE TABLE ${catalog}.${schema}.silver_hr_shifts_and_sickleave AS
WITH base AS (
  SELECT
    TRIM(shift_id) AS shift_id,
    TRIM(staff_id) AS staff_id,
    CASE TRIM(role)
      WHEN 'Nurse' THEN 'Nurse'
      WHEN 'Physician' THEN 'Physician'
      WHEN 'Tech' THEN 'Tech'
      WHEN 'Registration' THEN 'Registration'
      ELSE 'Other'
    END AS role,
    CASE TRIM(site)
      WHEN 'Lakeview Central' THEN 'Lakeview Central'
      WHEN 'Lakeview East' THEN 'Lakeview East'
      WHEN 'North Ridge' THEN 'North Ridge'
      WHEN 'South Point' THEN 'South Point'
      WHEN 'Pine Valley' THEN 'Pine Valley'
      WHEN 'Riverbend' THEN 'Riverbend'
      ELSE 'Unknown Site'
    END AS site,
    COALESCE(TRIM(unit),'ER') AS unit,
    CAST(scheduled_start AS TIMESTAMP) AS scheduled_start_utc,
    CAST(scheduled_end AS TIMESTAMP) AS scheduled_end_utc,
    COALESCE(actual_attended, TRUE) AS attended_flag,
    COALESCE(sick_leave_status, 'None') AS sick_leave_status,
    CAST(overtime_hours AS DOUBLE) AS overtime_hours,
    CAST(shift_coverage_hours AS DOUBLE) AS shift_coverage_hours,
    COALESCE(change_log_note, '') AS change_log_note
  FROM ${catalog}.${schema}.raw_hr_shifts_and_sickleave
)
SELECT
  shift_id,
  staff_id,
  role,
  site,
  unit,
  scheduled_start_utc,
  scheduled_end_utc,
  attended_flag,
  sick_leave_status,
  overtime_hours,
  shift_coverage_hours,
  change_log_note,
  CAST(scheduled_start_utc AS DATE) AS shift_date,
  DAYOFWEEK(scheduled_start_utc) AS day_of_week_num,
  CASE WHEN DAYOFWEEK(scheduled_start_utc) IN (1,7) THEN TRUE ELSE FALSE END AS is_weekend,
  HOUR(scheduled_start_utc) AS start_hour,
  HOUR(scheduled_end_utc) AS end_hour,
  CASE WHEN UPPER(sick_leave_status) IN ('REPORTED','CONFIRMED') THEN TRUE ELSE FALSE END AS sick_leave_flag,
  CASE WHEN attended_flag THEN shift_coverage_hours ELSE 0.0 END AS effective_shift_hours,
  CASE 
    WHEN site IN ('Lakeview Central','Lakeview East') THEN 'Urban'
    WHEN site IN ('North Ridge','South Point') THEN 'Suburban'
    WHEN site IN ('Pine Valley','Riverbend') THEN 'Rural'
    ELSE 'Unknown Region'
  END AS region,
  'ER' AS service_line
FROM base;

ALTER TABLE ${catalog}.${schema}.silver_hr_shifts_and_sickleave
  SET TBLPROPERTIES ('comment' = 'Clean HR shifts with attendance, sick leave, overtime, effective hours, weekend flag, region, and service_line. Used for coverage and finance.');

-- Silver Patient Flow Metrics
CREATE OR REPLACE TABLE ${catalog}.${schema}.silver_patient_flow_metrics AS
WITH base AS (
  SELECT
    TRIM(flow_id) AS flow_id,
    CASE TRIM(site)
      WHEN 'Lakeview Central' THEN 'Lakeview Central'
      WHEN 'Lakeview East' THEN 'Lakeview East'
      WHEN 'North Ridge' THEN 'North Ridge'
      WHEN 'South Point' THEN 'South Point'
      WHEN 'Pine Valley' THEN 'Pine Valley'
      WHEN 'Riverbend' THEN 'Riverbend'
      ELSE 'Unknown Site'
    END AS site,
    COALESCE(TRIM(unit),'ER') AS unit,
    CAST(event_time AS TIMESTAMP) AS event_time_utc,
    CAST(hour_of_day AS INT) AS hour_of_day,
    CAST(door_to_triage_minutes AS DOUBLE) AS door_to_triage_minutes,
    CAST(door_to_provider_minutes AS DOUBLE) AS door_to_provider_minutes,
    CAST(triage_level AS INT) AS triage_level,
    CAST(queue_length AS INT) AS queue_length,
    COALESCE(telemetry_status,'OK') AS telemetry_status
  FROM ${catalog}.${schema}.raw_patient_flow_metrics
), smoothed AS (
  SELECT
    flow_id,
    site,
    unit,
    event_time_utc,
    CAST(event_time_utc AS DATE) AS date,
    hour_of_day,
    door_to_triage_minutes,
    door_to_provider_minutes,
    triage_level,
    queue_length,
    telemetry_status,
    PERCENTILE_APPROX(queue_length, 0.5) OVER (PARTITION BY site, CAST(event_time_utc AS DATE), hour_of_day) AS queue_length_median_15min
  FROM base
)
SELECT
  flow_id,
  site,
  unit,
  event_time_utc,
  date,
  hour_of_day,
  door_to_triage_minutes AS triage_wait_minutes,
  door_to_provider_minutes,
  triage_level,
  queue_length,
  queue_length_median_15min,
  telemetry_status,
  CASE WHEN telemetry_status = 'DELAYED' THEN TRUE ELSE FALSE END AS telemetry_delayed,
  DAYOFWEEK(event_time_utc) AS day_of_week_num,
  CASE WHEN DAYOFWEEK(event_time_utc) IN (1,7) THEN TRUE ELSE FALSE END AS is_weekend,
  CASE 
    WHEN site IN ('Lakeview Central','Lakeview East') THEN 'Urban'
    WHEN site IN ('North Ridge','South Point') THEN 'Suburban'
    WHEN site IN ('Pine Valley','Riverbend') THEN 'Rural'
    ELSE 'Unknown Region'
  END AS region,
  'ER' AS service_line
FROM smoothed;

ALTER TABLE ${catalog}.${schema}.silver_patient_flow_metrics
  SET TBLPROPERTIES ('comment' = 'Telemetry for patient flow: triage/provider waits, queue length with 15-min median smoothing, weekend flag, region, service_line.');

-- Silver Patient Satisfaction Surveys (joined to visits for weekend/site alignment)
CREATE OR REPLACE TABLE ${catalog}.${schema}.silver_patient_satisfaction_surveys AS
WITH src AS (
  SELECT
    TRIM(survey_id) AS survey_id,
    TRIM(visit_id) AS visit_id,
    CASE TRIM(site)
      WHEN 'Lakeview Central' THEN 'Lakeview Central'
      WHEN 'Lakeview East' THEN 'Lakeview East'
      WHEN 'North Ridge' THEN 'North Ridge'
      WHEN 'South Point' THEN 'South Point'
      WHEN 'Pine Valley' THEN 'Pine Valley'
      WHEN 'Riverbend' THEN 'Riverbend'
      ELSE 'Unknown Site'
    END AS site,
    COALESCE(TRIM(unit),'ER') AS unit,
    CAST(survey_date AS DATE) AS survey_date,
    CAST(overall_score AS DOUBLE) AS overall_score,
    CAST(staff_courtesy AS DOUBLE) AS staff_courtesy,
    CAST(communication_clarity AS DOUBLE) AS communication_clarity,
    CAST(cleanliness AS DOUBLE) AS cleanliness,
    comments
  FROM ${catalog}.${schema}.raw_patient_satisfaction_surveys
)
SELECT
  s.survey_id,
  s.visit_id,
  COALESCE(s.site, v.site) AS site,
  COALESCE(s.unit, v.unit) AS unit,
  s.survey_date,
  s.overall_score,
  s.staff_courtesy,
  s.communication_clarity,
  s.cleanliness,
  s.comments,
  v.arrival_date,
  v.is_weekend,
  v.region,
  'ER' AS service_line
FROM src s
LEFT JOIN ${catalog}.${schema}.silver_emr_er_visits v
  ON s.visit_id = v.visit_id;

ALTER TABLE ${catalog}.${schema}.silver_patient_satisfaction_surveys
  SET TBLPROPERTIES ('comment' = 'Clean survey results aligned to visits to derive weekend/site segmentation; includes subscores and comments.');

-- Silver Readmission Risk Feed (joined to visits)
CREATE OR REPLACE TABLE ${catalog}.${schema}.silver_readmission_risk_feed AS
WITH src AS (
  SELECT
    TRIM(visit_id) AS visit_id,
    TRIM(patient_id) AS patient_id,
    CAST(prediction_date AS DATE) AS prediction_date,
    CAST(readmission_probability AS DOUBLE) AS readmission_probability,
    CASE UPPER(TRIM(risk_band))
      WHEN 'LOW' THEN 'Low'
      WHEN 'MEDIUM' THEN 'Medium'
      WHEN 'HIGH' THEN 'High'
      ELSE 'Medium'
    END AS risk_band
  FROM ${catalog}.${schema}.raw_readmission_risk_feed
)
SELECT
  r.visit_id,
  r.patient_id,
  r.prediction_date,
  r.readmission_probability,
  r.risk_band,
  v.site,
  v.unit,
  v.arrival_date,
  v.is_weekend,
  v.region,
  'ER' AS service_line,
  DATEDIFF(r.prediction_date, v.arrival_date) AS lag_days
FROM src r
LEFT JOIN ${catalog}.${schema}.silver_emr_er_visits v
  ON r.visit_id = v.visit_id AND r.patient_id = v.patient_id;

ALTER TABLE ${catalog}.${schema}.silver_readmission_risk_feed
  SET TBLPROPERTIES ('comment' = 'Predictive readmission probabilities aligned to ER visits; includes lag_days, weekend flag, region, and service_line.');

-- =============================
-- GOLD LAYER (aggregations)
-- =============================

-- Operational Hourly: arrivals, throughput, waits, staffing, coverage
CREATE OR REPLACE TABLE ${catalog}.${schema}.gold_er_operational_hourly AS
WITH hour_spine AS (
  SELECT
    site,
    'ER' AS unit,
    d AS date,
    h AS hour_of_day,
    CASE WHEN DAYOFWEEK(d) IN (1,7) THEN TRUE ELSE FALSE END AS is_weekend
  FROM (
    SELECT EXPLODE(SEQUENCE(
             (SELECT MIN(arrival_date) FROM ${catalog}.${schema}.silver_emr_er_visits),
             (SELECT MAX(arrival_date) FROM ${catalog}.${schema}.silver_emr_er_visits),
             INTERVAL 1 DAY
           )) AS d
  ) dates
  CROSS JOIN (
    SELECT EXPLODE(SEQUENCE(0,23,1)) AS h
  ) hours
  CROSS JOIN (
    SELECT DISTINCT site FROM ${catalog}.${schema}.silver_emr_er_visits
  ) sites
), arrivals AS (
  SELECT site, arrival_date AS date, arrival_hour AS hour_of_day, COUNT(*) AS arrivals
  FROM ${catalog}.${schema}.silver_emr_er_visits
  GROUP BY site, arrival_date, arrival_hour
), throughput AS (
  SELECT site, CAST(discharge_time_utc AS DATE) AS date, HOUR(discharge_time_utc) AS hour_of_day, COUNT(*) AS throughput
  FROM ${catalog}.${schema}.silver_emr_er_visits
  WHERE discharge_time_utc IS NOT NULL
  GROUP BY site, CAST(discharge_time_utc AS DATE), HOUR(discharge_time_utc)
), waits AS (
  SELECT site, date, hour_of_day,
         PERCENTILE_APPROX(triage_wait_minutes, 0.5) AS door_to_triage_median,
         PERCENTILE_APPROX(door_to_provider_minutes, 0.5) AS door_to_provider_median,
         PERCENTILE_APPROX(queue_length_median_15min, 0.5) AS queue_length_median
  FROM ${catalog}.${schema}.silver_patient_flow_metrics
  GROUP BY site, date, hour_of_day
), staffing AS (
  -- Expand effective hours into hourly buckets by start hour; approximation for coverage per hour
  SELECT site,
         CAST(scheduled_start_utc AS DATE) AS date,
         HOUR(scheduled_start_utc) AS hour_of_day,
         SUM(effective_shift_hours) AS effective_staffing_hours
  FROM ${catalog}.${schema}.silver_hr_shifts_and_sickleave
  GROUP BY site, CAST(scheduled_start_utc AS DATE), HOUR(scheduled_start_utc)
)
SELECT
  sp.site,
  CASE 
    WHEN sp.site IN ('Lakeview Central','Lakeview East') THEN 'Urban'
    WHEN sp.site IN ('North Ridge','South Point') THEN 'Suburban'
    WHEN sp.site IN ('Pine Valley','Riverbend') THEN 'Rural'
    ELSE 'Unknown Region'
  END AS region,
  sp.unit,
  sp.date,
  sp.hour_of_day,
  sp.is_weekend,
  COALESCE(a.arrivals, 0) AS arrivals,
  COALESCE(t.throughput, 0) AS throughput,
  COALESCE(w.queue_length_median, 0.0) AS queue_length_median,
  COALESCE(w.door_to_triage_median, NULL) AS door_to_triage_median,
  COALESCE(w.door_to_provider_median, NULL) AS door_to_provider_median,
  COALESCE(s.effective_staffing_hours, 0.0) AS effective_staffing_hours,
  CASE WHEN COALESCE(a.arrivals,0) > 0 THEN ROUND(COALESCE(s.effective_staffing_hours,0.0) * 60.0 / (COALESCE(a.arrivals,0) * 240.0), 3) ELSE NULL END AS nurse_to_patient_ratio,
  CASE WHEN COALESCE(a.arrivals,0) > 0 THEN ROUND(COALESCE(t.throughput,0) * 1.0 / COALESCE(a.arrivals,0), 3) ELSE NULL END AS occupancy_pct
FROM hour_spine sp
LEFT JOIN arrivals a  ON a.site = sp.site AND a.date = sp.date AND a.hour_of_day = sp.hour_of_day
LEFT JOIN throughput t ON t.site = sp.site AND t.date = sp.date AND t.hour_of_day = sp.hour_of_day
LEFT JOIN waits w      ON w.site = sp.site AND w.date = sp.date AND w.hour_of_day = sp.hour_of_day
LEFT JOIN staffing s   ON s.site = sp.site AND s.date = sp.date AND s.hour_of_day = sp.hour_of_day;

ALTER TABLE ${catalog}.${schema}.gold_er_operational_hourly
  SET TBLPROPERTIES ('comment' = 'Hourly ER operational metrics by site: arrivals, throughput, queue median, triage and door-to-provider medians, effective staffing hours, computed nurse_to_patient_ratio approximation, and occupancy_pct. Shows weekend surge dynamics.');

-- Quality Daily: LWBS rate, medians, satisfaction, throughput
CREATE OR REPLACE TABLE ${catalog}.${schema}.gold_er_quality_daily AS
WITH visits AS (
  SELECT site, unit, arrival_date AS date, is_weekend,
         COUNT(*) AS visits_total,
         COUNT_IF(discharge_disposition = 'LWBS') AS lwbs_count,
         COUNT_IF(discharge_time_utc IS NOT NULL) AS throughput_daily
  FROM ${catalog}.${schema}.silver_emr_er_visits
  GROUP BY site, unit, arrival_date, is_weekend
), waits AS (
  SELECT site, unit, date,
         PERCENTILE_APPROX(triage_wait_minutes, 0.5) AS median_triage_wait_minutes,
         PERCENTILE_APPROX(door_to_provider_minutes, 0.5) AS median_door_to_provider_minutes
  FROM ${catalog}.${schema}.silver_patient_flow_metrics
  GROUP BY site, unit, date
), sats AS (
  SELECT site, unit, arrival_date AS date,
         AVG(overall_score) AS satisfaction_overall_avg
  FROM ${catalog}.${schema}.silver_patient_satisfaction_surveys
  GROUP BY site, unit, arrival_date
)
SELECT
  v.site,
  CASE 
    WHEN v.site IN ('Lakeview Central','Lakeview East') THEN 'Urban'
    WHEN v.site IN ('North Ridge','South Point') THEN 'Suburban'
    WHEN v.site IN ('Pine Valley','Riverbend') THEN 'Rural'
    ELSE 'Unknown Region'
  END AS region,
  v.unit,
  v.date,
  v.is_weekend,
  v.visits_total,
  v.throughput_daily,
  ROUND(CASE WHEN v.visits_total > 0 THEN v.lwbs_count * 1.0 / v.visits_total ELSE 0 END, 4) AS lwbs_rate,
  w.median_triage_wait_minutes,
  w.median_door_to_provider_minutes,
  s.satisfaction_overall_avg,
  DAYOFWEEK(v.date) AS day_of_week_num
FROM visits v
LEFT JOIN waits w ON w.site = v.site AND w.unit = v.unit AND w.date = v.date
LEFT JOIN sats s  ON s.site = v.site AND s.unit = v.unit AND s.date = v.date;

ALTER TABLE ${catalog}.${schema}.gold_er_quality_daily
  SET TBLPROPERTIES ('comment' = 'Daily ER quality KPIs per site: LWBS rate, median triage and door-to-provider minutes, throughput, satisfaction average, weekend flag, and day_of_week_num.');

-- Finance Daily: overtime, reimbursement at risk, cost per visit, cumulative
CREATE OR REPLACE TABLE ${catalog}.${schema}.gold_er_finance_daily AS
WITH overtime AS (
  SELECT site, unit, shift_date AS date, is_weekend,
         SUM(overtime_hours) AS overtime_hours_sum
  FROM ${catalog}.${schema}.silver_hr_shifts_and_sickleave
  GROUP BY site, unit, shift_date, is_weekend
), costs AS (
  SELECT site, unit, arrival_date AS date,
         AVG(cost_per_visit_usd) AS cost_per_visit_avg
  FROM ${catalog}.${schema}.silver_emr_er_visits
  GROUP BY site, unit, arrival_date
), quality AS (
  SELECT site, unit, date, lwbs_rate,
         COALESCE(median_door_to_provider_minutes, 0) AS median_door_to_provider_minutes
  FROM ${catalog}.${schema}.gold_er_quality_daily
)
SELECT
  o.site,
  CASE 
    WHEN o.site IN ('Lakeview Central','Lakeview East') THEN 'Urban'
    WHEN o.site IN ('North Ridge','South Point') THEN 'Suburban'
    WHEN o.site IN ('Pine Valley','Riverbend') THEN 'Rural'
    ELSE 'Unknown Region'
  END AS region,
  o.unit,
  o.date,
  o.is_weekend,
  o.overtime_hours_sum,
  c.cost_per_visit_avg,
  -- Simple reimbursement at risk proxy: base * (lwbs_rate * 100) + door-to-provider breach surcharge
  ROUND((COALESCE(q.lwbs_rate,0) * 100.0) * 250.0 + CASE WHEN COALESCE(q.median_door_to_provider_minutes,0) > 35 THEN 750.0 ELSE 0.0 END, 2) AS reimbursement_at_risk_usd,
  SUM(
    ROUND((COALESCE(q.lwbs_rate,0) * 100.0) * 250.0 + CASE WHEN COALESCE(q.median_door_to_provider_minutes,0) > 35 THEN 750.0 ELSE 0.0 END, 2)
  ) OVER (PARTITION BY o.site ORDER BY o.date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_reimbursement_at_risk_usd
FROM overtime o
LEFT JOIN costs c   ON c.site = o.site AND c.unit = o.unit AND c.date = o.date
LEFT JOIN quality q ON q.site = o.site AND q.unit = o.unit AND q.date = o.date;

ALTER TABLE ${catalog}.${schema}.gold_er_finance_daily
  SET TBLPROPERTIES ('comment' = 'Daily ER finance KPIs: overtime hours sum, average cost per visit, estimated reimbursement at risk based on LWBS and door-to-provider breaches, plus cumulative per site.');

-- Staffing Daily: scheduled/effective hours, sick leave rate, coverage gap flag
CREATE OR REPLACE TABLE ${catalog}.${schema}.gold_er_staffing_daily AS
WITH hr AS (
  SELECT site, unit, shift_date AS date, is_weekend, role,
         SUM(shift_coverage_hours) AS scheduled_hours,
         SUM(effective_shift_hours) AS effective_hours,
         AVG(CASE WHEN sick_leave_flag THEN 1.0 ELSE 0.0 END) AS sick_leave_rate
  FROM ${catalog}.${schema}.silver_hr_shifts_and_sickleave
  GROUP BY site, unit, shift_date, is_weekend, role
), op AS (
  SELECT site, date,
         AVG(nurse_to_patient_ratio) AS avg_nurse_to_patient_ratio
  FROM ${catalog}.${schema}.gold_er_operational_hourly
  GROUP BY site, date
)
SELECT
  h.site,
  CASE 
    WHEN h.site IN ('Lakeview Central','Lakeview East') THEN 'Urban'
    WHEN h.site IN ('North Ridge','South Point') THEN 'Suburban'
    WHEN h.site IN ('Pine Valley','Riverbend') THEN 'Rural'
    ELSE 'Unknown Region'
  END AS region,
  h.unit,
  h.date,
  h.is_weekend,
  h.role,
  h.scheduled_hours,
  h.effective_hours,
  h.sick_leave_rate,
  o.avg_nurse_to_patient_ratio,
  CASE WHEN h.role = 'Nurse' AND COALESCE(o.avg_nurse_to_patient_ratio, 0) > 0.25 THEN TRUE ELSE FALSE END AS coverage_gap_flag
FROM hr h
LEFT JOIN op o ON o.site = h.site AND o.date = h.date;

ALTER TABLE ${catalog}.${schema}.gold_er_staffing_daily
  SET TBLPROPERTIES ('comment' = 'Daily staffing by site/unit/role: scheduled vs effective hours, sick leave rate, and coverage_gap_flag using nurse-to-patient ratio threshold.');

-- Readmission Risk Daily: averages and realized readmissions
CREATE OR REPLACE TABLE ${catalog}.${schema}.gold_er_readmission_risk_daily AS
WITH risk AS (
  SELECT site, unit, arrival_date AS date, is_weekend,
         AVG(readmission_probability) AS avg_readmission_probability,
         AVG(CASE WHEN risk_band = 'High' THEN 1.0 ELSE 0.0 END) AS high_risk_share
  FROM ${catalog}.${schema}.silver_readmission_risk_feed
  GROUP BY site, unit, arrival_date, is_weekend
), realized AS (
  SELECT site, unit, arrival_date AS date,
         COUNT_IF(readmission_30d_flag) AS realized_readmissions_30d
  FROM ${catalog}.${schema}.silver_emr_er_visits
  GROUP BY site, unit, arrival_date
)
SELECT
  r.site,
  CASE 
    WHEN r.site IN ('Lakeview Central','Lakeview East') THEN 'Urban'
    WHEN r.site IN ('North Ridge','South Point') THEN 'Suburban'
    WHEN r.site IN ('Pine Valley','Riverbend') THEN 'Rural'
    ELSE 'Unknown Region'
  END AS region,
  r.unit,
  r.date,
  r.is_weekend,
  r.avg_readmission_probability,
  r.high_risk_share,
  z.realized_readmissions_30d
FROM risk r
LEFT JOIN realized z ON z.site = r.site AND z.unit = r.unit AND z.date = r.date;

ALTER TABLE ${catalog}.${schema}.gold_er_readmission_risk_daily
  SET TBLPROPERTIES ('comment' = 'Daily readmission risk metrics and realized 30-day readmissions by site; captures uplift on surge weekends and exposed cohorts.');

-- Global Filters Bridge
CREATE OR REPLACE TABLE ${catalog}.${schema}.gold_global_filters_bridge AS
SELECT DISTINCT
  v.arrival_date AS date,
  v.site,
  CASE 
    WHEN v.site IN ('Lakeview Central','Lakeview East') THEN 'Urban'
    WHEN v.site IN ('North Ridge','South Point') THEN 'Suburban'
    WHEN v.site IN ('Pine Valley','Riverbend') THEN 'Rural'
    ELSE 'Unknown Region'
  END AS region,
  v.unit,
  v.is_weekend,
  CAST(NULL AS STRING) AS role,
  DAYOFWEEK(v.arrival_date) AS day_of_week_num,
  'ER' AS service_line
FROM ${catalog}.${schema}.silver_emr_er_visits v
UNION
SELECT DISTINCT
  h.shift_date AS date,
  h.site,
  h.region,
  h.unit,
  h.is_weekend,
  h.role,
  DAYOFWEEK(h.shift_date) AS day_of_week_num,
  'ER' AS service_line
FROM ${catalog}.${schema}.silver_hr_shifts_and_sickleave h;

ALTER TABLE ${catalog}.${schema}.gold_global_filters_bridge
  SET TBLPROPERTIES ('comment' = 'Denormalized bridge providing common filter fields: date, site, region, unit, is_weekend, role, day_of_week_num, and service_line for dashboards.');
