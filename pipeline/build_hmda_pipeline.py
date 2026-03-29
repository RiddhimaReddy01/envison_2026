"""
HMDA Complete Pipeline ? Envision Hackathon 2026
================================================
Downloads, processes, and aggregates HMDA data 2007-2017.
Produces 7 output files from ~25GB of raw nationwide data.

Source: https://www.consumerfinance.gov/data-research/hmda/historic-data/

File formats (verified from CFPB data dictionary PDFs):
  LAR  : comma-separated, labeled _labels.zip adds header + _name columns
  TS   : tab-delimited, NO header, 22 positional columns:
           [0] Activity Year  [1] Respondent-ID  [2] Agency Code
           [3] Fed Tax ID     [4] Respondent Name (TS)  [7] State (TS)

Run:
    pip install polars pyarrow requests psutil
    python data_ingestion.py

Outputs (./hmda_output/):
    hmda_aggregates.parquet  ? count charts         (Ch 1-7)
    hmda_sample.parquet      ? 10% row sample        (Ch 4 violin, Ch 5 scissor)
    rvs_by_state.parquet     ? Recovery Velocity Score
    rvs_full.parquet         ? year-by-year recovery
    msa_scissor.parquet      ? MSA loan/income heatmap
    lender_names.parquet     ? respondent ? institution name
    external_overlays.csv    ? homeownership, Fed rate, unemployment
"""

import io
import os
import time
import threading
import zlib
import zipfile
from pathlib import Path

import requests
import polars as pl
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("  [WARN] psutil not installed ? pip install psutil for dynamic memory management")

# ?????????????????????????????????????????????????????????????????????????????
# CONFIGURATION
# ?????????????????????????????????????????????????????????????????????????????

TARGET_STATES = ["CA", "FL", "NV", "AZ", "TX", "CO", "WA", "MI", "OH", "NY", "IL"]
YEARS         = list(range(2007, 2018))
PROJECT_ROOT  = Path(__file__).resolve().parents[1]
OUTPUT_DIR    = str(PROJECT_ROOT / "hmda_output")

# Verified URLs from https://www.consumerfinance.gov/data-research/hmda/historic-data/
LAR_URL = (
    "https://files.consumerfinance.gov/hmda-historic-loan-data/"
    "hmda_{year}_nationwide_first-lien-owner-occupied-1-4-family-records_labels.zip"
)
TS_URL = (
    "https://files.consumerfinance.gov/hmda-historic-institution-data/"
    "hmda_{year}_transmittal_sheet.zip"
)

SAMPLE_FRACTION   = 0.10
RANDOM_SEED       = 42
MAX_LTI           = 20.0
OS_RESERVE_GB     = 1.0    # RAM kept free for OS + other processes
RAM_PER_WORKER_GB = 1.0    # conservative peak per nationwide file (200MB?800MB typical)

# ?????????????????????????????????????????????????????????????????????????????
# KNOWN SCHEMAS (from CFPB data dictionary PDFs)
# ?????????????????????????????????????????????????????????????????????????????

# TS: tab-delimited, NO header ? positional columns (0-indexed, confirmed from PDF)
TS_COL_YEAR   = 0   # Activity Year
TS_COL_RESP   = 1   # Respondent-ID
TS_COL_AGENCY = 2   # Agency Code
TS_COL_NAME   = 4   # Respondent Name (TS)

# LAR labeled file: comma-separated, has header.
# Candidate column names for each logical field ? probe fills in the exact names;
# these are the fallback priority lists used when probe returns None.
LAR_CANDIDATES = {
    "state":        ["state_abbr", "state_code", "state"],
    "year":         ["as_of_year", "activity_year"],
    "respondent":   ["respondent_id"],
    "agency":       ["agency_code"],
    "msa":          ["msa_md"],
    "action":       ["action_taken", "action_type"],
    "loan_type":    ["loan_type"],
    "loan_purpose": ["loan_purpose"],
    "income":       ["applicant_income_000s"],
    "amount":       ["loan_amount_000s"],
    "race":         ["applicant_race_name_1", "applicant_race_1"],
    "lien":         ["lien_status"],
    "property":     ["property_type"],
}

# FIPS state code ? 2-letter abbreviation for TARGET_STATES.
# Used when state_code contains "06" (FIPS) instead of "CA" (abbreviation).
FIPS_TO_ABBR = {
    "06": "CA", "12": "FL", "32": "NV", "04": "AZ",
    "48": "TX", "08": "CO", "53": "WA", "26": "MI",
    "39": "OH", "36": "NY", "17": "IL",
}

RACE_LABELS = {
    1: "American Indian / Alaska Native",
    2: "Asian",
    3: "Black / African American",
    4: "Native Hawaiian / Pacific Islander",
    5: "White",
    6: "Information not provided",
    7: "Not applicable",
}

