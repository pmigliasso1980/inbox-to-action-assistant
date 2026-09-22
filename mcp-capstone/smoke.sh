#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR"

INSPECTOR=(
  npx --yes
  --package node@22.19.0
  --package @modelcontextprotocol/inspector
  mcp-inspector --cli .venv/bin/python server.py
)

echo "### tools/list"
TOOLS_OUTPUT="$("${INSPECTOR[@]}" --method tools/list)"
echo "$TOOLS_OUTPUT"
grep -q 'triage_case' <<<"$TOOLS_OUTPUT"
grep -q 'assign_case' <<<"$TOOLS_OUTPUT"
grep -q 'set_case_status' <<<"$TOOLS_OUTPUT"

echo "### resources/list"
RESOURCES_OUTPUT="$("${INSPECTOR[@]}" --method resources/list)"
echo "$RESOURCES_OUTPUT"
grep -q 'inbox://cases' <<<"$RESOURCES_OUTPUT"
grep -q 'inbox://workload' <<<"$RESOURCES_OUTPUT"

echo "### prompts/list"
PROMPTS_OUTPUT="$("${INSPECTOR[@]}" --method prompts/list)"
echo "$PROMPTS_OUTPUT"
grep -q 'draft_case_reply' <<<"$PROMPTS_OUTPUT"
grep -q 'review_case' <<<"$PROMPTS_OUTPUT"

echo "### one tool call"
TOOL_OUTPUT="$("${INSPECTOR[@]}" --method tools/call --tool-name assign_case --tool-arg case_id=CASE-101 --tool-arg assignee=finance-team)"
echo "$TOOL_OUTPUT"
grep -q 'Assigned CASE-101 to finance-team' <<<"$TOOL_OUTPUT"

echo "### one resource"
RESOURCE_OUTPUT="$("${INSPECTOR[@]}" --method resources/read --uri inbox://cases/CASE-101)"
echo "$RESOURCE_OUTPUT"
grep -q 'Quarterly report approval' <<<"$RESOURCE_OUTPUT"
grep -q 'application/json' <<<"$RESOURCE_OUTPUT"

echo "### one prompt"
PROMPT_OUTPUT="$("${INSPECTOR[@]}" --method prompts/get --prompt-name draft_case_reply --prompt-args case_id=CASE-101 tone=concise)"
echo "$PROMPT_OUTPUT"
grep -q 'Draft a concise reply' <<<"$PROMPT_OUTPUT"

echo "Capstone smoke checks passed."
