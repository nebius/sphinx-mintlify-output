"""YAML frontmatter rendering for Mintlify ``.mdx`` pages."""

from __future__ import annotations

import json
import re
from typing import Any


def render_frontmatter(data: dict[str, Any], defaults: dict[str, Any] | None) -> str:
    """Merge ``defaults`` and ``data`` and serialize as a YAML frontmatter block.

    ``data`` overrides ``defaults`` on conflicting keys. Returns an empty
    string when the merged mapping has no keys, so callers can prepend
    unconditionally.
    """
    merged: dict[str, Any] = {}
    merged.update(defaults or {})
    merged.update(data)
    if not merged:
        return ""
    lines = ["---"]
    for key, value in merged.items():
        lines.append(f"{key}: {format_yaml_value(value)}")
    lines.append("---")
    return "\n".join(lines)


# Strings that YAML 1.1/1.2 parses as bool, null or special floats.
# A title="true" must round-trip as the string "true", not as boolean True.
_YAML_AMBIGUOUS_KEYWORDS = frozenset(
    {
        "true",
        "false",
        "yes",
        "no",
        "on",
        "off",
        "y",
        "n",
        "null",
        "~",
        ".nan",
        ".inf",
        "-.inf",
    }
)

# A plain integer / float / scientific-notation / explicit-sign number.
_YAML_NUMBER_RE = re.compile(
    r"""
    ^[+-]?
    (?:
        \d+(?:\.\d*)?  # 12, 12.5, 12.
        | \.\d+        # .5
    )
    (?:[eE][+-]?\d+)?  # optional exponent
    $
    """,
    re.VERBOSE,
)


def _looks_like_yaml_scalar(text: str) -> bool:
    """Would PyYAML parse ``text`` as something other than a plain string?"""
    if text.lower() in _YAML_AMBIGUOUS_KEYWORDS:
        return True
    return bool(_YAML_NUMBER_RE.match(text))


def format_yaml_value(value: Any) -> str:
    """Serialize a single YAML value, supporting scalars + list/dict containers.

    Ambiguous strings — ``"true"`` / ``"yes"`` / ``"null"`` / numeric-looking
    — are emitted double-quoted so they round-trip as strings rather than
    being parsed as the matching YAML scalar type.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if value is None:
        return "null"
    if isinstance(value, list | tuple | dict):
        # JSON is a strict subset of YAML 1.2, so json.dumps produces
        # a valid (flow-style) YAML node for any JSON-compatible value.
        return json.dumps(value, ensure_ascii=False)
    text = str(value)
    needs_quote = (
        text == ""
        or any(ch in text for ch in ":#\n\"'")
        or text.strip() != text
        or _looks_like_yaml_scalar(text)
    )
    if needs_quote:
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return text
