# Module 5 Lab Submission — MCP Client

> Module 6 resource evidence is in [`MODULE_6_LAB_NOTES.md`](MODULE_6_LAB_NOTES.md). This file remains
> the Module 5 client record.

## Submission files

| Required artifact | Repository-root file | Extended evidence |
|---|---|---|
| MCP client | [`client.py`](client.py) | [`mcp-document-server/client.py`](mcp-document-server/client.py) |
| MCP server | [`server.py`](server.py) | [`mcp-document-server/server.py`](mcp-document-server/server.py) |
| Lab notes | This file | [`mcp-document-server/MODULE_5_LAB_NOTES.md`](mcp-document-server/MODULE_5_LAB_NOTES.md) |

Run the graded client from the repository root:

```bash
mcp-document-server/.venv/bin/python client.py
```

The server is launched by the client through `sys.executable`; it must not be started separately.

## Handshake and discovery evidence

Observed initialization:

```text
connected to: inbox-case-server 1.30.0
```

`inbox-case-server` comes from `FastMCP("inbox-case-server")`. Version 1.30.0 is the SDK-generated
implementation version, not a separately configured product release. The response advertises tools,
resources, and prompts, which says those method families are supported—not that each has inventory.

Observed `tools/list` inventory:

```text
read_document(doc_id) required=['doc_id']
edit_document(doc_id, old_text, new_text) required=['doc_id', 'old_text', 'new_text']
list_documents() required=[]
search_documents(query, scope, limit) required=['query']
```

The metadata matches Inspector because both use the server-owned `tools/list` response. The SDK wraps
the list in a result object so pagination metadata can be added alongside `.tools`.

## Deliberate buggy version

The required naive loop was run temporarily and then removed. It printed:

```text
report.pdf -> The quarterly report covers revenue and costs.
ghost.md -> Error executing tool read_document: Unknown document: ghost.md. Call list_documents for valid ids.
```

No exception propagated. The loop's two bugs were failure to check `result.isError` and assuming
`result.content[0]` was text representing the complete result. A consumer could mistake the error text
for document contents.

## Correct content handling

The submitted client checks `isError` and iterates over typed content. `list_documents` produced:

```text
blocks returned: 3
text_of(...)      -> 'onboarding.docx\nplan.md\nreport.pdf'
structuredContent -> {'result': ['onboarding.docx', 'plan.md', 'report.pdf']}
```

There is one text block per item. Reading only the first would silently lose two documents. A script
that needs a list should use `structuredContent["result"]`; text blocks are suitable for a model or
human reader.

## State round trip

```text
before: Project plan: phase one, phase two, phase three.
edit  : Updated plan.md.
after : Project plan: phase 1, phase two, phase three.
```

The edit remains visible because the calls share one server process and its in-memory dictionary. It
resets after reconnecting because a new subprocess creates a fresh dictionary.

## Five failure modes

| Failure | Raised? | `isError` | Detector |
|---|---:|---:|---|
| Bad document ID | No | `True` | Tool code |
| Text not found | No | `True` | Tool code |
| Missing required argument | No | `True` | SDK/Pydantic validation |
| Limit 99 | No | `True` | SDK/Pydantic validation |
| Unknown tool | No | `True` | Server dispatcher |

Under MCP SDK 1.30.0 all five arrived as tool-error results. `try/except` alone would therefore
mishandle all five. Checking only `isError` handles these five but misses raised transport, protocol,
resource, and subprocess failures. Robust clients need both mechanisms.

`run_tool` converts tool-error results to `RuntimeError`, which is convenient for scripts. A model host
should retain a lower-level path that passes readable failure content back to the model so it can repair
its call.

## Additional verification

- Removing `initialize()` still launched the server, but performed no handshake or useful operation.
- Both the transport and session use `async with`, guaranteeing subprocess and pipe cleanup.
- The final client never indexes `result.content[0]`.
- Two concurrent reads returned the correct corresponding contents; JSON-RPC request IDs make response
  correlation safe.
- The client ran end to end without an unhandled exception.
