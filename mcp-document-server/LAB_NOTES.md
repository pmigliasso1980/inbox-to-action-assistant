# Module 3 Lab Notes — First MCP Server

## Toolchain

| Tool | Observed version |
|---|---|
| Python | 3.11.3 |
| Node.js | 20.10.0 |
| `uv` | Not installed |
| Environment path | Path B: `venv` + `pip` |
| MCP Python SDK | 1.30.0 |

## Healthy startup

Verified with stdin held open: the process was still running after 0.5 seconds and stdout contained no
bytes. A healthy stdio server waits without protocol output because stdout is reserved for JSON-RPC;
the retained startup diagnostic goes to stderr and therefore does not corrupt the client connection.
The process terminated when sent a termination signal.

## Controlled failure observations

| Break | Observed distinguishing symptom |
|---|---|
| Bad import: `mcp.server.fastmcpp` | `ModuleNotFoundError: No module named 'mcp.server.fastmcpp'` |
| Missing entry point | No output or traceback; immediate normal exit with `exit=0` |
| Invalid transport: `studio` | `ValueError: Unknown transport: studio` |
| Stray `print()` | Unbuffered/terminal stdout contained `Server starting up!\n`; no error is raised before a client tries to parse it |

### Why the missing entry point is silent

Python successfully imports the SDK and constructs the server object, but no code calls `mcp.run()`,
so the program reaches the end normally and exits with status zero.

### Why a stray print appears to work

A direct run has no client parsing stdout, so `print("Server starting up!")` looks harmless while the
server continues waiting. Once a client connects, it interprets that non-JSON line as a protocol
message and fails JSON decoding; the diagnostic belongs on stderr via `logging`.

## Stream separation

Verified by discarding stderr while holding stdin open: the process remained running and stdout was
empty. This proves the retained startup log uses stderr and stdout remains protocol-only.

## Raw initialization response

Captured from `bash handshake.sh`:

```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18","capabilities":{"experimental":{},"prompts":{"listChanged":false},"resources":{"subscribe":false,"listChanged":false},"tools":{"listChanged":false}},"serverInfo":{"name":"inbox-case-server","version":"1.30.0"}}}
```

FastMCP 1.x declares the tools, resources, and prompts capability groups even when their inventories
are empty. The handshake therefore says which method families are safe to call, not whether anything
is registered; a client must call `tools/list`, `resources/list`, or `prompts/list` to learn inventory.

After the first tools are added in Module 4, the capability block is expected to remain the same while
the result of `tools/list` changes from an empty array to registered tool schemas.

## Reproduction

A colleague can reproduce the isolated environment with:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

The version constraint prevents an automatic upgrade to the incompatible 2.x API; an exact
`requirements-lock.txt` records the exact successful environment in addition to the intentional 1.x
range in `requirements.txt`.
