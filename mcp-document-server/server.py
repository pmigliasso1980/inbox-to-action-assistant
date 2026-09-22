"""MCP document server used by the inbox assistant course project."""

import json
import logging
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from pydantic import Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The name a connecting client sees as serverInfo.name.
mcp = FastMCP("inbox-case-server")

# A tiny in-memory store standing in for the future case-document store.
docs: dict[str, str] = {
    "report.pdf": "The quarterly report covers revenue and costs.",
    "plan.md": "Project plan: phase one, phase two, phase three.",
    "onboarding.docx": "New hires receive a laptop on their first day.",
}


@mcp.tool()
def read_document(
    doc_id: Annotated[
        str,
        Field(
            description=(
                "Case-sensitive document id returned by list_documents, such as plan.md."
            ),
            min_length=1,
        ),
    ],
) -> str:
    """Return the complete text of one known document.

    Use this for exact content retrieval after obtaining a case-sensitive id
    from list_documents. It does not change the document.
    """
    if doc_id not in docs:
        raise ValueError(f"Unknown document: {doc_id}. Call list_documents for valid ids.")
    return docs[doc_id]


@mcp.tool()
def edit_document(
    doc_id: Annotated[
        str,
        Field(description="Case-sensitive document id returned by list_documents.", min_length=1),
    ],
    old_text: Annotated[
        str,
        Field(description="Exact case-sensitive text to replace; must be non-empty.", min_length=1),
    ],
    new_text: Annotated[str, Field(description="Replacement text, which may be empty.")],
) -> str:
    """Replace only the first exact occurrence of text in a known document.

    Use this only when the requested old and replacement text are explicit.
    It changes the in-memory document and fails without modifying anything if
    the id or old text is not found.
    """
    if doc_id not in docs:
        raise ValueError(f"Unknown document: {doc_id}. Call list_documents for valid ids.")
    if old_text not in docs[doc_id]:
        raise ValueError(
            f"Text not found in {doc_id}: {old_text!r}. Read the document and retry with exact text."
        )
    docs[doc_id] = docs[doc_id].replace(old_text, new_text, 1)
    return f"Updated {doc_id}."


@mcp.tool()
def list_documents() -> list[str]:
    """Return sorted case-sensitive ids for every document available on this server."""
    return sorted(docs)


@mcp.tool()
def search_documents(
    query: Annotated[
        str,
        Field(description="Non-empty text to search for, using case-insensitive matching.", min_length=1),
    ],
    scope: Annotated[
        Literal["title", "body", "both"],
        Field(description="Search document ids, document contents, or both."),
    ] = "both",
    limit: Annotated[
        int,
        Field(description="Maximum number of document ids to return, from 1 through 10.", ge=1, le=10),
    ] = 5,
) -> list[str]:
    """Return document ids whose id or content contains a query.

    Matching is a case-insensitive substring search. Use scope to restrict the
    search to document ids (title), contents (body), or both; at most limit ids
    are returned in sorted order.
    """
    needle = query.lower()
    hits: list[str] = []
    for doc_id, text in sorted(docs.items()):
        in_title = needle in doc_id.lower()
        in_body = needle in text.lower()
        if (
            (scope == "title" and in_title)
            or (scope == "body" and in_body)
            or (scope == "both" and (in_title or in_body))
        ):
            hits.append(doc_id)
    return hits[:limit]


@mcp.resource("docs://documents", mime_type="application/json")
def document_catalog() -> str:
    """Return all available case-sensitive document ids as a JSON array."""
    return json.dumps(sorted(docs))


@mcp.resource("docs://documents/{doc_id}", mime_type="text/plain")
def document_contents(doc_id: str) -> str:
    """Return the complete text of one known document without modifying it."""
    if doc_id not in docs:
        raise ValueError(f"Unknown document: {doc_id}")
    return docs[doc_id]


@mcp.resource("docs://documents/{doc_id}/stats", mime_type="application/json")
def document_stats(doc_id: str) -> str:
    """Return document identity, character count, and word count as JSON."""
    if doc_id not in docs:
        raise ValueError(f"Unknown document: {doc_id}")
    text = docs[doc_id]
    return json.dumps(
        {"doc_id": doc_id, "characters": len(text), "words": len(text.split())}
    )


@mcp.prompt()
def format_document(doc_id: str) -> list[base.Message]:
    """Produce instructions to reformat a document into clean Markdown."""
    return [
        base.UserMessage(
            f"Reformat the document '{doc_id}' into clean, well-structured "
            "Markdown. Use a single top-level heading for the title, section "
            "headings for major parts, bullet lists where items are enumerated, "
            "and fenced code blocks for any code. Preserve all original meaning "
            "and do not invent new content."
        )
    ]


@mcp.prompt()
def summarize_document(
    doc_id: Annotated[str, Field(description="Which document to summarize.")],
    max_words: Annotated[int, Field(description="Upper bound on summary length.")] = 100,
) -> list[base.Message]:
    """Produce instructions to summarize a document within a word limit."""
    return [
        base.UserMessage(
            f"Summarize the document '{doc_id}' in no more than {max_words} words. "
            "Keep every factual claim faithful to the source, do not add information "
            "that is not present, and prefer plain language over jargon. If the "
            "document is already shorter than the limit, return it essentially "
            "unchanged rather than padding it."
        )
    ]


@mcp.prompt()
def review_document(
    doc_id: str, audience: str = "a new team member"
) -> list[base.Message]:
    """Produce a two-turn review exchange for a document."""
    return [
        base.UserMessage(
            f"Review the document '{doc_id}' for clarity and completeness, "
            f"assuming the reader is {audience}."
        ),
        base.AssistantMessage(
            "I will review it in three passes: first what is unclear, then what is "
            "missing, then what could be cut. Here is the review:"
        ),
    ]


if __name__ == "__main__":
    logger.info("Server starting up!")
    mcp.run(transport="stdio")
