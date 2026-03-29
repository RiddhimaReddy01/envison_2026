"""
patch_denials.py — Envision Hackathon 2026
==========================================
The existing hmda_aggregates.parquet only contains action_taken=1 (originated).
This script re-downloads each year's LAR ZIP, extracts ONLY the denied (3) and
approved-not-accepted (2) rows, aggregates them, and merges into the existing file.

What it skips (already correct):
    hmda_sample.parquet     -- LTI sample only needs originated loans
    lender_names.parquet    -- lender bubble only needs originated loans
    rvs_full/by_state       -- recovery metric only needs originated loans

What it fixes:
    hmda_aggregates.parquet -- adds action_taken 2 and 3 rows so that
                               origination rates and denial rates are real

Run:
    python patch_denials.py            # all 10 existing years
    python patch_denials.py 2009 2010  # retry specific years
"""

import io, sys, time, zipfile, requests, polars as pl
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "processed" / "parquet"
AGG_FILE   = OUTPUT_DIR / "hmda_aggregates.parquet"

MAX_WORKERS = 1   # 1 year at a time — each decompressed CSV is 2-4GB

LAR_BASE = "https://files.consumerfinance.gov/hmda-historic-loan-data"

def lar_url(y):
    # 2012 labeled file is missing from CFPB; use the codes (positional) file instead
    if y == 2012:
        return (f"{LAR_BASE}/hmda_{y}_nationwide"
                "_first-lien-owner-occupied-1-4-family-records_codes.zip")
    return (f"{LAR_BASE}/hmda_{y}_nationwide"
            "_first-lien-owner-occupied-1-4-family-records_labels.zip")

FILE_MB = {
    2007:453, 2008:331, 2009:467, 2010:455, 2011:399,
    2012:190, 2013:492, 2014:323, 2015:486, 2016:483, 2017:370,
}

# Column aliases — same as main pipeline
ALIASES = {
    "state_code":            ["state_code", "state_abbr", "state"],
    "applicant_race_label":  ["applicant_race_name_1", "applicant_race_1"],
    "loan_type":             ["loan_type", "loan_type_code"],
    "loan_purpose":          ["loan_purpose", "loan_purpose_code"],
    "action_taken":          ["action_taken", "action_taken_type"],
    "applicant_income_000s": ["applicant_income_000s", "income"],
}

# Only the columns we need for the denial aggregate
NEED = [
    "as_of_year", "state_code", "action_taken",
    "loan_type", "loan_purpose", "applicant_race_label",
    "applicant_income_000s",   # for income_band
]

LOAN_PURPOSE_TEXT_MAP = {
    # Labels files may encode these as text
    "Purchase":                 "1",
    "Home improvement":         "2",
    "Home Improvement":         "2",
    "Refinancing":              "3",
    "Refinance":                "3",
    "Multi-family dwelling":    "4",
    "Multi Family":             "4",
}

ACTION_TAKEN_TEXT_MAP = {
    "Loan originated":                                          "1",
    "Application approved but not accepted":                    "2",
    "Application denied by financial institution":              "3",
    "Application withdrawn by applicant":                       "4",
    "File closed for incompleteness":                           "5",
    "Loan purchased by the institution":                        "6",
    "Preapproval request denied by financial institution":      "7",
    "Preapproval request approved but not accepted":            "8",
}

RACE_MAP = {
    # Numeric codes (older files)
    "1": "American Indian",
    "2": "Asian",
    "3": "Black / African American",
    "4": "Pacific Islander",
    "5": "White",
    "6": "Not provided",
    "7": "Not applicable",
    # Label variants — all collapse to canonical short labels
    "American Indian Or Alaska Native":        "American Indian",
    "American Indian or Alaska Native":        "American Indian",
    "Black Or African American":               "Black / African American",
    "Black or African American":               "Black / African American",
    "Black":                                   "Black / African American",
    "Native Hawaiian Or Other Pacific Islander": "Pacific Islander",
    "Native Hawaiian or Other Pacific Islander": "Pacific Islander",
    "Information Not Provided By Applicant In Mail, Internet, Or Telephone Application":
        "Not provided",
    "Information not provided by applicant in mail, Internet, or telephone application":
        "Not provided",
    "Not Applicable": "Not applicable",
}


def log(msg, lvl="  "):
    m = {"OK": "OK  ", "ERR": "ERR ", "WARN": "WARN", "HEAD": "\n >> "}
    print(f"[{time.strftime('%H:%M:%S')}] {m.get(lvl,'    ')}{msg}", flush=True)


def download(url, expected_mb=0, retries=3, timeout=600):
    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, stream=True, timeout=timeout) as r:
                if r.status_code == 404:
                    return None
                r.raise_for_status()
                total = int(r.headers.get("Content-Length", expected_mb * 1e6))
                buf   = io.BytesIO()
                recv  = 0
                for chunk in r.iter_content(1 << 20):
                    buf.write(chunk)
                    recv += len(chunk)
                    if total:
                        print(f"\r      {recv/1e6:.0f}/{total/1e6:.0f}MB "
                              f"({recv/total*100:.0f}%)   ", end="", flush=True)
                print()
                buf.seek(0)
                return buf
        except requests.Timeout:
            log(f"Timeout attempt {attempt}/{retries}", "WARN")
            time.sleep(5 * attempt)
        except Exception as e:
            if attempt == retries:
                log(f"Download failed: {e}", "ERR")
                return None
            time.sleep(3)
    return None


