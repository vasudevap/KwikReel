"""WO-117 · Frozen contract models v2 — the single source of truth for SPEC.md §3.

These Pydantic v2 models are the canonical, machine-checked expression of the
contract frozen in `SPEC.md` §3 (accepted 2026-07-28). They replace schema v1,
which was cut from the archived ES-001 and described a materially different
product: five approval gates, a nine-stage pipeline, three mutually-exclusive
audio modes, an AI selection assist, and no speed.

`frontend/src/types/contracts.ts` is GENERATED from these models by
`gen_types.py`; do not hand-edit the TypeScript. A drift-guard test
(`tests/contracts/test_ts_in_sync.py`) fails if the two disagree — that test IS
the "TS types and Pydantic models share one source of truth" gate.

Interfaces and types only. **No behaviour lives here** (WO-117 excludes it, as
WO-101 did). In particular the §3.1 derivation — `effective_trim` /
`effective_speed` — is WO-118's, in `backend/store/`. Any change to these shapes
is a change to a frozen contract: a stop-and-ask.

## The one structural idea, because everything below depends on it

**The assists do not mutate clips** (`SPEC.md` §3.1). `Clip.segment` and
`Clip.speed_ranges` hold *the user's* value and are null/empty unless the
matching `origin` field says `"user"`. What renders is derived at render time
from the user's value, the retained proposal, and the assist toggle. So:

- a field here is **not** "what renders" — it is "what the human set";
- reverting an assist is lossless because nothing was ever overwritten;
- stickiness is structural: once `origin.segments == "user"`, no assist can
  reach `segment`, because the derivation stops looking at proposals.

## What v1 had that v2 does not

`stage_approvals`, `AudioMode` and `Export.audio_modes`, `Clip.included`,
`Clip.deleted`, `Origin.included`, `IncludedProposal`, `OrderProposal`, and
`Segment.speed`. Membership and removal are **derived** (`SPEC.md` §3.4):
a clip is out of the reel when it is trimmed to nothing (`out_s <= in_s`),
unlinked, or damaged. There is no boolean for it.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# --- shared enums (SPEC.md §3) --------------------------------------------

# A field begins "default" (system initial, unedited); the first machine proposal
# moves the touched field to "proposed"; the first human edit to "user". Once
# "user", no assist may write it again — SPEC.md §4.4, a tested requirement.
OriginValue = Literal["default", "proposed", "user"]

# SPEC.md §4.5. Retained against the v3z draft by DECISIONS A-3, because it is
# the only thing that measures whether the assists earn their place. Its three
# writers: handle movement -> "adjusted", reject key -> "dismissed", and export
# -> "accepted" for everything untouched (A-3b). A field with no writer measures
# nothing, so the writers are part of the contract, not an implementation detail.
Disposition = Literal["pending", "accepted", "adjusted", "dismissed"]

Orientation = Literal["portrait", "landscape"]
Confidence = Literal["high", "med", "low"]

# SPEC.md §3.2. All 9:16 — 720x1280, 1080x1920, 2160x3840. The renderer reads
# the setting; WO-121 stops hardcoding TARGET_W/TARGET_H.
OutputResolution = Literal["720p", "1080p", "4k"]


class _Base(BaseModel):
    # Frozen contracts: reject unknown fields so schema drift surfaces loudly
    # rather than round-tripping silently. This is also what makes a v1 document
    # fail fast against v2 rather than load with fields quietly dropped.
    model_config = ConfigDict(extra="forbid")


# --- §4.1 · ReasonRecord (the transparency primitive) ---------------------

class ReasonRecord(_Base):
    """Why the machine proposed what it did. SPEC.md §4.1.

    `human_text` is written to be read: DECISIONS A-2 puts these in the Log,
    which is the only place a reason now appears. It is not a debug string.
    """
    code: str                       # machine-readable, stable (e.g. "LEADING_BLUR")
    human_text: str                 # plain-language; rendered verbatim into the Log
    evidence_refs: list[str]        # MUST cite the signal range that drove it
    score: float
    confidence: Confidence


# --- §3.2 · the two time primitives ---------------------------------------

class Segment(_Base):
    """A kept region of one clip, in seconds from that clip's start.

    **`out_s <= in_s` means "not in the reel"** (SPEC.md §3.4). Removal is
    trimming to nothing, which is why it needs no state of its own and why
    dragging a handle back revives the clip for free.

    Exactly one segment per clip — the Editor has one trim bar. Cutting a clip
    into several kept pieces is deferred (§13).
    """
    in_s: float
    out_s: float


class SpeedRange(_Base):
    """A speed ramp over a stretch of one clip.

    **Stored in SOURCE time — seconds from the clip's start, not fractions of
    the kept region** (SPEC.md §3.2). A ramp describes a stretch of *content*,
    so moving a trim handle must not slide the ramp off the thing it was
    computed for. The renderer clips ranges to the kept region at render time.

    `rate > 0`, and there is **no cap** (DECISIONS N-6). The assist's own rule
    never proposes above 2.0x; hand-set rates are uncapped, at a known and
    accepted audio cost (SPEC.md §4.2).
    """
    from_s: float
    to_s: float
    rate: float


class AudioSettings(_Base):
    """Per-clip audio. `retain=False` IS the row's mute switch (SPEC.md §5).

    Distinct from `AudioMix.clip_level`: the level is the *mix* across the whole
    reel, this is per-source. Default `True` — a clip keeps its own sound unless
    the user silences it.
    """
    retain: bool = True
    gain_db: float = 0.0


# --- §3.2 · origin + proposals --------------------------------------------

class Origin(_Base):
    """Did the effective value come from the system default, the machine, or the human?

    Four fields, not five: `included` is gone with the selection assist
    (DECISIONS A-5b). This is the whole stickiness mechanism — see the module
    docstring and SPEC.md §4.4.
    """
    order: OriginValue = "default"
    segments: OriginValue = "default"
    speed: OriginValue = "default"
    audio: OriginValue = "default"


class SegmentsProposal(_Base):
    """The machine's trim for one clip. Singular — one segment per clip (§3.2).

    `value` may be empty (`out_s <= in_s`), which removes the clip from the reel:
    DECISIONS A-6 retired the 1.0 s floor for user and machine alike. That case
    is **warned in the Log, never blocked** (SPEC.md §4.1 rule 4, §7.1).
    """
    value: Segment
    at: str                         # ISO-8601
    reasons: list[ReasonRecord]
    disposition: Disposition


class SpeedProposal(_Base):
    """The machine's ramps for one clip. Live in v2 — one clip may carry several.

    Retained after override for the same reason trim proposals are: it is what
    makes reverting the Speed toggle lossless (DECISIONS N-10).
    """
    value: list[SpeedRange]
    at: str
    reasons: list[ReasonRecord]
    disposition: Disposition


class Proposals(_Base):
    """What the assists last proposed — RETAINED after override (SPEC.md §3.1).

    Retention is not history-keeping; it is the mechanism. Reverting a toggle
    reads the proposal back, so nothing had to be stashed and nothing was lost.
    """
    segments: Optional[SegmentsProposal] = None
    speed: Optional[SpeedProposal] = None


class Clip(_Base):
    """One source's place in the reel.

    `segment` and `speed_ranges` hold **the user's** values and are null/empty
    unless the matching `origin` field says `"user"` (SPEC.md §3.1). They are
    not "what renders".
    """
    source_id: str
    order: int                      # dense, unique

    segment: Optional[Segment] = None            # the USER's trim
    speed_ranges: list[SpeedRange] = Field(default_factory=list)   # the USER's ramps

    # What bin/restore returns to (SPEC.md §4.3). Bin sets the effective trim to
    # zero length, stashing the previous effective value first; pressing it again
    # restores the stash. This field is the only reason removal is genuinely
    # non-destructive, and it is the one place a *derived* value is written down.
    stashed_segment: Optional[Segment] = None

    audio: AudioSettings = Field(default_factory=AudioSettings)
    origin: Origin = Field(default_factory=Origin)
    proposals: Proposals = Field(default_factory=Proposals)


# --- §3.3 · SourceIndex (immutable facts) ---------------------------------

class SourceIndex(_Base):
    """Unchanged from v1 (SPEC.md §3.3 says so explicitly)."""
    source_id: str                  # opaque, stable
    content_hash: str               # sha256 of bytes; also the relink repair key (§8.3)
    path: str                       # read-only absolute path; basename(path) is the
                                    # display label — there is no clip rename (§1)
    duration_s: float
    captured_at: Optional[str]      # ISO-8601 with tz offset, or null
    orientation: Orientation
    codec: str                      # "hevc" | "h264" | ...
    fps: float                      # float: real footage is often 29.97
    width: int
    height: int
    has_audio: bool
    has_gps: bool                   # presence flag only; coordinates never stored
    readable: bool = True           # false -> "damaged": out of the reel, surfaced (§3.4)
    proxy_path: Optional[str] = None  # derived; separate output directory


# --- §3.3 · analysis.json (facts, not decisions) --------------------------

class Signals(_Base):
    blur: list[float]               # per-second sharpness (Laplacian variance)
    exposure: list[float]           # per-second clipping score
    shake: list[float]              # per-second frame-to-frame instability
    motion_energy: list[float]      # per-second
    audio_rms: list[float]          # per-second
    people_count: Optional[int] = None   # declared and unused; a COUNT ONLY if it
                                         # ever arrives — identity never (§3.3)
    saliency_ref: Optional[str] = None   # deferred (§13)


class Analysis(_Base):
    source_id: str
    signals: Signals
    scene_cuts_s: list[float]
    dup_group: Optional[str] = None  # perceptual-hash cluster across clips
    run_id: str


# --- §3.2 · audio, music, export ------------------------------------------

class AudioMix(_Base):
    """The two levels, 0.0-1.0 — the UI's 0-100 divided by 100 (SPEC.md §3.2).

    **No on/off booleans.** "Lit" is derived from `> 0`, and the Sound unit's
    trace brightness is the slider position, so the display *is* the mix (§5).
    Both at zero exports silent — and must still carry a valid AAC track (§9).

    No defaults, deliberately. `SPEC.md` does not state an opening mix, and the
    v3z generator has none to transcribe: its `empty` state is 0/0 and its
    `loaded` state is a hand-drawn 62/78, which is a drawing, not a decision.
    Requiring both makes whoever creates a project choose visibly, rather than
    having the contract invent a product default nobody signed off.
    """
    music_level: float
    clip_level: float


class Music(_Base):
    """A user-supplied local track. Optional on `Project` — a track may be chosen
    before a project exists, which is why its peaks are keyed by content hash
    (SPEC.md §8).

    No `beats_s`/`sections`: beat and section detection are excluded (§1, §13).
    No peaks field: computed on demand and cached (§8).
    """
    track_ref: str                  # absolute path to a user-supplied local track
    content_hash: str
    duration_s: float
    in_s: float = 0.0               # where in the track the reel starts, set by
                                    # dragging the waveform (§5)


class QAReport(_Base):
    """Output QA verdict (SPEC.md §9). QA blocks export and states why.

    `resolution_ok` is checked against **the project's setting**, not a
    hardcoded 1080x1920 — that hardcoding is what WO-122 removes. `audio_ok` is
    re-derived from the two levels: `music_level > 0` means the output must not
    be silent; both at zero means it must be silent *and* still carry a valid
    AAC track.
    """
    passed: bool
    not_black: bool
    audio_ok: bool
    duration_ok: bool               # within ±0.5 s of the computed reel length
    resolution_ok: bool             # against the setting
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
    """One file, not one per mode (SPEC.md §3.2).

    v1 kept a map keyed by audio mode because the flow produced one file per
    mode. DECISIONS A-4 retired the modes, so a single record describes the one
    output there now is.
    """
    last_render: Optional[RenderRecord] = None


# --- §3.2 · project.json (the canonical document) -------------------------

class Project(_Base):
    """Canonical state. Versioned, and round-trips losslessly.

    Local only, and never committed — see `docs/CONSTRAINTS.md`. It holds an
    absolute path to private footage.
    """
    schema_version: Literal[2] = 2
    project_id: str                 # uuid
    created_at: str                 # ISO-8601
    updated_at: str                 # ISO-8601 — optimistic-concurrency key (§8.1)
    app_version: str

    name: Optional[str] = None      # display; basename(media_root) when unset
    media_root: str                 # absolute, read-only, one folder per project
    target_duration_s: float        # a reference shown to the user; **nothing
                                    # optimises toward it** (§4)
    output_resolution: OutputResolution

    # The assists. Live derivations, not stored mutations — see §3.1 and the
    # module docstring. Both default off: nothing happens until the user presses
    # one (DECISIONS A-1, which is what replaced the approval gates).
    trim_assist_on: bool = False
    speed_assist_on: bool = False

    audio: AudioMix
    music: Optional[Music] = None
    sources: list[SourceIndex]
    clips: list[Clip]
    export: Export = Field(default_factory=Export)


# The models WO-117 freezes, in dependency order — consumed by gen_types.py so
# the generated TypeScript covers exactly this set.
CONTRACT_MODELS = [
    ReasonRecord, Segment, SpeedRange, AudioSettings, Origin,
    SegmentsProposal, SpeedProposal, Proposals, Clip,
    SourceIndex, Signals, Analysis,
    AudioMix, Music, QAReport, RenderRecord, Export, Project,
]
