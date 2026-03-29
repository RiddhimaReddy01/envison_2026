"""
Compatibility wrapper.
Preferred entrypoint: `pipeline/analyze_fha_recovery.py`
"""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "pipeline" / "analyze_fha_recovery.py"), run_name="__main__")

