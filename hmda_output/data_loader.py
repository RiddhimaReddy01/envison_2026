"""
data_loader.py
==============
Single source of truth for all chart data.
Set USE_REAL_DATA = True once hmda_pipeline.py finishes.
Every chart function stays identical — only the source changes.
"""

import os
import polars as pl

# ─────────────────────────────────────────────
# TOGGLE — flip this ONE line when data arrives
# ─────────────────────────────────────────────
USE_REAL_DATA = True   

DATA_DIR = "./hmda_output"

# ─────────────────────────────────────────────
import mock_data as mock

def _real_available():
    return os.path.exists(f"{DATA_DIR}/hmda_aggregates.parquet")


def _load(fname):
    path = f"{DATA_DIR}/{fname}"
    if not os.path.exists(path):
        return None
    return pl.read_parquet(path)


# ─────────────────────────────────────────────
# PUBLIC API — one function per chart
# ─────────────────────────────────────────────

def collapse_data():
    """Ch 2: Applications vs Originations by year"""
    if USE_REAL_DATA and _real_available():
        agg = _load("hmda_aggregates.parquet")
        apps = (
            agg.group_by("as_of_year")
            .agg(pl.col("n_records").sum().alias("applications"))
        )
        orig = (
            agg.filter(pl.col("action_taken") == 1)
            .group_by("as_of_year")
            .agg(pl.col("n_records").sum().alias("originations"))
        )
        df = apps.join(orig, on="as_of_year").sort("as_of_year")
        df = df.with_columns([
            (pl.col("applications") - pl.col("originations")).alias("denied"),
            (pl.col("originations") / pl.col("applications")).alias("origination_rate"),
        ])
        return df.rename({"as_of_year": "year"})
    return mock.get_collapse_data()


def loan_type_share():
    """Ch 3: FHA / Conventional / VA / FSA share by year"""
    if USE_REAL_DATA and _real_available():
        agg = _load("hmda_aggregates.parquet")
        df = (
            agg.filter(pl.col("action_taken") == 1)
            .group_by(["as_of_year", "loan_type_label"])
            .agg(pl.col("n_records").sum().alias("count"))
        )
        totals = df.group_by("as_of_year").agg(pl.col("count").sum().alias("total"))
        df = df.join(totals, on="as_of_year")
        df = df.with_columns(
            (pl.col("count") / pl.col("total")).alias("share")
        )
        return df.rename({"as_of_year": "year", "loan_type_label": "loan_type"})
    return mock.get_loan_type_share()


def purchase_refi():
    """Ch 4: Purchase vs Refinance volume by year"""
    if USE_REAL_DATA and _real_available():
        agg = _load("hmda_aggregates.parquet")
        df = (
            agg.filter(pl.col("action_taken") == 1)
            .group_by(["as_of_year", "loan_purpose_label"])
            .agg(pl.col("n_records").sum().alias("count"))
        )
        purchase = df.filter(pl.col("loan_purpose_label") == "Purchase").rename({"count": "purchase"})
        refi = df.filter(pl.col("loan_purpose_label") == "Refinance").rename({"count": "refinance"})
        out = purchase.join(refi.select(["as_of_year", "refinance"]), on="as_of_year")
        out = out.with_columns([
            (pl.col("purchase") + pl.col("refinance")).alias("total"),
            (pl.col("purchase") / (pl.col("purchase") + pl.col("refinance"))).alias("purchase_pct"),
        ])
        return out.rename({"as_of_year": "year"})
    return mock.get_purchase_refi()


def lti_sample():
    """Ch 4: Loan-to-income ratio sample for violin/distribution"""
    if USE_REAL_DATA and _real_available():
        df = _load("hmda_sample.parquet")
        if df is not None:
            return df.rename({"as_of_year": "year"}) if "as_of_year" in df.columns else df
    return mock.get_lti_sample()


