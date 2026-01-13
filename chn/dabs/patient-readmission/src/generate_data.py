# SummitCare Health Network - ER Weekend Surges (RAW generation)
# Generates 5 RAW datasources according to demo_story.json
# - emr_er_visits
# - hr_shifts_and_sickleave
# - patient_flow_metrics
# - patient_satisfaction_surveys
# - readmission_risk_feed
#
# Rules:
# - Reproducible seeds
# - Vectorized, performant generation
# - Story-aware: Sep-2025 weekend surges starting 2025-09-05 with peaks 09-13..14 and 09-20..21
# - Exact schemas per story, no derived fields beyond what RAW defines
# - Timestamps are tz-naive; save_to_parquet handles precision

from utils import save_to_parquet
import numpy as np
import pandas as pd
import random
from faker import Faker

# Set environment variables for Databricks Volumes
import os
os.environ.setdefault('CATALOG', 'chn_etl_demo_catalog')
os.environ.setdefault('SCHEMA', 'patient_readmission_dev')
os.environ.setdefault('VOLUME', 'raw_data')



np.random.seed(42)
random.seed(42)
fake = Faker()
Faker.seed(42)

# Global constants
RANGE_START = pd.Timestamp('2025-08-15')
RANGE_END = pd.Timestamp('2025-09-30')
EVENT_START = pd.Timestamp('2025-09-05')  # first surge weekend begins Fri
PEAK_WKND1_START = pd.Timestamp('2025-09-13')
PEAK_WKND1_END = pd.Timestamp('2025-09-14')
PEAK_WKND2_START = pd.Timestamp('2025-09-20')
PEAK_WKND2_END = pd.Timestamp('2025-09-21')
ALL_DAYS = pd.date_range(RANGE_START, RANGE_END, freq='D')
ALL_HOURS = pd.date_range(RANGE_START, RANGE_END + pd.Timedelta(days=1) - pd.Timedelta(hours=1), freq='h')

SITES = ['Lakeview Central', 'Lakeview East', 'North Ridge', 'South Point', 'Pine Valley', 'Riverbend']
SITE_TYPES = {
    'Lakeview Central': 'urban',
    'Lakeview East': 'urban',
    'North Ridge': 'suburban',
    'South Point': 'suburban',
    'Pine Valley': 'rural',
    'Riverbend': 'rural',
}
SITE_BASE_RATE = {
    'urban': 1.35,
    'suburban': 1.00,
    'rural': 0.70,
}

# Helper: weekend flag
def is_weekend(ts: pd.Timestamp) -> bool:
    ts = pd.Timestamp(ts)
    return ts.weekday() >= 5

# Helper: normalized choice
def np_choice(values, probs, size):
    p = np.array(probs, dtype=float)
    p = p / p.sum()
    return np.random.choice(values, size=int(size), p=p)

# ------------------------------
# 1) EMR ER VISITS (primary fact)
# ------------------------------
# Target rows ~312,450

