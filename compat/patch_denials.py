"""
Compatibility wrapper.
Preferred entrypoint: `pipeline/patch_denials.py`
"""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "pipeline" / "patch_denials.py"), run_name="__main__")
