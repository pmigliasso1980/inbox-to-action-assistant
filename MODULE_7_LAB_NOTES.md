# Module 7 Lab Submission — Prompts

## Submission files

| Required artifact | Grader-facing path | Canonical implementation |
|---|---|---|
| Server with tools, resources, and prompts | [`server.py`](server.py) | [`mcp-document-server/server.py`](mcp-document-server/server.py) |
| Prompt-aware client and slash UI | [`client.py`](client.py) | Root file is canonical |
| Prompt inspection helper | [`show_prompts.py`](show_prompts.py) | [`mcp-document-server/show_prompts.py`](mcp-document-server/show_prompts.py) |
| Protocol smoke test | [`smoke.sh`](smoke.sh) | [`mcp-document-server/smoke.sh`](mcp-document-server/smoke.sh) |
| Lab notes | This file | — |

Run the non-interactive checks with:

```bash
mcp-document-server/.venv/bin/python show_prompts.py
mcp-document-server/.venv/bin/python client.py
bash smoke.sh
```

Run the slash-command interface with:

```bash
mcp-document-server/.venv/bin/python client.py --interactive
```

The explicit flag keeps automated grading and CI runs from blocking on `input()`.

## Part A — Define prompts

### A1. First prompt

Observed metadata and resolution:

```text
/format_document - Produce instructions to reformat a document into clean Markdown.
    doc_id (required)  -- no description --

/format_document -> 1 message(s)
[user] Reformat the document 'plan.md' into clean, well-structured Markdown. ...
```

- `/format_document` comes from the decorated Python function name; its menu description comes from
  that function's docstring.
- `doc_id` is required because its function parameter has no default value.
- The resolved message has the `user` role because the prompt function explicitly returned
  `base.UserMessage`; the SDK serialized that choice rather than inventing it.
- “Preserve all original meaning and do not invent new content” does the most work because it sets the
  fidelity boundary while the other instructions primarily control presentation.

### A2. Optional parameter and default

```text
/summarize_document - Produce instructions to summarize a document within a word limit.
    doc_id (required)  Which document to summarize.
    max_words (optional)  Upper bound on summary length.

[user] Summarize the document 'plan.md' in no more than 100 words. ...
```

Omitting `max_words` produced `100`, supplied by the Python function default. Sensible defaults are a
user-experience decision because they reduce questions and typing while preserving an override for the
less common case.

### A3. Multi-message prompt

`review_document` returned two messages in order: `user`, then `assistant`. The prefixed assistant
turn commits the conversation to a three-pass review structure before model generation begins, so the
next completion should continue that structure instead of deciding on a new one.

Prediction: the assistant prefill will usually be more reliable than appending another user
instruction because the generated continuation begins inside the promised structure. The user-only
version is less forceful but can be preferable for providers or hosts that do not support assistant
prefill consistently.

### A4. Real protocol and Inspector UI

Inspector CLI `prompts/list` returned all three prompts. Its metadata included:

```json
{
  "name": "summarize_document",
  "description": "Produce instructions to summarize a document within a word limit.",
  "arguments": [
    {"name": "doc_id", "description": "Which document to summarize.", "required": true},
    {"name": "max_words", "description": "Upper bound on summary length.", "required": false}
  ]
}
```

Inspector CLI `prompts/get` with `doc_id=plan.md max_words=40` returned one user message containing
`no more than 40 words`.

In the Inspector browser UI, the Prompts tab listed all three names and their human-readable
descriptions. Selecting `summarize_document` showed separate inputs: the text beneath `doc_id` was
`Which document to summarize. (Required)`, while `max_words` showed `Upper bound on summary length.`
without the required marker. Thus the UI derives both validation cues and help text from server-owned
prompt metadata.

## Part B — Consume prompts

### B1. Discovery

```text
/format_document(doc_id) - Produce instructions to reformat a document into clean Markdown.
/summarize_document(doc_id, max_words?) - Produce instructions to summarize a document within a word limit.
/review_document(doc_id, audience?) - Produce a two-turn review exchange for a document.
```

- The `?` comes from each argument's `required` field when it is `false`.
- `prompt.arguments or []` protects against a prompt with no arguments, where the SDK may expose
  `None`; iterating `None` directly would raise `TypeError`.
- All three descriptions read as user-facing menu actions rather than model tool-selection guidance.

### B2. String argument rule

Passing integer `40` produced:

```text
ValidationError
1 validation error for GetPromptRequestParams
arguments.max_words
  Input should be a valid string [type=string_type, input_value=40, input_type=int]
```

`GetPromptRequestParams` proves the SDK rejected the value while constructing the client request,
before it was sent over the wire. Passing `"40"` succeeded; FastMCP/Pydantic converted the transported
string to the server function's declared `int` before calling it.

Rule: declare the semantic type the prompt implementation needs on the server, but send every prompt
argument as a string from the client. The server framework validates and coerces those strings against
the function annotations.

### B3. Conversation turns

`review_document` returned two turns with `user` and `assistant` roles; the other prompts each returned
one user turn. `as_conversation` checks `content.type` before reading `.text` because an embedded image
or other non-text content block may not expose that attribute, which would otherwise crash the client.

The client contributed discovery, correct argument transport, safe content conversion, and preservation
of message order and roles. It did not author or improve the instructions themselves; that model-facing
expertise came from the server prompt.

### B4. Slash-command interface

Recorded interactions:

1. `sum` resolved by prefix to `/summarize_document`.
2. `f` resolved by prefix to `/format_document`.
3. `re` resolved by prefix to `/review_document`; there was exactly one match, so it was not ambiguous.
4. Skipping optional `max_words` resolved the prompt with the server default of `100`.
5. Entering `25` produced `no more than 25 words`; `input()` already returned the digits as a string.
6. Leaving required `doc_id` empty printed `doc_id is required — aborting`, and no prompt request was sent.

Case 6 was possible because the server supplied `required: true`. Without that metadata-driven client
check, the user would receive a lower-level protocol/validation error after submission instead of an
immediate field-specific message.

The loop never converts input types because Python `input()` returns strings, exactly the transport type
required by MCP prompt arguments. A production host would add richer form controls and persistent
history; it would also need cancellation, accessibility, authentication, and more detailed error states.

## Self-check

- Three prompts appear in both in-process and protocol discovery.
- `summarize_document` exposes two described arguments with correct required flags and defaulting.
- `review_document` resolves to ordered user and assistant messages.
- The integer failure is demonstrated and attributed to client request validation.
- Every successful client argument is transported as a string.
- Conversation conversion ignores non-text content safely.
- The slash loop supports prefix completion, optional omission, and required-field validation.
- Inspector smoke covers tools, resources, prompt listing, and prompt resolution.