EXTERNAL_DATA = {
    "year":               [2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017],
    "homeownership_rate": [68.1, 67.8, 67.4, 66.9, 66.1, 65.4, 65.1, 64.5, 63.7, 63.5, 63.9],
    "fed_funds_rate_avg": [5.02, 1.93, 0.24, 0.18, 0.10, 0.14, 0.11, 0.09, 0.13, 0.40, 1.00],
    "unemployment_rate":  [4.6,  5.8,  9.3,  9.6,  8.9,  8.1,  7.4,  6.2,  5.3,  4.9,  4.4],
}

# ?????????????????????????????????????????????????????????????????????????????
# UTILITIES
# ?????????????????????????????????????????????????????????????????????????????

def log(msg, level="INFO"):
    prefix = {"INFO": "  ", "OK": "OK ", "WARN": "!! ", "ERR": "XX ", "HEAD": "\n>>"}
    print(f"{prefix.get(level, '  ')}{msg}", flush=True)


def add_income_band(df):
    return df.with_columns(
        pl.when(pl.col("applicant_income_000s") < 50).then(pl.lit("<50K"))
          .when(pl.col("applicant_income_000s") < 80).then(pl.lit("50-80K"))
          .when(pl.col("applicant_income_000s") < 100).then(pl.lit("80-100K"))
          .when(pl.col("applicant_income_000s") < 150).then(pl.lit("100-150K"))
          .otherwise(pl.lit("150K+"))
          .alias("income_band")
    )


def resolve_col(candidates, actual_cols):
    """Return the first candidate present in actual_cols (case-insensitive)."""
    lower_map = {c.lower(): c for c in actual_cols}
    for cand in candidates:
        hit = lower_map.get(cand.lower())
        if hit:
            return hit
    return None


# ?????????????????????????????????????????????????????????????????????????????
# SCHEMA PROBE ? HTTP Range + zlib, ~64 KB downloaded, no full file needed
# ?????????????????????????????????????????????????????????????????????????????

def probe_lar_header(year=2017, chunk=65_536):
    """
    Fetch the first 64 KB of the zip and decompress just enough bytes to read
    the CSV header row.  Avoids downloading the full file (200 MB ? 1 GB).

    Returns (col_map dict, separator str) where col_map maps logical key ?
    actual column name.  Returns ({}, ',') on any failure.
    """
    url = LAR_URL.format(year=year)
    log(f"Probing LAR schema from {year} via HTTP Range (~{chunk//1024}KB)...")
    try:
        r = requests.get(url, headers={"Range": f"bytes=0-{chunk - 1}"}, timeout=30)
        if r.status_code not in (200, 206):
            log(f"  Server returned HTTP {r.status_code} ? Range not supported", "WARN")
            return {}, ","

        data = r.content

        # ?? Parse ZIP local-file header (PKZIP spec) ????????????????
        if data[:4] != b"PK\x03\x04":
            log("  Chunk does not begin with ZIP signature", "WARN")
            return {}, ","

        compression = int.from_bytes(data[8:10],  "little")   # 0=stored, 8=deflate
        fname_len   = int.from_bytes(data[26:28], "little")
        extra_len   = int.from_bytes(data[28:30], "little")
        data_start  = 30 + fname_len + extra_len
        compressed  = data[data_start:]

        if compression == 0:
            # Stored ? raw bytes immediately follow the local header
            first_line_bytes = compressed.split(b"\n")[0]
        elif compression == 8:
            # Raw DEFLATE ? decompress incrementally.
            # decompressobj returns however many bytes it can decode from the
            # partial chunk; it does NOT raise on a truncated stream.
            decompressor     = zlib.decompressobj(-zlib.MAX_WBITS)
            decompressed     = decompressor.decompress(compressed)
            first_line_bytes = decompressed.split(b"\n")[0]
        else:
            log(f"  Unknown ZIP compression method {compression}", "WARN")
            return {}, ","

        first_line = first_line_bytes.decode("utf-8", errors="replace").strip()
        if not first_line:
            log("  Empty first line in probed chunk", "WARN")
            return {}, ","

        # ?? Auto-detect separator ???????????????????????????????????
        counts = {"|": first_line.count("|"), ",": first_line.count(","), "\t": first_line.count("\t")}
        sep    = max(counts, key=counts.get)
        cols   = [c.strip().strip('"') for c in first_line.split(sep)]

        # If first token is a year number the file has no header row
        if cols[0].isdigit():
            log(f"  Labeled file has NO header (first token = '{cols[0]}')", "WARN")
            return {}, sep

        # ?? Build col_map: logical key ? actual column name ?????????
        col_map = {}
        for key, candidates in LAR_CANDIDATES.items():
            hit = resolve_col(candidates, cols)
            if hit:
                col_map[key] = hit

        log(
            f"  {len(cols)} columns detected, sep='{sep}' ? "
            f"state='{col_map.get('state')}', action='{col_map.get('action')}', "
            f"race='{col_map.get('race')}'",
            "OK"
        )
        return col_map, sep

    except Exception as e:
        log(f"  Probe failed: {e}", "WARN")
        return {}, ","


