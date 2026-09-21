"""Minimal MCP server for the inbox assistant's case store.

Capabilities are added in later course modules. Logging is deliberately sent to
stderr because stdout belongs exclusively to the stdio JSON-RPC transport.
"""

import logging

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The name a connecting client sees as serverInfo.name.
mcp = FastMCP("inbox-case-server")


if __name__ == "__main__":
    logger.info("Server starting up!")
    mcp.run(transport="stdio")