def resolve(cols, key):
    idx = {c.lower(): c for c in cols}
    for c in ALIASES.get(key, [key]):
        if c in cols:        return c
        if c.lower() in idx: return idx[c.lower()]
    return None


def fetch_denial_agg(year):
    """
    Download year LAR, keep ONLY action_taken in (2, 3).
    Returns a small aggregated DataFrame or None on failure.
    """
    t0 = time.time()
    log(f"Year {year}  downloading {FILE_MB.get(year,400)}MB ...")
    buf = download(lar_url(year), expected_mb=FILE_MB.get(year, 400))
    if buf is None:
        log(f"Year {year}  not found (404)", "WARN")
        return {"year": year, "ok": False, "agg": None}

    try:
        with zipfile.ZipFile(buf) as z:
            raw = z.read(z.namelist()[0])
        del buf
    except Exception as e:
        log(f"Year {year}  unzip failed: {e}", "ERR")
        return {"year": year, "ok": False, "agg": None}

    log(f"Year {year}  parsing {len(raw)/1e6:.0f}MB ...")
    try:
        first = raw.split(b"\n")[0].decode("latin-1", errors="replace")
        sep   = "|" if first.count("|") > first.count(",") else ","
        header_cols = first.split(sep)

        # Resolve column names
        wanted = []
        canon  = {}
        for key in NEED:
            actual = resolve(header_cols, key)
            if actual:
                wanted.append(actual)
                if actual != key:
                    canon[actual] = key

        df = pl.read_csv(
            io.BytesIO(raw),
            separator=sep, has_header=True,
            columns=wanted,
            infer_schema_length=2000,
            ignore_errors=True,
            truncate_ragged_lines=True,
            encoding="utf8-lossy",
        )
        del raw

        if canon:
            df = df.rename(canon)

        # Ensure as_of_year
        if "as_of_year" not in df.columns:
            df = df.with_columns(pl.lit(year).alias("as_of_year"))

        # Normalise text-label columns to numeric strings before casting
        if "loan_purpose" in df.columns:
            df = df.with_columns(
                pl.col("loan_purpose").cast(pl.Utf8, strict=False)
                  .replace(LOAN_PURPOSE_TEXT_MAP)
                  .alias("loan_purpose")
            )
        if "action_taken" in df.columns:
            df = df.with_columns(
                pl.col("action_taken").cast(pl.Utf8, strict=False)
                  .replace(ACTION_TAKEN_TEXT_MAP)
                  .alias("action_taken")
            )

        # Cast types
        for c in ["action_taken", "loan_type", "loan_purpose"]:
            if c in df.columns:
                df = df.with_columns(pl.col(c).cast(pl.Int32, strict=False))
        if "applicant_income_000s" in df.columns:
            df = df.with_columns(
                pl.col("applicant_income_000s").cast(pl.Float64, strict=False)
            )

        # Keep ONLY denied (3) and approved-not-accepted (2)
        # Also filter to purchase + refi only (same as main pipeline)
        df = df.filter(
            pl.col("action_taken").is_in([2, 3]) &
            pl.col("loan_purpose").is_in([1, 3])
        )

        if len(df) == 0:
            log(f"Year {year}  no denial rows found", "WARN")
            return {"year": year, "ok": False, "agg": None}

        # Normalise race labels to match existing agg
        if "applicant_race_label" in df.columns:
            df = df.with_columns(
                pl.col("applicant_race_label")
                  .cast(pl.Utf8, strict=False)
                  .replace(RACE_MAP)
                  .alias("applicant_race_label")
            )

        # Income band (matches main pipeline exactly)
        if "applicant_income_000s" in df.columns:
            df = df.with_columns(
                pl.when(pl.col("applicant_income_000s") <  50).then(pl.lit("<50K"))
                  .when(pl.col("applicant_income_000s") <  80).then(pl.lit("50-80K"))
                  .when(pl.col("applicant_income_000s") < 100).then(pl.lit("80-100K"))
                  .when(pl.col("applicant_income_000s") < 150).then(pl.lit("100-150K"))
                  .otherwise(pl.lit("150K+")).alias("income_band")
            )

        # Aggregate — same groupby as main pipeline
        gcols = [c for c in [
            "as_of_year", "state_code", "action_taken",
            "loan_type", "loan_purpose", "applicant_race_label", "income_band",
        ] if c in df.columns]

        agg = df.group_by(gcols).agg(pl.len().alias("n_records"))

        # Add label columns (same logic as main pipeline save())
        agg = agg.with_columns([
            pl.when(pl.col("action_taken") == 2).then(pl.lit("Approved Not Accepted"))
              .when(pl.col("action_taken") == 3).then(pl.lit("Denied"))
              .otherwise(pl.lit("Other")).alias("action_label"),
            pl.when(pl.col("loan_type") == 1).then(pl.lit("Conventional"))
              .when(pl.col("loan_type") == 2).then(pl.lit("FHA"))
              .when(pl.col("loan_type") == 3).then(pl.lit("VA"))
              .when(pl.col("loan_type") == 4).then(pl.lit("FSA/RHS"))
              .otherwise(pl.lit("Unknown")).alias("loan_type_label"),
            pl.when(pl.col("loan_purpose") == 1).then(pl.lit("Purchase"))
              .when(pl.col("loan_purpose") == 3).then(pl.lit("Refinance"))
              .otherwise(pl.lit("Other")).alias("loan_purpose_label"),
        ])

        n_denied = int(df.filter(pl.col("action_taken") == 3)["action_taken"].len())
        log(f"Year {year}  {n_denied:,} denials  agg={len(agg):,} rows  "
            f"{time.time()-t0:.0f}s", "OK")
        return {"year": year, "ok": True, "agg": agg}

    except Exception as e:
        log(f"Year {year}  parse error: {e}", "ERR")
        return {"year": year, "ok": False, "agg": None}


