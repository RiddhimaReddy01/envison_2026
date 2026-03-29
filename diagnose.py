"""
Compatibility wrapper.
Preferred location: `scripts/dev/diagnose_data.py`
"""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "scripts" / "dev" / "diagnose_data.py"), run_name="__main__")
