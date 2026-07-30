"""WO-118 · Store v2 — `project.json` persistence, the §3.1 derivation, and the Log.

Four modules, and the split matters:

  * `project_store` — lossless persistence and the §3 invariants, including
    §4.4's origin protection.
  * `derive` — `SPEC.md` §3.1 and §3.4. **What renders is derived, never
    stored.** Anything reading `clip.segment` directly has misread v2.
  * `edits` — §4.3's controls (bin, restore, the hand edits) and §4.5's
    disposition writers.
  * `log_store` — §7.3's `log.json` sidecar: append, 500-entry eviction, the
    standing lines that are never evicted.

`FileProjectStore` satisfies the `ProjectStore` Protocol in
`backend/contracts/interfaces.py`. No HTTP concerns live here (WO-123).
"""

from backend.store.derive import (
    OutReason,
    effective_speed,
    effective_trim,
    in_reel,
    out_reason,
    played_duration_s,
    reel_length_s,
    source_for,
    unlinked_source_ids,
    whole_clip,
)
from backend.store.edits import (
    AcceptanceSummary,
    EditError,
    bin_clip,
    mark_proposals_accepted,
    reject_trim_proposal,
    restore_clip,
    set_clip_order,
    set_user_audio,
    set_user_segment,
    set_user_speed_ranges,
    toggle_bin,
)
from backend.store.log_store import (
    LOG_CAPACITY,
    FileLogStore,
    LogEntry,
    SessionLogBuffer,
    STANDING_TEXTS,
    evict,
    standing_entries,
)
from backend.store.project_store import (
    SUPPORTED_SCHEMA_VERSION,
    ConflictError,
    FileProjectStore,
    InvariantError,
    OriginProtectionError,
    ProjectNotFoundError,
    SchemaVersionError,
    StoreError,
    now_iso,
)

__all__ = [
    # persistence
    "FileProjectStore",
    "SUPPORTED_SCHEMA_VERSION",
    "StoreError",
    "ConflictError",
    "InvariantError",
    "OriginProtectionError",
    "ProjectNotFoundError",
    "SchemaVersionError",
    "now_iso",
    # §3.1 / §3.4 derivation
    "OutReason",
    "effective_trim",
    "effective_speed",
    "in_reel",
    "out_reason",
    "played_duration_s",
    "reel_length_s",
    "source_for",
    "unlinked_source_ids",
    "whole_clip",
    # §4.3 / §4.5 controls
    "AcceptanceSummary",
    "EditError",
    "bin_clip",
    "restore_clip",
    "toggle_bin",
    "set_clip_order",
    "set_user_audio",
    "set_user_segment",
    "set_user_speed_ranges",
    "mark_proposals_accepted",
    "reject_trim_proposal",
    # §7.3 Log sidecar
    "FileLogStore",
    "LogEntry",
    "LOG_CAPACITY",
    "STANDING_TEXTS",
    "SessionLogBuffer",
    "evict",
    "standing_entries",
]
