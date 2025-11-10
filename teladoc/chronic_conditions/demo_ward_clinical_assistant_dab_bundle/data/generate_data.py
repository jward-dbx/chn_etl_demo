# Databricks notebook source
# MAGIC %md
# MAGIC # Data Generation Notebook
# MAGIC 
# MAGIC This notebook generates synthetic RAW datasets for the Clinical CCM Monitoring story.
# MAGIC Generates: patient_master, device_readings, encounter_notes, medication_lists, device_change_log, care_actions

# COMMAND ----------
# Databricks notebook source
# MAGIC %md
# MAGIC ## Setup: Install Libraries and Configure Environment

# COMMAND ----------
# Databricks notebook source
# MAGIC %pip install faker>=19.0.0 holidays>=0.35 pyarrow

# COMMAND ----------
# Databricks notebook source
# MAGIC %md
# MAGIC ## Import Libraries

# COMMAND ----------
import random
import numpy as np
import pandas as pd
from faker import Faker
import holidays
import os

# Set environment variables for Databricks Volumes
# These will be set from job parameters, but provide defaults
try:
    catalog = dbutils.widgets.get("catalog")
except:
    catalog = None
try:
    bronze_schema = dbutils.widgets.get("bronze_schema")
except:
    bronze_schema = None
try:
    volume = dbutils.widgets.get("volume")
except:
    volume = None

# Use defaults if not provided
catalog = catalog if catalog else "ward_demo"
bronze_schema = bronze_schema if bronze_schema else "bronze"
volume = volume if volume else "raw_data"

os.environ['CATALOG'] = catalog
os.environ['BRONZE_SCHEMA'] = bronze_schema
os.environ['VOLUME'] = volume

print(f"Configuration:")
print(f"  CATALOG: {catalog}")
print(f"  BRONZE_SCHEMA: {bronze_schema}")
print(f"  VOLUME: {volume}")

# COMMAND ----------
# Databricks notebook source
# MAGIC %md
# MAGIC ## Import Utils

# COMMAND ----------
# Import utils from the same directory
# In Databricks notebooks, files in the same directory are automatically available
try:
    from utils import save_to_table
except ImportError:
    # If import fails, load utils.py directly
    import importlib.util
    import sys
    
    # Get the current notebook path and construct utils path
    notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    # Remove the notebook name and add utils.py
    base_path = '/'.join(notebook_path.split('/')[:-1])
    utils_path = f"/Workspace{base_path}/utils.py"
    
    if os.path.exists(utils_path):
        spec = importlib.util.spec_from_file_location("utils", utils_path)
        utils = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(utils)
        save_to_table = utils.save_to_table
    else:
        # Fallback: use the utils.py from the workspace sync location
        # Files are synced to workspace_path/data/
        workspace_path = os.getenv('WORKSPACE_PATH', '/Users/justin.ward@databricks.com/demo_ward_clinical_assistant')
        utils_path = f"{workspace_path}/data/utils.py"
        if os.path.exists(utils_path):
            spec = importlib.util.spec_from_file_location("utils", utils_path)
            utils = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(utils)
            save_to_table = utils.save_to_table
        else:
            # Final fallback: define a simple version that writes to table
            def save_to_table(df, table_name, num_files=5):
                from pyspark.sql import SparkSession
                spark = SparkSession.builder.getOrCreate()
                catalog = os.getenv('CATALOG', 'ward_demo')
                schema = os.getenv('BRONZE_SCHEMA', os.getenv('SCHEMA', 'bronze'))
                full_table_name = f"{catalog}.{schema}.raw_{table_name}"
                spark_df = spark.createDataFrame(df)
                spark_df.coalesce(num_files).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(full_table_name)
                print(f'✓ Saved {len(df):,} rows to {full_table_name}')

# COMMAND ----------
# Databricks notebook source
# MAGIC %md
# MAGIC ## Configuration and Constants

# COMMAND ----------
# ===============================
# === REPRO & GLOBAL WINDOWS ====
# ===============================
SEED = 42
np.random.seed(SEED)
random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

# Time windows (tz-naive and floored to ms)
RANGE_START = pd.Timestamp("2025-08-01").tz_localize(None).floor("ms")
RANGE_END = pd.Timestamp("2025-11-10").tz_localize(None).floor("ms")
EVENT_ROLLOUT = pd.Timestamp("2025-10-02").tz_localize(None).floor("ms")
EVENT_CONFIG_PUSH = pd.Timestamp("2025-10-12").tz_localize(None).floor("ms")
EVENT_HOTFIX = pd.Timestamp("2025-10-21").tz_localize(None).floor("ms")

DAYS = pd.date_range(RANGE_START.normalize(), RANGE_END.normalize(), freq="D")
DAYS = pd.to_datetime(DAYS, utc=False).tz_localize(None)

US_HOLIDAYS = set()
for y in range(RANGE_START.year, RANGE_END.year + 1):
    US_HOLIDAYS |= set(holidays.UnitedStates(years=y).keys())
US_HOLIDAYS = {pd.Timestamp(d).tz_localize(None).normalize() for d in US_HOLIDAYS}

REGIONS = ["East", "Central", "West"]
REGION_PROBS = np.array([0.40, 0.30, 0.30])

