# Module 5 Lab Notes — Python MCP Client

## Step 1 — Connection and handshake

The client reported:

```text
connected to: inbox-case-server 1.30.0
capability groups: tools, resources, prompts
```

- `serverInfo.name` is `inbox-case-server`, from `FastMCP("inbox-case-server")` in `server.py`.
- Version `1.30.0` is the SDK-generated server implementation version; the application did not set an
  independent product version in `FastMCP(...)`. A host should not present it as though it were the
  inbox workflow's release version.
- Tools, resources, and prompts appear as supported capability groups. This means their MCP method
  families are safe to call; it does not prove any inventory exists, which requires the corresponding
  list operation.

With `initialize()` removed, the subprocess still launched—its safe stderr startup log appeared—but
the session performed no handshake or useful MCP operation and exited normally with status zero. This
proves that opening transport starts the server, while initialization is a separate required protocol
step.

## Step 2 — Tool discovery

Observed inventory:

```text
read_document(doc_id)  required=['doc_id']
edit_document(doc_id, old_text, new_text)  required=['doc_id', 'old_text', 'new_text']
list_documents()  required=[]
search_documents(query, scope, limit)  required=['query']
```

The names, descriptions, and schemas are identical to Inspector because both clients obtain the same
server-owned metadata through `tools/list`. `list_tools()` returns a result wrapper with `.tools` so
the protocol can add pagination cursors or other metadata without changing the list itself. All four
raw first-line descriptions remain distinguishable and concise outside Inspector's formatted UI.

## Step 3 — Deliberately buggy client

The temporary naive loop printed:

```text
report.pdf -> The quarterly report covers revenue and costs.
ghost.md -> Error executing tool read_document: Unknown document: ghost.md. Call list_documents for valid ids.
```

No exception propagated and the program did not stop. Without an explicit failure label, a downstream
consumer could treat the second line as the document's contents. The loop had two independent bugs: it
never checked `result.isError`, and it assumed the first content block was text and represented the
entire result.

The temporary buggy file was removed after the observation; the submitted `client.py` contains neither
mistake.

## Step 4 — Correct content handling

The corrected client clearly printed `ghost.md -> FAILED: ...`. For `list_documents` it observed:

```text
blocks returned: 3
text_of(...)      -> 'onboarding.docx\nplan.md\nreport.pdf'
structuredContent -> {'result': ['onboarding.docx', 'plan.md', 'report.pdf']}
```

There is one text block per list item because the SDK renders the typed `list[str]` result that way.
Using only the first block would incorrectly report that `onboarding.docx` was the entire inventory.
For code that needs a Python list, `structuredContent["result"]` is correct because it preserves the
declared machine-readable list; joined text is intended for a model or human reader.

## Step 5 — Full round trip and failure taxonomy

Within one client/server session, `plan.md` changed from `phase one` to `phase 1`, proving all calls
shared the same server subprocess and in-memory store.

| Failure | Raised? | `isError` | Detector |
|---|---:|---:|---|
| Bad document ID | No | `True` | Our `read_document` code |
| Text not found | No | `True` | Our `edit_document` code |
| Missing required argument | No | `True` | SDK/Pydantic argument validation |
| Limit 99 | No | `True` | SDK/Pydantic constraint validation |
| Unknown tool | No | `True` | MCP server dispatcher |

The unknown tool differs in origin: it never maps to a registered function or generated argument model,
so the dispatcher detects it. Under MCP SDK 1.30.0 it still uses the same tool-error result channel;
SDKs/servers may surface some dispatch failures differently, so client code must not assume this
version's exact mapping universally.

A client using only `try/except` would mishandle all five observed failures because none raised. A
client checking only `isError` would correctly handle all five in this experiment, but would mishandle
raised protocol, resource, subprocess, or connection failures outside this set. Therefore robust code
must check `isError` after every tool result **and** retain exception handling around the session and
transport.

## Step 6 — Reusable runner

`run_tool` centralizes text extraction and converts `isError:true` into `RuntimeError` for script-style
callers. The deliberate failure produced:

```text
RuntimeError | tool read_document failed: Error executing tool read_document: Unknown document: ghost.md. Call list_documents for valid ids.
```

Exception conversion is convenient for a script that should stop or branch immediately. A model host
often wants the opposite: preserve the failure content so the model can repair its arguments. I would
keep a lower-level function returning the complete MCP result, then layer `run_tool` for strict scripts
and a separate host adapter that converts both success and error blocks into model context.

## Stretch goal — Concurrent calls

Two `read_document` calls issued with `asyncio.gather` returned the correct report and onboarding text.
JSON-RPC request `id` values allow the client to correlate out-of-order responses with their requests;
that field was introduced in Module 2's wire exercise.

## Self-check

- Both transport and session use `async with`.
- `initialize()` is awaited before discovery or invocation.
- The subprocess command uses `sys.executable` and an absolute server path.
- Every final tool call checks `isError` directly or goes through `run_tool`.
- No final code indexes `result.content[0]`.
- The client completes without an unhandled exception and cleans up its subprocess.
