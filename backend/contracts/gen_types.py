"""WO-101 · Generate `frontend/src/types/contracts.ts` from the Pydantic models.

The Pydantic models in `models.py` are the single source of truth. This script
walks their JSON Schema and emits matching TypeScript interfaces, so the two
cannot drift. `tests/contracts/test_ts_in_sync.py` regenerates and asserts the
committed `.ts` is byte-identical to this output — that test IS the "one source
of truth" gate. Standard library only (no new dependency; the manifest set is
frozen and WO-101-owned).

Run `python -m backend.contracts.gen_types` to (re)write the committed file.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic.json_schema import models_json_schema

from backend.contracts.models import CONTRACT_MODELS

# frontend/src/types/contracts.ts, relative to the repo root (this file is at
# backend/contracts/gen_types.py → parents[2] is the repo root).
TS_OUTPUT_PATH = Path(__file__).resolve().parents[2] / "frontend" / "src" / "types" / "contracts.ts"

_HEADER = """\
// GENERATED FILE — DO NOT EDIT.
// Source of truth: backend/contracts/models.py (ES-001 §4, as amended §4.5).
// Regenerate with:  python -m backend.contracts.gen_types
// Drift is caught by tests/contracts/test_ts_in_sync.py.
"""

# JSON Schema primitive type -> TypeScript type
_PRIMITIVES = {
    "string": "string",
    "integer": "number",
    "number": "number",
    "boolean": "boolean",
    "null": "null",
}


def _ref_name(ref: str) -> str:
    """'#/$defs/SourceIndex' -> 'SourceIndex'."""
    return ref.rsplit("/", 1)[-1]


def _literal(value: object) -> str:
    """A Python/JSON value -> its TypeScript literal form."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, str):
        return json.dumps(value)  # quoted, escaped
    return str(value)  # int / float


def _ts_type(node: dict) -> str:
    """Map a JSON Schema node to a TypeScript type expression."""
    if "$ref" in node:
        return _ref_name(node["$ref"])

    if "const" in node:
        return _literal(node["const"])

    if "enum" in node:
        return " | ".join(_literal(v) for v in node["enum"]) or "never"

    # Optional / unions: anyOf | oneOf -> a TS union (e.g. `T | null`)
    for key in ("anyOf", "oneOf"):
        if key in node:
            parts = [_ts_type(sub) for sub in node[key]]
            # de-duplicate while preserving order
            seen: list[str] = []
            for p in parts:
                if p not in seen:
                    seen.append(p)
            return " | ".join(seen)

    node_type = node.get("type")

    if node_type == "array":
        items = node.get("items")
        if not items:
            return "unknown[]"
        inner = _ts_type(items)
        # Parenthesise a union before the [] suffix: `("a" | "b")[]`, not `"a" | "b"[]`.
        if "|" in inner:
            inner = f"({inner})"
        return f"{inner}[]"

    if node_type == "object":
        # dict[str, X] -> { [key: string]: X }
        addl = node.get("additionalProperties")
        if isinstance(addl, dict):
            return f"{{ [key: string]: {_ts_type(addl)} }}"
        if "properties" in node:  # inline object (not used by our models, handled for completeness)
            return _inline_object(node)
        return "{ [key: string]: unknown }"

    if isinstance(node_type, list):  # e.g. ["string", "null"]
        return " | ".join(_PRIMITIVES.get(t, "unknown") for t in node_type)

    if node_type in _PRIMITIVES:
        return _PRIMITIVES[node_type]

    return "unknown"


def _inline_object(schema: dict) -> str:
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    fields = []
    for prop, sub in props.items():
        opt = "" if prop in required else "?"
        fields.append(f"{prop}{opt}: {_ts_type(sub)}")
    return "{ " + "; ".join(fields) + " }"


def _emit_interface(name: str, schema: dict) -> str:
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    lines = [f"export interface {name} {{"]
    for prop, sub in props.items():  # property order follows field definition order
        optional = prop not in required
        ts = _ts_type(sub)
        lines.append(f"  {prop}{'?' if optional else ''}: {ts};")
    lines.append("}")
    return "\n".join(lines)


def generate() -> str:
    """Return the full TypeScript contract source as a string."""
    _, combined = models_json_schema(
        [(m, "serialization") for m in CONTRACT_MODELS],
        ref_template="#/$defs/{model}",
    )
    defs: dict = combined.get("$defs", {})

    blocks = [_HEADER]
    # Deterministic order so the drift-guard is stable run-to-run.
    for name in sorted(defs):
        blocks.append(_emit_interface(name, defs[name]))
    return "\n\n".join(blocks) + "\n"


def main() -> None:
    TS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    TS_OUTPUT_PATH.write_text(generate(), encoding="utf-8")
    print(f"wrote {TS_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