CONDITIONS = ["diabetes", "hypertension"]
COND_PROBS = np.array([0.63, 0.37])  # diabetes primary ~60-65%

RISK_TIERS = ["low", "medium", "high"]
RISK_PROBS = np.array([0.48, 0.38, 0.14])  # high ~12-15%

PROGRAMS = ["CCM", "CCM+Nutrition"]
PROGRAM_PROBS = np.array([0.68, 0.32])  # CCM+Nutrition 25-35%, more in West later
HOURS_RANGE = np.arange(24)

# COMMAND ----------
# Databricks notebook source
# MAGIC %md
# MAGIC ## Utility Functions

# COMMAND ----------
# ===============================
# === UTIL HELPERS ==============
# ===============================

def _choose(values, probs, size):
    p = np.array(probs, dtype=float)
    p = p / p.sum()
    return np.random.choice(values, size=size, p=p)


def build_business_hours_probs(is_weekend: bool) -> np.ndarray:
    if not is_weekend:
        hour_probs = np.array([
            0.005, 0.005, 0.005, 0.005, 0.005, 0.010,
            0.020, 0.030, 0.055, 0.075, 0.085, 0.085,
            0.085, 0.080, 0.075, 0.060, 0.050, 0.050,
            0.045, 0.035, 0.030, 0.020, 0.015, 0.010,
        ])
    else:
        hour_probs = np.array([
            0.005, 0.005, 0.005, 0.005, 0.010, 0.010,
            0.020, 0.030, 0.040, 0.050, 0.060, 0.070,
            0.070, 0.065, 0.060, 0.055, 0.050, 0.050,
            0.055, 0.060, 0.045, 0.030, 0.020, 0.015,
        ])
    hour_probs = hour_probs / hour_probs.sum()
    return hour_probs

# COMMAND ----------
# Databricks notebook source
# MAGIC %md
# MAGIC ## Generate Patient Master

# COMMAND ----------
# ===============================
# === 1) PATIENT MASTER =========
# ===============================

def generate_patient_master(n_rows: int = 18240) -> pd.DataFrame:
    print(f"Generating patient_master ({n_rows:,})...")

    # Region distribution non-flat; West higher CCM+Nutrition rate
    region = _choose(REGIONS, REGION_PROBS, n_rows)
    condition = _choose(CONDITIONS, COND_PROBS, n_rows)
    risk_tier = _choose(RISK_TIERS, RISK_PROBS, n_rows)

    # Program with West tilt to CCM+Nutrition
    base_program = _choose(PROGRAMS, PROGRAM_PROBS, n_rows)
    west_mask = region == "West"
    # Increase CCM+Nutrition in West by shifting a fraction from CCM
    shift_mask = west_mask & (base_program == "CCM") & (np.random.rand(n_rows) < 0.20)
    base_program[shift_mask] = "CCM+Nutrition"

    # Enrollment dates spread over the last 400 days, bias earlier
    enroll_offsets = np.random.randint(30, 400, size=n_rows)
    enrollment_date = (
        (RANGE_START.normalize() - pd.to_timedelta(enroll_offsets, unit="D"))
        .tz_localize(None)
        .floor("ms")
    )

    # Active flags mostly true
    active_flag = np.random.rand(n_rows) < 0.92

    patient_ids = np.char.mod("PT-%06d", np.arange(1, n_rows + 1))

    df = pd.DataFrame({
        "patient_id": patient_ids,
        "region": region,
        "condition": condition,
        "risk_tier": risk_tier,
        "program": base_program,
        "enrollment_date": enrollment_date,
        "active_flag": active_flag,
    })

    df["enrollment_date"] = pd.to_datetime(df["enrollment_date"], errors="coerce").dt.floor("ms")
    return df

patient_master = generate_patient_master(18240)
save_to_table(patient_master, "patient_master", num_files=4)

# COMMAND ----------
# Databricks notebook source
# MAGIC %md
# MAGIC ## Generate Device Readings

# COMMAND ----------
# ===============================
# === 2) DEVICE READINGS =========
# ===============================

