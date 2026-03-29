# Pipeline Layout

This folder contains reproducible build, enrichment, and analysis steps.

## Core Build

- `build_hmda_pipeline.py`: main ingestion/build for HMDA 2007-2017 outputs
- `patch_denials.py`: backfill denied and approved-not-accepted actions into aggregates

## Analysis Builders

- `build_recovery_drivers.py`: state demand/credit/friction recovery dataset
- `analyze_fha_recovery.py`: FHA share versus recovery-speed analysis

## Reproducibility Notes

- Scripts resolve `data/processed/{parquet,csv}` from project root, not the shell cwd.
- Backward-compatible wrappers are in `compat/`:
  - `compat/data_ingestion.py`, `compat/hmda_pipeline.py`
  - `compat/patch_denials.py`
  - `compat/build_recovery_drivers.py`, `compat/fha_recovery_analysis.py`
