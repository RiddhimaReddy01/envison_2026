"""
Compatibility wrapper.
Preferred location: `scripts/dev/fix_encoding.py`
"""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "scripts" / "dev" / "fix_encoding.py"), run_name="__main__")