def generate_device_readings(patient_master: pd.DataFrame, target_rows: int = 312450) -> pd.DataFrame:
    print(f"Generating device_readings (~{target_rows:,})...")
    pm = patient_master[patient_master["active_flag"]].copy().reset_index(drop=True)
    patient_ids = pm["patient_id"].values
    regions = pm["region"].values
    conditions = pm["condition"].values

    # Device type mix
    DEVICE_TYPES = ["glucose", "bp", "weight"]
    DEVICE_PROBS = np.array([0.50, 0.36, 0.14])

    vendors = {"glucose": "DEVCO-GM", "bp": "DEVCO-BP", "weight": "DEVCO-SC"}

    # Firmware baseline versions
    fw_pre = {"glucose": "v3.8", "bp": "v2.6", "weight": "v1.4"}
    fw_roll = {"glucose": "v3.9", "bp": "v2.7", "weight": "v1.5"}

    rows = []
    reading_seq = 1

    # Daily volume logic: baseline 2.2k-2.8k valid readings weekdays; weekends -30-40%
    # We'll generate additional invalid readings during event windows.
    for d in DAYS:
        day = pd.Timestamp(d).tz_localize(None).normalize()
        is_weekend = day.weekday() >= 5
        in_rollout = day >= EVENT_ROLLOUT.normalize()
        in_config_push = day >= EVENT_CONFIG_PUSH.normalize()
        in_hotfix = day >= EVENT_HOTFIX.normalize()

        # Base total readings target per day (including invalids), scaled for weekend
        base_valid = np.random.randint(2200, 2800)
        if is_weekend:
            base_valid = int(base_valid * np.random.uniform(0.60, 0.70))  # -30-40%

        # Create total readings slightly above valid baseline to allow invalids and bp diastolic nulls
        total_readings = int(base_valid * np.random.uniform(1.05, 1.15))

        # Device type assignments
        device_types = _choose(DEVICE_TYPES, DEVICE_PROBS, total_readings)

        # Patient sampling with region coherence
        chosen_idx = np.random.choice(len(patient_ids), size=total_readings, replace=True)
        pid = patient_ids[chosen_idx]
        pregion = regions[chosen_idx]
        pcond = conditions[chosen_idx]

        # Vendor/firmware based on device type and date
        is_glucose = device_types == "glucose"
        is_bp = device_types == "bp"
        is_weight = device_types == "weight"
        vendor = np.empty(total_readings, dtype=object)
        vendor[is_glucose] = vendors["glucose"]
        vendor[is_bp] = vendors["bp"]
        vendor[is_weight] = vendors["weight"]
        firmware = np.empty(total_readings, dtype=object)

        # Pre-populate firmware based on rollout timing, only Central/West targeted for GM/BP
        is_glucose = device_types == "glucose"
        is_bp = device_types == "bp"
        is_weight = device_types == "weight"
        in_central_west = np.isin(pregion, ["Central", "West"])

        # Initialize firmware with pre versions, then selectively override
        firmware[:] = None
        firmware[is_weight] = fw_pre["weight"] if not in_rollout else fw_roll["weight"]
        # For glucose and bp, use np.where on the masked subset to avoid shape mismatch
        if is_glucose.any():
            fw_glu = np.where(
                (in_rollout & in_central_west)[is_glucose],
                fw_roll["glucose"],
                fw_pre["glucose"]
            )
            firmware[is_glucose] = fw_glu
        if is_bp.any():
            fw_bp = np.where(
                (in_rollout & in_central_west)[is_bp],
                fw_roll["bp"],
                fw_pre["bp"]
            )
            firmware[is_bp] = fw_bp

        # Build reading times with business hours
        hour_probs = build_business_hours_probs(is_weekend)
        hours = np.random.choice(HOURS_RANGE, size=total_readings, p=hour_probs)
        minutes = np.random.randint(0, 60, size=total_readings)
        reading_time = (
            pd.to_datetime(day)
            + pd.to_timedelta(hours, unit="h")
            + pd.to_timedelta(minutes, unit="m")
        )
        # Ensure milliseconds precision; DatetimeIndex has no .dt, so use .floor directly
        reading_time = pd.to_datetime(reading_time, errors="coerce")
        reading_time = reading_time.floor("ms")

        # Values and flags
        glucose_vals = np.empty(total_readings)
        bp_sys = np.empty(total_readings)
        bp_dia = np.empty(total_readings)
        weight_vals = np.empty(total_readings)

        glucose_vals[:] = np.nan
        bp_sys[:] = np.nan
        bp_dia[:] = np.nan
        weight_vals[:] = np.nan

        # Glucose heavy-tailed distribution (mg/dL)
        g_mask = is_glucose
        if g_mask.any():
            # fasting median 110-125; lognormal-ish with tails
            g_base = np.random.lognormal(mean=np.log(120), sigma=0.25, size=g_mask.sum())
            # occasional outliers
            out_mask = np.random.rand(g_mask.sum()) < 0.02
            g_base[out_mask] *= np.random.uniform(2.0, 3.0, size=out_mask.sum())
            glucose_vals[g_mask] = np.clip(g_base, 60, 380)

        # BP systolic and diastolic
        bp_mask = is_bp
        if bp_mask.any():
            sys_base = np.random.normal(loc=136, scale=12, size=bp_mask.sum())
            dia_base = np.random.normal(loc=83, scale=8, size=bp_mask.sum())
            # occasional outliers
            sys_base += np.random.normal(0, 6, size=bp_mask.sum())
            dia_base += np.random.normal(0, 4, size=bp_mask.sum())
            bp_sys[bp_mask] = np.clip(sys_base, 90, 220)
            bp_dia[bp_mask] = np.clip(dia_base, 50, 120)

        # Weight log-normal
        w_mask = is_weight
        if w_mask.any():
            w_base = np.random.lognormal(mean=np.log(83), sigma=0.12, size=w_mask.sum())
            weight_vals[w_mask] = np.clip(w_base, 45, 180)

        # Valid flag baseline true; adjust for event
        valid_flag = np.ones(total_readings, dtype=bool)
        error_code = np.empty(total_readings, dtype=object)
        error_code[:] = None

        # Drop valid glucose readings in Central/West for DEVCO-GM v3.9 during 10-02..10-11 strongly, then partial recovery until 10-20
        in_event_window = (day >= EVENT_ROLLOUT.normalize()) & (day < EVENT_CONFIG_PUSH.normalize())
        in_partial_recovery = (day >= EVENT_CONFIG_PUSH.normalize()) & (day < EVENT_HOTFIX.normalize())
        in_post_hotfix = day >= EVENT_HOTFIX.normalize()

        # Glucose validity drop
        gm_event_mask = g_mask & in_central_west & (firmware == fw_roll["glucose"]) & (vendor == "DEVCO-GM")
        if in_event_window and gm_event_mask.any():
            drop = 0.28  # ~28%
            invalidate = np.random.rand(gm_event_mask.sum()) < drop
            valid_flag[gm_event_mask] = ~invalidate
            inv_idx = np.where(gm_event_mask)[0]
            error_code[inv_idx[invalidate]] = "BT-GM-3921"
        elif in_partial_recovery and gm_event_mask.any():
            drop = 0.12  # restored 85-90% => 10-15% residual invalid
            invalidate = np.random.rand(gm_event_mask.sum()) < drop
            valid_flag[gm_event_mask] = ~invalidate
            inv_idx = np.where(gm_event_mask)[0]
            error_code[inv_idx[invalidate]] = "BT-GM-3921"
        elif in_post_hotfix and gm_event_mask.any():
            # Weekend residual gaps until 10-21 addressed; after hotfix back to baseline
            valid_flag[gm_event_mask] = True

        # BP diastolic missing rate increase 15-20% for DEVCO-BP v2.7 Central/West
        bp_event_mask = bp_mask & in_central_west & (firmware == fw_roll["bp"]) & (vendor == "DEVCO-BP")
        if in_event_window and bp_event_mask.any():
            miss_rate = np.random.uniform(0.15, 0.20)
            miss = np.random.rand(bp_event_mask.sum()) < miss_rate
            bp_idx = np.where(bp_event_mask)[0]
            miss_idx = bp_idx[miss]
            bp_dia[miss_idx] = np.nan
            error_code[miss_idx] = "BT-BP-2710"
        elif in_partial_recovery and bp_event_mask.any():
            miss_rate = np.random.uniform(0.06, 0.10)  # residuals 6-10%
            miss = np.random.rand(bp_event_mask.sum()) < miss_rate
            bp_idx = np.where(bp_event_mask)[0]
            miss_idx = bp_idx[miss]
            bp_dia[miss_idx] = np.nan
            error_code[miss_idx] = "BT-BP-2710"
        elif in_post_hotfix and bp_event_mask.any():
            # back to baseline null rate
            pass

        # Baseline rare errors
        baseline_err_mask = (~in_event_window & ~in_partial_recovery) & (np.random.rand(total_readings) < 0.001)
        if baseline_err_mask.any():
            count = int(baseline_err_mask.sum())
            error_code_choices = np.random.choice(["NONE", "BT-GM-3901", "BT-BP-2701"], size=count, p=[0.7, 0.15, 0.15])
            # Assign choices to the positions where baseline_err_mask is True
            idx = np.where(baseline_err_mask)[0]
            error_code[idx] = error_code_choices

        # For non-glucose invalids baseline very small
        non_glucose_mask = ~g_mask
        valid_flag[non_glucose_mask] = valid_flag[non_glucose_mask] & (np.random.rand(non_glucose_mask.sum()) > 0.005)

        # Build frame
        rd_ids = np.char.mod("RD-%06d", np.arange(reading_seq, reading_seq + total_readings))
        reading_seq += total_readings

        df_day = pd.DataFrame({
            "reading_id": rd_ids,
            "patient_id": pid,
            "region": pregion,
            "device_type": device_types,
            "vendor": vendor,
            "firmware_version": firmware,
            "reading_time": reading_time,
            "glucose_mg_dl": glucose_vals,
            "bp_systolic_mm_hg": bp_sys,
            "bp_diastolic_mm_hg": bp_dia,
            "weight_kg": weight_vals,
            "valid_flag": valid_flag,
            "error_code": error_code,
        })
        rows.append(df_day)

        if day.day in (1, 10, 20, 28):
            print(f"  {day.date()} - device readings rows so far: {sum(len(r) for r in rows):,}")

    df = pd.concat(rows, ignore_index=True)

    # Normalize datetime columns to ms
    df["reading_time"] = pd.to_datetime(df["reading_time"], errors="coerce").dt.floor("ms")

    # Ensure schema types and small nulls where allowed
    # Limit error_code to very small nulls if any
    null_err_mask = pd.isna(df["error_code"]) & (np.random.rand(len(df)) < 0.001)
    df.loc[null_err_mask, "error_code"] = None

    print(f"device_readings total rows: {len(df):,}")
    return df

