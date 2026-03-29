import polars as pl
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARQUET_DIR = ROOT / "data" / "processed" / "parquet"

print("=== hmda_aggregates ===")
df = pl.read_parquet(str(PARQUET_DIR / "hmda_aggregates.parquet"))
print("Columns     :", df.columns)
print("action_taken:", sorted(df["action_taken"].drop_nulls().unique().to_list()))
print("states      :", sorted(df["state_code"].drop_nulls().unique().to_list()))
print("income_bands:", df["income_band"].drop_nulls().unique().to_list())
print("loan_types  :", df["loan_type_label"].drop_nulls().unique().to_list())
print("race labels :", df["applicant_race_label"].drop_nulls().unique().to_list())
print("years       :", sorted(df["as_of_year"].drop_nulls().unique().to_list()))
print("total n_records:", df["n_records"].sum())

print()
print("=== lender_names ===")
ld = pl.read_parquet(str(PARQUET_DIR / "lender_names.parquet"))
print("Columns:", ld.columns)
print(ld.head(3))

print()
print("=== rvs_full ===")
rv = pl.read_parquet(str(PARQUET_DIR / "rvs_full.parquet"))
print("Columns:", rv.columns)
print(rv.head(8))

print()
print("=== rvs_by_state ===")
rs = pl.read_parquet(str(PARQUET_DIR / "rvs_by_state.parquet"))
print(rs)

print()
print("=== hmda_sample ===")
s = pl.read_parquet(str(PARQUET_DIR / "hmda_sample.parquet"))
print("Columns:", s.columns)
print("Rows   :", len(s))
print(s.head(3))