def rvs_scores():
    """Ch 5: Recovery Velocity Score per state"""
    if USE_REAL_DATA and _real_available():
        df = _load("rvs_by_state.parquet")
        if df is not None:
            return df.rename({"state_code": "state"}) if "state_code" in df.columns else df
    return mock.get_rvs_data()


def state_year_originations():
    """Ch 5: State origination volume by year for animated map"""
    if USE_REAL_DATA and _real_available():
        agg = _load("rvs_full.parquet")
        if agg is not None:
            return agg.rename({"state_code": "state", "as_of_year": "year"})
    return mock.get_state_year_originations()


def msa_scissor():
    """Ch 5: Median loan/income ratio per MSA per year"""
    if USE_REAL_DATA and _real_available():
        df = _load("msa_scissor.parquet")
        if df is not None:
            return df.rename({"as_of_year": "year"}) if "as_of_year" in df.columns else df
    return mock.get_msa_scissor()


def denial_rates():
    """Ch 6: Denial rate by income band × race × year"""
    if USE_REAL_DATA and _real_available():
        agg = _load("hmda_aggregates.parquet")
        total = (
            agg.group_by(["as_of_year", "income_band", "race_label"])
            .agg(pl.col("n_records").sum().alias("applications"))
        )
        denied = (
            agg.filter(pl.col("action_taken") == 3)
            .group_by(["as_of_year", "income_band", "race_label"])
            .agg(pl.col("n_records").sum().alias("denied_count"))
        )
        df = total.join(denied, on=["as_of_year", "income_band", "race_label"], how="left")
        df = df.with_columns(
            (pl.col("denied_count") / pl.col("applications")).alias("denial_rate")
        )
        return df.rename({"as_of_year": "year", "race_label": "race"})
    return mock.get_denial_rates()


def moderate_income_denial():
    """Ch 6: Credit desert — $50-80K income band denial rate vs unemployment"""
    if USE_REAL_DATA and _real_available():
        agg = _load("hmda_aggregates.parquet")
        band = (
            agg.filter(pl.col("income_band") == "50-80K")
            .group_by("as_of_year")
            .agg([
                pl.col("n_records").sum().alias("applications"),
                pl.col("n_records").filter(pl.col("action_taken") == 3).sum().alias("denied"),
            ])
            .with_columns(
                (pl.col("denied") / pl.col("applications")).alias("denial_rate_moderate_income")
            )
        )
        ext = pl.read_csv(f"{DATA_DIR}/external_overlays.csv")
        return band.join(ext.rename({"year": "as_of_year"}), on="as_of_year").rename({"as_of_year": "year"})
    return mock.get_moderate_income_denial()


def purchase_homeownership():
    """Ch 6: Purchase originations vs Census homeownership rate"""
    if USE_REAL_DATA and _real_available():
        purchase = (
            _load("hmda_aggregates.parquet")
            .filter((pl.col("action_taken") == 1) & (pl.col("loan_purpose_label") == "Purchase"))
            .group_by("as_of_year")
            .agg(pl.col("n_records").sum().alias("purchase_originations"))
        )
        ext = pl.read_csv(f"{DATA_DIR}/external_overlays.csv")
        return purchase.join(ext.rename({"year": "as_of_year"}), on="as_of_year").rename({"as_of_year": "year"})
    return mock.get_purchase_homeownership()


def lender_bubble():
    """Ch 7: Top lender origination volumes animated by year"""
    if USE_REAL_DATA and _real_available():
        df = _load("lender_names.parquet")
        if df is not None:
            top = (
                df.group_by("institution_name")
                .agg(pl.col("originations").sum())
                .sort("originations", descending=True)
                .head(25)
            )
            result = df.filter(pl.col("institution_name").is_in(top["institution_name"]))
            return result.rename({"as_of_year": "year", "institution_name": "institution"})
    return mock.get_lender_bubble()


def exec_kpis():
    """Ch 7: Executive summary KPI values"""
    return mock.get_exec_kpis()  # always use computed values


def scoping_sankey():
    """Ch 1: Data scoping Sankey"""
    return mock.get_scoping_sankey()  # structural — same with real data