device_readings = generate_device_readings(patient_master, 312450)
save_to_table(device_readings, "device_readings", num_files=10)

# COMMAND ----------
# Databricks notebook source
# MAGIC %md
# MAGIC ## Generate Encounter Notes

# COMMAND ----------
# ===============================
# === 3) ENCOUNTER NOTES =========
# ===============================

def generate_encounter_notes(patient_master: pd.DataFrame, target_rows: int = 128640) -> pd.DataFrame:
    print(f"Generating encounter_notes (~{target_rows:,})...")
    pm = patient_master[patient_master["active_flag"]].copy().reset_index(drop=True)
    patient_ids = pm["patient_id"].values
    regions = pm["region"].values
    conditions = pm["condition"].values

    # We will sample notes per day with weekday-heavy distribution
    rows = []
    note_seq = 1

    for d in DAYS:
        day = pd.Timestamp(d).tz_localize(None).normalize()
        is_weekend = day.weekday() >= 5
        in_rollout_window = (day >= EVENT_ROLLOUT.normalize()) & (day < EVENT_HOTFIX.normalize())
        # daily volume baseline proportional to active patients (~500-700 weekday, ~280-380 weekend)
        base = np.random.randint(520, 680)
        if is_weekend:
            base = int(base * np.random.uniform(0.55, 0.70))

        # Sample patients
        chosen_idx = np.random.choice(len(patient_ids), size=base, replace=True)
        pid = patient_ids[chosen_idx]
        pregion = regions[chosen_idx]
        pcond = conditions[chosen_idx]

        # Build note_time
        hour_probs = build_business_hours_probs(is_weekend)
        hours = np.random.choice(HOURS_RANGE, size=base, p=hour_probs)
        minutes = np.random.randint(0, 60, size=base)
        note_time = (
            pd.to_datetime(day)
            + pd.to_timedelta(hours, unit="h")
            + pd.to_timedelta(minutes, unit="m")
        )
        note_time = pd.to_datetime(note_time, errors="coerce")
        note_time = note_time.floor("ms")

        # Diet non-adherence flags: baseline 18-22%; event uptick 27-31%
        base_diet_rate = np.random.uniform(0.18, 0.22)
        event_diet_rate = np.random.uniform(0.27, 0.31)
        diet_rate = np.where(in_rollout_window, event_diet_rate, base_diet_rate)
        diet_flag = np.random.rand(base) < diet_rate

        # Medication adherence flags: event increases, focused on diabetics
        base_med_rate = np.random.uniform(0.10, 0.14)
        event_med_rate = np.random.uniform(0.16, 0.22)
        med_flag = np.random.rand(base) < base_med_rate
        if in_rollout_window:
            diabetes_mask = pcond == "diabetes"
            med_flag[diabetes_mask] = np.random.rand(diabetes_mask.sum()) < event_med_rate

        # Note text pointer placeholders
        note_text = np.array([f"ptr://note/{note_seq + i}" for i in range(base)], dtype=object)
        note_ids = np.char.mod("NT-%06d", np.arange(note_seq, note_seq + base))
        note_seq += base

        df_day = pd.DataFrame({
            "note_id": note_ids,
            "patient_id": pid,
            "region": pregion,
            "note_time": note_time,
            "note_text": note_text,
            "diet_non_adherence_flag": diet_flag,
            "med_adherence_flag": med_flag,
        })
        rows.append(df_day)

        if day.day in (1, 10, 20, 28):
            print(f"  {day.date()} - encounter notes rows so far: {sum(len(r) for r in rows):,}")

    df = pd.concat(rows, ignore_index=True)
    df["note_time"] = pd.to_datetime(df["note_time"], errors="coerce").dt.floor("ms")
    print(f"encounter_notes total rows: {len(df):,}")
    return df

