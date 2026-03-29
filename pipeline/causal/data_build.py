"""
causal_data_build.py
Builds panel datasets for causal modeling from HMDA-derived aggregates.

Outputs (default: hmda_output/causal):
- state_year_panel.parquet / .csv
- national_year_panel.parquet / .csv
"""

from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd
import polars as pl
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import data_loader as dl


GOV_TYPES = {"FHA", "VA", "FSA/RHS"}


def _load_agg(data_dir: Path) -> pl.DataFrame:
    path = data_dir / "hmda_aggregates.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return pl.read_parquet(path)


def build_state_year_panel(data_dir: str = "hmda_output") -> pd.DataFrame:
    ddir = Path(data_dir)
    if not ddir.is_absolute():
        ddir = ROOT / ddir
    agg = _load_agg(ddir)

    orig = agg.filter(pl.col("action_taken") == 1)

    by_sy = (
        orig.group_by(["state_code", "as_of_year"]).agg(
            pl.col("n_records").sum().alias("originations")
        )
    )

    by_type = (
        orig.group_by(["state_code", "as_of_year", "loan_type_label"]).agg(
            pl.col("n_records").sum().alias("count")
        )
    )
    totals = (
        by_type.group_by(["state_code", "as_of_year"]).agg(
            pl.col("count").sum().alias("total_type")
        )
    )
    by_type = by_type.join(totals, on=["state_code", "as_of_year"], how="left")
    by_type = by_type.with_columns((pl.col("count") / pl.col("total_type")).alias("type_share"))

    gov_share = (
        by_type.filter(pl.col("loan_type_label").is_in(sorted(GOV_TYPES)))
        .group_by(["state_code", "as_of_year"])
        .agg(pl.col("type_share").sum().alias("gov_share"))
    )

    conv_share = (
        by_type.filter(pl.col("loan_type_label") == "Conventional")
        .select(["state_code", "as_of_year", pl.col("type_share").alias("conventional_share")])
    )

    by_purpose = (
        orig.group_by(["state_code", "as_of_year", "loan_purpose_label"]).agg(
            pl.col("n_records").sum().alias("count")
        )
    )
    p_tot = (
        by_purpose.group_by(["state_code", "as_of_year"]).agg(
            pl.col("count").sum().alias("total_purpose")
        )
    )
    by_purpose = by_purpose.join(p_tot, on=["state_code", "as_of_year"], how="left")
    by_purpose = by_purpose.with_columns((pl.col("count") / pl.col("total_purpose")).alias("purpose_share"))

    purchase_share = (
        by_purpose.filter(pl.col("loan_purpose_label") == "Purchase")
        .select(["state_code", "as_of_year", pl.col("purpose_share").alias("purchase_share")])
    )
    refi_share = (
        by_purpose.filter(pl.col("loan_purpose_label") == "Refinance")
        .select(["state_code", "as_of_year", pl.col("purpose_share").alias("refi_share")])
    )

    panel = (
        by_sy.join(gov_share, on=["state_code", "as_of_year"], how="left")
        .join(conv_share, on=["state_code", "as_of_year"], how="left")
        .join(purchase_share, on=["state_code", "as_of_year"], how="left")
        .join(refi_share, on=["state_code", "as_of_year"], how="left")
        .fill_null(0.0)
        .rename({"as_of_year": "year", "state_code": "state"})
        .sort(["state", "year"])
    )

    pdf = panel.to_pandas()

    # Exposure definitions based on pre-crisis structure.
    pre = pdf[pdf["year"].between(2007, 2008)].copy()
    exp = (
        pre.groupby("state", as_index=False)
        .agg(
            gse_exposure_pre=("gov_share", "mean"),
            private_exposure_pre=("conventional_share", "mean"),
        )
    )
    gse_med = exp["gse_exposure_pre"].median()
    priv_med = exp["private_exposure_pre"].median()

    exp["high_gse_exposure"] = (exp["gse_exposure_pre"] > gse_med).astype(int)
    exp["high_private_exposure"] = (exp["private_exposure_pre"] > priv_med).astype(int)

    pdf = pdf.merge(exp, on="state", how="left")
    pdf["post_2008"] = (pdf["year"] >= 2008).astype(int)
    pdf["post_2009"] = (pdf["year"] >= 2009).astype(int)
    pdf["log_originations"] = np.log(pdf["originations"].clip(lower=1))

    overlay = pd.read_csv(ddir / "external_overlays.csv")
    pdf = pdf.merge(overlay, on="year", how="left")

    return pdf


def build_national_year_panel(data_dir: str = "hmda_output") -> pd.DataFrame:
    ddir = Path(data_dir)
    if not ddir.is_absolute():
        ddir = ROOT / ddir

    collapse = dl.collapse_data().to_pandas().sort_values("year")
    lt = dl.loan_type_share().to_pandas()
    denial = dl.denial_rates().to_pandas()

    gov = (
        lt[lt["loan_type"].isin(["FHA", "VA", "FSA/RHS"])]
        .groupby("year", as_index=False)["share"].sum()
        .rename(columns={"share": "gov_share"})
    )
    conv = (
        lt[lt["loan_type"] == "Conventional"][["year", "share"]]
        .rename(columns={"share": "conventional_share"})
    )

    denial_nat = (
        denial.groupby("year", as_index=False)["denial_rate"].mean()
        .rename(columns={"denial_rate": "denial_rate_proxy"})
    )

    out = collapse.merge(gov, on="year", how="left").merge(conv, on="year", how="left").merge(denial_nat, on="year", how="left")
    out["post_2008"] = (out["year"] >= 2008).astype(int)
    out["trend"] = out["year"] - int(out["year"].min())
    out["post_trend"] = out["post_2008"] * out["trend"]

    overlay = pd.read_csv(ddir / "external_overlays.csv")
    out = out.merge(overlay, on="year", how="left")

    return out.sort_values("year")


def write_outputs(data_dir: str = "hmda_output") -> dict[str, str]:
    ddir = Path(data_dir)
    if not ddir.is_absolute():
        ddir = ROOT / ddir
    out_dir = ddir / "causal"
    out_dir.mkdir(parents=True, exist_ok=True)

    state = build_state_year_panel(data_dir=data_dir)
    nat = build_national_year_panel(data_dir=data_dir)

    state_csv = out_dir / "state_year_panel.csv"
    nat_csv = out_dir / "national_year_panel.csv"
    state_parquet = out_dir / "state_year_panel.parquet"
    nat_parquet = out_dir / "national_year_panel.parquet"

    state.to_csv(state_csv, index=False)
    nat.to_csv(nat_csv, index=False)
    state.to_parquet(state_parquet, index=False)
    nat.to_parquet(nat_parquet, index=False)

    return {
        "state_csv": str(state_csv),
        "national_csv": str(nat_csv),
        "state_parquet": str(state_parquet),
        "national_parquet": str(nat_parquet),
    }


if __name__ == "__main__":
    paths = write_outputs(str(ROOT / "hmda_output"))
    for k, v in paths.items():
        print(f"{k}: {v}")
