"""Nested compatibility launcher for the canonical repository-root client."""

import runpy
from pathlib import Path


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).parents[1] / "client.py"), run_name="__main__")