encounter_notes = generate_encounter_notes(patient_master, 128640)
save_to_table(encounter_notes, "encounter_notes", num_files=6)

# COMMAND ----------
# Databricks notebook source
# MAGIC %md
# MAGIC ## Generate Medication Lists

# COMMAND ----------
# ===============================
# === 4) MEDICATION LISTS ========
# ===============================

def generate_medication_lists(patient_master: pd.DataFrame, target_rows: int = 15420) -> pd.DataFrame:
    print(f"Generating medication_lists (~{target_rows:,})...")
    pm = patient_master[patient_master["active_flag"]].copy().reset_index(drop=True)
    patient_ids = pm["patient_id"].values
    regions = pm["region"].values
    conditions = pm["condition"].values

    MED_CLASSES = ["Metformin", "Insulin", "GLP-1", "ACE_inhibitor", "ARB", "Beta_blocker", "Diuretic"]
    MED_PROBS = np.array([0.24, 0.18, 0.14, 0.16, 0.10, 0.09, 0.09])

    CHANGE_TYPES = ["new", "stop", "dose_change", "no_change"]
    CHANGE_PROBS_BASE = np.array([0.22, 0.10, 0.18, 0.50])

    rows = []
    list_seq = 1

    for d in DAYS:
        day = pd.Timestamp(d).tz_localize(None).normalize()
        is_weekend = day.weekday() >= 5
        in_rollout_window = (day >= EVENT_ROLLOUT.normalize()) & (day < EVENT_HOTFIX.normalize())

        # Weekly cadence typical; sample more during event
        base_count = np.random.randint(280, 360)  # per day snapshots across cohort
        if is_weekend:
            base_count = int(base_count * np.random.uniform(0.55, 0.75))
        if in_rollout_window:
            base_count = int(base_count * np.random.uniform(1.10, 1.25))

        chosen_idx = np.random.choice(len(patient_ids), size=base_count, replace=True)
        pid = patient_ids[chosen_idx]
        pregion = regions[chosen_idx]
        pcond = conditions[chosen_idx]

        med_class = _choose(MED_CLASSES, MED_PROBS, base_count)
        change_type = _choose(CHANGE_TYPES, CHANGE_PROBS_BASE, base_count)

        # Event increases dose_change/new for Metformin and ACE inhibitors
        if in_rollout_window:
            target_mask = np.isin(med_class, ["Metformin", "ACE_inhibitor"]) & (pcond == "diabetes")
            bump_mask = target_mask & (np.random.rand(base_count) < 0.35)
            change_type[bump_mask] = _choose(["dose_change", "new"], [0.6, 0.4], bump_mask.sum())

        # Snapshot times
        hour_probs = build_business_hours_probs(is_weekend)
        hours = np.random.choice(HOURS_RANGE, size=base_count, p=hour_probs)
        minutes = np.random.randint(0, 60, size=base_count)
        snap_time = (
            pd.to_datetime(day)
            + pd.to_timedelta(hours, unit="h")
            + pd.to_timedelta(minutes, unit="m")
        )
        snap_time = pd.to_datetime(snap_time, errors="coerce")
        snap_time = snap_time.floor("ms")

        list_ids = np.char.mod("ML-%06d", np.arange(list_seq, list_seq + base_count))
        list_seq += base_count

        df_day = pd.DataFrame({
            "list_id": list_ids,
            "patient_id": pid,
            "region": pregion,
            "snapshot_time": snap_time,
            "med_class": med_class,
            "change_type": change_type,
        })
        rows.append(df_day)

        if day.day in (1, 10, 20, 28):
            print(f"  {day.date()} - medication lists rows so far: {sum(len(r) for r in rows):,}")

    df = pd.concat(rows, ignore_index=True)
    df["snapshot_time"] = pd.to_datetime(df["snapshot_time"], errors="coerce").dt.floor("ms")
    print(f"medication_lists total rows: {len(df):,}")
    return df