def generate_emr_er_visits() -> pd.DataFrame:
    print('Generating emr_er_visits...')

    # Build hourly spine per site
    spine = (
        pd.MultiIndex.from_product([SITES, ALL_HOURS], names=['site', 'hour_ts'])
        .to_frame(index=False)
    )
    spine['unit'] = 'ER'

    # Hour-of-day arrival shape: evening peaks; rural earlier peak
    hours = np.arange(24)
    weekday_hour_weights = np.array([
        0.02, 0.02, 0.015, 0.015, 0.015, 0.02,  # 0-5
        0.03, 0.04, 0.045, 0.05, 0.055, 0.06,   # 6-11
        0.06, 0.065, 0.07, 0.075, 0.08, 0.085,  # 12-17
        0.09, 0.095, 0.085, 0.07, 0.05, 0.035   # 18-23 (evening peak)
    ])
    weekend_hour_weights = np.array([
        0.02, 0.02, 0.015, 0.015, 0.015, 0.02,
        0.03, 0.04, 0.05, 0.055, 0.06, 0.065,
        0.07, 0.075, 0.085, 0.095, 0.105, 0.11,  # stronger evening
        0.11, 0.10, 0.085, 0.06, 0.04, 0.03
    ])
    weekday_hour_weights = weekday_hour_weights / weekday_hour_weights.sum()
    weekend_hour_weights = weekend_hour_weights / weekend_hour_weights.sum()

    # Day-of-week multiplier baseline (Fri-Sun +10-15%)
    dow_mult = {0: 1.00, 1: 1.03, 2: 1.05, 3: 1.04, 4: 1.115, 5: 1.12, 6: 1.12}

    # Weekend surge uplift during Sep weekends
    def surge_multiplier(ts: pd.Timestamp) -> float:
        if ts < EVENT_START:
            return 1.0
        if is_weekend(ts):
            # heightened on peak weekends
            if PEAK_WKND1_START <= ts.normalize() <= PEAK_WKND1_END or PEAK_WKND2_START <= ts.normalize() <= PEAK_WKND2_END:
                return np.random.uniform(1.30, 1.35)
            # other Sep weekends
            return np.random.uniform(1.25, 1.30)
        return 1.0

    # Base arrivals per hour scaling to hit ~312k rows
    # 6 sites * 24 * 47 = 6,768 hours; to reach 312,450 -> mean ~46.2 arrivals/hour overall
    # We'll modulate by site type and hour weights
    base_overall_lambda = 46.2

    # Compute lambda per spine row
    site_type_arr = spine['site'].map(SITE_TYPES).values
    site_rate = np.array([SITE_BASE_RATE[t] for t in site_type_arr], dtype=float)
    is_wkend = spine['hour_ts'].dt.weekday.values >= 5
    hour = spine['hour_ts'].dt.hour.values
    hour_weight = np.where(is_wkend, weekend_hour_weights[hour], weekday_hour_weights[hour])
    day_weight = np.array([dow_mult[int(d)] for d in spine['hour_ts'].dt.weekday.values], dtype=float)
    surge = np.array([surge_multiplier(pd.Timestamp(ts)) for ts in spine['hour_ts'].values])

    lam = base_overall_lambda * site_rate * hour_weight * day_weight * surge
    lam = np.clip(lam, 2.0, None)

    arrivals = np.random.poisson(lam)
    spine['arrivals'] = arrivals

    total_visits = int(arrivals.sum())
    print(f'  Planned total visits: {total_visits:,}')

    # Expand to visits
    rows = total_visits
    # Repeat arrays
    repeat_idx = np.repeat(spine.index.values, arrivals)
    site_col = spine.loc[repeat_idx, 'site'].values
    unit_col = np.repeat('ER', rows)
    base_ts = spine.loc[repeat_idx, 'hour_ts'].values.astype('datetime64[ms]')
    # Random minute/second
    minute = np.random.randint(0, 60, size=rows)
    second = np.random.randint(0, 60, size=rows)
    arrival_time = base_ts + pd.to_timedelta(minute, unit='m') + pd.to_timedelta(second, unit='s')
    # efficient: derive hour directly from spine
    arrival_hour_int = pd.Series(spine.loc[repeat_idx, 'hour_ts'].dt.hour.values)

    # patient_id pool with heavy-tail revisit
    n_patients = max(50000, int(rows * 0.6))
    patient_ids = np.array([f'P-{i:06d}' for i in range(1, n_patients + 1)])
    # Zipf-like probabilities
    ranks = np.arange(1, n_patients + 1)
    probs = (1.0 / ranks**1.1)
    probs = probs / probs.sum()
    chosen_patients = np.random.choice(patient_ids, size=rows, p=probs)

    # Acuity distribution baseline vs weekend
    # baseline: 3:50%, 4:27%, 2:15%, 5:4%, 1:2%
    acuity_base_vals = np.array([1, 2, 3, 4, 5])
    acuity_base_probs = np.array([0.02, 0.15, 0.50, 0.27, 0.06])
    # Note: ensure sum to 1
    acuity_base_probs = acuity_base_probs / acuity_base_probs.sum()
    # weekend uplift to 3-4
    acuity_wknd_probs = np.array([0.015, 0.13, 0.53, 0.285, 0.04])
    acuity_wknd_probs = acuity_wknd_probs / acuity_wknd_probs.sum()
    is_weekend_arrival = pd.to_datetime(arrival_time).weekday >= 5
    acuity = np.where(is_weekend_arrival,
                      np.random.choice(acuity_base_vals, size=rows, p=acuity_wknd_probs),
                      np.random.choice(acuity_base_vals, size=rows, p=acuity_base_probs))

    # Diagnosis group baseline vs weekend (Respiratory/Injury up on weekends)
    dx_vals = np.array(['Respiratory', 'GI', 'Injury', 'Cardiac', 'Neuro', 'Other'])
    dx_probs_weekday = np.array([0.22, 0.17, 0.20, 0.11, 0.08, 0.22])
    dx_probs_weekend = np.array([0.30, 0.14, 0.24, 0.09, 0.07, 0.16])
    dx_probs_weekday = dx_probs_weekday / dx_probs_weekday.sum()
    dx_probs_weekend = dx_probs_weekend / dx_probs_weekend.sum()
    dx = np.where(is_weekend_arrival,
                  np.random.choice(dx_vals, size=rows, p=dx_probs_weekend),
                  np.random.choice(dx_vals, size=rows, p=dx_probs_weekday))

    # LWBS rate baseline ~3.0%, weekends +15% relative -> ~3.45%
    lwbs_rate = np.where(is_weekend_arrival, 0.0345, 0.0300)
    is_lwbs = np.random.rand(rows) < lwbs_rate

    # Discharge disposition
    disp_vals = np.array(['Discharged', 'Admitted', 'Transferred', 'LWBS'])
    disp_probs_base = np.array([0.78, 0.16, 0.06, 0.03])
    disp_probs_wknd = np.array([0.765, 0.165, 0.055, 0.0345])
    disp_probs_base = disp_probs_base / disp_probs_base.sum()
    disp_probs_wknd = disp_probs_wknd / disp_probs_wknd.sum()
    disp = np.where(is_weekend_arrival,
                    np.random.choice(disp_vals, size=rows, p=disp_probs_wknd),
                    np.random.choice(disp_vals, size=rows, p=disp_probs_base))
    # Enforce LWBS flag consistency
    disp = np.where(is_lwbs, 'LWBS', disp)

    # Provider start time (door-to-provider); null for LWBS and rare telemetry delay (<0.1%)
    base_dtp = np.random.lognormal(mean=np.log(30), sigma=0.35, size=rows)  # baseline ~30 min
    # weekends +18%
    base_dtp = base_dtp * np.where(is_weekend_arrival, 1.18, 1.0)
    # urban sites worse at peaks
    site_types_arr = np.vectorize(lambda s: SITE_TYPES[s])(site_col)
    urban_mask = (site_types_arr == 'urban')
    # additional uplift on peak weekends evenings
    # precompute hour-of-day once for masks
    hod = pd.to_datetime(arrival_time).hour

    # Build peak weekend mask on dates
    arr_date = pd.to_datetime(arrival_time).normalize()
    arr_date_ts = pd.to_datetime(arrival_time).normalize()
    peak_wknd_mask = (
        ((arr_date_ts >= PEAK_WKND1_START) & (arr_date_ts <= PEAK_WKND1_END)) |
        ((arr_date_ts >= PEAK_WKND2_START) & (arr_date_ts <= PEAK_WKND2_END))
    ) & (np.isin(pd.to_datetime(arrival_time).weekday, [5, 6]))
    evening_mask = (pd.to_datetime(arrival_time).hour >= 18) & (pd.to_datetime(arrival_time).hour <= 23)
    extra_uplift_mask = urban_mask & peak_wknd_mask & evening_mask
    if extra_uplift_mask.any():
        base_dtp[extra_uplift_mask] *= 1.08

    provider_start_time = (pd.to_datetime(arrival_time) + pd.to_timedelta(base_dtp, unit='m')).astype('datetime64[ms]')
    # Nullify for LWBS and 0.1% telemetry delay
    delay_null = (np.random.rand(rows) < 0.001)
    provider_start_time = provider_start_time.astype('datetime64[ms]').astype('datetime64[ms]')
    # Convert to numpy array to allow mutation
    provider_start_time = provider_start_time.values
    provider_start_time[is_lwbs | delay_null] = np.datetime64('NaT')

    # Discharge time: depends on acuity and disposition; null for LWBS
    base_stay = np.random.lognormal(mean=np.log(3.5), sigma=0.6, size=rows)  # hours
    # admitted longer
    admitted = (disp == 'Admitted')
    base_stay[admitted] *= np.random.uniform(2.5, 4.0, size=int(admitted.sum()))
    # acuity influence
    base_stay = base_stay * (1.0 + (np.array(acuity) - 3) * 0.15)
    discharge_time = (pd.to_datetime(arrival_time) + pd.to_timedelta(base_stay, unit='h')).astype('datetime64[ms]')
    # Convert to numpy array to allow mutation
    discharge_time = discharge_time.values if hasattr(discharge_time, 'values') else discharge_time
    discharge_time[is_lwbs] = np.datetime64('NaT')

    # Readmission 30d flag: higher among LWBS/long waits
    readm_prob = 0.11 + (np.clip(base_dtp / 60.0, 0, 3) * 0.01)
    readm_prob[is_lwbs] += 0.03
    readm_prob = np.clip(readm_prob, 0.02, 0.45)
    readmission_flag = np.random.rand(rows) < readm_prob

    # Cost per visit: log-normal; uplift with acuity and weekend overtime (12-20%)
    cost = np.random.lognormal(mean=np.log(480.0), sigma=0.55, size=rows)
    cost *= (1.0 + (np.array(acuity) - 3) * 0.12)
    cost *= np.where(is_weekend_arrival, np.random.uniform(1.12, 1.20, size=rows), 1.0)

    # visit_id
    visit_id = np.array([f'V-{pd.Timestamp(RANGE_START).strftime("%Y%m")}-{i:06d}' for i in range(1, rows + 1)])

    df = pd.DataFrame({
        'visit_id': visit_id,
        'patient_id': chosen_patients,
        'site': site_col,
        'unit': unit_col,
        'arrival_time': pd.to_datetime(arrival_time),
        'arrival_hour': arrival_hour_int.values.astype(int),
        'acuity_level': acuity.astype(int),
        'diagnosis_group': dx,
        'discharge_time': discharge_time,
        'discharge_disposition': disp,
        'provider_start_time': provider_start_time,
        'readmission_30d_flag': readmission_flag.astype(bool),
        'cost_per_visit_usd': np.round(cost, 2),
    })

    # Minimal QA
    print(f'  emr_er_visits rows: {len(df):,}')
    return df

