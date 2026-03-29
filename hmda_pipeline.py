"""
Compatibility wrapper.
Preferred entrypoint: `pipeline/build_hmda_pipeline.py`
"""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(
        str(Path(__file__).resolve().parent / "pipeline" / "build_hmda_pipeline.py"),
        run_name="__main__",
    )
