"""
Compatibility wrapper.
Preferred location: `scripts/dev/profile_data.py`
"""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "dev" / "profile_data.py"), run_name="__main__")

