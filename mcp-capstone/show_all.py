"""Print the complete in-process inventory for design verification."""

import asyncio
import json
import logging

logging.disable(logging.CRITICAL)

from server import mcp  # noqa: E402


async def main() -> None:
    print("=== tools ===")
    for tool in await mcp.list_tools():
        print(f"{tool.name}: {tool.description.splitlines()[0]}")
        print(json.dumps(tool.inputSchema, indent=2, sort_keys=True))

    print("\n=== direct resources ===")
    for resource in await mcp.list_resources():
        print(f"{resource.uri} | {resource.mimeType} | {resource.name}")

    print("\n=== resource templates ===")
    for template in await mcp.list_resource_templates():
        print(f"{template.uriTemplate} | {template.mimeType} | {template.name}")

    print("\n=== prompts ===")
    for prompt in await mcp.list_prompts():
        args = ", ".join(
            f"{arg.name}{'' if arg.required else '?'}: {arg.description or 'no description'}"
            for arg in (prompt.arguments or [])
        )
        print(f"/{prompt.name}({args}) - {prompt.description}")


if __name__ == "__main__":
    asyncio.run(main())