medication_lists = generate_medication_lists(patient_master, 15420)
save_to_table(medication_lists, "medication_lists", num_files=3)

# COMMAND ----------
# Databricks notebook source
# MAGIC %md
# MAGIC ## Generate Device Change Log

# COMMAND ----------
# ===============================
# === 5) DEVICE CHANGE LOG =======
# ===============================

def generate_device_change_log() -> pd.DataFrame:
    print("Generating device_change_log (~weekly changes + key events)...")
    rows = []
    change_seq = 1

    # Routine weekly changes
    dates = pd.date_range(RANGE_START - pd.Timedelta(days=30), RANGE_END, freq="7D")
    for d in dates:
        d = pd.Timestamp(d).tz_localize(None).normalize()
        # random vendor/device
        vendor = np.random.choice(["DEVCO-GM", "DEVCO-BP", "DEVCO-SC"]) 
        device_type = {"DEVCO-GM": "glucose", "DEVCO-BP": "bp", "DEVCO-SC": "weight"}[vendor]
        version = np.random.choice(["v3.7", "v3.8", "v3.9", "v2.6", "v2.7", "v1.4", "v1.5"]) 
        scope = np.random.choice(["East", "Central", "West", "East,Central", "Central,West", "East,West", "East,Central,West"], p=[0.20,0.14,0.14,0.16,0.18,0.09,0.09])
        ctype = np.random.choice(["rollout", "config_push", "hotfix"], p=[0.35, 0.35, 0.30])
        err = None
        if vendor == "DEVCO-GM":
            err = f"BT-GM-{np.random.randint(3900, 3999)}"
        elif vendor == "DEVCO-BP":
            err = f"BT-BP-{np.random.randint(2700, 2799)}"
        else:
            err = "NONE"
        notes = f"Routine {ctype} for {vendor} {device_type} {version} in {scope}."
        change_time = (d + pd.Timedelta(hours=np.random.randint(6, 18))).floor("ms")

        rows.append({
            "change_id": f"CH-{change_seq:06d}",
            "change_date": change_time,
            "vendor": vendor,
            "device_type": device_type,
            "version": version,
            "regions_scope": scope,
            "change_type": ctype,
            "error_codes": err,
            "notes": notes,
        })
        change_seq += 1

    # Key events
    rows.append({
        "change_id": f"CH-{change_seq:06d}",
        "change_date": (EVENT_ROLLOUT.normalize() + pd.Timedelta(hours=9)).floor("ms"),
        "vendor": "DEVCO-GM",
        "device_type": "glucose",
        "version": "v3.9",
        "regions_scope": "Central,West",
        "change_type": "rollout",
        "error_codes": "BT-GM-3921",
        "notes": "Bluetooth stack update rollout for glucometers v3.9 across Central & West.",
    }); change_seq += 1

    rows.append({
        "change_id": f"CH-{change_seq:06d}",
        "change_date": (EVENT_ROLLOUT.normalize() + pd.Timedelta(hours=9)).floor("ms"),
        "vendor": "DEVCO-BP",
        "device_type": "bp",
        "version": "v2.7",
        "regions_scope": "Central,West",
        "change_type": "rollout",
        "error_codes": "BT-BP-2710",
        "notes": "Bluetooth update rollout for BP cuffs v2.7 across Central & West.",
    }); change_seq += 1

    rows.append({
        "change_id": f"CH-{change_seq:06d}",
        "change_date": (EVENT_CONFIG_PUSH.normalize() + pd.Timedelta(hours=10)).floor("ms"),
        "vendor": "DEVCO-GM",
        "device_type": "glucose",
        "version": "v3.9",
        "regions_scope": "Central,West",
        "change_type": "config_push",
        "error_codes": "BT-GM-3921",
        "notes": "Configuration push to reduce ingestion errors for glucometers.",
    }); change_seq += 1

    rows.append({
        "change_id": f"CH-{change_seq:06d}",
        "change_date": (EVENT_CONFIG_PUSH.normalize() + pd.Timedelta(hours=10)).floor("ms"),
        "vendor": "DEVCO-BP",
        "device_type": "bp",
        "version": "v2.7",
        "regions_scope": "Central,West",
        "change_type": "config_push",
        "error_codes": "BT-BP-2710",
        "notes": "Configuration push to mitigate diastolic missing fields.",
    }); change_seq += 1

    rows.append({
        "change_id": f"CH-{change_seq:06d}",
        "change_date": (EVENT_HOTFIX.normalize() + pd.Timedelta(hours=11)).floor("ms"),
        "vendor": "DEVCO-GM",
        "device_type": "glucose",
        "version": "v3.9",
        "regions_scope": "Central,West",
        "change_type": "hotfix",
        "error_codes": "BT-GM-3921",
        "notes": "Vendor hotfix restores ingestion to baseline; weekend residuals resolved.",
    }); change_seq += 1

    rows.append({
        "change_id": f"CH-{change_seq:06d}",
        "change_date": (EVENT_HOTFIX.normalize() + pd.Timedelta(hours=11)).floor("ms"),
        "vendor": "DEVCO-BP",
        "device_type": "bp",
        "version": "v2.7",
        "regions_scope": "Central,West",
        "change_type": "hotfix",
        "error_codes": "BT-BP-2710",
        "notes": "Vendor hotfix restores diastolic fields to baseline.",
    }); change_seq += 1

    df = pd.DataFrame(rows).sort_values("change_date", kind="stable").reset_index(drop=True)
    df["change_date"] = pd.to_datetime(df["change_date"], errors="coerce").dt.floor("ms")
    print(f"device_change_log total rows: {len(df):,}")
    return df