# ?????????????????????????????????????????????????????????????????????????????
# DYNAMIC MEMORY MANAGEMENT
# ?????????????????????????????????????????????????????????????????????????????

def compute_max_workers():
    """
    Derive safe parallel-worker count from available RAM.

    Each worker holds one decompressed nationwide LAR file.
    Typical uncompressed size: 200 MB (trough years) ? 800 MB (peak years).
    We budget RAM_PER_WORKER_GB (1 GB) per worker to be safe.
    Capped at 4 ? beyond that network I/O becomes the bottleneck anyway.
    """
    if not HAS_PSUTIL:
        log("psutil unavailable ? defaulting to 2 workers", "WARN")
        return 2
    avail_gb  = psutil.virtual_memory().available / 1e9
    usable_gb = max(0.0, avail_gb - OS_RESERVE_GB)
    workers   = max(1, min(4, int(usable_gb / RAM_PER_WORKER_GB)))
    log(
        f"RAM available: {avail_gb:.1f} GB  "
        f"({OS_RESERVE_GB} GB reserved) ? {workers} parallel workers "
        f"@ {RAM_PER_WORKER_GB} GB each"
    )
    return workers


def get_content_length(url, timeout=15):
    """HEAD request ? return Content-Length in bytes, or None if unavailable."""
    try:
        r  = requests.head(url, timeout=timeout, allow_redirects=True)
        cl = r.headers.get("Content-Length")
        return int(cl) if cl else None
    except Exception:
        return None


class MemoryGate:
    """
    Tracks bytes currently held across all workers and blocks new downloads
    when the budget would be exceeded.

    Design rule: always lets at least one worker through even if it alone
    exceeds the budget ? prevents permanent deadlock when a single file is
    larger than the total budget.
    """

    def __init__(self, max_bytes):
        self._max        = max_bytes
        self._in_flight  = 0
        self._cond       = threading.Condition(threading.Lock())

    def acquire(self, nbytes):
        with self._cond:
            while self._in_flight > 0 and self._in_flight + nbytes > self._max:
                self._cond.wait(timeout=10)
            self._in_flight += nbytes

    def release(self, nbytes):
        with self._cond:
            self._in_flight = max(0, self._in_flight - nbytes)
            self._cond.notify_all()

    @property
    def in_flight_gb(self):
        return self._in_flight / 1e9


# ?????????????????????????????????????????????????????????????????????????????
# GATED ZIP FETCH
# ?????????????????????????????????????????????????????????????????????????????

def fetch_zip_gated(url, gate, timeout=300, retries=3):
    """
    Download a zip into memory, gating on available RAM.

    1. HEAD request ? Content-Length (falls back to 500 MB estimate).
    2. gate.acquire(size) ? blocks if budget would be exceeded.
    3. Stream download into BytesIO.
    4. Returns (buf, size_bytes).  Caller must call gate.release(size_bytes)
       once the raw bytes are no longer needed.
    5. Returns (None, 0) on 404 or repeated failure; gate is released internally.
    """
    estimated = get_content_length(url) or 500_000_000
    gate.acquire(estimated)

    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, timeout=timeout, stream=True)
            if r.status_code == 404:
                gate.release(estimated)
                return None, 0
            r.raise_for_status()
            return io.BytesIO(r.content), estimated   # caller releases gate
        except requests.exceptions.Timeout:
            log(f"Timeout attempt {attempt}/{retries}: {url.split('/')[-1]}", "WARN")
            time.sleep(5 * attempt)
        except Exception as e:
            if attempt == retries:
                log(f"Download failed after {retries} attempts: {e}", "ERR")
                gate.release(estimated)
                return None, 0
            time.sleep(3)

    gate.release(estimated)
    return None, 0


# ?????????????????????????????????????????????????????????????????????????????
# PER-YEAR WORKER (runs in thread pool)
# ?????????????????????????????????????????????????????????????????????????????

