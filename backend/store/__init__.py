"""C-2 · Project store (WO-103). Lossless project.json persistence.

`FileProjectStore` satisfies the `ProjectStore` interface (WO-101) and enforces
the ES-001 §4.1 invariants on every save. No HTTP concerns live here (§6 / WO-106).
"""

from backend.store.project_store import (
    ConflictError,
    FileProjectStore,
    InvariantError,
    OriginProtectionError,
    ProjectNotFoundError,
    SchemaVersionError,
    StoreError,
)

__all__ = [
    "FileProjectStore",
    "StoreError",
    "ConflictError",
    "InvariantError",
    "OriginProtectionError",
    "ProjectNotFoundError",
    "SchemaVersionError",
]
