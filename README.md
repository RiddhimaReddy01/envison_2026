# Envision 2026 - Reproducibility Guide

## 1) Environment

Create and activate a fresh Python environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If `python` is not on PATH, use your interpreter directly (example):

```powershell
& 'C:\Users\riddh\anaconda3\python.exe' -m pip install -r requirements.txt
```

## 2) Build data outputs

Run full pipeline:

```powershell
python compat/hmda_pipeline.py
```

Patch denial rows only (if needed):

```powershell
python compat/patch_denials.py
```

Build recovery drivers for Chapter 5:

```powershell
python compat/build_recovery_drivers.py
```

Verify output files:

```powershell
python compat/hmda_pipeline.py verify
```

## 3) Run app

```powershell
python app.py
```

Open:

`http://127.0.0.1:8050`

## Notes

- Cached dataframes are used in `app.py` for smoother interactions.  
  Restart the app after regenerating parquet files.
- Chapter 6 denial heatmap is sourced/interpolated and labeled as such; other Chapter 6 race-share visuals are computed directly from local HMDA aggregates.
- Data layout:
  - `data/raw/` for raw source extracts
  - `data/processed/parquet/` for processed parquet files
  - `data/processed/csv/` for processed csv files
  - `data/processed/cache/` for API/cache artifacts

## Codebase layout (reproducible)

- Dashboard/runtime:
  - `app.py`
  - `charts.py`
  - `data_loader.py`
  - `world_bank_data.py`
- Pipeline:
  - `pipeline/build_hmda_pipeline.py`
  - `pipeline/patch_denials.py`
  - `pipeline/build_recovery_drivers.py`
  - `pipeline/analyze_fha_recovery.py`
- Dev diagnostics:
  - `scripts/dev/diagnose_data.py`
  - `scripts/dev/profile_data.py`

Compatibility wrappers live in `compat/`:
- `compat/hmda_pipeline.py`
- `compat/data_ingestion.py`
- `compat/patch_denials.py`
- `compat/build_recovery_drivers.py`
- `compat/fha_recovery_analysis.py`
- `compat/diagnose.py`
- `compat/profile_data.py`
