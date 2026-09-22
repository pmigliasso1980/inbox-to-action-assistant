"""Inspect prompt metadata and representative resolved messages."""

import asyncio
import logging

logging.disable(logging.CRITICAL)

from server import mcp  # noqa: E402


async def print_result(name: str, arguments: dict[str, str]) -> None:
    result = await mcp.get_prompt(name, arguments)
    print(f"\n/{name} -> {len(result.messages)} message(s)")
    for message in result.messages:
        print(f"[{message.role}] {message.content.text}")


async def main() -> None:
    for prompt in await mcp.list_prompts():
        print(f"/{prompt.name} - {prompt.description}")
        for arg in prompt.arguments or []:
            flag = "required" if arg.required else "optional"
            print(f"    {arg.name} ({flag})  {arg.description or '-- no description --'}")

    print("\n=== resolved ===")
    await print_result("format_document", {"doc_id": "plan.md"})

    print("\n=== defaults ===")
    await print_result("summarize_document", {"doc_id": "plan.md"})

    print("\n=== multi-message ===")
    await print_result("review_document", {"doc_id": "report.pdf"})


if __name__ == "__main__":
    asyncio.run(main())
