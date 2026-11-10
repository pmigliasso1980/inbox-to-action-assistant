"""Stable prompt-prefix helpers that avoid silent cache invalidation."""
from __future__ import annotations

import json
from typing import Any


def stable_json(value: Any) -> str:
    """Serialize prompt data deterministically; never include run ids or timestamps here."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def split_prompt(stable_instructions: str, item_payload: dict) -> tuple[str, str]:
    """Keep the reusable prefix in the cacheable system block and item data late."""
    return stable_instructions.strip(), stable_json(item_payload)
