"""MCP server for an in-memory inbox case-management system."""

import json
import logging
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from pydantic import Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("inbox-action-server")

cases: dict[str, dict[str, str | None]] = {
    "CASE-101": {
        "sender": "ana@example.com",
        "subject": "Quarterly report approval",
        "body": "Please approve the attached report by Friday.",
        "status": "open",
        "priority": "normal",
        "assignee": None,
    },
    "CASE-102": {
        "sender": "ops@example.com",
        "subject": "Production alert follow-up",
        "body": "Please confirm ownership of the database latency investigation.",
        "status": "pending",
        "priority": "high",
        "assignee": "platform-team",
    },
    "CASE-103": {
        "sender": "hr@example.com",
        "subject": "Benefits information",
        "body": "The updated benefits guide is available for reference.",
        "status": "open",
        "priority": "low",
        "assignee": None,
    },
}


def require_case(case_id: str) -> dict[str, str | None]:
    """Return one case or raise an actionable domain error."""
    if case_id not in cases:
        raise ValueError(
            f"Unknown case: {case_id}. Read inbox://cases for valid case ids."
        )
    return cases[case_id]


@mcp.tool()
def triage_case(
    case_id: Annotated[
        str,
        Field(description="Case-sensitive id from inbox://cases, such as CASE-101."),
    ],
    priority: Annotated[
        Literal["low", "normal", "high", "urgent"],
        Field(
            description=(
                "Justified priority to store: low, normal, high, or urgent."
            )
        ),
    ],
    rationale: Annotated[
        str,
        Field(
            description=(
                "Evidence-based reason for the priority decision, 10–240 characters."
            ),
            min_length=10,
            max_length=240,
        ),
    ],
) -> str:
    """Store a justified priority when message meaning indicates triage is needed.

    Use only after examining the case content. Priority must be one of the declared
    levels, and rationale must cite the evidence that drove the judgment.
    """
    case = require_case(case_id)
    case["priority"] = priority
    return f"Triaged {case_id} as {priority}: {rationale}"


@mcp.tool()
def assign_case(
    case_id: Annotated[
        str,
        Field(description="Case-sensitive id from inbox://cases, such as CASE-101."),
    ],
    assignee: Annotated[
        str,
        Field(
            description="Team or person that accepts responsibility for the case.",
            min_length=2,
            max_length=80,
        ),
    ],
) -> str:
    """Assign ownership when a responsible team or person is known.

    This changes shared workflow state. Do not guess an assignee from weak evidence.
    """
    case = require_case(case_id)
    case["assignee"] = assignee
    return f"Assigned {case_id} to {assignee}."


@mcp.tool()
def set_case_status(
    case_id: Annotated[
        str,
        Field(description="Case-sensitive id from inbox://cases, such as CASE-101."),
    ],
    status: Annotated[
        Literal["open", "pending", "closed"],
        Field(description="Target workflow status: open, pending, or closed."),
    ],
) -> str:
    """Change workflow status only when the requested transition is explicit.

    Closing a case removes it from active work views, so use closed only after the
    outcome is verified or a human explicitly requests closure.
    """
    case = require_case(case_id)
    previous = case["status"]
    if previous == status:
        raise ValueError(
            f"{case_id} is already {status}. Choose a different target status."
        )
    case["status"] = status
    return f"Changed {case_id} from {previous} to {status}."


@mcp.resource("inbox://cases", mime_type="application/json")
def case_catalog() -> str:
    """Case catalog with workflow metadata."""
    catalog = [
        {
            "case_id": case_id,
            "subject": case["subject"],
            "status": case["status"],
            "priority": case["priority"],
            "assignee": case["assignee"],
        }
        for case_id, case in sorted(cases.items())
    ]
    return json.dumps(catalog)


@mcp.resource("inbox://workload", mime_type="application/json")
def workload_summary() -> str:
    """Current case counts grouped by workflow status and priority."""
    status_counts = {status: 0 for status in ("open", "pending", "closed")}
    priority_counts = {
        priority: 0 for priority in ("low", "normal", "high", "urgent")
    }
    for case in cases.values():
        status_counts[str(case["status"])] += 1
        priority_counts[str(case["priority"])] += 1
    return json.dumps({"by_status": status_counts, "by_priority": priority_counts})


@mcp.resource("inbox://cases/{case_id}", mime_type="application/json")
def case_details(case_id: str) -> str:
    """Complete case content and workflow metadata."""
    return json.dumps({"case_id": case_id, **require_case(case_id)})


@mcp.prompt()
def draft_case_reply(
    case_id: Annotated[str, Field(description="Case to answer, such as CASE-101.")],
    tone: Annotated[
        str,
        Field(description="Desired reply tone, such as professional or concise."),
    ] = "professional",
) -> list[base.Message]:
    """Draft a grounded reply for a selected inbox case."""
    return [
        base.UserMessage(
            f"Draft a {tone} reply for case '{case_id}'. First read the case resource "
            f"inbox://cases/{case_id}. Use only facts found there, clearly label any "
            "needed clarification, and do not promise actions that are not already "
            "authorized. Return a subject line followed by the reply body."
        )
    ]


@mcp.prompt()
def review_case(
    case_id: Annotated[str, Field(description="Case to review, such as CASE-102.")],
) -> list[base.Message]:
    """Review a case for clarity, ownership, risk, and next action."""
    return [
        base.UserMessage(
            f"Review case '{case_id}'. Read inbox://cases/{case_id}; identify missing "
            "facts, ownership gaps, and risk. If priority judgment is needed, explain "
            "the evidence before recommending the triage_case tool. Do not call "
            "set_case_status unless closure is explicitly supported."
        ),
        base.AssistantMessage(
            "I will structure the review as: Facts, Gaps, Risk, and Recommended next "
            "action. I will separate observed evidence from recommendations."
        ),
    ]


if __name__ == "__main__":
    logger.info("Starting inbox action MCP server")
    mcp.run(transport="stdio")
