"""
Compatibility wrapper.
Preferred entrypoint: `pipeline/causal/data_build.py`
"""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "pipeline" / "causal" / "data_build.py"), run_name="__main__")