# -------------------------------------
# 2) HR SHIFTS AND SICK LEAVE (schedules)
# -------------------------------------
# Target rows ~18,420

def generate_hr_shifts_and_sickleave() -> pd.DataFrame:
    print('Generating hr_shifts_and_sickleave...')
    roles = ['Nurse', 'Physician', 'Tech', 'Registration']

    # Shift templates
    nurse_shifts = [7, 19]  # 12h shifts
    physician_shifts = [0, 8, 16]  # staggered 8h
    tech_shifts = [6, 14, 22]  # variable 8h
    reg_shifts = [7, 15, 23]  # variable 8h

    rows = []
    seq = 1

    # Staffing levels by site type (per shift)
    staff_levels = {
        'urban': {'Nurse': (10, 14), 'Physician': (4, 5), 'Tech': (5, 7), 'Registration': (4, 5)},
        'suburban': {'Nurse': (7, 9), 'Physician': (3, 4), 'Tech': (3, 5), 'Registration': (3, 4)},
        'rural': {'Nurse': (4, 6), 'Physician': (2, 3), 'Tech': (2, 3), 'Registration': (2, 3)},
    }

    progress_interval = max(1, len(ALL_DAYS) // 10)

    for i, day in enumerate(ALL_DAYS):
        if (i + 1) % progress_interval == 0 or i == 0:
            progress = ((i + 1) / len(ALL_DAYS)) * 100
            print(f"  Days progress: {progress:.0f}% ({i + 1:,}/{len(ALL_DAYS):,})")

        wkend = is_weekend(day)
        in_event_wkend = wkend and (day >= EVENT_START)
        for site in SITES:
            stype = SITE_TYPES[site]
            # For each role, create shift instances with counts
            # Nurses
            for start_h in nurse_shifts:
                staff_count = np.random.randint(*staff_levels[stype]['Nurse'])
                # Elevated absenteeism on Sep weekends: ~2x baseline 3.2% -> ~6.5%
                sick_rate = 0.065 if in_event_wkend else 0.032
                sick_flags = np.random.rand(staff_count) < sick_rate
                # attendance is false when sick confirmed/reported
                status = np.where(sick_flags,
                                   np.random.choice(['Reported', 'Confirmed'], size=staff_count, p=[0.45, 0.55]),
                                   'None')
                attended = (status == 'None')
                # overtime uplift on weekends +22%
                base_ot = np.random.lognormal(mean=np.log(0.6), sigma=0.6, size=staff_count)
                ot = base_ot * (1.22 if in_event_wkend else 1.0)
                # coverage hours: 12h if attended, else 0
                scheduled_start = day + pd.Timedelta(hours=int(start_h))
                scheduled_end = scheduled_start + pd.Timedelta(hours=12)
                shift_cov = np.where(attended, 12.0, 0.0)
                for j in range(staff_count):
                    rows.append({
                        'shift_id': f'S-ER-{day.strftime("%Y%m%d")}-{start_h:02d}00-{site[:3].upper()}-{seq:03d}',
                        'staff_id': f'STAFF-{site[:3].upper()}-N-{seq:05d}',
                        'role': 'Nurse',
                        'site': site,
                        'unit': 'ER',
                        'scheduled_start': scheduled_start,
                        'scheduled_end': scheduled_end,
                        'actual_attended': bool(attended[j]),
                        'sick_leave_status': status[j],
                        'overtime_hours': float(np.round(ot[j], 2)),
                        'shift_coverage_hours': float(np.round(shift_cov[j], 2)),
                        'change_log_note': '',
                    })
                    seq += 1
            # Physicians
            for start_h in physician_shifts:
                staff_count = np.random.randint(*staff_levels[stype]['Physician'])
                sick_rate = 0.018 if in_event_wkend else 0.012
                sick_flags = np.random.rand(staff_count) < sick_rate
                status = np.where(sick_flags,
                                   np.random.choice(['Reported', 'Confirmed'], size=staff_count, p=[0.60, 0.40]),
                                   'None')
                attended = (status == 'None')
                base_ot = np.random.lognormal(mean=np.log(0.4), sigma=0.7, size=staff_count)
                ot = base_ot * (1.10 if in_event_wkend else 1.0)
                scheduled_start = day + pd.Timedelta(hours=int(start_h))
                scheduled_end = scheduled_start + pd.Timedelta(hours=8)
                shift_cov = np.where(attended, 8.0, 0.0)
                for j in range(staff_count):
                    rows.append({
                        'shift_id': f'S-ER-{day.strftime("%Y%m%d")}-{start_h:02d}00-{site[:3].upper()}-{seq:03d}',
                        'staff_id': f'STAFF-{site[:3].upper()}-P-{seq:05d}',
                        'role': 'Physician',
                        'site': site,
                        'unit': 'ER',
                        'scheduled_start': scheduled_start,
                        'scheduled_end': scheduled_end,
                        'actual_attended': bool(attended[j]),
                        'sick_leave_status': status[j],
                        'overtime_hours': float(np.round(ot[j], 2)),
                        'shift_coverage_hours': float(np.round(shift_cov[j], 2)),
                        'change_log_note': '',
                    })
                    seq += 1
            # Techs
            for start_h in tech_shifts:
                staff_count = np.random.randint(*staff_levels[stype]['Tech'])
                sick_rate = 0.03 if in_event_wkend else 0.02
                sick_flags = np.random.rand(staff_count) < sick_rate
                status = np.where(sick_flags,
                                   np.random.choice(['Reported', 'Confirmed'], size=staff_count, p=[0.55, 0.45]),
                                   'None')
                attended = (status == 'None')
                base_ot = np.random.lognormal(mean=np.log(0.5), sigma=0.7, size=staff_count)
                ot = base_ot * (1.15 if in_event_wkend else 1.0)
                scheduled_start = day + pd.Timedelta(hours=int(start_h))
                scheduled_end = scheduled_start + pd.Timedelta(hours=8)
                shift_cov = np.where(attended, 8.0, 0.0)
                for j in range(staff_count):
                    rows.append({
                        'shift_id': f'S-ER-{day.strftime("%Y%m%d")}-{start_h:02d}00-{site[:3].upper()}-{seq:03d}',
                        'staff_id': f'STAFF-{site[:3].upper()}-T-{seq:05d}',
                        'role': 'Tech',
                        'site': site,
                        'unit': 'ER',
                        'scheduled_start': scheduled_start,
                        'scheduled_end': scheduled_end,
                        'actual_attended': bool(attended[j]),
                        'sick_leave_status': status[j],
                        'overtime_hours': float(np.round(ot[j], 2)),
                        'shift_coverage_hours': float(np.round(shift_cov[j], 2)),
                        'change_log_note': '',
                    })
                    seq += 1
            # Registration
            for start_h in reg_shifts:
                staff_count = np.random.randint(*staff_levels[stype]['Registration'])
                sick_rate = 0.02 if in_event_wkend else 0.015
                sick_flags = np.random.rand(staff_count) < sick_rate
                status = np.where(sick_flags,
                                   np.random.choice(['Reported', 'Confirmed'], size=staff_count, p=[0.60, 0.40]),
                                   'None')
                attended = (status == 'None')
                base_ot = np.random.lognormal(mean=np.log(0.3), sigma=0.7, size=staff_count)
                ot = base_ot * (1.10 if in_event_wkend else 1.0)
                scheduled_start = day + pd.Timedelta(hours=int(start_h))
                scheduled_end = scheduled_start + pd.Timedelta(hours=8)
                shift_cov = np.where(attended, 8.0, 0.0)
                for j in range(staff_count):
                    rows.append({
                        'shift_id': f'S-ER-{day.strftime("%Y%m%d")}-{start_h:02d}00-{site[:3].upper()}-{seq:03d}',
                        'staff_id': f'STAFF-{site[:3].upper()}-R-{seq:05d}',
                        'role': 'Registration',
                        'site': site,
                        'unit': 'ER',
                        'scheduled_start': scheduled_start,
                        'scheduled_end': scheduled_end,
                        'actual_attended': bool(attended[j]),
                        'sick_leave_status': status[j],
                        'overtime_hours': float(np.round(ot[j], 2)),
                        'shift_coverage_hours': float(np.round(shift_cov[j], 2)),
                        'change_log_note': '',
                    })
                    seq += 1

    df = pd.DataFrame(rows)

    # Inject change_log_note entries on 09-12 and 09-19 for a subset
    for memo_date, note in [
        (pd.Timestamp('2025-09-12'), 'Change Log: 2025-09-12 float pool memo enacted.'),
        (pd.Timestamp('2025-09-19'), 'Change Log: 2025-09-19 on-call expansion implemented.'),
    ]:
        mask = (pd.to_datetime(df['scheduled_start']).dt.normalize() == memo_date)
        # randomly tag ~15% of rows that day per site
        idx = df[mask].sample(frac=0.15, random_state=42).index if mask.any() else []
        if len(idx) > 0:
            df.loc[idx, 'change_log_note'] = note

    print(f'  hr_shifts_and_sickleave rows: {len(df):,}')
    return df

# --------------------------------
# 3) PATIENT FLOW TELEMETRY (2-3m)
# --------------------------------
# Target rows ~226,450

def generate_patient_flow_metrics() -> pd.DataFrame:
    print('Generating patient_flow_metrics...')

    # Base grid: every 3 minutes across all sites
    base_grid = pd.date_range(RANGE_START, RANGE_END, freq='3min')
    # Add extra density for Fri-Sun 16:00-23:59 (every 2 minutes)
    extra_rows = []
    for d in ALL_DAYS:
        if is_weekend(d):
            start = d + pd.Timedelta(hours=16)
            end = d + pd.Timedelta(hours=23, minutes=59)
            extra_rows.append(pd.date_range(start, end, freq='2min'))
    extra_grid = pd.DatetimeIndex([]) if not extra_rows else extra_rows[0].append(extra_rows[1:])
    times = base_grid.union(extra_grid).unique()

    # Sample to approximate target row count by selecting subset of times per site
    # We will not use all times for all sites; we will randomly drop ~30% of times for rural sites
    rows = []
    hour_of_day = times.hour
    is_wkend = times.weekday >= 5

    for site in SITES:
        stype = SITE_TYPES[site]
        keep_prob = 1.0 if stype != 'rural' else 0.70
        keep_mask = (np.random.rand(len(times)) < keep_prob)
        t_site = times[keep_mask]
        n = len(t_site)
        if n == 0:
            continue
        hod = t_site.hour
        wkend = t_site.weekday >= 5
        # door_to_triage baseline ~12, weekends ~19
        dtt = np.random.lognormal(mean=np.log(12), sigma=0.35, size=n)
        dtt *= np.where(wkend, 19.0/12.0, 1.0)
        # door_to_provider baseline ~30; weekends +18%
        dtp = np.random.lognormal(mean=np.log(30), sigma=0.35, size=n)
        dtp *= np.where(wkend, 1.18, 1.0)
        # urban peak evenings a bit worse
        if stype == 'urban':
            evening = (hod >= 18) & (hod <= 23)
            if evening.any():
                dtp[evening] *= 1.06
        # triage level aligned with acuity skew
        triage = np.random.choice([1, 2, 3, 4, 5], size=n, p=[0.02, 0.15, 0.50, 0.27, 0.06])
        # queue length with bursts
        base_q = np.random.negative_binomial(n=3, p=0.45, size=n)
        base_q = base_q + (wkend.astype(int) * np.random.randint(1, 4, size=n))
        peak_mask = wkend & (hod >= 18) & (hod <= 23)
        base_q[peak_mask] = (base_q[peak_mask] * np.random.uniform(1.4, 1.6, size=int(peak_mask.sum()))).astype(int)
        # Telemetry status: delayed <0.1%
        status = np.where(np.random.rand(n) < 0.001, 'DELAYED', 'OK')

        df_site = pd.DataFrame({
            'flow_id': [f'F-{pd.Timestamp(RANGE_START).strftime("%Y%m")}-{t.strftime("%Y%m%d-%H%M")}-{site[:3].upper()}-{k:04d}' for k, t in enumerate(t_site, start=1)],
            'site': site,
            'unit': 'ER',
            'event_time': t_site,
            'hour_of_day': hod.astype(int),
            'door_to_triage_minutes': np.round(dtt, 2),
            'door_to_provider_minutes': np.round(dtp, 2),
            'triage_level': triage.astype(int),
            'queue_length': base_q.astype(int),
            'telemetry_status': status,
        })
        rows.append(df_site)

    df = pd.concat(rows, ignore_index=True)
    print(f'  patient_flow_metrics rows: {len(df):,}')
    return df

# --------------------------------------
# 4) PATIENT SATISFACTION SURVEYS (post)
# --------------------------------------
# Target rows ~15,480

def generate_patient_satisfaction_surveys(emr: pd.DataFrame) -> pd.DataFrame:
    print('Generating patient_satisfaction_surveys...')

    # choose subset of visits that are not LWBS and have discharge_time
    eligible = emr[(emr['discharge_disposition'] != 'LWBS') & emr['discharge_time'].notna()]
    target = 15480
    frac = min(1.0, target / max(1, len(eligible)))
    sample = eligible.sample(n=int(target), replace=False, random_state=42) if frac < 1.0 else eligible

    visit_id = sample['visit_id'].values
    site = sample['site'].values
    unit = np.repeat('ER', len(sample))
    arrival_date = pd.to_datetime(sample['arrival_time']).dt.normalize().values.astype('datetime64[ms]')
    # survey date = arrival + 0..3 days
    lag = np.random.randint(0, 4, size=len(sample))
    survey_date = (pd.to_datetime(arrival_date) + pd.to_timedelta(lag, unit='D')).astype('datetime64[ms]')

    # scores: baseline 4.1; weekend dips ~0.3
    wk_bool = pd.Series(pd.to_datetime(sample['arrival_time']).dt.weekday >= 5).values

    base_overall = np.random.normal(4.1, 0.25, size=len(sample))
    dip = np.where(wk_bool, np.random.uniform(0.25, 0.35, size=len(sample)), 0.0)
    overall = np.clip(base_overall - dip, 1.0, 5.0)

    # subscores correlated
    staff_courtesy = np.clip(np.random.normal(overall - 0.05, 0.25, size=len(sample)), 1.0, 5.0)
    communication = np.clip(np.random.normal(overall - 0.08, 0.25, size=len(sample)), 1.0, 5.0)
    cleanliness = np.clip(np.random.normal(4.2, 0.20, size=len(sample)), 1.0, 5.0)

    themes = [
        'Long wait times during evening rush.',
        'Crowded waiting area; staff doing their best.',
        'Nurse was attentive and courteous.',
        'Communication could be clearer about delays.',
        'Registration was efficient; overall good care.',
        'Provider took time to explain next steps.',
        'Concerned about wait; pleased with outcome.',
        'Observed staffing seemed thin on weekend.',
    ]
    comments = np.random.choice(themes, size=len(sample))

    df = pd.DataFrame({
        'survey_id': [f'SV-{pd.Timestamp(RANGE_START).strftime("%Y%m")}-{i:06d}' for i in range(1, len(sample) + 1)],
        'visit_id': visit_id,
        'site': site,
        'unit': unit,
        'survey_date': pd.to_datetime(survey_date).normalize().date,
        'overall_score': np.round(overall, 2),
        'staff_courtesy': np.round(staff_courtesy, 2),
        'communication_clarity': np.round(communication, 2),
        'cleanliness': np.round(cleanliness, 2),
        'comments': comments,
    })
    print(f'  patient_satisfaction_surveys rows: {len(df):,}')
    return df

# ------------------------------------
# 5) READMISSION RISK FEED (predictions)
# ------------------------------------
# Target rows ~318,640

def generate_readmission_risk_feed(emr: pd.DataFrame) -> pd.DataFrame:
    print('Generating readmission_risk_feed...')
    n_visits = len(emr)
    target_rows = 318640

    # Decide number of predictions per visit (1 or 2) to reach target_rows
    # Compute how many need 2 predictions
    extra = target_rows - n_visits
    extra = max(0, extra)
    two_mask = np.zeros(n_visits, dtype=bool)
    if extra > 0:
        size = min(extra, n_visits)
        pick_idx = np.random.choice(n_visits, size=size, replace=False)
        two_mask[pick_idx] = True

    # Build rows
    visit_ids = emr['visit_id'].values
    patient_ids = emr['patient_id'].values
    arrival_dates = pd.to_datetime(emr['arrival_time']).dt.normalize().values.astype('datetime64[ms]')
    is_wkend = pd.to_datetime(emr['arrival_time']).dt.weekday.values >= 5
    is_lwbs = (emr['discharge_disposition'].values == 'LWBS')

    # For each visit, 1 or 2 prediction dates
    lag1 = np.random.randint(0, 4, size=n_visits)
    lag2 = np.random.randint(1, 5, size=n_visits)

    pred_dates_1 = (pd.to_datetime(arrival_dates) + pd.to_timedelta(lag1, unit='D')).astype('datetime64[ms]')
    pred_dates_2 = (pd.to_datetime(arrival_dates) + pd.to_timedelta(lag2, unit='D')).astype('datetime64[ms]')

    # Base probability ~0.11; weekends +0.02 in affected cohorts; LWBS/long-wait proxy by disposition/acuity
    base_prob = np.full(n_visits, 0.11)
    base_prob[is_wkend] += 0.02
    # acuity influence (higher for 4-5 and 1-2 extremes)
    acuity = emr['acuity_level'].values.astype(int)
    base_prob += (np.abs(acuity - 3) * 0.01)
    # LWBS increase
    base_prob[is_lwbs] += 0.04
    base_prob = np.clip(base_prob, 0.01, 0.80)

    def prob_to_band(p):
        if p < 0.10:
            return 'Low'
        elif p < 0.20:
            return 'Medium'
        else:
            return 'High'

    # Compose arrays
    rows_1 = pd.DataFrame({
        'visit_id': visit_ids,
        'patient_id': patient_ids,
        'prediction_date': pd.to_datetime(pred_dates_1).date,
        'readmission_probability': np.round(base_prob + np.random.normal(0, 0.02, size=n_visits), 3),
    })
    rows_1['readmission_probability'] = rows_1['readmission_probability'].clip(0.0, 1.0)
    p1 = rows_1['readmission_probability'].values
    rows_1['risk_band'] = np.where(p1 < 0.10, 'Low', np.where(p1 < 0.20, 'Medium', 'High'))

    rows_list = [rows_1]

    if two_mask.any():
        idx = np.where(two_mask)[0]
        n2 = len(idx)
        rows_2 = pd.DataFrame({
            'visit_id': visit_ids[idx],
            'patient_id': patient_ids[idx],
            'prediction_date': pd.to_datetime(pred_dates_2[idx]).date,
            'readmission_probability': np.round(base_prob[idx] + np.random.normal(0.01, 0.02, size=n2), 3),
        })
        rows_2['readmission_probability'] = rows_2['readmission_probability'].clip(0.0, 1.0)
        p2 = rows_2['readmission_probability'].values
        rows_2['risk_band'] = np.where(p2 < 0.10, 'Low', np.where(p2 < 0.20, 'Medium', 'High'))
        rows_list.append(rows_2)

    df = pd.concat(rows_list, ignore_index=True)
    # If we overshot due to clipping or duplicates, trim or pad modestly
    if len(df) > target_rows:
        df = df.sample(n=target_rows, random_state=42).reset_index(drop=True)
    elif len(df) < target_rows:
        pad_n = target_rows - len(df)
        pad_idx = np.random.choice(len(rows_1), size=pad_n, replace=True)
        df_pad = rows_1.iloc[pad_idx].copy()
        # shift prediction_date by +1 day for pad to avoid exact duplicates
        df_pad['prediction_date'] = pd.to_datetime(df_pad['prediction_date']) + pd.to_timedelta(1, unit='D')
        df = pd.concat([df, df_pad], ignore_index=True)

    print(f'  readmission_risk_feed rows: {len(df):,}')
    return df

# -------------------------
# MAIN EXECUTION AND SAVING
# -------------------------
if __name__ == '__main__':
    print('Starting SummitCare ER data generation...')
    print('-' * 60)

    emr = generate_emr_er_visits()
    save_to_parquet(emr, 'emr_er_visits', num_files=12)

    hr = generate_hr_shifts_and_sickleave()
    save_to_parquet(hr, 'hr_shifts_and_sickleave', num_files=4)

    flow = generate_patient_flow_metrics()
    save_to_parquet(flow, 'patient_flow_metrics', num_files=8)

    surveys = generate_patient_satisfaction_surveys(emr)
    save_to_parquet(surveys, 'patient_satisfaction_surveys', num_files=2)

    risk = generate_readmission_risk_feed(emr)
    save_to_parquet(risk, 'readmission_risk_feed', num_files=8)

    print('\nSummary signals check:')
    # Weekend surge check
    emr_df = emr.copy()
    emr_df['date'] = pd.to_datetime(emr_df['arrival_time']).dt.tz_localize(None).dt.normalize()
    emr_df['is_weekend'] = pd.to_datetime(emr_df['arrival_time']).dt.tz_localize(None).dt.weekday >= 5
    sep_mask = (emr_df['date'] >= pd.Timestamp('2025-09-01')) & (emr_df['date'] <= pd.Timestamp('2025-09-30'))
    weekend_sep = emr_df[sep_mask & emr_df['is_weekend']]['visit_id'].count()
    weekday_sep = emr_df[sep_mask & (~emr_df['is_weekend'])]['visit_id'].count()
    print(f"  Sep-2025 weekend visits: {weekend_sep:,}; weekdays: {weekday_sep:,} (expect weekend higher vs baseline)")

    # HR sick leave check
    hr_df = hr.copy()
    hr_df['date'] = pd.to_datetime(hr_df['scheduled_start']).dt.tz_localize(None).dt.normalize()
    hr_df['is_weekend'] = pd.to_datetime(hr_df['scheduled_start']).dt.tz_localize(None).dt.weekday >= 5
    nurse = hr_df[hr_df['role'] == 'Nurse']
    sick_wkend = (nurse[ (nurse['date'] >= EVENT_START) & (nurse['is_weekend']) ]['sick_leave_status'] != 'None').mean()
    sick_wkday = (nurse[ (nurse['date'] >= EVENT_START) & (~nurse['is_weekend']) ]['sick_leave_status'] != 'None').mean()
    print(f"  Nurse sick leave weekend >= {sick_wkend:.3f} vs weekday {sick_wkday:.3f} (expect ~2x on weekends)")

    # Flow wait times check
    flow_df = flow.copy()
    flow_df['is_weekend'] = pd.to_datetime(flow_df['event_time']).dt.tz_localize(None).dt.weekday >= 5
    print(f"  Flow median DTT weekend: {flow_df[flow_df['is_weekend']]['door_to_triage_minutes'].median():.1f} vs weekday {flow_df[~flow_df['is_weekend']]['door_to_triage_minutes'].median():.1f}")

    print('Generation complete. Parquet files saved for all 5 datasources.')
