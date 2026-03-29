"""
causal_models.py
Causal-model scaffold for HMDA dashboard.

Implements:
- Two-way fixed-effects DiD (state-year panel)
- Event-study coefficients (relative to a reference year)
- Interrupted time series (national annual panel)

Writes chart-ready outputs to hmda_output/causal.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from pipeline.causal import data_build as cdb


def _ols_fit(df: pd.DataFrame, y_col: str, x_cols: list[str]) -> tuple[np.ndarray, pd.DataFrame]:
    work = df[[y_col] + x_cols].dropna().copy()
    y = work[y_col].to_numpy(dtype=float)
    X = work[x_cols].to_numpy(dtype=float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    yhat = X @ beta
    resid = y - yhat
    out = work.copy()
    out["yhat"] = yhat
    out["resid"] = resid
    return beta, out


def twfe_did(
    panel: pd.DataFrame,
    outcome: str,
    treat_col: str,
    post_col: str,
    unit_col: str = "state",
    time_col: str = "year",
    controls: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    controls = controls or []

    df = panel.copy()
    df["did"] = df[treat_col] * df[post_col]

    unit_d = pd.get_dummies(df[unit_col], prefix="u", drop_first=True)
    time_d = pd.get_dummies(df[time_col].astype(int), prefix="t", drop_first=True)

    X = pd.concat(
        [
            pd.Series(1.0, index=df.index, name="const"),
            df[["did"] + controls].astype(float),
            unit_d.astype(float),
            time_d.astype(float),
        ],
        axis=1,
    )

    betas, fit = _ols_fit(pd.concat([df[[outcome]], X], axis=1), outcome, X.columns.tolist())
    coef = pd.DataFrame({"term": X.columns, "coef": betas})

    return coef, pd.concat([df[[unit_col, time_col, outcome, treat_col, post_col, "did"]], fit[["yhat", "resid"]]], axis=1)


def event_study(
    panel: pd.DataFrame,
    outcome: str,
    treat_col: str,
    unit_col: str = "state",
    time_col: str = "year",
    ref_year: int = 2007,
    controls: list[str] | None = None,
) -> pd.DataFrame:
    controls = controls or []

    df = panel.copy()
    years = sorted(int(y) for y in df[time_col].dropna().unique().tolist())
    rel_terms = []
    for y in years:
        if y == ref_year:
            continue
        col = f"event_{y}"
        df[col] = ((df[time_col] == y).astype(int) * df[treat_col]).astype(float)
        rel_terms.append(col)

    unit_d = pd.get_dummies(df[unit_col], prefix="u", drop_first=True)
    time_d = pd.get_dummies(df[time_col].astype(int), prefix="t", drop_first=True)

    X = pd.concat(
        [
            pd.Series(1.0, index=df.index, name="const"),
            df[controls + rel_terms].astype(float),
            unit_d.astype(float),
            time_d.astype(float),
        ],
        axis=1,
    )

    betas, _ = _ols_fit(pd.concat([df[[outcome]], X], axis=1), outcome, X.columns.tolist())
    coef = pd.DataFrame({"term": X.columns, "coef": betas})
    ev = coef[coef["term"].str.startswith("event_")].copy()
    ev["year"] = ev["term"].str.replace("event_", "", regex=False).astype(int)
    ev["ref_year"] = ref_year
    ev = ev[["year", "coef", "ref_year"]].sort_values("year")
    return ev


def interrupted_time_series(
    nat: pd.DataFrame,
    outcome: str = "origination_rate",
    controls: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    controls = controls or ["unemployment_rate", "fed_funds_rate", "gov_share"]

    df = nat.copy().sort_values("year")
    if "trend" not in df.columns:
        df["trend"] = df["year"] - int(df["year"].min())
    if "post_2008" not in df.columns:
        df["post_2008"] = (df["year"] >= 2008).astype(int)
    if "post_trend" not in df.columns:
        df["post_trend"] = df["post_2008"] * df["trend"]

    xcols = ["const", "trend", "post_2008", "post_trend"] + controls
    X = pd.DataFrame({"const": 1.0}, index=df.index)
    X["trend"] = df["trend"].astype(float)
    X["post_2008"] = df["post_2008"].astype(float)
    X["post_trend"] = df["post_trend"].astype(float)
    for c in controls:
        X[c] = df[c].astype(float)

    betas, fit = _ols_fit(pd.concat([df[[outcome]], X], axis=1), outcome, xcols)
    coef = pd.DataFrame({"term": xcols, "coef": betas})

    # Counterfactual paths:
    # - no SEC leverage shock: set post terms to 0
    # - no GSE housing channel: set gov_share to 0
    # - both: set both post terms and gov_share to 0
    X_cf = X.copy()
    X_cf["post_2008"] = 0.0
    X_cf["post_trend"] = 0.0
    X_no_gse = X.copy()
    if "gov_share" in X_no_gse.columns:
        X_no_gse["gov_share"] = 0.0
    X_both = X_cf.copy()
    if "gov_share" in X_both.columns:
        X_both["gov_share"] = 0.0
    beta_map = {t: b for t, b in zip(xcols, betas)}
    df["pred_observed"] = sum(X[c] * beta_map[c] for c in xcols)
    df["pred_no_sec_leverage"] = sum(X_cf[c] * beta_map[c] for c in xcols)
    df["pred_no_gse"] = sum(X_no_gse[c] * beta_map[c] for c in xcols)
    df["pred_no_gse_no_sec"] = sum(X_both[c] * beta_map[c] for c in xcols)
    df["delta_no_sec_leverage"] = df["pred_no_sec_leverage"] - df["pred_observed"]
    df["delta_no_gse"] = df["pred_no_gse"] - df["pred_observed"]
    df["delta_no_gse_no_sec"] = df["pred_no_gse_no_sec"] - df["pred_observed"]

    return coef, pd.concat([df, fit[["yhat", "resid"]]], axis=1)


ROOT = Path(__file__).resolve().parents[2]


def run_all(data_dir: str = "hmda_output") -> dict[str, str]:
    ddir = Path(data_dir)
    if not ddir.is_absolute():
        ddir = ROOT / ddir
    out_dir = ddir / "causal"
    out_dir.mkdir(parents=True, exist_ok=True)

    cdb.write_outputs(data_dir=str(ddir))
    state = pd.read_parquet(out_dir / "state_year_panel.parquet")
    nat = pd.read_parquet(out_dir / "national_year_panel.parquet")

    did_coef, did_fit = twfe_did(
        panel=state,
        outcome="log_originations",
        treat_col="high_gse_exposure",
        post_col="post_2009",
        controls=["unemployment_rate"],
    )
    did_coef["model"] = "did_gse_originations"

    ev = event_study(
        panel=state,
        outcome="log_originations",
        treat_col="high_gse_exposure",
        ref_year=2007,
        controls=["unemployment_rate"],
    )
    ev["model"] = "event_study_gse_originations"

    its_coef, its_fit = interrupted_time_series(
        nat=nat,
        outcome="origination_rate",
        controls=["unemployment_rate", "fed_funds_rate", "gov_share"],
    )
    its_coef["model"] = "its_approval_rate"

    coef_all = pd.concat([did_coef, its_coef], axis=0, ignore_index=True)

    p_coef = out_dir / "causal_coefficients.csv"
    p_event = out_dir / "causal_event_study.csv"
    p_did_fit = out_dir / "causal_did_fitted.csv"
    p_its_fit = out_dir / "causal_its_fitted.csv"

    coef_all.to_csv(p_coef, index=False)
    ev.to_csv(p_event, index=False)
    did_fit.to_csv(p_did_fit, index=False)
    its_fit.to_csv(p_its_fit, index=False)

    return {
        "coefficients": str(p_coef),
        "event_study": str(p_event),
        "did_fitted": str(p_did_fit),
        "its_fitted": str(p_its_fit),
    }


if __name__ == "__main__":
    out = run_all(str(ROOT / "hmda_output"))
    for k, v in out.items():
        print(f"{k}: {v}")
