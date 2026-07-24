"""WO-101 · Frozen contract models — the single source of truth for ES-001 §4.

These Pydantic v2 models are the canonical, machine-checked expression of the
schemas frozen in `docs/specs/ES-001-manual-editor-core.md` §4 (as amended by
the 2026-07-24 WO-100 prototype gap resolutions, ES-001 §4.5).

`frontend/src/types/contracts.ts` is GENERATED from these models by
`gen_types.py`; do not hand-edit the TypeScript. A drift-guard test
(`tests/contracts/test_ts_in_sync.py`) fails if the two disagree — this is how
the "TS types and Pydantic models share one source of truth" gate is met.

Interfaces and types only. No behaviour lives here (WO-101 excludes behaviour).
Any change to these shapes is a change to a frozen contract: a stop-and-ask.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# --- shared enums (ES-001 §4) ---------------------------------------------

# G-1: a clip begins in "default" (system initial, unedited); the first machine
# proposal moves the touched field to "proposed"; the first human edit to "user".
OriginValue = Literal["default", "proposed", "user"]

# ADR-010: the user's terminal action on a proposal.
Disposition = Literal["pending", "accepted", "adjusted", "dismissed"]

Orientation = Literal["portrait", "landscape"]
Confidence = Literal["high", "med", "low"]
AudioMode = Literal["music", "clip", "silent"]


class _Base(BaseModel):
    # Frozen contracts: reject unknown fields so schema drift surfaces loudly
    # rather than round-tripping silently. Every M2/M3 field is already declared
    # in schema_version 1 (ES-001 §4), so `forbid` costs nothing here.
    model_config = ConfigDict(extra="forbid")


# --- §4.4 · ReasonRecord (the transparency primitive) ---------------------

class ReasonRecord(_Base):
    code: str                       # machine-readable, stable (e.g. "LEADING_BLUR")
    human_text: str                 # plain-language reason shown inline (ADR-006)
    evidence_refs: list[str]        # MUST cite the signal range that drove it
    score: float
    confidence: Confidence


# --- §4.1 · clip segment + speed ------------------------------------------

class SpeedRange(_Base):
    from_s: float
    to_s: float
    rate: float                     # always 1.0 in M1 (no speed assist until M3)


class Segment(_Base):
    in_s: float
    out_s: float
    speed: list[SpeedRange] = Field(default_factory=list)


class AudioSettings(_Base):
    retain: bool = False            # always False in v1 (§8.2); ducking is M2+
    gain_db: float = 0.0


# --- §4.1 · origin + proposals --------------------------------------------

class Origin(_Base):
    """Did the effective value come from the system default, the machine, or the human?"""
    included: OriginValue = "default"
    order: OriginValue = "default"
    segments: OriginValue = "default"
    speed: OriginValue = "default"
    audio: OriginValue = "default"


class SegmentsProposal(_Base):
    value: list[Segment]
    at: str                         # ISO-8601
    reasons: list[ReasonRecord]
    disposition: Disposition


class IncludedProposal(_Base):      # M2 — null in M1
    value: bool
    at: str
    reasons: list[ReasonRecord]
    disposition: Disposition


class OrderProposal(_Base):         # M2 — null in M1
    value: int
    at: str
    reasons: list[ReasonRecord]
    disposition: Disposition


class SpeedProposal(_Base):         # M3 — null in M1
    value: list[SpeedRange]
    at: str
    reasons: list[ReasonRecord]
    disposition: Disposition


class Proposals(_Base):
    """What the AI last proposed — RETAINED after override (ES-001 §4.1)."""
    segments: Optional[SegmentsProposal] = None
    included: Optional[IncludedProposal] = None   # M2
    order: Optional[OrderProposal] = None         # M2
    speed: Optional[SpeedProposal] = None         # M3


class Clip(_Base):
    source_id: str
    included: bool = True
    order: int
    deleted: bool = False           # a flag, never removal — restore is exact
    segments: list[Segment]         # effective value — what renders
    audio: AudioSettings = Field(default_factory=AudioSettings)
    origin: Origin = Field(default_factory=Origin)
    proposals: Proposals = Field(default_factory=Proposals)


# --- §4.2 · SourceIndex (immutable facts) ---------------------------------

class SourceIndex(_Base):
    source_id: str                  # opaque, stable
    content_hash: str               # sha256 of bytes
    path: str                       # read-only absolute path; basename(path) is
                                    # the canonical display label (G-3)
    duration_s: float
    captured_at: Optional[str]      # ISO-8601 with tz offset, or null
    orientation: Orientation
    codec: str                      # "hevc" | "h264" | ...
    fps: float                      # float: real footage is often 29.97
    width: int
    height: int
    has_audio: bool
    has_gps: bool                   # presence flag only; coordinates never stored
    readable: bool = True           # false → surfaced, never silently dropped
    proxy_path: Optional[str] = None  # derived; separate output directory


# --- §4.3 · analysis.json (facts, not decisions) --------------------------

class Signals(_Base):
    blur: list[float]               # per-second sharpness (Laplacian variance)
    exposure: list[float]           # per-second clipping score
    shake: list[float]              # per-second frame-to-frame instability
    motion_energy: list[float]      # per-second
    audio_rms: list[float]          # per-second
    people_count: Optional[int] = None   # M2 — COUNT ONLY when it arrives; identity never
    saliency_ref: Optional[str] = None   # deferred


class Analysis(_Base):
    source_id: str
    signals: Signals
    scene_cuts_s: list[float]
    dup_group: Optional[str] = None  # perceptual-hash cluster across clips
    run_id: str


# --- §4.1 · music, stage approvals, export --------------------------------

class Music(_Base):
    track_ref: str                  # absolute path to user-supplied local track (ADR-003)
    content_hash: str
    duration_s: float
    beats_s: list[float] = Field(default_factory=list)   # M3 — empty in M1
    sections: list = Field(default_factory=list)          # M3 — shape owned by M3


class StageApprovals(_Base):
    """Timestamps, so approvals survive reload and are auditable (§7).

    Live in M1: ingest, trim, finalize. selection (M2) and speed (M3) stay null
    and inert. Manual curation is un-gated human editing (G-6) — no field here.
    The resume point is DERIVED from these (G-8): the earliest live stage whose
    gate is still null; no `current_stage` field exists.
    """
    ingest: Optional[str] = None
    trim: Optional[str] = None       # LIVE in M1
    selection: Optional[str] = None  # M2 — inert
    speed: Optional[str] = None      # M3 — inert
    finalize: Optional[str] = None


class QAReport(_Base):
    """Output QA verdict (§8.3). Concretised here because project.json embeds it
    in export.last_render; WO-105 implements the checks that populate it."""
    passed: bool
    not_black: bool
    audio_ok: bool                  # matched to the mode's expectation (§8.3)
    duration_ok: bool               # within ±0.5 s of the timeline sum
    resolution_ok: bool             # exactly 1080×1920
    codec_ok: bool                  # H.264 / AAC
    safe_margins_ok: bool
    frame_count_ok: bool
    duration_s: float
    width: int
    height: int
    reasons: list[str] = Field(default_factory=list)  # human-readable failures


class RenderRecord(_Base):
    path: str
    rendered_at: str                # ISO-8601
    qa: Optional[QAReport] = None


class Export(_Base):
    audio_modes: list[AudioMode]    # modes the user has chosen to export
    # G-5: one render record per audio_mode — the flow produces one file per
    # mode, so a single last_render could not describe two outputs. Keys ∈ AudioMode.
    last_render: dict[str, RenderRecord] = Field(default_factory=dict)


# --- §4.1 · project.json (the canonical document) -------------------------

class Project(_Base):
    schema_version: Literal[1] = 1
    project_id: str                 # uuid
    created_at: str                 # ISO-8601
    updated_at: str                 # ISO-8601 — optimistic-concurrency key (§6)
    app_version: str

    name: Optional[str] = None      # G-2: display-only; basename(media_root) when unset
    media_root: str                 # absolute path — opened read-only, never written
    target_duration_s: float        # M1: displayed reference only; no optimizer

    music: Music
    sources: list[SourceIndex]
    clips: list[Clip]
    stage_approvals: StageApprovals = Field(default_factory=StageApprovals)
    export: Export


# The models WO-101 freezes, in dependency order — consumed by gen_types.py so
# the generated TypeScript covers exactly this set.
CONTRACT_MODELS = [
    ReasonRecord, SpeedRange, Segment, AudioSettings, Origin,
    SegmentsProposal, IncludedProposal, OrderProposal, SpeedProposal, Proposals,
    Clip, SourceIndex, Signals, Analysis, Music, StageApprovals,
    QAReport, RenderRecord, Export, Project,
]
