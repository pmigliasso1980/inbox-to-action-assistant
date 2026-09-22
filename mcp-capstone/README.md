# MCP Capstone — Inbox Action Server

This standalone capstone implements an in-memory inbox case-management MCP server with all three
primitives: three model-controlled tools, three application-controlled resources, and two
user-controlled prompts.

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python show_all.py
.venv/bin/python client.py
bash smoke.sh
```

See [`DESIGN.md`](DESIGN.md) for primitive classification and [`REVIEW.md`](REVIEW.md) for the design
defence and risk audit.