def process_year(year, col_map, sep, gate):
    """
    Download and process one year's nationwide labeled LAR file.

    col_map : dict of logical_key ? actual_column_name (from probe or fallback)
    sep     : CSV separator char (',' or '|' or '\\t')
    gate    : MemoryGate ? released after raw bytes are freed

    Returns dict with keys: year, agg, sample, lender, raw_count, kept_count
    or None on failure.
    """
    url = LAR_URL.format(year=year)
    log(f"Year {year}: downloading {url.split('/')[-1]}")
    t0 = time.time()

    buf, buf_bytes = fetch_zip_gated(url, gate)
    if buf is None:
        log(f"Year {year}: not found ? skipping", "WARN")
        return None

    dl_secs = time.time() - t0

    try:
        # ── Decompress to temp file → Polars scan_csv ────────────────
        # Strategy:
        #   1. shutil.copyfileobj streams the zip entry to a temp file in 4MB
        #      chunks — never holds the full 2-5 GB decompressed content in RAM.
        #   2. pl.scan_csv on the temp file path uses Polars' Rust CSV parser
        #      (~100M rows/sec, multi-threaded) with a state predicate — 100x
        #      faster than Python csv.reader on the same 15M-row nationwide file.
        #   3. Temp file is deleted immediately after collect().
        # Peak RAM : ~600 MB compressed zip + Polars working memory (~300 MB)
        # Peak disk : ~2-5 GB per worker (temp file, deleted after use)
        import shutil, tempfile

        with zipfile.ZipFile(buf) as z:
            names     = z.namelist()
            dat_files = [n for n in names if n.lower().endswith((".dat", ".txt", ".csv", ".pipe"))]
            fname     = dat_files[0] if dat_files else names[0]
            with z.open(fname) as zf, tempfile.NamedTemporaryFile(
                suffix=".csv", delete=False, mode="wb", dir=OUTPUT_DIR
            ) as tmp:
                tmp_path = tmp.name
                shutil.copyfileobj(zf, tmp, length=4 * 1024 * 1024)   # 4MB chunks

        del buf
        gate.release(buf_bytes)

        # Resolve state column name from probe result
        state_col = col_map.get("state") or resolve_col(LAR_CANDIDATES["state"], []) or "state_abbr"

        # Lazy scan: Polars reads all 78 cols but only materialises the state filter
        lf = pl.scan_csv(
            tmp_path,
            separator=sep,
            has_header=True,
            infer_schema_length=5000,
            ignore_errors=True,
            truncate_ragged_lines=True,
            null_values=["NA", "N/A", "", " "],
        )
        df = lf.filter(pl.col(state_col).is_in(TARGET_STATES)).collect()
        os.unlink(tmp_path)   # delete temp file immediately

        # ?? Resolve column names ?????????????????????????????????????
        # col_map comes from the schema probe; resolve_col is the fallback.
        actual = df.columns

        def col(key):
            if key in col_map and col_map[key] in actual:
                return col_map[key]
            return resolve_col(LAR_CANDIDATES.get(key, []), actual)

        c_state  = col("state")
        c_year   = col("year")
        c_resp   = col("respondent")
        c_agency = col("agency")
        c_msa    = col("msa")
        c_action = col("action")
        c_ltype  = col("loan_type")
        c_lpurp  = col("loan_purpose")
        c_income = col("income")
        c_amount = col("amount")
        c_race   = col("race")

        if not c_state or not c_action:
            log(
                f"Year {year}: required columns missing. "
                f"state='{c_state}' action='{c_action}' | "
                f"first 10 cols: {actual[:10]}",
                "ERR"
            )
            return None

        # ?? State filter + FIPS normalisation ???????????????????????
        # state_code may be FIPS int-string ("06") or abbreviation ("CA").
        # Check a sample to decide, then remap if necessary.
        sample_vals = df.select(pl.col(c_state).drop_nulls().head(5)).to_series().to_list()
        if sample_vals and str(sample_vals[0]).zfill(2) in FIPS_TO_ABBR:
            df = df.with_columns(
                pl.col(c_state).cast(pl.Utf8, strict=False)
                  .str.zfill(2)
                  .replace(FIPS_TO_ABBR)
                  .alias(c_state)
            )

        df = df.filter(pl.col(c_state).is_in(TARGET_STATES))
        if len(df) == 0:
            log(f"Year {year}: zero rows for target states after state filter", "WARN")
            return None

        raw_count = len(df)

        # ?? Rename to standard internal column names ?????????????????
        renames = {
            c_state:  "state_code",
            c_msa:    "msa_md",
        }
        for src, dst in [
            (c_year,   "as_of_year"),
            (c_resp,   "respondent_id"),
            (c_agency, "agency_code"),
            (c_action, "action_taken"),
            (c_ltype,  "loan_type"),
            (c_lpurp,  "loan_purpose"),
            (c_income, "applicant_income_000s"),
            (c_amount, "loan_amount_000s"),
        ]:
            if src and src != dst:
                renames[src] = dst

        renames = {k: v for k, v in renames.items() if k and k in df.columns}
        if renames:
            # Drop any column whose name is a rename target to avoid duplicate error.
            # e.g. file has both 'state_abbr' and 'state_code'; renaming state_abbr->state_code
            # would collide with the existing state_code (FIPS int) column.
            cols_to_drop = [v for v in renames.values() if v in df.columns and v not in renames]
            if cols_to_drop:
                df = df.drop(cols_to_drop)
            df = df.rename(renames)

        # Ensure as_of_year exists even if column was missing
        if "as_of_year" not in df.columns:
            df = df.with_columns(pl.lit(year).cast(pl.Int32).alias("as_of_year"))

        # ?? Safe numeric casts ???????????????????????????????????????
        for c in ["action_taken", "loan_type", "loan_purpose", "agency_code",
                  "as_of_year", "lien_status", "property_type"]:
            if c in df.columns:
                df = df.with_columns(pl.col(c).cast(pl.Int32, strict=False))

        for c in ["loan_amount_000s", "applicant_income_000s"]:
            if c in df.columns:
                df = df.with_columns(pl.col(c).cast(pl.Float64, strict=False))

        # ?? Action + purpose filter ??????????????????????????????????
        # File is already pre-filtered (first-lien, owner-occ, 1?4 family) at source.
        df = df.filter(
            pl.col("action_taken").is_in([1, 2, 3]) &   # originated/approved-not-acc/denied
            pl.col("loan_purpose").is_in([1, 3])         # purchase or refinance
        )
        kept_count = len(df)
        log(
            f"Year {year}: {raw_count:>8,} in states ? {kept_count:>8,} after filter "
            f"({dl_secs:.0f}s dl)",
            "OK"
        )
        if kept_count == 0:
            return None

        df = add_income_band(df)

        # ?? Resolve race column after renames ????????????????????????
        # Prefer the text-label column from labeled file; fall back to numeric.
        race_col = None
        if "applicant_race_name_1" in df.columns:
            race_col = "applicant_race_name_1"
        elif c_race and c_race in df.columns:
            race_col = c_race
        elif "applicant_race_1" in df.columns:
            race_col = "applicant_race_1"

        # ?? Aggregate ????????????????????????????????????????????????
        grp = ["as_of_year", "state_code", "msa_md",
               "action_taken", "loan_type", "loan_purpose", "income_band"]
        if race_col:
            grp.append(race_col)
        grp = [c for c in grp if c in df.columns]

        agg = df.group_by(grp).agg(pl.len().alias("n_records"))

        # Normalise race to a single applicant_race_label column
        if race_col and race_col in agg.columns:
            if race_col == "applicant_race_1":
                agg = (
                    agg.with_columns(
                        pl.col("applicant_race_1")
                          .replace(RACE_LABELS)
                          .alias("applicant_race_label")
                    ).drop("applicant_race_1")
                )
            elif race_col != "applicant_race_label":
                agg = agg.rename({race_col: "applicant_race_label"})

        # ?? Lender aggregate ? FIX: join key = (respondent_id, agency_code) ??
        lender_grp = ["as_of_year", "respondent_id", "state_code", "loan_type"]
        if "agency_code" in df.columns:
            lender_grp.insert(2, "agency_code")
        lender_grp = [c for c in lender_grp if c in df.columns]

        lender_agg = (
            df.filter(pl.col("action_taken") == 1)
              .group_by(lender_grp)
              .agg(pl.len().alias("originations"))
        )

        # ?? 10% sample for distribution charts ??????????????????????
        sample_size = max(1, int(kept_count * SAMPLE_FRACTION))
        sample      = df.sample(n=sample_size, seed=RANDOM_SEED, shuffle=True)

        sample_cols = [c for c in [
            "as_of_year", "state_code", "msa_md", "income_band",
            "loan_amount_000s", "applicant_income_000s",
            "loan_type", "loan_purpose",
        ] if c in sample.columns]
        sample = (
            sample.select(sample_cols)
            .with_columns(
                (pl.col("loan_amount_000s") / pl.col("applicant_income_000s"))
                .alias("lti_ratio")
            )
            .filter(
                pl.col("lti_ratio").is_not_null() &
                pl.col("lti_ratio").is_finite() &
                (pl.col("lti_ratio") > 0) &
                (pl.col("lti_ratio") < MAX_LTI)
            )
        )

        del df   # free the large per-year frame

        return {
            "year":       year,
            "agg":        agg,
            "sample":     sample,
            "lender":     lender_agg,
            "raw_count":  raw_count,
            "kept_count": kept_count,
        }

    except Exception as e:
        gate.release(buf_bytes)   # ensure gate is released on any error path
        log(f"Year {year}: processing error: {e}", "ERR")
        import traceback; traceback.print_exc()
        return None


