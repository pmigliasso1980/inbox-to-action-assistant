"""Reference MCP client for the document server.

The client demonstrates the required lifecycle—connect, initialize, discover,
invoke—and handles both MCP tool-error results and raised protocol failures.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

logging.disable(logging.CRITICAL)

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

SERVER_FILE = Path(__file__).with_name("server.py")
SERVER = StdioServerParameters(command=sys.executable, args=[str(SERVER_FILE)])


def text_of(result: Any) -> str:
    """Join every text block in a tool result without assuming block order."""
    return "\n".join(
        block.text
        for block in result.content
        if getattr(block, "type", None) == "text"
    )


async def run_tool(session: ClientSession, name: str, args: dict[str, Any]) -> str:
    """Call a tool and return all text, raising on a tool-level failure."""
    result = await session.call_tool(name, args)
    if result.isError:
        raise RuntimeError(f"tool {name} failed: {text_of(result)}")
    return text_of(result)


async def main() -> None:
    # Opening stdio owns a subprocess; both context managers guarantee cleanup.
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print("connected to:", init.serverInfo.name, init.serverInfo.version)
            print("capability groups: tools, resources, prompts")

            print("\n--- tools ---")
            tools = await session.list_tools()
            for tool in tools.tools:
                required = tool.inputSchema.get("required", [])
                params = ", ".join(tool.inputSchema.get("properties", {}))
                print(f"{tool.name}({params})  required={required}")
                print(f"    {tool.description.splitlines()[0]}")

            print("\n--- correct calls ---")
            for doc_id in ["report.pdf", "ghost.md"]:
                result = await session.call_tool("read_document", {"doc_id": doc_id})
                if result.isError:
                    print(f"{doc_id} -> FAILED: {text_of(result)}")
                else:
                    print(f"{doc_id} -> {text_of(result)}")

            listed = await session.call_tool("list_documents", {})
            if listed.isError:
                print("list_documents -> FAILED:", text_of(listed))
            else:
                print("\nblocks returned:", len(listed.content))
                print("text_of(...)      ->", repr(text_of(listed)))
                print("structuredContent ->", listed.structuredContent)

            print("\n--- round trip through run_tool ---")
            print("before:", await run_tool(session, "read_document", {"doc_id": "plan.md"}))
            print(
                "edit  :",
                await run_tool(
                    session,
                    "edit_document",
                    {"doc_id": "plan.md", "old_text": "phase one", "new_text": "phase 1"},
                ),
            )
            print("after :", await run_tool(session, "read_document", {"doc_id": "plan.md"}))

            print("\n--- failure modes ---")
            failures = [
                ("bad document id", "read_document", {"doc_id": "ghost.md"}),
                (
                    "text not found",
                    "edit_document",
                    {"doc_id": "plan.md", "old_text": "zzz", "new_text": "x"},
                ),
                ("missing required arg", "read_document", {}),
                ("constraint violation", "search_documents", {"query": "a", "limit": 99}),
                ("unknown tool", "no_such_tool", {}),
            ]
            for label, name, args in failures:
                try:
                    result = await session.call_tool(name, args)
                    print(f"{label}: isError={result.isError} | {text_of(result)[:160]}")
                except Exception as exc:
                    print(f"{label}: RAISED {type(exc).__name__} | {str(exc)[:160]}")

            print("\n--- run_tool conversion ---")
            try:
                await run_tool(session, "read_document", {"doc_id": "ghost.md"})
            except RuntimeError as exc:
                print(type(exc).__name__, "|", exc)

            print("\n--- concurrent reads ---")
            report, onboarding = await asyncio.gather(
                run_tool(session, "read_document", {"doc_id": "report.pdf"}),
                run_tool(session, "read_document", {"doc_id": "onboarding.docx"}),
            )
            print("report.pdf ->", report)
            print("onboarding.docx ->", onboarding)


if __name__ == "__main__":
    asyncio.run(main())
