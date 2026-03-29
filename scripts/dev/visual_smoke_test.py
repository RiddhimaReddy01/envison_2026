"""
Quick non-UI smoke test for data loaders, chart builders, and page constructors.

Usage:
    python visual_smoke_test.py
"""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app


def _run(name, fn, failures):
    try:
        out = fn()
        print(f"[OK]   {name}: {type(out).__name__}")
    except Exception as exc:
        failures.append((name, exc))
        print(f"[FAIL] {name}: {type(exc).__name__}: {exc}")


def main() -> int:
    failures = []

    # Cached dataframe loaders
    _run("_df_collapse", app._df_collapse, failures)
    _run("_df_loan_type_share", app._df_loan_type_share, failures)
    _run("_df_purchase_refi", app._df_purchase_refi, failures)
    _run("_df_lti_sample", app._df_lti_sample, failures)
    _run("_df_rvs_scores", app._df_rvs_scores, failures)
    _run("_df_state_year_originations", app._df_state_year_originations, failures)
    _run("_df_msa_scissor", app._df_msa_scissor, failures)
    _run("_df_denial_rates", app._df_denial_rates, failures)
    _run("_df_origination_share_by_race", app._df_origination_share_by_race, failures)
    _run("_df_moderate_income_denial", app._df_moderate_income_denial, failures)
    _run("_df_purchase_homeownership", app._df_purchase_homeownership, failures)
    _run("_df_lender_bubble", app._df_lender_bubble, failures)

    # Page constructors
    _run("p1", lambda: app.p1("civilian"), failures)
    _run("p2", lambda: app.p2("civilian"), failures)
    _run("p3", lambda: app.p3("civilian"), failures)
    _run("p4", lambda: app.p4("civilian"), failures)
    _run("p5", lambda: app.p5("civilian"), failures)
    _run("p6", lambda: app.p6("civilian"), failures)
    _run("p7", lambda: app.p7("civilian"), failures)
    _run("p8", lambda: app.p8("civilian"), failures)
    _run("p9", lambda: app.p9("civilian"), failures)

    # Callback figure builders
    _run("fha_chart", lambda: app.fha_chart("All states"), failures)
    _run("map_chart", lambda: app.map_chart(2017), failures)
    _run("bubble_chart", lambda: app.bubble_chart(2017), failures)

    if failures:
        print("\n--- Failures ---")
        for name, exc in failures:
            print(f"\n{name}")
            traceback.print_exception(type(exc), exc, exc.__traceback__)
        return 1

    print("\nAll smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