device_change_log = generate_device_change_log()
save_to_table(device_change_log, "device_change_log", num_files=1)

# COMMAND ----------
# Databricks notebook source
# MAGIC %md
# MAGIC ## Generate Care Actions

# COMMAND ----------
# ===============================
# === 6) CARE ACTIONS ============
# ===============================

def generate_care_actions(patient_master: pd.DataFrame, target_rows: int = 98560) -> pd.DataFrame:
    print(f"Generating care_actions (~{target_rows:,})...")
    pm = patient_master[patient_master["active_flag"]].copy().reset_index(drop=True)
    patient_ids = pm["patient_id"].values
    regions = pm["region"].values
    conditions = pm["condition"].values
    risk_tiers = pm["risk_tier"].values

    ACTION_TYPES = ["nurse_outreach", "medication_review", "nutrition_check_in", "device_troubleshoot"]
    ACTION_PROBS_BASE = np.array([0.38, 0.26, 0.24, 0.12])

    rows = []
    action_seq = 1

    for d in DAYS:
        day = pd.Timestamp(d).tz_localize(None).normalize()
        is_weekend = day.weekday() >= 5
        in_rollout_window = (day >= EVENT_ROLLOUT.normalize()) & (day < EVENT_HOTFIX.normalize())

        # Daily volume baseline with weekday peaks
        base = np.random.randint(900, 1200)
        if is_weekend:
            base = int(base * np.random.uniform(0.58, 0.68))
        if in_rollout_window:
            base = int(base * np.random.uniform(1.22, 1.28))  # workload increase ~22-28%

        chosen_idx = np.random.choice(len(patient_ids), size=base, replace=True)
        pid = patient_ids[chosen_idx]
        pregion = regions[chosen_idx]
        pcond = conditions[chosen_idx]
        prisk = risk_tiers[chosen_idx]

        # Action mix pivot toward nurse outreach and medication review during event
        action_probs = ACTION_PROBS_BASE.copy()
        if in_rollout_window:
            action_probs = np.array([0.44, 0.30, 0.18, 0.08])
        action_probs = action_probs / action_probs.sum()
        action_type = _choose(ACTION_TYPES, action_probs, base)

        # Executed flag higher during event for priority actions
        executed_flag = np.random.rand(base) < 0.86
        if in_rollout_window:
            highrisk_mask = prisk == "high"
            # bump executed for high-risk diabetics
            bump = (np.random.rand(base) < 0.06) & highrisk_mask & (pcond == "diabetes")
            executed_flag[bump] = True

        # Costs by action type
        cost = np.random.lognormal(mean=np.log(70), sigma=0.35, size=base)
        outreach_mask = action_type == "nurse_outreach"
        medrev_mask = action_type == "medication_review"
        cost[outreach_mask] *= np.random.uniform(0.80, 0.95)
        cost[medrev_mask] *= np.random.uniform(1.10, 1.35)

        # Event surge costs
        if in_rollout_window:
            surge_mask = outreach_mask | medrev_mask
            cost[surge_mask] *= np.random.uniform(1.10, 1.20)

        # Action times
        hour_probs = build_business_hours_probs(is_weekend)
        hours = np.random.choice(HOURS_RANGE, size=base, p=hour_probs)
        minutes = np.random.randint(0, 60, size=base)
        action_time = (
            pd.to_datetime(day)
            + pd.to_timedelta(hours, unit="h")
            + pd.to_timedelta(minutes, unit="m")
        )
        action_time = pd.to_datetime(action_time, errors="coerce")
        action_time = action_time.floor("ms")

        action_ids = np.char.mod("AC-%06d", np.arange(action_seq, action_seq + base))
        action_seq += base

        df_day = pd.DataFrame({
            "action_id": action_ids,
            "patient_id": pid,
            "region": pregion,
            "action_time": action_time,
            "action_type": action_type,
            "condition": pcond,
            "executed_flag": executed_flag,
            "estimated_cost_usd": np.round(cost, 2),
        })
        rows.append(df_day)

        if day.day in (1, 10, 20, 28):
            print(f"  {day.date()} - care actions rows so far: {sum(len(r) for r in rows):,}")

    df = pd.concat(rows, ignore_index=True)
    df["action_time"] = pd.to_datetime(df["action_time"], errors="coerce").dt.floor("ms")
    print(f"care_actions total rows: {len(df):,}")
    return df

