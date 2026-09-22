# Inbox Action MCP Server — Design

## Domain and store

This server represents the case-management boundary of an inbox-to-action assistant. A user wants an
AI assistant to inspect incoming cases, decide when a case needs triage, assign ownership, update
workflow state, and invoke consistent reply or review instructions without connecting to a real inbox.

The implementation uses this in-memory store:

```python
cases = {
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
```

Each process starts with a fresh copy; persistence is intentionally outside the capstone scope.

## Capability inventory

1. **List cases** — provide the current case catalog and workflow metadata.
2. **Read case details** — provide the complete content and metadata for one case.
3. **Triage a case** — let the model decide when a case should receive a justified priority.
4. **Assign a case** — set the team or person responsible for a case.
5. **Set case status** — move a case among open, pending, and closed states.
6. **Draft a reply** — inject the fixed rules for a grounded customer reply.
7. **Review a case** — inject a structured completeness and risk review exchange.
8. **Load triage policy** — provide the application with the fixed priority policy.
9. **Summarize open workload** — load current counts by status and priority.
10. **Prepare a handoff** — inject a repeatable handoff structure for a user-selected case.

## Classification

The deciding questions are applied in order: Q1 asks whether the capability changes state or needs
model-selected timing; Q2 asks whether it is read-only context chosen by the application/user; Q3 asks
whether it is a named repeatable instruction template.

| Capability | Primitive | Question that decided it | One-line justification |
|---|---|---|---|
| List cases | Resource | Q2: read-only context selected by application/user? | A host can load the JSON catalog without asking the model to invoke an action. |
| Read case details | Resource | Q2: read-only context selected by application/user? | A selected case is addressable, immutable context under an application-controlled URI. |
| Triage a case | Tool | Q1: does the model need to decide when it runs? | Triage is model-selected judgment whose timing depends on message meaning, even before state changes. |
| Assign a case | Tool | Q1: does it change anything? | Assignment mutates accountable ownership. |
| Set case status | Tool | Q1: does it change anything? | Status transition mutates workflow state and can close work. |
| Draft a reply | Prompt | Q3: named repeatable instruction template? | A user deliberately requests the same grounded-reply rules with only case and tone varying. |
| Review a case | Prompt | Q3: named repeatable instruction template? | A user triggers a stable three-pass review structure by name. |
| Load triage policy | Resource | Q2: read-only context selected by application/user? | Policy is fixed application-loaded context, not an executable action. |
| Summarize open workload | Resource | Q2: read-only context selected by application/user? | Counts are a computed read-only view with no reason for model-controlled invocation. |
| Prepare a handoff | Prompt | Q3: named repeatable instruction template? | The organization’s handoff format is reusable expert instruction selected by a user. |

The implementation focuses on three tools, three resources, and two prompts; the policy and handoff
capabilities remain documented extension points rather than inflating the assessed server.

## Three hard calls

### Triage a case: tool, not resource

Triage can be read-only in some systems, so a computed resource was plausible. I chose a tool because
the model must decide when semantic judgment is needed and supply the priority; Q1’s second clause wins
even without relying on the side effect of storing the result. The explicit invocation also makes the
model’s judgment auditable instead of silently embedding it in a read.

### Case details: resource, not tool

`read_case` would be easy to implement as a tool, but the application or user already knows which case
is selected and simply needs read-only context. A templated resource makes that control model explicit,
gives the data a stable identity, and avoids teaching the model to call a function merely to retrieve a
known record.

### Draft a reply: prompt, not tool

A `draft_reply` tool could appear convenient, but this server does not own or call a model. The real
capability is reusable instruction authored by the domain expert and intentionally selected by a user,
so a prompt preserves user control and leaves model execution to the host.

## Resource URI scheme

Scheme: `inbox` identifies read-only context owned by the inbox case system.

| URI | Kind | MIME type | Reason |
|---|---|---|---|
| `inbox://cases` | Direct | `application/json` | The catalog is structured data decoded into a list by clients. |
| `inbox://workload` | Direct | `application/json` | Status and priority counts are structured dashboard context. |
| `inbox://cases/{case_id}` | Template | `application/json` | A complete case is a structured object addressed by exact id. |

Every resource is side-effect free, and each decorator declares its MIME type explicitly.
