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
python hmda_pipeline.py
```

Patch denial rows only (if needed):

```powershell
python patch_denials.py
```

Verify output files:

```powershell
python hmda_pipeline.py verify
```

## 3) Smoke test visuals (no browser)

```powershell
python visual_smoke_test.py
```

This checks:
- data loader outputs
- chart construction
- page constructors
- callback figure functions

## 4) Run app

```powershell
python app.py
```

Open:

`http://127.0.0.1:8050`

## Notes

- Cached dataframes are used in `app.py` for smoother interactions.  
  Restart the app after regenerating parquet files.
- Chapter 6 denial heatmap is sourced/interpolated and labeled as such; other Chapter 6 race-share visuals are computed directly from local HMDA aggregates.
