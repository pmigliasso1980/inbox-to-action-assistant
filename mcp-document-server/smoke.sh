#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Inspector 2.7 requires Node >=22.19. The temporary Node package avoids
# modifying the developer's system installation and keeps this check reproducible.
INSPECTOR=(
  npx --yes
  --package node@22.19.0
  --package @modelcontextprotocol/inspector
  mcp-inspector --cli .venv/bin/python server.py
)

echo "### tools/list"
TOOLS_OUTPUT="$("${INSPECTOR[@]}" --method tools/list)"
echo "$TOOLS_OUTPUT"
grep -q 'read_document' <<<"$TOOLS_OUTPUT"
grep -q 'edit_document' <<<"$TOOLS_OUTPUT"
grep -q 'list_documents' <<<"$TOOLS_OUTPUT"
grep -q 'search_documents' <<<"$TOOLS_OUTPUT"

echo "### read_document (valid)"
VALID_OUTPUT="$("${INSPECTOR[@]}" --method tools/call --tool-name read_document --tool-arg doc_id=plan.md)"
echo "$VALID_OUTPUT"
grep -q 'Project plan: phase one, phase two, phase three.' <<<"$VALID_OUTPUT"
grep -q '"isError": false' <<<"$VALID_OUTPUT"

echo "### read_document (invalid — expect isError true)"
INVALID_OUTPUT="$("${INSPECTOR[@]}" --method tools/call --tool-name read_document --tool-arg doc_id=ghost.md || true)"
echo "$INVALID_OUTPUT"
grep -q 'Unknown document: ghost.md' <<<"$INVALID_OUTPUT"
grep -q '"isError": true' <<<"$INVALID_OUTPUT"

echo "MCP smoke checks passed."
