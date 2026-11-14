# Báo cáo chất lượng dữ liệu mẫu

- File đã đọc: 156
- Dòng nguồn đã đọc: 3230857
- Dòng nguồn đưa vào quarantine: 95031

## Bảng đầu ra

| Bảng | Số dòng |
|---|---:|
| mmash_activity.csv | 454 |
| mmash_minutes.csv.gz | 29360 |
| mmash_questionnaires.csv | 418 |
| mmash_saliva.csv | 84 |
| mmash_sleep.csv | 18 |
| mmash_subjects.csv | 22 |
| noaa_observations.csv.gz | 15472 |
| radlab_observations.csv.gz | 5694 |
| rejected_rows.csv.gz | 95031 |

## Cờ dữ liệu

Một dòng có thể có nhiều cờ; số cờ không phải số dòng lỗi.

- `conflicting_duplicate`: 3
- `duplicate_observation`: 3
- `invalid_day`: 95025
- `invalid_interval`: 4
- `invalid_time`: 2
- `missing_subject_files`: 1
- `missing_value`: 2849
- `nonpositive_value`: 1
- `timezone_unresolved`: 2847
- `unknown_activity_code`: 32

## Giới hạn

- MMASH minute bins are descriptive proxies; no clinical artifact rejection is applied.
- Absent minute bins are not filled; invalid values are blank, not zero.
- Negative study days are quarantined, not automatically repaired.
- Sleep/questionnaire/saliva availability times are unknown; use as retrospective summaries.
- RadLab naive time is unresolved unless explicitly configured as UTC.
- Environmental measurements are not individual doses or medical risk probabilities.
- Duplicate environmental observations are retained and flagged; reconcile before training.
- No model training, personal baseline, cohort scaling or missing-data imputation is performed.
