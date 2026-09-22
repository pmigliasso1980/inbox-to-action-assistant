"""MCP client — repository-root graded deliverable.

Run with the pinned environment:

    mcp-document-server/.venv/bin/python client.py

The client launches ``server.py`` itself; do not start the server separately.
"""

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
    """Join every text block without assuming its position or block count."""
    return "\n".join(
        block.text
        for block in result.content
        if getattr(block, "type", None) == "text"
    )


def as_conversation(prompt_result: Any) -> list[dict[str, Any]]:
    """Convert resolved prompt text messages into plain conversation turns."""
    turns = []
    for message in prompt_result.messages:
        content = message.content
        if getattr(content, "type", None) == "text":
            turns.append({"role": message.role, "content": content.text})
    return turns


async def slash_command_loop(session: ClientSession) -> None:
    """Run a minimal slash-command interface with server-driven autocomplete."""
    prompts = (await session.list_prompts()).prompts

    print("\nAvailable commands (type part of a name, or 'quit'):")
    for prompt in prompts:
        print(f"  /{prompt.name} - {prompt.description}")

    while True:
        typed = input("\n/").strip()
        if typed in {"quit", "exit", ""}:
            return

        matches = [prompt for prompt in prompts if prompt.name.startswith(typed)]
        if not matches:
            print(f"no command starts with {typed!r}")
            continue
        if len(matches) > 1:
            print("ambiguous:", ", ".join(f"/{prompt.name}" for prompt in matches))
            continue

        chosen = matches[0]
        print(f"-> /{chosen.name}")
        arguments: dict[str, str] = {}
        for argument in chosen.arguments or []:
            label = argument.name
            if argument.description:
                label += f" ({argument.description})"
            if not argument.required:
                label += " [optional, press Enter to skip]"
            value = input(f"    {label}: ").strip()
            if value:
                arguments[argument.name] = value
            elif argument.required:
                print(f"    {argument.name} is required — aborting")
                break
        else:
            result = await session.get_prompt(chosen.name, arguments)
            print(f"\n--- injected context ({len(result.messages)} message(s)) ---")
            for turn in as_conversation(result):
                print(f"[{turn['role']}] {turn['content']}")


async def run_tool(session: ClientSession, name: str, args: dict[str, Any]) -> str:
    """Call a tool and return its text, raising on a tool-level failure."""
    result = await session.call_tool(name, args)
    if result.isError:
        raise RuntimeError(f"tool {name} failed: {text_of(result)}")
    return text_of(result)


async def read_uri(session: ClientSession, uri: str) -> Any:
    """Read one resource and interpret it according to its declared MIME type."""
    result = await session.read_resource(uri)
    if not result.contents:
        raise ValueError(f"Resource returned no contents: {uri}")
    entry = result.contents[0]

    # Binary resources contain base64 in `blob` rather than a `text` field.
    if not hasattr(entry, "text"):
        return entry.blob

    if (entry.mimeType or "").startswith("application/json"):
        return json.loads(entry.text)

    return entry.text


async def try_read_uri(session: ClientSession, uri: str, default: Any = None) -> Any:
    """Return a resource or a caller-supplied default when MCP cannot read it."""
    try:
        return await read_uri(session, uri)
    except McpError:
        return default


async def main() -> None:
    # Both context managers are required: stdio owns the subprocess and the
    # session owns the protocol streams layered on top of it.
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            # The handshake must finish before discovery or invocation.
            init = await session.initialize()
            print("connected to:", init.serverInfo.name, init.serverInfo.version)
            print("capabilities:", init.capabilities)

            print("\n--- tools ---")
            tools = await session.list_tools()
            for tool in tools.tools:
                required = tool.inputSchema.get("required", [])
                params = ", ".join(tool.inputSchema.get("properties", {}))
                print(f"{tool.name}({params}) required={required}")
                print(f"    {tool.description.splitlines()[0]}")

            print("\n--- success and failure ---")
            for doc_id in ("report.pdf", "ghost.md"):
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

            print("\n--- state round trip ---")
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

            print("\n--- five failure modes ---")
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

            print("\n--- concurrent calls ---")
            report, onboarding = await asyncio.gather(
                run_tool(session, "read_document", {"doc_id": "report.pdf"}),
                run_tool(session, "read_document", {"doc_id": "onboarding.docx"}),
            )
            print("report.pdf ->", report)
            print("onboarding.docx ->", onboarding)

            print("\n--- direct resources ---")
            resources = await session.list_resources()
            for resource in resources.resources:
                print(f"{resource.uri}  ({resource.mimeType})  {resource.name}")

            print("\n--- resource templates ---")
            templates = await session.list_resource_templates()
            for template in templates.resourceTemplates:
                print(f"{template.uriTemplate}  ({template.mimeType})")

            print("\n--- MIME-aware reads ---")
            ids = await read_uri(session, "docs://documents")
            print("catalog:", ids, "| type:", type(ids).__name__)
            for doc_id in ids:
                text = await read_uri(session, f"docs://documents/{doc_id}")
                stats = await read_uri(session, f"docs://documents/{doc_id}/stats")
                print(f"[{doc_id}] {text}")
                print(f"    stats: {stats['words']} words, {stats['characters']} chars")

            print("\n--- tool/resource failure comparison ---")
            tool_result = await session.call_tool("read_document", {"doc_id": "ghost.md"})
            print("tool  -> raised? no | isError:", tool_result.isError)
            print("        text:", text_of(tool_result)[:120])

            for label, uri in (
                ("resource", "docs://documents/ghost.md"),
                ("bad scheme", "nonsense://nowhere"),
            ):
                try:
                    await read_uri(session, uri)
                    print(label, "-> raised? no")
                except McpError as exc:
                    print(label, "-> raised", type(exc).__name__, "|", str(exc)[:120])

            optional = await try_read_uri(session, "nonsense://optional", default=[])
            print("optional missing context ->", optional)

            print("\n--- prompts ---")
            prompts = await session.list_prompts()
            for prompt in prompts.prompts:
                args = ", ".join(
                    f"{arg.name}{'' if arg.required else '?'}"
                    for arg in (prompt.arguments or [])
                )
                print(f"/{prompt.name}({args}) - {prompt.description}")

            print("\n--- argument types ---")
            try:
                bad = await session.get_prompt(
                    "summarize_document", {"doc_id": "plan.md", "max_words": 40}
                )
                print("int argument accepted:", bad.messages[0].content.text[:60])
            except Exception as exc:
                print("int argument REJECTED:", type(exc).__name__)
                print(str(exc)[:500])

            corrected = await session.get_prompt(
                "summarize_document", {"doc_id": "plan.md", "max_words": "40"}
            )
            print("string argument accepted:", corrected.messages[0].content.text[:75])

            print("\n--- resolved prompts ---")
            for name, args in [
                ("format_document", {"doc_id": "plan.md"}),
                ("summarize_document", {"doc_id": "plan.md", "max_words": "40"}),
                ("review_document", {"doc_id": "report.pdf"}),
            ]:
                result = await session.get_prompt(name, args)
                print(f"\n/{name} -> {len(result.messages)} message(s)")
                for turn in as_conversation(result):
                    print(f"  [{turn['role']}] {turn['content'][:100]}...")

            # Keep automated runs non-interactive; pass --interactive for the lab UI.
            if "--interactive" in sys.argv:
                await slash_command_loop(session)


if __name__ == "__main__":
    asyncio.run(main())
