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

echo "### resources/list"
RESOURCES_OUTPUT="$("${INSPECTOR[@]}" --method resources/list)"
echo "$RESOURCES_OUTPUT"
grep -q 'docs://documents' <<<"$RESOURCES_OUTPUT"
grep -q 'application/json' <<<"$RESOURCES_OUTPUT"

echo "### resources/templates/list"
TEMPLATES_OUTPUT="$("${INSPECTOR[@]}" --method resources/templates/list)"
echo "$TEMPLATES_OUTPUT"
grep -q 'docs://documents/{doc_id}' <<<"$TEMPLATES_OUTPUT"
grep -q 'docs://documents/{doc_id}/stats' <<<"$TEMPLATES_OUTPUT"

echo "### resources/read (direct JSON catalog)"
CATALOG_OUTPUT="$("${INSPECTOR[@]}" --method resources/read --uri docs://documents)"
echo "$CATALOG_OUTPUT"
grep -q 'application/json' <<<"$CATALOG_OUTPUT"
grep -q 'onboarding.docx' <<<"$CATALOG_OUTPUT"

echo "### resources/read (templated text)"
DOCUMENT_OUTPUT="$("${INSPECTOR[@]}" --method resources/read --uri docs://documents/plan.md)"
echo "$DOCUMENT_OUTPUT"
grep -q 'text/plain' <<<"$DOCUMENT_OUTPUT"
grep -q 'Project plan: phase one' <<<"$DOCUMENT_OUTPUT"

echo "### prompts/list"
PROMPTS_OUTPUT="$("${INSPECTOR[@]}" --method prompts/list)"
echo "$PROMPTS_OUTPUT"
grep -q 'format_document' <<<"$PROMPTS_OUTPUT"
grep -q 'summarize_document' <<<"$PROMPTS_OUTPUT"
grep -q 'review_document' <<<"$PROMPTS_OUTPUT"

echo "### prompts/get (summarize_document)"
PROMPT_OUTPUT="$("${INSPECTOR[@]}" --method prompts/get --prompt-name summarize_document --prompt-args doc_id=plan.md max_words=40)"
echo "$PROMPT_OUTPUT"
grep -q 'no more than 40 words' <<<"$PROMPT_OUTPUT"

echo "MCP smoke checks passed."
