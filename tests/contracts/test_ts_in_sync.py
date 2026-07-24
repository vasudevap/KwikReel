"""WO-101 gate · TS types and Pydantic models share one source of truth.

The committed `frontend/src/types/contracts.ts` must be exactly what
`gen_types.generate()` produces from the models. If this fails, the models
changed without regenerating — run `python -m backend.contracts.gen_types`.
"""

from __future__ import annotations

from backend.contracts.gen_types import TS_OUTPUT_PATH, generate


def test_committed_typescript_matches_the_models() -> None:
    assert TS_OUTPUT_PATH.exists(), "run: python -m backend.contracts.gen_types"
    on_disk = TS_OUTPUT_PATH.read_text(encoding="utf-8")
    assert on_disk == generate(), (
        "frontend/src/types/contracts.ts is out of sync with the Pydantic models. "
        "Regenerate: python -m backend.contracts.gen_types"
    )