# ?????????????????????????????????????????????????????????????????????????????
# TRANSMITTAL SHEET WORKER
# ?????????????????????????????????????????????????????????????????????????????

def process_ts(year, gate):
    """
    Download and parse one year's transmittal sheet.

    Format (from CFPB data dictionary PDF ? HMDA Institution Record Format):
        Tab-delimited, NO header row, 22 positional columns.
        [0] Activity Year  [1] Respondent-ID  [2] Agency Code
        [3] Fed Tax ID     [4] Respondent Name (TS)

    Returns a small DataFrame (respondent_id, agency_code, institution_name,
    as_of_year) or None.
    """
    url = TS_URL.format(year=year)
    buf, buf_bytes = fetch_zip_gated(url, gate)
    if buf is None:
        log(f"TS {year}: not found", "WARN")
        return None

    try:
        with zipfile.ZipFile(buf) as z:
            with z.open(z.namelist()[0]) as f:
                raw = f.read()
        del buf
        gate.release(buf_bytes)

        # TS files: tab-delimited, no header ? confirmed from PDF
        # Try tab first; fall back to pipe if fewer than 4 fields detected
        for sep in ("\t", "|", ","):
            n_fields = raw.split(b"\n")[0].count(sep.encode())
            if n_fields >= 3:
                break

        ts = pl.read_csv(
            io.BytesIO(raw),
            separator=sep,
            has_header=False,
            infer_schema_length=500,
            ignore_errors=True,
            truncate_ragged_lines=True,
        )

        if ts.width <= TS_COL_NAME:
            log(f"TS {year}: only {ts.width} columns ? expected ?{TS_COL_NAME + 1}", "WARN")
            return None

        result = ts.select([
            pl.col(ts.columns[TS_COL_RESP  ]).alias("respondent_id"),
            pl.col(ts.columns[TS_COL_AGENCY]).cast(pl.Int32, strict=False).alias("agency_code"),
            pl.col(ts.columns[TS_COL_NAME  ]).alias("institution_name"),
        ]).with_columns(pl.lit(year).alias("as_of_year"))

        log(f"TS {year}: {len(result):,} institutions", "OK")
        return result

    except Exception as e:
        gate.release(buf_bytes)
        log(f"TS {year}: parse error: {e}", "WARN")
        return None


