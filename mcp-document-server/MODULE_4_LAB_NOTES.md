# Module 4 Lab Notes — Tools and Inspector

## Environment

- Python: 3.11.3
- MCP Python SDK: 1.30.0
- Default Node visible in the project shell: 18.14.2
- Inspector: 2.7.0, run with a temporary Node 22.19.0 package because Inspector requires Node
  22.19.0 or newer
- Server identity: `inbox-case-server`, retained from the Module 3 honest-naming stretch goal

The current Inspector initially failed under the default Node runtime with
`Error running MCP Inspector: CustomEvent is not defined`. Running the same Inspector with Node
22.19.0 succeeded. This was an Inspector runtime failure, not a server or MCP transport failure.

## Part A — Tools and generated schemas

### A2. Schema origins

1. The tool `name` comes from the decorated Python function name, such as `read_document`.
2. The tool `description` comes from the complete function docstring, including its second paragraph.
3. `inputSchema.properties.doc_id.description` comes from the `Field(description=...)` metadata inside
   `Annotated`.
4. `required` contains `doc_id` because that parameter has no Python default.
5. A `str` return becomes an object output schema with a required `result` property of type `string`:

```json
{
  "properties": {"result": {"title": "Result", "type": "string"}},
  "required": ["result"],
  "type": "object"
}
```

### A3. Remaining schemas

`edit_document` lists `doc_id`, `old_text`, and `new_text` as required. `list_documents` has
`"properties": {}`, which tells the model to call it with an empty argument object.

### A4. Direct calls

The direct happy path returned the sorted ids `onboarding.docx`, `plan.md`, and `report.pdf`.
`read_document("plan.md")` initially returned `Project plan: phase one, phase two, phase three.` After
`edit_document` replaced the first occurrence, a second read returned
`Project plan: phase 1, phase two, phase three.` The edit persisted because all direct calls shared one
imported server process and its in-memory `docs` dictionary.

The three direct failures were:

```text
ToolError - Error executing tool read_document: Unknown document: ghost.md. Call list_documents for valid ids.
ToolError - Error executing tool edit_document: Text not found in plan.md: 'not present'. Read the document and retry with exact text.
ToolError - Error executing tool read_document: 1 validation error for read_documentArguments
doc_id
  Field required [type=missing, input_value={}, input_type=dict]
```

Direct `mcp.call_tool` converts domain and validation exceptions into `ToolError` in the caller's
Python process. Across MCP transport, the server/SDK catches the same failure and serializes it as a
normal JSON-RPC result with `isError: true`, making the message available to the model without breaking
the connection.

The missing `doc_id` was rejected by SDK/Pydantic validation before `read_document` ran. The phrase
`validation error for read_documentArguments` and `Field required` proves that the generated argument
model, not the function's dictionary lookup, rejected it.

### A5. Constraint enforcement

The generated `search_documents` schema contains:

```json
{
  "scope": {
    "default": "both",
    "enum": ["title", "body", "both"]
  },
  "limit": {
    "default": 5,
    "minimum": 1,
    "maximum": 10
  },
  "required": ["query"]
}
```

The SDK rejected `limit=99` with `Input should be less than or equal to 10` and rejected
`scope="footer"` with `Input should be 'title', 'body' or 'both'`. Neither call reached the function
body: argument-model validation failed before dispatch, so there was no search result or tool logic to
observe.

## Part B — Inspector and real transport

### B1. Connection

Inspector CLI completed the initialization handshake and reported server name `inbox-case-server`.
`tools/list` returned exactly four tools. No resources or prompts are registered yet, so those
inventories are empty; Modules 6 and 7 add them. The direct Inspector route needed only a command that
starts the stdio server: `.venv/bin/python server.py`.

### B2. Happy path

Observed results, combining direct same-process verification with Inspector transport checks:

