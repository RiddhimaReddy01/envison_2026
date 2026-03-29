"""
Dataset diagnostic utility.

Run:
    python diagnose.py
"""

from pathlib import Path
import polars as pl

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed" / "parquet"
CSV_DIR = ROOT / "data" / "processed" / "csv"

FILES = [
    "hmda_aggregates.parquet",
    "hmda_sample.parquet",
    "rvs_by_state.parquet",
    "rvs_full.parquet",
    "msa_scissor.parquet",
    "lender_names.parquet",
]

print("=" * 60)
print("HMDA PARQUET DIAGNOSTIC")
print("=" * 60)

for fname in FILES:
    path = DATA_DIR / fname
    if not path.exists():
        print(f"\nX MISSING: {fname}")
        continue

    size_mb = path.stat().st_size / 1e6
    print(f"\n{'-' * 60}")
    print(f"FILE: {fname}  ({size_mb:.1f}MB)")

    try:
        if fname.endswith(".csv"):
            df = pl.read_csv(str(path))
        else:
            df = pl.read_parquet(str(path))

        print(f"  rows:    {len(df):,}")
        print(f"  columns: {df.width}")
        print("  schema:")
        for col, dtype in zip(df.columns, df.dtypes):
            print(f"    {col:<35} {dtype}")

        print("  sample values:")
        for col in df.columns[:6]:
            vals = df[col].drop_nulls().unique().head(5).to_list()
            print(f"    {col}: {vals}")

    except Exception as exc:
        print(f"  ERROR reading: {exc}")

csv_path = CSV_DIR / "external_overlays.csv"
if csv_path.exists():
    print(f"\n{'-' * 60}")
    print(f"FILE: external_overlays.csv  ({csv_path.stat().st_size / 1e6:.1f}MB)")
    try:
        df = pl.read_csv(str(csv_path))
        print(f"  rows:    {len(df):,}")
        print(f"  columns: {df.width}")
        print(f"  schema: {[f'{c}:{t}' for c, t in zip(df.columns, df.dtypes)]}")
    except Exception as exc:
        print(f"  ERROR reading external_overlays.csv: {exc}")

print(f"\n{'=' * 60}")
print("KEY CHECKS")
print("=" * 60)

path = DATA_DIR / "hmda_aggregates.parquet"
if path.exists():
    agg = pl.read_parquet(str(path))
    print(f"\nhmda_aggregates columns: {agg.columns}")

    if "action_taken" in agg.columns:
        print(f"  action_taken unique: {sorted(agg['action_taken'].drop_nulls().unique().to_list())}")
    if "action_label" in agg.columns:
        print(f"  action_label unique: {agg['action_label'].drop_nulls().unique().to_list()}")

    if "loan_type" in agg.columns:
        print(f"  loan_type unique: {sorted(agg['loan_type'].drop_nulls().unique().to_list())}")
    if "loan_type_label" in agg.columns:
        print(f"  loan_type_label unique: {agg['loan_type_label'].drop_nulls().unique().to_list()}")

    if "loan_purpose" in agg.columns:
        print(f"  loan_purpose unique: {sorted(agg['loan_purpose'].drop_nulls().unique().to_list())}")
    if "loan_purpose_label" in agg.columns:
        print(f"  loan_purpose_label unique: {agg['loan_purpose_label'].drop_nulls().unique().to_list()}")

    race_cols = [c for c in agg.columns if "race" in c.lower()]
    print(f"  race columns: {race_cols}")
    for rc in race_cols:
        print(f"    {rc} unique: {agg[rc].drop_nulls().unique().to_list()[:8]}")

    if "income_band" in agg.columns:
        print(f"  income_band unique: {agg['income_band'].drop_nulls().unique().to_list()}")

    state_cols = [c for c in agg.columns if "state" in c.lower()]
    print(f"  state columns: {state_cols}")
    for sc in state_cols:
        print(f"    {sc} sample: {agg[sc].drop_nulls().unique().head(5).to_list()}")

    year_cols = [c for c in agg.columns if "year" in c.lower()]
    print(f"  year columns: {year_cols}")
    for yc in year_cols:
        print(f"    {yc} unique: {sorted(agg[yc].drop_nulls().unique().to_list())}")

path = DATA_DIR / "hmda_sample.parquet"
if path.exists():
    samp = pl.read_parquet(str(path))
    print(f"\nhmda_sample columns: {samp.columns}")
    year_col = next((c for c in samp.columns if "year" in c.lower()), None)
    if year_col:
        print(f"  {year_col} unique: {sorted(samp[year_col].drop_nulls().unique().to_list())}")
    if "lti_ratio" in samp.columns:
        print(f"  lti_ratio: min={samp['lti_ratio'].min():.2f} max={samp['lti_ratio'].max():.2f} nulls={samp['lti_ratio'].null_count()}")
    else:
        print("  WARNING: lti_ratio column MISSING")
        for c in ["loan_amount_000s", "applicant_income_000s"]:
            print(f"  {c} present: {c in samp.columns}")

path = DATA_DIR / "msa_scissor.parquet"
if path.exists():
    msa = pl.read_parquet(str(path))
    print(f"\nmsa_scissor columns: {msa.columns}")
    msa_col = next((c for c in msa.columns if "msa" in c.lower()), None)
    if msa_col:
        print(f"  {msa_col} sample: {msa[msa_col].drop_nulls().unique().head(5).to_list()}")
    if "median_lti" in msa.columns:
        print(f"  median_lti: min={msa['median_lti'].min():.2f} max={msa['median_lti'].max():.2f}")

path = DATA_DIR / "rvs_by_state.parquet"
if path.exists():
    rvs = pl.read_parquet(str(path))
    print(f"\nrvs_by_state columns: {rvs.columns}")
    print(f"  all rows:\n{rvs.to_pandas().to_string(index=False)}")

path = DATA_DIR / "lender_names.parquet"
if path.exists():
    lend = pl.read_parquet(str(path))
    print(f"\nlender_names columns: {lend.columns}")
    if "institution_name" in lend.columns:
        top = (
            lend.group_by("institution_name")
            .agg(pl.col("originations").sum())
            .sort("originations", descending=True)
            .head(10)
        )
        print(f"  top 10 institutions:\n{top.to_pandas().to_string(index=False)}")
    else:
        print("  WARNING: institution_name column MISSING - TS join failed")
        print(f"  columns present: {lend.columns}")

print(f"\n{'=' * 60}")
print("DONE - paste this output to Claude")
print("=" * 60)
