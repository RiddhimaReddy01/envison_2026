"""
world_bank_data.py
==================
Chapter 9 global shockwave loader.

Returns a compact country summary with API/cache/backup fallback:
    load_global_shockwave_summary() -> (DataFrame, source_tag)
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple
import json
import os
import urllib.request

import pandas as pd
from paths import PROCESSED_CACHE_DIR, ensure_data_dirs


_COUNTRIES: List[Tuple[str, str, str]] = [
    ("USA", "United States", "Housing and financial contagion"),
    ("ISL", "Iceland", "Banking-system collapse"),
    ("ESP", "Spain", "Housing and banking stress"),
    ("GRC", "Greece", "Sovereign-debt stress"),
    ("JPN", "Japan", "Trade and demand shock"),
    ("CHN", "China", "Export and external-demand shock"),
]

_INDICATORS = {
    "gdp_growth_2009": "NY.GDP.MKTP.KD.ZG",      # GDP growth (annual %)
    "unemployment": "SL.UEM.TOTL.ZS",            # Unemployment (% labor force)
    "export_growth_2009": "NE.EXP.GNFS.KD.ZG",   # Exports growth (annual %)
}

_CACHE_PATH = PROCESSED_CACHE_DIR / "global_shockwave_cache.json"


def _backup_frame() -> pd.DataFrame:
    # Backup snapshot aligned to 2007-2011 interpretation window.
    rows = [
        {
            "country_code": "USA",
            "country": "United States",
            "crisis_channel": "Housing and financial contagion",
            "gdp_growth_2009": -2.6,
            "unemployment_2007": 4.6,
            "unemployment_peak": 9.6,
            "unemployment_peak_year": 2010,
            "unemployment_change_peak": 5.0,
            "export_growth_2009": -9.5,
        },
        {
            "country_code": "ISL",
            "country": "Iceland",
            "crisis_channel": "Banking-system collapse",
            "gdp_growth_2009": -6.8,
            "unemployment_2007": 2.3,
            "unemployment_peak": 7.6,
            "unemployment_peak_year": 2010,
            "unemployment_change_peak": 5.3,
            "export_growth_2009": -8.8,
        },
        {
            "country_code": "ESP",
            "country": "Spain",
            "crisis_channel": "Housing and banking stress",
            "gdp_growth_2009": -3.8,
            "unemployment_2007": 8.2,
            "unemployment_peak": 21.4,
            "unemployment_peak_year": 2011,
            "unemployment_change_peak": 13.2,
            "export_growth_2009": -11.1,
        },
        {
            "country_code": "GRC",
            "country": "Greece",
            "crisis_channel": "Sovereign-debt stress",
            "gdp_growth_2009": -4.3,
            "unemployment_2007": 8.4,
            "unemployment_peak": 17.9,
            "unemployment_peak_year": 2011,
            "unemployment_change_peak": 9.5,
            "export_growth_2009": -17.2,
        },
        {
            "country_code": "JPN",
            "country": "Japan",
            "crisis_channel": "Trade and demand shock",
            "gdp_growth_2009": -5.7,
            "unemployment_2007": 3.9,
            "unemployment_peak": 5.1,
            "unemployment_peak_year": 2009,
            "unemployment_change_peak": 1.2,
            "export_growth_2009": -24.2,
        },
        {
            "country_code": "CHN",
            "country": "China",
            "crisis_channel": "Export and external-demand shock",
            "gdp_growth_2009": 9.4,
            "unemployment_2007": 4.0,
            "unemployment_peak": 4.3,
            "unemployment_peak_year": 2009,
            "unemployment_change_peak": 0.3,
            "export_growth_2009": -10.1,
        },
    ]
    return pd.DataFrame(rows)


def _wb_indicator_series(country: str, indicator: str, start: int, end: int) -> Dict[int, float]:
    url = (
        f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
        f"?format=json&per_page=80&date={start}:{end}"
    )
    with urllib.request.urlopen(url, timeout=8) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    items = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    out: Dict[int, float] = {}
    for row in items:
        year = int(row.get("date"))
        val = row.get("value")
        if val is None:
            continue
        out[year] = float(val)
    return out


def _from_api() -> pd.DataFrame:
    rows = []
    for code, name, channel in _COUNTRIES:
        gdp = _wb_indicator_series(code, _INDICATORS["gdp_growth_2009"], 2009, 2009)
        unemp = _wb_indicator_series(code, _INDICATORS["unemployment"], 2007, 2011)
        exp = _wb_indicator_series(code, _INDICATORS["export_growth_2009"], 2009, 2009)

        u2007 = unemp.get(2007)
        peak_year = max(unemp, key=lambda yr: unemp[yr]) if unemp else None
        peak = unemp[peak_year] if peak_year is not None else None
        d_peak = (peak - u2007) if (peak is not None and u2007 is not None) else None

        rows.append({
            "country_code": code,
            "country": name,
            "crisis_channel": channel,
            "gdp_growth_2009": gdp.get(2009),
            "unemployment_2007": u2007,
            "unemployment_peak": peak,
            "unemployment_peak_year": peak_year,
            "unemployment_change_peak": d_peak,
            "export_growth_2009": exp.get(2009),
        })
    return pd.DataFrame(rows)


def _write_cache(df: pd.DataFrame) -> None:
    ensure_data_dirs()
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "rows": df.to_dict(orient="records"),
    }
    _CACHE_PATH.write_text(json.dumps(payload), encoding="utf-8")


def _read_cache() -> pd.DataFrame | None:
    if not _CACHE_PATH.exists():
        return None
    try:
        payload = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        return pd.DataFrame(payload.get("rows", []))
    except Exception:
        return None


def global_shockwave_cache_signature() -> str:
    """
    Cache-buster signature for app-level memoization.
    Changes when configured countries or local cache file mtime changes.
    """
    countries_sig = "|".join([f"{c}:{n}:{ch}" for c, n, ch in _COUNTRIES])
    mtime = "none"
    try:
        if _CACHE_PATH.exists():
            mtime = str(int(os.path.getmtime(_CACHE_PATH)))
    except Exception:
        mtime = "err"
    return f"{countries_sig}::{mtime}"


def _canonicalize(df: pd.DataFrame) -> pd.DataFrame:
    need_cols = [
        "country_code",
        "country",
        "crisis_channel",
        "gdp_growth_2009",
        "unemployment_2007",
        "unemployment_peak",
        "unemployment_peak_year",
        "unemployment_change_peak",
        "export_growth_2009",
    ]
    out = df.copy()
    for c in need_cols:
        if c not in out.columns:
            out[c] = pd.NA
    out = out[need_cols]

    # Ensure every configured country is present even if cache/API payload is stale.
    backup = _backup_frame().set_index("country_code")
    configured = {code: (name, channel) for code, name, channel in _COUNTRIES}

    if "country_code" in out.columns:
        out = out.drop_duplicates(subset=["country_code"], keep="first")
        existing = set(out["country_code"].astype(str).tolist())
    else:
        existing = set()

    missing_rows = []
    for code, (name, channel) in configured.items():
        if code in existing:
            continue
        if code in backup.index:
            row = backup.loc[code].to_dict()
            row["country_code"] = code
            missing_rows.append({c: row.get(c, pd.NA) for c in need_cols})
        else:
            missing_rows.append({
                "country_code": code,
                "country": name,
                "crisis_channel": channel,
                "gdp_growth_2009": pd.NA,
                "unemployment_2007": pd.NA,
                "unemployment_peak": pd.NA,
                "unemployment_peak_year": pd.NA,
                "unemployment_change_peak": pd.NA,
                "export_growth_2009": pd.NA,
            })

    if missing_rows:
        out = pd.concat([out, pd.DataFrame(missing_rows)], ignore_index=True)

    # Fill key identity fields from configured mapping if missing.
    for code, (name, channel) in configured.items():
        m = out["country_code"] == code
        out.loc[m & out["country"].isna(), "country"] = name
        out.loc[m & out["crisis_channel"].isna(), "crisis_channel"] = channel

    out = out.sort_values("gdp_growth_2009", ascending=True, na_position="last")
    out = out.reset_index(drop=True)
    return out


def load_global_shockwave_summary() -> Tuple[pd.DataFrame, str]:
    # Fast path: local cache first for low-latency page loads.
    cache_df = _read_cache()
    if cache_df is not None and not cache_df.empty:
        return _canonicalize(cache_df), "cache"

    # If cache unavailable, try live API and persist.
    try:
        api_df = _from_api()
        api_df = _canonicalize(api_df)
        _write_cache(api_df)
        return api_df, "api"
    except Exception:
        pass

    # Final fallback snapshot.
    return _canonicalize(_backup_frame()), "backup"
