# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current state (updated 2026-11-14 12:10)

`sky-ml` is partly built and runs on the user's Windows machine:

- Done and verified: `copy-data` (37 files, 496.3 MB, 25 hash-checked against NASA-cl manifests), `check`, and `prepare hr` (5301 windows / 22 subjects; this matches the 11/11 NASA-cl run).
- Config is **YAML**, not TOML and not Python:
  - `sky_ml.yaml` holds `nasa_cl_data`, `data_dir`, `runs_dir`, `tasks_config`;
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
