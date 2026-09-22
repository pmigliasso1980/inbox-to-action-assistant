"""Inspect direct resources, templates, and representative direct reads."""

import asyncio
import logging

logging.disable(logging.CRITICAL)

from server import mcp  # noqa: E402


async def main() -> None:
    print("=== direct resources ===")
    for resource in await mcp.list_resources():
        print(f"{resource.uri}  mime={resource.mimeType}  name={resource.name}")
        print(f"    {resource.description}")

    print("\n=== resource templates ===")
    for template in await mcp.list_resource_templates():
        print(f"{template.uriTemplate}  mime={template.mimeType}")

    print("\n=== reads ===")
    for uri in (
        "docs://documents",
        "docs://documents/plan.md",
        "docs://documents/plan.md/stats",
    ):
        print(uri, "->", await mcp.read_resource(uri))


if __name__ == "__main__":
    asyncio.run(main())
