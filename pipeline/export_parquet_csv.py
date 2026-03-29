"""
Export all `hmda_output/*.parquet` files to CSV.
Run: python export_csvs.py
"""

from pathlib import Path
import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "hmda_output"
CSV_DIR = OUTPUT_DIR / "csv_exports"

CSV_DIR.mkdir(parents=True, exist_ok=True)

parquet_files = [f.name for f in OUTPUT_DIR.glob("*.parquet")]

if not parquet_files:
    print("No parquet files found in", OUTPUT_DIR.as_posix())
else:
    print(f"\nExporting {len(parquet_files)} parquet file(s) to CSV...\n")
    for fname in parquet_files:
        in_path = OUTPUT_DIR / fname
        out_name = fname.replace(".parquet", ".csv")
        out_path = CSV_DIR / out_name

        df = pl.read_parquet(str(in_path))
        df.write_csv(str(out_path))

        rows, cols = df.shape
        size_kb = out_path.stat().st_size / 1024
        print(f"  {fname:<40s}  {rows:>9,} rows x {cols:>2} cols  ({size_kb:>9,.0f} KB)")

    print(f"\nAll CSVs saved to: {CSV_DIR.resolve()}\n")
