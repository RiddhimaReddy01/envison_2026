"""
Compatibility wrapper.
Preferred entrypoint: `pipeline/export_parquet_csv.py`
"""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "pipeline" / "export_parquet_csv.py"), run_name="__main__")

