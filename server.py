"""Repository-root entry point for the current MCP server submission.

The course server is maintained in ``mcp-document-server/server.py`` across
Modules 3–8. This root entry point makes the graded deliverable immediately
discoverable while executing that canonical server unchanged.
"""

import runpy
from pathlib import Path


if __name__ == "__main__":
    runpy.run_path(
        str(Path(__file__).parent / "mcp-document-server" / "server.py"),
        run_name="__main__",
    )