- `list_documents` → `onboarding.docx`, `plan.md`, `report.pdf`.
- `read_document(plan.md)` → `Project plan: phase one, phase two, phase three.`
- `edit_document(plan.md, "phase one", "phase 1")` → `Updated plan.md.`
- A subsequent read in the same process → `Project plan: phase 1, phase two, phase three.`
- `search_documents("laptop")` → `onboarding.docx`, because its body contains “laptop.”
- `search_documents("report", scope="title")` → `report.pdf`; body scope returns no match because the
  word “report” occurs in the id but not in its contents.

Reconnecting launches a new subprocess and recreates the in-memory dictionary, so `plan.md` returns to
`phase one`. Persistence across calls proves process-local state; reset after reconnect proves it is not
durable storage.

### B3. Failure path and recovery

| Failure | Returned message | Recoverable from message alone? |
|---|---|---|
| Unknown document | `Unknown document: ghost.md. Call list_documents for valid ids.` | Yes; it names the bad id and the discovery action. |
| Text absent | `Text not found in plan.md: 'this text is not present'. Read the document and retry with exact text.` | Yes; it names the file/text and tells the caller how to recover. |
| Missing `doc_id` | `Field required` in `read_documentArguments` validation | Mostly; it identifies the missing field, though a host should present it cleanly. |
| `limit=99` | `Input should be less than or equal to 10` | Yes; it states the accepted boundary. |

The first two calls passed schema validation, entered our functions, and raised domain-specific
`ValueError`s. The latter two were rejected by generated SDK validation before our functions ran. The
limit rejection is a design win because invalid state is excluded centrally and consistently instead
of being reimplemented inside every code path.

Inspector showed the domain failure as a result containing a text content block and `"isError": true`,
not as a JSON-RPC `error` object. The process and connection remained healthy.

### B4. Model-facing design review

| Tool | Can its form be completed without source? | Design finding |
|---|---|---|
| `read_document` | Yes | The id description names `list_documents`, case sensitivity, and an example. |
| `edit_document` | Yes | All three fields distinguish exact input, replacement, and empty replacement behavior. |
| `list_documents` | Yes | It has no fields and clearly describes the returned ids. |
| `search_documents` | Yes | Scope choices, default, query behavior, and the 1–10 limit are visible in schema. |

The names make selection unambiguous: use `edit_document` to change a typo and `list_documents` to
discover available ids. Descriptions are limited to purpose, selection guidance, and non-obvious
constraints.

Two improvements over the starter version were made before final inspection:

1. `doc_id` now says that ids are case-sensitive, gives an example, and tells the caller to obtain them
   from `list_documents`; a plain “id of the document” did not tell the model which strings are valid.
2. `edit_document.old_text` now declares exact, case-sensitive, non-empty matching, while the docstring
   states first-occurrence-only behavior and failure atomicity. The error also tells the caller to read
   and retry with exact text.

The Inspector subprocess caches the server code for the life of the connection. A description edited
on disk is therefore absent from the existing connection's cached `tools/list` result and appears only
after reconnecting; this is expected subprocess isolation, not a failed edit.

### B5. Scripted Inspector checks

`tools/list` returned the four names, descriptions, input schemas, and output schemas. A valid
`read_document` transport call returned:

```json
{
  "content": [{"type": "text", "text": "Project plan: phase one, phase two, phase three."}],
  "structuredContent": {"result": "Project plan: phase one, phase two, phase three."},
  "isError": false
}
```

The invalid call returned:

```json
{
  "content": [{"type": "text", "text": "Error executing tool read_document: Unknown document: ghost.md. Call list_documents for valid ids."}],
  "isError": true
}
```

This matches the Module 2 wire shape: typed `content`, optional `structuredContent` on success, and an
`isError` flag. `smoke.sh` asserts all four tools, the valid content, and the expected error result; it
exits nonzero if any assertion fails.

### B6. Summary

Direct calls and transport calls executed the same logic, but failures changed representation:
`ToolError` exceptions in the direct Python caller became readable `isError:true` MCP results over the
wire. `read_document` had the weakest starter description, so it was strengthened with identifier
provenance, case sensitivity, and a concrete example. A server should work in Inspector before a model
is connected because Inspector isolates transport, handshake, schema, validation, dispatch, and tool
logic from model selection and host orchestration.
