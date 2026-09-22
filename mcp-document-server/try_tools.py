"""Exercise every tool directly, including validation and domain failures."""

import asyncio
import logging

logging.disable(logging.CRITICAL)

from server import mcp  # noqa: E402


async def call(name: str, args: dict) -> None:
    print(f"\n=== {name}({args}) ===")
    try:
        result = await mcp.call_tool(name, args)
        print("returned:", result)
    except Exception as exc:
        print("raised:", type(exc).__name__, "-", exc)


async def main() -> None:
    await call("list_documents", {})
    await call("read_document", {"doc_id": "plan.md"})
    await call(
        "edit_document",
        {"doc_id": "plan.md", "old_text": "phase one", "new_text": "phase 1"},
    )
    await call("read_document", {"doc_id": "plan.md"})

    await call("read_document", {"doc_id": "ghost.md"})
    await call(
        "edit_document",
        {"doc_id": "plan.md", "old_text": "not present", "new_text": "x"},
    )
    await call("read_document", {})

    await call("search_documents", {"query": "phase"})
    await call("search_documents", {"query": "report", "scope": "title"})
    await call("search_documents", {"query": "x", "limit": 99})
    await call("search_documents", {"query": "x", "scope": "footer"})


if __name__ == "__main__":
    asyncio.run(main())
