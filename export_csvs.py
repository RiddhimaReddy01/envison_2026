"""
export_csvs.py — Export all hmda_output parquet files to CSV.
Run: python export_csvs.py
"""

import os
import polars as pl

OUTPUT_DIR = "./hmda_output"
CSV_DIR    = "./hmda_output/csv_exports"

os.makedirs(CSV_DIR, exist_ok=True)

parquet_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".parquet")]

if not parquet_files:
    print("No parquet files found in", OUTPUT_DIR)
else:
    print(f"\nExporting {len(parquet_files)} parquet file(s) to CSV...\n")
    for fname in parquet_files:
        in_path  = os.path.join(OUTPUT_DIR, fname)
        out_name = fname.replace(".parquet", ".csv")
        out_path = os.path.join(CSV_DIR, out_name)

        df = pl.read_parquet(in_path)
        df.write_csv(out_path)

        rows, cols = df.shape
        size_kb = os.path.getsize(out_path) / 1024
        print(f"  {fname:<40s}  {rows:>9,} rows x {cols:>2} cols  ({size_kb:>9,.0f} KB)")

    print(f"\nAll CSVs saved to: {os.path.abspath(CSV_DIR)}\n")