# ?????????????????????????????????????????????????????????????????????????????
# MAIN PIPELINE
# ?????????????????????????????????????????????????????????????????????????????

def run_pipeline():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ?? Pre-flight: schema probe + worker count ??????????????????????
    log("HMDA PIPELINE ? ENVISION HACKATHON 2026", "HEAD")
    log(f"States : {TARGET_STATES}")
    log(f"Years  : {YEARS[0]}?{YEARS[-1]}")

    col_map, sep = probe_lar_header(year=2017)
    if not col_map:
        log("Schema probe returned no mappings ? using fallback candidate lists", "WARN")
        sep = ","   # PDF confirms comma-separated

    max_workers = compute_max_workers()
    log(f"Workers: {max_workers}")
    log(f"Output : {OUTPUT_DIR}/")

    # MemoryGate budget = workers ? RAM_PER_WORKER_GB
    gate_budget = int(max_workers * RAM_PER_WORKER_GB * 1e9)
    gate        = MemoryGate(gate_budget)

    agg_frames    = []
    sample_frames = []
    lender_frames = []
    ts_frames     = []
    total_raw     = 0
    total_kept    = 0
    failed_years  = []

    # ?? Phase 1: Parallel download + processing ??????????????????????
    log("PHASE 1: Parallel download + processing", "HEAD")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        lar_futures = {executor.submit(process_year, y, col_map, sep, gate): y for y in YEARS}
        ts_futures  = {executor.submit(process_ts,   y, gate):               y for y in YEARS}

        for future in as_completed(lar_futures):
            year = lar_futures[future]
            try:
                result = future.result()
                if result:
                    agg_frames.append(result["agg"])
                    sample_frames.append(result["sample"])
                    lender_frames.append(result["lender"])
                    total_raw  += result["raw_count"]
                    total_kept += result["kept_count"]
                else:
                    failed_years.append(year)
            except Exception as e:
                log(f"Year {year}: unhandled exception: {e}", "ERR")
                failed_years.append(year)

        for future in as_completed(ts_futures):
            try:
                result = future.result()
                if result is not None:
                    ts_frames.append(result)
            except Exception as e:
                log(f"TS: unhandled exception: {e}", "WARN")

    if not agg_frames:
        log("No data collected ? check URLs and network access.", "ERR")
        return

    # ?? Phase 2: Build output files ??????????????????????????????????
    log("PHASE 2: Building output files", "HEAD")

    # ?? A: Aggregates ????????????????????????????????????????????????
    log("Building hmda_aggregates.parquet...")
    agg_final = pl.concat(agg_frames, how="diagonal").with_columns([
        pl.when(pl.col("action_taken") == 1).then(pl.lit("Originated"))
          .when(pl.col("action_taken") == 2).then(pl.lit("Approved Not Accepted"))
          .when(pl.col("action_taken") == 3).then(pl.lit("Denied"))
          .otherwise(pl.lit("Other"))
          .alias("action_label"),

        pl.when(pl.col("loan_type") == 1).then(pl.lit("Conventional"))
          .when(pl.col("loan_type") == 2).then(pl.lit("FHA"))
          .when(pl.col("loan_type") == 3).then(pl.lit("VA"))
          .when(pl.col("loan_type") == 4).then(pl.lit("FSA/RHS"))
          .otherwise(pl.lit("Unknown"))
          .alias("loan_type_label"),

        pl.when(pl.col("loan_purpose") == 1).then(pl.lit("Purchase"))
          .when(pl.col("loan_purpose") == 3).then(pl.lit("Refinance"))
          .otherwise(pl.lit("Other"))
          .alias("loan_purpose_label"),
    ])
    path_agg = f"{OUTPUT_DIR}/hmda_aggregates.parquet"
    agg_final.write_parquet(path_agg, compression="snappy")
    log(f"hmda_aggregates.parquet  ? {os.path.getsize(path_agg)/1e6:.1f} MB  ({len(agg_final):,} rows)", "OK")

    # ?? B: Sample ?????????????????????????????????????????????????????
    log("Building hmda_sample.parquet...")
    sample_final = pl.concat(sample_frames, how="diagonal")
    path_sample  = f"{OUTPUT_DIR}/hmda_sample.parquet"
    sample_final.write_parquet(path_sample, compression="snappy")
    log(f"hmda_sample.parquet      ? {os.path.getsize(path_sample)/1e6:.1f} MB  ({len(sample_final):,} rows)", "OK")

    # ?? C: Recovery Velocity Score ????????????????????????????????????
    log("Computing Recovery Velocity Score...")
    state_year_vol = (
        agg_final.filter(pl.col("action_taken") == 1)
        .group_by(["as_of_year", "state_code"])
        .agg(pl.col("n_records").sum().alias("originations"))
        .sort(["state_code", "as_of_year"])
    )
    baseline = (
        state_year_vol.filter(pl.col("as_of_year") == 2007)
        .select(["state_code", pl.col("originations").alias("baseline_2007")])
    )
    rvs = (
        state_year_vol.join(baseline, on="state_code", how="left")
        .with_columns(
            (pl.col("originations") / pl.col("baseline_2007")).alias("recovery_ratio")
        )
    )
    rvs_score = (
        rvs.filter((pl.col("as_of_year") >= 2010) & (pl.col("recovery_ratio") >= 0.80))
        .group_by("state_code")
        .agg(pl.col("as_of_year").min().alias("first_recovery_year"))
        .with_columns((pl.col("first_recovery_year") - 2009).alias("rvs_years_from_trough"))
        .sort("rvs_years_from_trough")
    )
    path_rvs = f"{OUTPUT_DIR}/rvs_by_state.parquet"
    rvs_score.write_parquet(path_rvs)
    log(f"rvs_by_state.parquet     ? {os.path.getsize(path_rvs)/1024:.0f} KB  ({len(rvs_score)} states)", "OK")

    path_rvs_full = f"{OUTPUT_DIR}/rvs_full.parquet"
    rvs.write_parquet(path_rvs_full)
    log(f"rvs_full.parquet         ? {os.path.getsize(path_rvs_full)/1024:.0f} KB", "OK")

    log("\nRecovery Velocity Score preview:")
    print(rvs_score.head(11).to_pandas().to_string(index=False))

    # ?? D: Lender names ???????????????????????????????????????????????
    if ts_frames and lender_frames:
        log("Building lender_names.parquet...")
        ts_final = (
            pl.concat(ts_frames, how="diagonal")
            .group_by(["respondent_id", "agency_code", "institution_name"])
            .agg(pl.col("as_of_year").max().alias("last_seen_year"))
            .sort("institution_name")
        )
        lender_final = pl.concat(lender_frames, how="diagonal")

        # FIX: join on both keys ? agency_code disambiguates same respondent_id
        join_keys = ["respondent_id"]
        if "agency_code" in lender_final.columns and "agency_code" in ts_final.columns:
            join_keys.append("agency_code")

        lender_final = lender_final.join(
            ts_final.select(join_keys + ["institution_name"]),
            on=join_keys, how="left"
        )
        path_lender = f"{OUTPUT_DIR}/lender_names.parquet"
        lender_final.write_parquet(path_lender, compression="snappy")
        log(f"lender_names.parquet     ? {os.path.getsize(path_lender)/1e6:.1f} MB", "OK")

    # ?? E: External overlays ??????????????????????????????????????????
    path_ext = f"{OUTPUT_DIR}/external_overlays.csv"
    pl.DataFrame(EXTERNAL_DATA).write_csv(path_ext)
    log(f"external_overlays.csv    ? {os.path.getsize(path_ext)} bytes", "OK")

    # ?? F: MSA scissor heatmap ????????????????????????????????????????
    log("Computing MSA scissor heatmap...")
    msa_scissor = (
        sample_final.filter(pl.col("msa_md").is_not_null())
        .group_by(["as_of_year", "msa_md", "state_code"])
        .agg([
            pl.col("lti_ratio").median().alias("median_lti"),
            pl.col("lti_ratio").quantile(0.25).alias("lti_p25"),
            pl.col("lti_ratio").quantile(0.75).alias("lti_p75"),
            pl.len().alias("n_loans"),
        ])
        .filter(pl.col("n_loans") >= 10)
        .sort(["msa_md", "as_of_year"])
    )
    path_msa = f"{OUTPUT_DIR}/msa_scissor.parquet"
    msa_scissor.write_parquet(path_msa)
    log(f"msa_scissor.parquet      ? {os.path.getsize(path_msa)/1024:.0f} KB  ({len(msa_scissor):,} rows)", "OK")

    # ?? Summary ???????????????????????????????????????????????????????
    log("PIPELINE COMPLETE", "HEAD")
    manifest = [
        ("hmda_aggregates.parquet", "Ch 1,2,3,4,5,6,7"),
        ("hmda_sample.parquet",     "Ch 4 violin, Ch 5 scissor"),
        ("rvs_by_state.parquet",    "Ch 5 map ranking"),
        ("rvs_full.parquet",        "Ch 5 time-slider map"),
        ("msa_scissor.parquet",     "Ch 5 MSA heatmap"),
        ("lender_names.parquet",    "Ch 7 bubble chart"),
        ("external_overlays.csv",   "Ch 6 overlays"),
    ]
    total_mb = 0
    print(f"\n  {'File':<38} {'Size':>8}  Serves")
    print(f"  {'-'*38} {'-'*8}  {'-'*25}")
    for fname, serves in manifest:
        fpath = f"{OUTPUT_DIR}/{fname}"
        if os.path.exists(fpath):
            mb = os.path.getsize(fpath) / 1e6
            total_mb += mb
            print(f"  {fname:<38} {mb:>6.1f}MB  {serves}")

    print(f"\n  {'TOTAL':<38} {total_mb:>6.1f}MB")
    print(f"\n  Rows in target states : {total_raw:,}")
    print(f"  Rows after filters    : {total_kept:,}")
    if total_raw:
        print(f"  Retention rate        : {total_kept / total_raw * 100:.1f}%")
    if failed_years:
        print(f"\n  Failed/skipped years  : {sorted(failed_years)}")
    print(f"\n  Output : {os.path.abspath(OUTPUT_DIR)}/\n")