def merge_into_aggregates(new_results):
    """
    Splice new denial rows into the existing hmda_aggregates.parquet.
    Strips any existing rows for the patched years first (idempotent).
    """
    ok        = [r for r in new_results if r["ok"]]
    new_years = {r["year"] for r in ok}

    if not ok:
        log("No successful years — nothing to merge.", "WARN")
        return

    new_agg = pl.concat([r["agg"] for r in ok], how="diagonal")

    existing = pl.read_parquet(AGG_FILE)

    # Cast new rows to match the exact dtypes of the existing file
    for col, dtype in zip(existing.columns, existing.dtypes):
        if col in new_agg.columns and new_agg[col].dtype != dtype:
            new_agg = new_agg.with_columns(
                pl.col(col).cast(dtype, strict=False)
            )

    # Remove any prior denial rows for these years (makes patch idempotent)
    existing_clean = existing.filter(
        ~(pl.col("as_of_year").is_in(new_years) & pl.col("action_taken").is_in([2, 3]))
    )

    merged = pl.concat([existing_clean, new_agg], how="diagonal").sort(
        ["as_of_year", "action_taken"]
    )
    merged.write_parquet(AGG_FILE, compression="snappy")

    log(f"hmda_aggregates.parquet  {AGG_FILE.stat().st_size/1e6:.1f}MB  "
        f"{len(merged):,} rows  (was {len(existing):,})", "OK")

    # Quick sanity check
    at_counts = (merged.group_by("action_taken")
                       .agg(pl.col("n_records").sum())
                       .sort("action_taken"))
    log("action_taken distribution after patch:", "OK")
    for row in at_counts.iter_rows():
        label = {1: "Originated", 2: "Approved Not Accepted", 3: "Denied"}.get(row[0], "?")
        log(f"  action_taken={row[0]} ({label}): {row[1]:,} records")


def run(years=None):
    if not AGG_FILE.exists():
        print("ERROR: hmda_aggregates.parquet not found — run the main pipeline first.")
        sys.exit(1)

    existing_agg  = pl.read_parquet(AGG_FILE)
    existing_years = sorted(existing_agg["as_of_year"].unique().to_list())

    # Only patch years that are missing action_taken 2 or 3
    if years is None:
        patched = set(
            existing_agg.filter(pl.col("action_taken").is_in([2, 3]))
            ["as_of_year"].unique().to_list()
        )
        years_needing_patch = [y for y in existing_years if y not in patched]
        if not years_needing_patch:
            log("All years already have denial rows — nothing to do.", "OK")
            return
        target = years_needing_patch
    else:
        target = years

    log("DENIAL PATCH PIPELINE  --  Envision Hackathon 2026", "HEAD")
    log(f"Patching years: {target}  (missing action_taken 2/3)")
    log(f"Workers: {min(MAX_WORKERS, len(target))}")
    log(f"Downloads: ~{sum(FILE_MB.get(y,400) for y in target)/1024:.1f}GB  "
        f"(same ZIPs, only denied rows kept)")

    results = []
    workers = min(MAX_WORKERS, len(target))

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_denial_agg, y): y for y in target}
        for f in as_completed(futures):
            y = futures[f]
            try:
                results.append(f.result())
            except Exception as e:
                log(f"Worker crashed year {y}: {e}", "ERR")
                results.append({"year": y, "ok": False, "agg": None})

    results.sort(key=lambda r: r["year"])
    merge_into_aggregates(results)

    failed = [r["year"] for r in results if not r["ok"]]
    if failed:
        yrs = " ".join(str(y) for y in sorted(failed))
        print(f"\n  Failed years: {sorted(failed)}")
        print(f"  Retry:  python patch_denials.py {yrs}\n")
    else:
        print(f"\n  All {len(target)} years patched successfully.")
        print("  Ch2 origination rates and Ch6 denial charts now have real data.\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and all(a.isdigit() for a in args):
        run(years=[int(a) for a in args])
    else:
        run()
