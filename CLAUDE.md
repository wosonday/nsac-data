# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current state (updated 2026-11-14 12:10)

`sky-ml` is partly built and runs on the user's Windows machine:

- Done and verified: `copy-data` (37 files, 496.3 MB, 25 hash-checked against NASA-cl manifests), `check`, and `prepare hr` (5301 windows / 22 subjects; this matches the 11/11 NASA-cl run).
- Config is **YAML**, not TOML and not Python:
  - `sky_ml.yaml` holds `nasa_cl_data`, `data_dir` (data/1_source), `features_dir`, `models_dir`, `predictions_dir`, `tasks_config`, `dictionary_config`;
  - `configs/tasks.yaml` holds per-task params;
  - `configs/crew_map.yaml` and `configs/rules.yaml` are planned;
  - `src/sky_ml/tasks.py` is obsolete and should be deleted.
- Next: `train` / `evaluate` for hr (reproduce ridge MAE 3.917428), then the six-indicator work.

Source-of-truth docs:

- `docs/superpowers/specs/2026-11-14-sky-ml-design.md`: spec. **Section 9 (12:10 update)** overrides earlier parts: YAML, the six indicators, `export-nsac`.
- `docs/superpowers/plans/2026-11-14-sky-ml.md`: plan. Tasks 1–4 are done; Tasks 13–17 cover the six indicators and the nsac bundle.
- `THIET_KE_TICH_HOP_SKY_NASA-CL_x_NSAC_2026-11-14.md` **v2**: integration with nsac `3704308`, which now has a TS + Bun + Drizzle backend in `apps/backend`, a 6-person fictional crew, and a SignalWell UI.
- `docs/HUONG_DAN_BUILD_COPY_PREPROCESS.md`: step-by-step build guide (Vietnamese).

Six indicators: heart rate, blood pressure, mood, activity & sleep, body temperature, blood glucose. Each fictional nsac astronaut maps to **one** de-identified UTMB analog subject:
- CFT70 5160 / 8072 / 8936: HR, BP, temperature, POMS mood;
- Campaign 1 C1G0001–3: HR, BP, temperature, actigraphy sleep, serum glucose.

Any metric that subject lacks is shown as UNKNOWN, never borrowed from another cohort. Vitals models train on Campaign 3 (23 subjects, LOSO) and are tested out-of-cohort on those six subjects; never pick a persona from Campaign 3.

## Commands

Windows + PowerShell, `uv` with Python 3.12 (`.python-version`). The build backend is `uv_build`.

```powershell
uv sync
uv run sky-ml copy-data [--dry-run]      # copy allowlisted NASA-cl files → data/, verify SHA-256, write COPY_MANIFEST.csv
uv run sky-ml check                      # verify data copy exists + SHA-256 matches COPY_MANIFEST
uv run sky-ml prepare|train|evaluate|explain|export <task> [--run latest]
uv run sky-ml run all                    # steps 1→6 for all tasks (planned)
uv run sky-ml export-nsac --out <dir>    # sky-bundle/v2 for nsac apps/backend (planned)
uv run pytest                            # fast tests (synthetic fixtures)
uv run pytest -m slow                    # reproduction test, needs real data
uv run pytest tests/test_x.py::test_y    # single test
uv run ruff check .
```

Implemented so far: `copy-data`, `check`, `prepare hr`; everything else is planned. Subcommand/flag names are left to the implementer; the spec suggests build order hr → dose → cpet → sleep (light → heavy; sleep needs `mne` and most RAM).

## Architecture (planned, per the spec)

Four tasks — `cpet`, `sleep`, `hr`, `dose` — each flow through the same independently-runnable stages: **copy → check → prepare → train → evaluate → explain → export**. Each stage writes readable intermediates (CSV.gz, JSON, not Parquet) to `runs/<task>/<YYYY-MM-DD_HHMMSS>/`; runs are never overwritten. `snapshot.json` in each run records input SHA-256s, library versions, seed (17), and git rev.

Things that span several files:

- **Data comes from a sibling repo, `D:\Project\NASA-cl\data`, via a one-time hash-verified copy** into `./data/` (gitignored, logged in `data/COPY_MANIFEST.csv`). All later steps read only the copy. `settings.py` reads `sky_ml.yaml` / env `SKY_NASA_CL_DATA` and must refuse to write anywhere inside NASA-cl. Never write to NASA-cl.
- **`prepare/<task>.py`** each return `(table, features)`; `prepare/windows.py` holds the shared `make_windows` which must use past → future only (no leakage). HR uses the pre-QA'd `processed/sample-v2` table, not raw MMASH.
- **`train.py`** builds folds (LOSO or by_month) and fits *all* models on identical folds; **`evaluate.py`** computes per-fold metrics, bootstrap CIs, baseline comparison, coverage, permutation tests.
- **`export.py`** must emit out-of-fold (held-out person) predictions only. NASA-cl's existing `payload_examples` is wrong because it predicts with a final model on its own training rows — do not reproduce that.
- Residual quantiles (q90/q95/q99) are computed per person, then median across people.
- CPET: report both `physio_only` and `with_group` feature sets; the GROUP variable does not exist for a real astronaut, so the demo card should use the `mean_delta` baseline.

## Constraints that govern changes

