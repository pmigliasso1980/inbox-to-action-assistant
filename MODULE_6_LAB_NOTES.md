# Module 6 Lab Submission — Resources

## Submission files

| Required artifact | Grader-facing path | Canonical implementation |
|---|---|---|
| Server with four tools and three resources | [`server.py`](server.py) | [`mcp-document-server/server.py`](mcp-document-server/server.py) |
| MIME-aware client | [`client.py`](client.py) | Root file is canonical |
| Resource inspection helper | [`show_resources.py`](show_resources.py) | [`mcp-document-server/show_resources.py`](mcp-document-server/show_resources.py) |
| Tool/resource smoke test | [`smoke.sh`](smoke.sh) | [`mcp-document-server/smoke.sh`](mcp-document-server/smoke.sh) |
| Lab notes | This file | — |

Run locally with the pinned environment:

```bash
mcp-document-server/.venv/bin/python show_resources.py
mcp-document-server/.venv/bin/python client.py
bash smoke.sh
```

## Part A — Define resources

### A1. Reproduced MIME-type bug

A temporary direct resource returned `list[str]` without `mime_type`. MCP SDK 1.30.0 reported and read:

```text
mime= text/plain
read= [ReadResourceContents(content='[\n  "a.md",\n  "b.md"\n]', mime_type='text/plain', meta=None)]
```

The return type did not make the resource JSON: the SDK serialized the list into JSON-looking text but
labelled it `text/plain`. A MIME-aware client would correctly decline JSON parsing and return a Python
string; calling code iterating it would then iterate individual characters without an exception or
warning.

The final catalog fixes both halves of the contract: it explicitly declares `application/json` and
returns a valid JSON string produced by `json.dumps`.

### A2. Correct direct and templated resources

`show_resources.py` observed:

```text
=== direct resources ===
docs://documents  mime=application/json  name=document_catalog

=== resource templates ===
docs://documents/{doc_id}  mime=text/plain
docs://documents/{doc_id}/stats  mime=application/json
```

Only the catalog appears in `list_resources()` because it is a concrete, immediately readable URI.
The other entries are URI patterns requiring a caller-provided `doc_id`; they describe families of
resources rather than concrete resources and therefore appear in `list_resource_templates()`.

The resource functions are named `document_catalog`, `document_contents`, and `document_stats`, so they
do not collide with the existing `list_documents` or `read_document` tools. Python function names form
server registration identities even though resource selection ultimately uses URIs.

### A3. Placeholder contract failure

Changing `{doc_id}` to `{document_id}` while leaving the function parameter unchanged failed immediately:

```text
ValueError: Mismatch between URI parameters {'document_id'} and function parameters {'doc_id'}
```

This occurred at decorator registration/import time, before any client read. Early failure is better
because a broken template cannot be advertised or survive until a production request.

### A4. Real-protocol verification

Inspector CLI `resources/list` returned:

```json
{
  "resources": [{
    "name": "document_catalog",
    "uri": "docs://documents",
    "mimeType": "application/json"
  }]
}
```

Inspector CLI `resources/templates/list` returned both patterns with `text/plain` and
`application/json`. The direct catalog read returned the expected wire shape:

```json
{
  "contents": [{
    "uri": "docs://documents",
    "mimeType": "application/json",
    "text": "[\"onboarding.docx\", \"plan.md\", \"report.pdf\"]"
  }]
}
```

The templated `docs://documents/plan.md` read returned a `contents` entry with its resolved URI,
`text/plain`, and document text. This matches the raw Module 2 protocol capture. In Inspector's resource
inventory, the direct resource is shown as a concrete selectable URI, while templates are shown
separately as parameterized URI patterns that require a `doc_id` before reading.

`smoke.sh` now asserts the tool inventory, successful and failed tool calls, direct resource inventory,
template inventory, JSON catalog read, and templated text read.

## Part B — Consume resources

### B1. Discover both inventories

The client observed one direct resource and two templates, matching in-process and Inspector results:

```text
--- direct resources ---
docs://documents  (application/json)  document_catalog

--- resource templates ---
docs://documents/{doc_id}  (text/plain)
docs://documents/{doc_id}/stats  (application/json)
```

The result fields are `.resources` and `.resourceTemplates`; the latter retains the protocol's
camelCase JSON field name. A client calling only `list_resources()` might report, “The document server
is missing its content and stats resources.” The answer is: “Those are templates; also call
`list_resource_templates()`.”

### B2. Deliberately naive reader

Before using the helper, the catalog's first entry had `text` of type `str`:

```text
["onboarding.docx", "plan.md", "report.pdf"]
```

A direct `for doc_id in ids` iterated `[`, `"`, `o`, `n`, and the remaining individual characters.
Nothing raised and no warning appeared. The client ignored the correctly declared
`application/json` MIME type and treated serialized JSON as an already-decoded collection.

### B3. MIME-aware reader

The centralized `read_uri` helper produced:

- catalog → Python `list`
- document contents → Python `str`
- stats → Python `dict`

Calling code therefore uses values without repeating MIME logic. Centralizing dispatch ensures every
resource read follows the same binary/JSON/text interpretation and future MIME support is added once.

Three defensive details matter:

- `hasattr(entry, "text")` supports a binary server returning `BlobResourceContents` with only `blob`.
- `startswith("application/json")` supports valid parameters such as
  `application/json; charset=utf-8`.
- `(entry.mimeType or "")` supports a nonconforming or legacy server omitting the MIME type without an
  `AttributeError`; its content safely falls back to text.

### B4. Failure asymmetry

Observed outcomes:

| Operation | Raises? | Error flag? | Observed mechanism |
|---|---:|---:|---|
| Failed `call_tool` | No | `isError=True` | Readable tool result |
| Failed templated `read_resource` | `McpError` | N/A | Resource exception |
| URI matching no resource/template | `McpError` | N/A | Resource dispatch exception |
| Dead server process | Connection-level exception | N/A | Transport/session failure |

The missing document message was more useful: it identified the failed template construction and
`Unknown document: ghost.md`. The nonsense scheme could only report `Unknown resource:
nonsense://nowhere`, because no resource implementation existed to add domain guidance.

Client rule: check `result.isError` after every tool call because tool failures return normally. Wrap
resource reads and the wider session in exception handling because resource, protocol, and connection
failures raise.

### Optional-context helper

`try_read_uri` returns a default only for `McpError`. This is appropriate when context is genuinely
optional and omission is visible or harmless, such as an optional enrichment panel. It is dangerous
for required policy, authorization, or decision context because substituting a default hides the loud
failure that resource semantics intentionally provide.

## Self-check

- Every resource decorator explicitly provides `mime_type`.
- Exactly one direct resource and two templates are registered.
- Resource function names do not collide with tool names.
- Catalog and stats decode to `list` and `dict`; document contents remain `str`.
- Client code checks tool `isError` and catches `McpError` for resource reads.
- Inspector smoke tests cover both tools and resources.