# ?????????????????????????????????????????????????????????????????????????????
# VERIFICATION
# ?????????????????????????????????????????????????????????????????????????????

def verify():
    log("VERIFICATION", "HEAD")
    agg = pl.read_parquet(f"{OUTPUT_DIR}/hmda_aggregates.parquet")
    log(f"Aggregates : {len(agg):,} rows, {agg.width} cols")
    log(f"Columns    : {agg.columns}")

    print("\n  Originations by year (target states):")
    print(
        agg.filter(pl.col("action_taken") == 1)
        .group_by("as_of_year")
        .agg(pl.col("n_records").sum().alias("originations"))
        .sort("as_of_year")
        .to_pandas().to_string(index=False)
    )

    print("\n  Loan type share (key years):")
    print(
        agg.filter(pl.col("action_taken") == 1)
        .filter(pl.col("as_of_year").is_in([2007, 2009, 2012, 2017]))
        .group_by(["as_of_year", "loan_type_label"])
        .agg(pl.col("n_records").sum())
        .sort(["as_of_year", "loan_type_label"])
        .to_pandas().to_string(index=False)
    )

    rvs = pl.read_parquet(f"{OUTPUT_DIR}/rvs_by_state.parquet")
    print("\n  Recovery Velocity Score:")
    print(rvs.to_pandas().to_string(index=False))

    sample = pl.read_parquet(f"{OUTPUT_DIR}/hmda_sample.parquet")
    log(f"Sample : {len(sample):,} rows")
    print("\n  Median LTI ratio by year:")
    print(
        sample.group_by("as_of_year")
        .agg(pl.col("lti_ratio").median().alias("median_lti"))
        .sort("as_of_year")
        .to_pandas().to_string(index=False)
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        verify()
    else:
        t0 = time.time()
        run_pipeline()
        print(f"  Total time: {(time.time() - t0) / 60:.1f} minutes")
