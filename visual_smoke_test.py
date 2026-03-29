"""
Compatibility wrapper.
Preferred location: `scripts/dev/visual_smoke_test.py`
"""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "scripts" / "dev" / "visual_smoke_test.py"), run_name="__main__")
