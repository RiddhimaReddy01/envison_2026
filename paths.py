"""
Shared project paths for data reproducibility.
"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_ROOT = PROJECT_ROOT / "data"
RAW_DIR = DATA_ROOT / "raw"
PROCESSED_DIR = DATA_ROOT / "processed"
PROCESSED_PARQUET_DIR = PROCESSED_DIR / "parquet"
PROCESSED_CSV_DIR = PROCESSED_DIR / "csv"
PROCESSED_CACHE_DIR = PROCESSED_DIR / "cache"

# Backward-compatible legacy location used by earlier versions.
LEGACY_OUTPUT_DIR = PROJECT_ROOT / "hmda_output"


def ensure_data_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_CSV_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def find_parquet(name: str) -> Path | None:
    p = PROCESSED_PARQUET_DIR / name
    if p.exists():
        return p
    legacy = LEGACY_OUTPUT_DIR / name
    if legacy.exists():
        return legacy
    return None


def find_csv(name: str) -> Path | None:
    p = PROCESSED_CSV_DIR / name
    if p.exists():
        return p
    legacy = LEGACY_OUTPUT_DIR / name
    if legacy.exists():
        return legacy
    legacy_export = LEGACY_OUTPUT_DIR / "csv_exports" / name
    if legacy_export.exists():
        return legacy_export
    return None