care_actions = generate_care_actions(patient_master, 98560)
save_to_table(care_actions, "care_actions", num_files=6)

# COMMAND ----------
# Databricks notebook source
# MAGIC %md
# MAGIC ## QA Summary

# COMMAND ----------
# ===============================
# === QA SUMMARY ================
# ===============================
print("\nQA Summary: Event signals and seasonality checks")
# 1) Device readings: glucose valid drop in Central/West during 10-02..10-11
dr = device_readings.copy()
dr["date"] = pd.to_datetime(dr["reading_time"], errors="coerce").dt.tz_localize(None).dt.normalize().dt.floor("ms")
pre = dr[(dr["date"] < EVENT_ROLLOUT) & (dr["device_type"] == "glucose") & (dr["region"].isin(["Central","West"]))]
during = dr[(dr["date"] >= EVENT_ROLLOUT) & (dr["date"] < EVENT_CONFIG_PUSH) & (dr["device_type"] == "glucose") & (dr["region"].isin(["Central","West"]))]
post = dr[(dr["date"] >= EVENT_CONFIG_PUSH) & (dr["date"] < EVENT_HOTFIX) & (dr["device_type"] == "glucose") & (dr["region"].isin(["Central","West"]))]
pre_valid_rate = pre["valid_flag"].mean() if len(pre) else np.nan
during_valid_rate = during["valid_flag"].mean() if len(during) else np.nan
post_valid_rate = post["valid_flag"].mean() if len(post) else np.nan
print(f"  Glucose valid_rate Central/West pre: {pre_valid_rate:.3f} | during: {during_valid_rate:.3f} | partial_recovery: {post_valid_rate:.3f}")

# 2) BP diastolic missing rate spike
bp = dr[dr["device_type"] == "bp"].copy()
bp_pre = bp[bp["date"] < EVENT_ROLLOUT]
bp_during = bp[(bp["date"] >= EVENT_ROLLOUT) & (bp["date"] < EVENT_CONFIG_PUSH)]
miss_pre = bp_pre["bp_diastolic_mm_hg"].isna().mean()
miss_during = bp_during["bp_diastolic_mm_hg"].isna().mean()
print(f"  BP diastolic missing rate pre: {miss_pre:.3f} | during: {miss_during:.3f}")

# 3) Encounter notes diet non-adherence uptick
en = encounter_notes.copy()
en["date"] = pd.to_datetime(en["note_time"], errors="coerce").dt.tz_localize(None).dt.normalize().dt.floor("ms")
en_pre = en[en["date"] < EVENT_ROLLOUT]
en_during = en[(en["date"] >= EVENT_ROLLOUT) & (en["date"] < EVENT_HOTFIX)]
print(f"  Diet non-adherence pre: {en_pre['diet_non_adherence_flag'].mean():.3f} | during: {en_during['diet_non_adherence_flag'].mean():.3f}")

# 4) Care actions surge
ca = care_actions.copy()
ca["date"] = pd.to_datetime(ca["action_time"], errors="coerce").dt.tz_localize(None).dt.normalize().dt.floor("ms")
ca_pre = ca[ca["date"] < EVENT_ROLLOUT]
ca_during = ca[(ca["date"] >= EVENT_ROLLOUT) & (ca["date"] < EVENT_HOTFIX)]
print(f"  Care actions executed pre: {ca_pre['executed_flag'].mean():.3f} | during: {ca_during['executed_flag'].mean():.3f}")

print("\nGeneration complete - All timestamps are naive, floored to ms.")
