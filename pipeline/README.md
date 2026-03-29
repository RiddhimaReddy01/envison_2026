# Pipeline Layout

This folder contains reproducible build, enrichment, and analysis steps.

## Core Build

- `build_hmda_pipeline.py`: main ingestion/build for HMDA 2007-2017 outputs
- `patch_denials.py`: backfill denied and approved-not-accepted actions into aggregates
- `export_parquet_csv.py`: export all `hmda_output/*.parquet` to CSV

## Analysis Builders

- `build_recovery_drivers.py`: state demand/credit/friction recovery dataset
- `analyze_fha_recovery.py`: FHA share versus recovery-speed analysis

## Causal Subpipeline

- `causal/data_build.py`: builds state-year and national-year causal panels
- `causal/models.py`: runs DiD/event-study/ITS and writes chart-ready files

## Reproducibility Notes

- Scripts resolve `hmda_output/` from project root, not the shell cwd.
- Root-level commands are preserved as wrappers for backward compatibility:
  - `data_ingestion.py`, `hmda_pipeline.py`
  - `patch_denials.py`, `export_csvs.py`
  - `build_recovery_drivers.py`, `fha_recovery_analysis.py`
  - `causal_data_build.py`, `causal_models.py`