- **Round 1 = reproduction**: metrics must match the 11/11 NASA-cl run (MAE / macro-F1 within 1e-6 for cpet/hr/dose, 0.005 for sleep). If they diverge, stop and find the cause before adding improvements. Round 2 (T0 snapshot, T1 feature sets, OOF export, residual quantiles) comes after.
- Never merge cohorts (MMASH, UTMB, Sleep-EDF, RadLab) by ID or time; never present in-sample predictions as results; no thresholds without a cited source.
- Dependencies must be OSI-licensed. Use `pathlib` (no hard-coded `/mnt/d`); commands must work in PowerShell.
- Out of scope: crawler, new downloads, raw MMASH processing, SEISS/omics, web UI code (lives in nsac), nested CV and sleep calibration (round 2 if time). The nsac bundle (`export-nsac`) is now IN scope.
- Bundles keep only relative `mission_day`, never real calendar dates of the analog studies.

## Naming convention and pipeline (user preference, 2026-11-14 14:15)

Pipeline steps are numbered in run order; support/config/off-pipeline modules start with `_`.

| Step | Module | Command | Writes to |
|---|---|---|---|
| 1 | `1_load_data.py` (copy + verify + snapshot) | `sky-ml load-data [--dry-run]`, `sky-ml check` | `data/1_source/` + `COPY_MANIFEST.csv` |
| 2 | `2_build_features/` (features chosen in `configs/tasks.yaml` → `features:`) | `sky-ml build-features <task>` | (1) `data/2_features/<task>/<run>/`: `table.csv.gz`, `features.json`, `snapshot.json` |
| 3 | `3_train.py` | `sky-ml train <task>` | (3) `data/3_models/<task>/<run>/`: `oof.csv.gz`, `folds.json`, `<model>/final.joblib`, `manifest.json` |
| 4 | `4_evaluate.py` | `sky-ml evaluate <task>` | (3) same folder: `metrics.csv`, `summary.json` |
| 5 | `5_predict.py` (load saved model, predict new data) | `sky-ml predict <task> --input X.csv [--mode latest\|backtest] [--model M]` | (2) `data/4_predictions/<task>/<run>/*.csv/json` |

- Data layout (user request 2026-11-14 14:47): three groups share one `run_id`; every run folder gets an auto `README.md` data card (`_datacards.write_card`, column text from `configs/data_dictionary.yaml`) and every file is appended to `data/CATALOG.csv` (`_datacards.register`). Docs: `data/README.md`, `docs/3_HUONG_DAN_DU_LIEU.md`; sources for all built models: `docs/Tong_hop_du_lieu_mo_hinh.xlsx` (add rows when a new task is built; only sources actually used). `runs/` is obsolete.
- Tasks built (2026-11-14 16:50), all reproduce NASA-cl 11/11 exactly: `hr`, `dose` (by_month), `cpet` (+ permutation test 200), `cpet_physio` (`builder: cpet`, features pre_vo2+age only), `sleep` (classification, `features: all` = 54); added 20:15: `dose_orbit` (`builder: dose`, `context: [latitude, longitude, altitude]` → `<col>_now` at cutoff), `sleep_act` (BRSMAct Campaign 1, 3 persona subjects, `measure:` efficiency|duration|latency). Summary: `docs/Tong_hop_du_lieu_mo_hinh.xlsx`, `docs/BAO_CAO_DU_LIEU_VA_MO_HINH_2026-11-14.md`. NSAC_Data_Supplement_20261114.zip was evaluated and NOT adopted (duplicates / no gain). Added 20:45: `vitals_sbp|dbp|temp|pulse` (`builder: vitals`, train Campaign 3, `external_cohorts` = the 6 personas → `external.csv.gz`, `external_metrics.csv`, `4_predictions/<task>/<run>/external_backtest.csv`), `mood` (POMS TMD), `glucose` (OGTT fasting delta, 1 row/person). SYNTHETIC data (user/BTC-approved, must be labelled): `sky-ml make-synthetic` → `data/1_synthetic/` (mood_c1_poms, sleep_cft70_actigraphy, glucose_daily_personas; params estimated from real data, seed 17, `is_synthetic` column, README + params.json + validation.csv + SYNTHETIC_MANIFEST.csv). Synthetic data is NEVER a training input (tested); predictions from it carry `input_synthetic=True` and `_SYNTHETIC-INPUT` in the file name. Persona ↔ analog + real/synthetic coverage: `configs/crew_map.yaml`. Builders live in `2_build_features/{hr,dose,cpet,sleep}.py`; `tasks.yaml › inputs` may use globs (expanded against COPY_MANIFEST); `builder:` lets several tasks share one builder. `predict --mode table` works for every task; classification output = label + `p_<class>`.
- Commands that run on the user's Linux VM must set `TZ=Asia/Bangkok` (run_id uses local time), `UV_PROJECT_ENVIRONMENT` outside the repo, and `SKY_NASA_CL_DATA=$HOME/mnt/NASA-cl/data` for load-data. The user does git themselves.
- Support modules: `_settings.py`, `_runs.py`, `_datacards.py`, `_jsonio.py`, `_models.py`, `_artifacts.py`, `_hashing.py`, `_steps.py`, `_cli.py`. The entry point is `sky_ml._cli:main`.
- Module names starting with a digit cannot be used with `import`. Load steps only via `sky_ml._steps` (importlib); a step that needs another step uses `importlib.import_module("sky_ml.4_evaluate")`.
- Ruff's N999 rule is ignored for these files in `pyproject.toml`.
- Tests: `test_<step>_*.py`; support tests use `test_0_*`; the slow reproduction test is `test_9_reproduce.py`.
- `deploy_model` in `tasks.yaml` is chosen up front (not by test score).
- `predict` refuses to run if `features` changed since training, abstains on missing or out-of-training-range features, and flags `in_sample` subjects.

