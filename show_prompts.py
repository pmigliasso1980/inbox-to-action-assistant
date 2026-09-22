"""Repository-root launcher for the Module 7 prompt inspection helper."""

import runpy
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).parent / "mcp-document-server"

if __name__ == "__main__":
    sys.path.insert(0, str(SERVER_DIR))
    runpy.run_path(str(SERVER_DIR / "show_prompts.py"), run_name="__main__")
