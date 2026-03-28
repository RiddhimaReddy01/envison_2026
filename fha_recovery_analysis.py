"""
fha_recovery_analysis.py
Hypothesis: States with higher FHA adoption during the crisis recovered faster.
"""
import polars as pl

agg = pl.read_parquet("./hmda_output/hmda_aggregates.parquet")
rvs = pl.read_parquet("./hmda_output/rvs_by_state.parquet")

# Column names in rvs_by_state: state, first_recovery_year, rvs_years
print("=== RVS States ===")
print(rvs.sort("rvs_years"))

# --- Compute FHA share per state in TWO windows ---
# 1) Crisis peak: 2008-2010
# 2) Full period: 2007-2017

def fha_share_window(df, year_start, year_end, label):
    w = df.filter(
        (pl.col("as_of_year") >= year_start) &
        (pl.col("as_of_year") <= year_end)
    )
    total = w.group_by("state_code").agg(
        pl.col("n_records").sum().alias("total")
    )
    fha = (
        w.filter(pl.col("loan_type_label") == "FHA")
        .group_by("state_code")
        .agg(pl.col("n_records").sum().alias("fha_count"))
    )
    result = (
        total.join(fha, on="state_code", how="left")
        .with_columns([
            (pl.col("fha_count") / pl.col("total")).alias(f"fha_share_{label}"),
            pl.col("fha_count").fill_null(0),
        ])
        .select(["state_code", f"fha_share_{label}"])
    )
    return result

crisis  = fha_share_window(agg, 2008, 2010, "crisis")
full    = fha_share_window(agg, 2007, 2017, "full")
pre     = fha_share_window(agg, 2007, 2007, "pre2007")

# Rename rvs state col to match aggregates
rvs_renamed = rvs.rename({"state": "state_code", "rvs_years": "rvs_years_from_trough"})

# Join everything
analysis = (
    rvs_renamed
    .join(crisis, on="state_code", how="left")
    .join(full,   on="state_code", how="left")
    .join(pre,    on="state_code", how="left")
    .sort("rvs_years_from_trough")
)

print("\n=== FHA Share vs Recovery Speed ===")
print(analysis.select([
    "state_code",
    "rvs_years_from_trough",
    "first_recovery_year",
    "fha_share_pre2007",
    "fha_share_crisis",
    "fha_share_full",
]))

# Correlation
import numpy as np
data = analysis.drop_nulls()
fha_crisis = data["fha_share_crisis"].to_numpy()
rvs_years  = data["rvs_years_from_trough"].to_numpy()
corr = float(np.corrcoef(fha_crisis, rvs_years)[0, 1])
print(f"\nCorrelation: FHA crisis share vs recovery years: {corr:.3f}")
if corr < -0.3:
    print("RESULT: States with MORE FHA adoption RECOVERED FASTER (negative correlation)")
elif corr > 0.3:
    print("RESULT: States with MORE FHA adoption RECOVERED SLOWER (positive correlation)")
else:
    print("RESULT: Weak/no clear relationship in this dataset")

print("\nFastest recoverers:")
print(data.sort("rvs_years_from_trough").head(3).select(
    ["state_code","rvs_years_from_trough","fha_share_crisis"]
))
print("\nSlowest recoverers:")
print(data.sort("rvs_years_from_trough", descending=True).head(3).select(
    ["state_code","rvs_years_from_trough","fha_share_crisis"]
))

# Save for chart
analysis.write_csv("./hmda_output/csv_exports/fha_recovery_analysis.csv")
print("\nSaved: hmda_output/csv_exports/fha_recovery_analysis.csv")
