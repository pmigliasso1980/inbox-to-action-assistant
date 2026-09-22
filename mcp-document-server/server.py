"""MCP document server used by the inbox assistant course project."""

import logging
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
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


if __name__ == "__main__":
    logger.info("Server starting up!")
    mcp.run(transport="stdio")
