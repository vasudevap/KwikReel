"""WO-117 · Service interfaces v2 — the seams every other ADP-002 lane codes against.

Structural `Protocol`s, not implementations (WO-117 excludes behaviour). Each
service WO provides a concrete class satisfying one Protocol; the HTTP layer
(WO-123) and the frontend code against these, never against implementations.
Signatures follow `SPEC.md` §8 and the ADP-002 §4 Work Order set.

## What changed from v1, and why

- **`Renderer.render_draft` is gone.** The Monitor sequences proxies in the
  browser (`SPEC.md` §6); the server renders once, on Save. There is no
  server-side draft to ask for.
- **`audio_mode` is gone from `Renderer.export` and `OutputQA.validate_render`.**
  DECISIONS A-4 replaced three mutually-exclusive modes with two levels and one
  exported file, so the mode is no longer a parameter of anything.
- **`TrimProposer` may now return an empty segment.** The 1.0 s floor is retired
  (A-6), which changes this seam's contract, not just its implementation.
- **`SpeedProposer` is new and live** (A-5a, N-10).
- **`MediaService` is new** — thumbnails, peaks and the native pickers, which v1
  had no seam for.
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from backend.contracts.models import (
    Analysis,
    Music,
    Project,
    QAReport,
    RenderRecord,
    SegmentsProposal,
    SourceIndex,
    SpeedProposal,
)


@runtime_checkable
class IngestService(Protocol):
    """WO-102 (survives). Probe sources and build proxies. Read-only beneath media_root."""

    def probe_clip(self, path: str) -> SourceIndex: ...

    def validate_readable(self, path: str) -> bool: ...

    def make_proxy(self, source: SourceIndex) -> str:
        """Return the proxy_path; never writes beneath media_root."""
        ...

    def build_source_index(self, media_root: str) -> list[SourceIndex]:
        """Probe every clip under media_root; unreadable ones retained readable=False."""
        ...


@runtime_checkable
class ProjectStore(Protocol):
    """WO-118. Lossless project.json persistence with optimistic concurrency."""

    def save(self, project: Project) -> Project:
        """Persist and return the project with a bumped updated_at.

        Raises on an updated_at mismatch (HTTP maps this to 409, SPEC.md §8.1).
        Enforces the §3 invariants: `origin` recorded on every mutation,
        proposals retained on override, `disposition` written by its three
        writers (§4.5), `order` dense and unique.

        **It also enforces the one that matters most (§4.4): an assist never
        changes a field whose `origin` is `"user"`.** With the approval gates
        gone that is the entire mechanism by which the person editing stays in
        charge, and it is a correctness requirement with its own tests.
        """
        ...

    def load(self, project_id: str) -> Project: ...


@runtime_checkable
class AnalysisService(Protocol):
    """WO-111 (survives). Per-clip quality signals — facts, not decisions."""

    def analyze(self, source: SourceIndex) -> Analysis: ...


@runtime_checkable
class TrimProposer(Protocol):
    """WO-112 (survives, minus the floor). Deterministic, legible trim (SPEC.md §4.1)."""

    def propose_trim(self, source: SourceIndex, analysis: Analysis) -> SegmentsProposal:
        """Return a proposal (disposition='pending') with a ReasonRecord per factor.

        If no second clears the floors, propose the whole clip and say so
        (`NO_CLEAR_WINDOW`).

        **There is no minimum window** (DECISIONS A-6). The returned segment may
        be shorter than a second, and may be empty — `out_s <= in_s`, which
        removes the clip from the reel. Both are **warned in the Log and neither
        is blocked**. A caller that treats an empty segment as an error has
        misread the contract.
        """
        ...


@runtime_checkable
class SpeedProposer(Protocol):
    """WO-120. Ramp the dull stretches (SPEC.md §4.2). **Held on §14 SO-1.**

    The seam is frozen here so the API and store lanes can code against it; the
    implementation waits on the thresholds, minimum ramp length and merge rule
    that `SPEC.md` §4.2 says must be fixed before it is written.
    """

    def propose_speed(self, source: SourceIndex, analysis: Analysis) -> SpeedProposal:
        """Return ramps in SOURCE time, at rates the assist never takes above 2.0x.

        One clip may carry several ranges. Everything not dull stays 1.0x and is
        simply absent from the list.
        """
        ...


@runtime_checkable
class MediaService(Protocol):
    """WO-119. Preview media and the native pickers (SPEC.md §8)."""

    def proxy_path(self, source: SourceIndex) -> str: ...

    def thumbnail(self, source: SourceIndex, at_s: float) -> bytes:
        """Computed on demand and cached."""
        ...

    def peaks(self, source: SourceIndex) -> list[float]: ...

    def music_peaks(self, track_ref: str, content_hash: str) -> list[float]:
        """**Keyed by content hash**, because a track may be chosen before a
        project exists (SPEC.md §8)."""
        ...

    def probe_music(self, track_ref: str, content_hash: str) -> Music:
        """Return server-computed track metadata before a project exists."""
        ...

    def pick_folder(self) -> Optional[str]:
        """Native picker; None when the user cancels."""
        ...

    def pick_file(self) -> Optional[str]:
        """Native picker, serving both track selection and relink. None on cancel."""
        ...


@runtime_checkable
class Renderer(Protocol):
    """WO-121. Render and export **one file** (SPEC.md §9)."""

    def export(self, project: Project) -> RenderRecord:
        """Render from originals — never proxies — and return the record.

        Per clip: seek to the *effective* in/out, apply `setpts` per effective
        speed range with `atempo` at matching rates, scale and centre-crop to
        `project.output_resolution`, concatenate in `order`, mix per §5.

        Clips not in the reel are skipped. **If every clip is out, this fails
        with a stated reason** rather than handing ffmpeg an empty concatenation.
        Upscaling beyond the source is refused or flagged, never silent. GPS and
        identifying metadata are stripped from the output.
        """
        ...


@runtime_checkable
class OutputQA(Protocol):
    """WO-122. The gate that blocks export and states why (SPEC.md §9)."""

    def validate_render(self, render_path: str, project: Project) -> QAReport:
        """Verdict for a rendered file against the project's own settings.

        Resolution is checked against `project.output_resolution`, and audio
        against `project.audio`'s two levels. Never mutates.
        """
        ...
