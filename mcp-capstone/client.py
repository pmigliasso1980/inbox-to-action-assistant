"""Reference client exercising every capstone primitive and failure channel."""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

logging.disable(logging.CRITICAL)

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402
from mcp.shared.exceptions import McpError  # noqa: E402

SERVER = StdioServerParameters(
    command=sys.executable,
    args=[str(Path(__file__).with_name("server.py"))],
)


def text_of(result: Any) -> str:
    """Join every text content block without assuming order or count."""
    return "\n".join(
        block.text
        for block in result.content
        if getattr(block, "type", None) == "text"
    )


def as_conversation(prompt_result: Any) -> list[dict[str, Any]]:
    """Convert resolved text messages into model-ready conversation turns."""
    turns = []
    for message in prompt_result.messages:
        if getattr(message.content, "type", None) == "text":
            turns.append({"role": message.role, "content": message.content.text})
    return turns


async def call_tool_checked(
    session: ClientSession, name: str, arguments: dict[str, Any]
) -> str:
    """Call a tool, check its MCP error flag, and return all text blocks."""
    result = await session.call_tool(name, arguments)
    if result.isError:
        raise RuntimeError(f"{name} failed: {text_of(result)}")
    return text_of(result)


async def read_uri(session: ClientSession, uri: str) -> Any:
    """Read a resource and decode text according to its declared MIME type."""
    try:
        result = await session.read_resource(uri)
    except McpError:
        raise
    if not result.contents:
        raise ValueError(f"Resource returned no content: {uri}")
    entry = result.contents[0]
    if not hasattr(entry, "text"):
        return entry.blob
    if (entry.mimeType or "").startswith("application/json"):
        return json.loads(entry.text)
    return entry.text


async def main() -> None:
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print("connected:", init.serverInfo.name, init.serverInfo.version)

            tools = await session.list_tools()
            resources = await session.list_resources()
            templates = await session.list_resource_templates()
            prompts = await session.list_prompts()

            print("\n=== discovery ===")
            print("tools:", ", ".join(tool.name for tool in tools.tools))
            print("resources:", ", ".join(str(item.uri) for item in resources.resources))
            print(
                "templates:",
                ", ".join(item.uriTemplate for item in templates.resourceTemplates),
            )
            print("prompts:", ", ".join(prompt.name for prompt in prompts.prompts))

            print("\n=== happy-path tools ===")
            print(
                await call_tool_checked(
                    session,
                    "triage_case",
                    {
                        "case_id": "CASE-101",
                        "priority": "high",
                        "rationale": "The sender requests approval by Friday.",
                    },
                )
            )
            print(
                await call_tool_checked(
                    session,
                    "assign_case",
                    {"case_id": "CASE-101", "assignee": "finance-team"},
                )
            )
            print(
                await call_tool_checked(
                    session,
                    "set_case_status",
                    {"case_id": "CASE-101", "status": "pending"},
                )
            )

            print("\n=== happy-path resources ===")
            catalog = await read_uri(session, "inbox://cases")
            details = await read_uri(session, "inbox://cases/CASE-101")
            workload = await read_uri(session, "inbox://workload")
            print("catalog entries:", len(catalog))
            print("CASE-101:", details)
            print("workload:", workload)

            print("\n=== happy-path prompts ===")
            for name, arguments in (
                ("draft_case_reply", {"case_id": "CASE-101", "tone": "concise"}),
                ("review_case", {"case_id": "CASE-102"}),
            ):
                resolved = await session.get_prompt(name, arguments)
                print(f"/{name} -> {len(resolved.messages)} message(s)")
                for turn in as_conversation(resolved):
                    print(f"  [{turn['role']}] {turn['content']}")

            print("\n=== four labelled failure paths ===")
            semantic = await session.call_tool(
                "assign_case", {"case_id": "CASE-999", "assignee": "ops-team"}
            )
            print(
                "1 semantic tool error ->",
                f"isError={semantic.isError}",
                "|",
                text_of(semantic),
            )

            constrained = await session.call_tool(
                "set_case_status", {"case_id": "CASE-101", "status": "archived"}
            )
            print(
                "2 SDK constraint rejection ->",
                f"isError={constrained.isError}",
                "|",
                text_of(constrained)[:220],
            )

            try:
                await read_uri(session, "inbox://cases/CASE-999")
            except McpError as exc:
                print("3 unresolved resource ->", type(exc).__name__, "|", str(exc)[:220])

            try:
                await session.get_prompt(
                    "draft_case_reply", {"case_id": "CASE-101", "tone": 7}
                )
            except Exception as exc:
                print("4 non-string prompt arg ->", type(exc).__name__, "|", str(exc)[:220])

            print("\n=== state-change round trip ===")
            before = await read_uri(session, "inbox://cases/CASE-103")
            print("before:", before["status"])
            print(
                await call_tool_checked(
                    session,
                    "set_case_status",
                    {"case_id": "CASE-103", "status": "closed"},
                )
            )
            after = await read_uri(session, "inbox://cases/CASE-103")
            print("after:", after["status"])


if __name__ == "__main__":
    asyncio.run(main())
