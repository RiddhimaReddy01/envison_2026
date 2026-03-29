"""
Build Chapter 5 state-level recovery drivers dataset.

Outputs:
    data/processed/parquet/recovery_drivers_state.parquet

Drivers:
  - Demand: employment recovery speed (BLS API, 2009 -> 2013)
  - Credit: nonbank acceleration (share change 2010 -> 2014)
  - Friction: price recovery lag (FHFA HPI, years to regain 2007 level)
  - Outcome: rvs_years (from existing HMDA-derived rvs_by_state.parquet)
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import polars as pl
import requests


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "processed" / "parquet"
OUT_PATH = OUT_DIR / "recovery_drivers_state.parquet"

BLS_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
FHFA_STATE_CSV = "https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_state.csv"

STATE_TO_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08",
    "CT": "09", "DE": "10", "FL": "12", "GA": "13", "HI": "15", "ID": "16",
    "IL": "17", "IN": "18", "IA": "19", "KS": "20", "KY": "21", "LA": "22",
    "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28",
    "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34",
    "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39", "OK": "40",
    "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46", "TN": "47",
    "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53", "WV": "54",
    "WI": "55", "WY": "56",
}


def _load_target_states() -> list[str]:
    rvs = pl.read_parquet(OUT_DIR / "rvs_by_state.parquet")
    states = sorted(set(rvs["state"].to_list()))
    return [s for s in states if s in STATE_TO_FIPS]


def _fetch_bls_employment_growth(states: list[str]) -> pd.DataFrame:
    # LAUS state employed persons series pattern (example: LASST480000000000005 for TX)
    series_ids = [f"LASST{STATE_TO_FIPS[s]}0000000000005" for s in states]
    payload = {
        "seriesid": series_ids,
        "startyear": "2007",
        "endyear": "2013",
    }
    res = requests.post(BLS_URL, json=payload, timeout=60)
    res.raise_for_status()
    body = res.json()
    if body.get("status") != "REQUEST_SUCCEEDED":
        raise RuntimeError(f"BLS API failed: {body.get('message')}")

    rows: list[dict] = []
    for series in body["Results"]["series"]:
        sid = series["seriesID"]
        # LASST + 2-digit FIPS + ... + 005 (employment)
        fips = sid[5:7]
        state = next((k for k, v in STATE_TO_FIPS.items() if v == fips), None)
        if state is None:
            continue
        for point in series["data"]:
            period = point.get("period", "")
            if not period.startswith("M") or period == "M13":
                continue
            rows.append(
                {
                    "state": state,
                    "year": int(point["year"]),
                    "employment": float(point["value"]),
                }
            )

    if not rows:
        raise RuntimeError("No BLS employment rows parsed")

    d = pd.DataFrame(rows)
    yearly = d.groupby(["state", "year"], as_index=False)["employment"].mean()
    pivot = yearly.pivot(index="state", columns="year", values="employment")
    out = pd.DataFrame({"state": pivot.index})
    out["employment_2009"] = pivot[2009].values
    out["employment_2013"] = pivot[2013].values
    out["employment_recovery_pct"] = (
        (out["employment_2013"] - out["employment_2009"]) / out["employment_2009"] * 100.0
    )
    return out[["state", "employment_recovery_pct"]]


def _compute_nonbank_acceleration(states: list[str]) -> pd.DataFrame:
    lender = pl.read_parquet(OUT_DIR / "lender_names.parquet")
    lender = lender.filter(
        pl.col("state_code").is_in(states) & pl.col("year").is_in([2010, 2014])
    ).with_columns(
        pl.when(pl.col("agency_code") == 7)
        .then(pl.lit("Nonbank"))
        .otherwise(pl.lit("Bank"))
        .alias("lender_type")
    )
    by = (
        lender.group_by(["state_code", "year", "lender_type"])
        .agg(pl.col("originations").sum().alias("originations"))
        .to_pandas()
    )
    if by.empty:
        return pd.DataFrame(columns=["state", "nonbank_accel_pp"])

    piv = by.pivot_table(
        index=["state_code", "year"],
        columns="lender_type",
        values="originations",
        aggfunc="sum",
        fill_value=0.0,
    ).reset_index()
    if "Bank" not in piv.columns:
        piv["Bank"] = 0.0
    if "Nonbank" not in piv.columns:
        piv["Nonbank"] = 0.0
    total = piv["Bank"] + piv["Nonbank"]
    piv["nonbank_share"] = piv["Nonbank"] / total.where(total != 0, 1.0)

    out = piv.pivot(index="state_code", columns="year", values="nonbank_share").reset_index()
    out["nonbank_accel_pp"] = (out[2014] - out[2010]) * 100.0
    out = out.rename(columns={"state_code": "state"})
    return out[["state", "nonbank_accel_pp"]]


def _fetch_fhfa_price_recovery_lag(states: list[str]) -> pd.DataFrame:
    res = requests.get(FHFA_STATE_CSV, timeout=60)
    res.raise_for_status()
    # File has no header: state,year,quarter,index
    hpi = pd.read_csv(io.StringIO(res.text), header=None, names=["state", "year", "quarter", "hpi"])
    hpi = hpi[hpi["state"].isin(states)].copy()
    hpi["year"] = hpi["year"].astype(int)
    hpi["hpi"] = hpi["hpi"].astype(float)
    annual = hpi.groupby(["state", "year"], as_index=False)["hpi"].mean()

    rows: list[dict] = []
    for st, g in annual.groupby("state"):
        g = g.sort_values("year")
        base = g.loc[g["year"] == 2007, "hpi"]
        if base.empty:
            rows.append({"state": st, "price_recovery_lag_years": None})
            continue
        base_2007 = float(base.iloc[0])
        recovered = g[(g["year"] >= 2008) & (g["hpi"] >= base_2007)]
        if recovered.empty:
            rows.append({"state": st, "price_recovery_lag_years": None})
            continue
        first_year = int(recovered["year"].iloc[0])
        rows.append({"state": st, "price_recovery_lag_years": first_year - 2007})

    return pd.DataFrame(rows)


def build_recovery_drivers() -> pl.DataFrame:
    states = _load_target_states()
    rvs = pl.read_parquet(OUT_DIR / "rvs_by_state.parquet").to_pandas().rename(columns={"rvs_years": "recovery_years"})
    emp = _fetch_bls_employment_growth(states)
    nb = _compute_nonbank_acceleration(states)
    lag = _fetch_fhfa_price_recovery_lag(states)

    df = rvs.merge(emp, on="state", how="left").merge(nb, on="state", how="left").merge(lag, on="state", how="left")
    out = pl.from_pandas(df).select(
        "state",
        "first_recovery_year",
        pl.col("recovery_years").cast(pl.Int32),
        pl.col("employment_recovery_pct").cast(pl.Float64),
        pl.col("nonbank_accel_pp").cast(pl.Float64),
        pl.col("price_recovery_lag_years").cast(pl.Float64),
    )
    return out


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    drivers = build_recovery_drivers()
    drivers.write_parquet(OUT_PATH)
    print(f"Wrote {OUT_PATH} ({drivers.height} states)")
