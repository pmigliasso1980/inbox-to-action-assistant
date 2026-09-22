"""Print the model-facing schemas generated from the registered Python tools."""

import asyncio
import json
import logging

logging.disable(logging.CRITICAL)

from server import mcp  # noqa: E402


async def main() -> None:
    for tool in await mcp.list_tools():
        print(
            json.dumps(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                    "outputSchema": tool.outputSchema,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
