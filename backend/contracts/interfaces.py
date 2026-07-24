"""WO-101 · Service interfaces — the seams every other M1 Work Order codes against.

Structural `Protocol`s, not implementations (WO-101 excludes behaviour). Each
service WO (WO-102 ingest, WO-103 store, WO-104 render, WO-105 qa, WO-111
analysis, WO-112 propose) provides a concrete class satisfying one Protocol;
the HTTP layer (WO-106) and frontend code against these, never against
implementations. Signatures follow ES-001 §6 and the M1 backlog.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.contracts.models import (
    Analysis,
    AudioMode,
    Project,
    QAReport,
    RenderRecord,
    SegmentsProposal,
    SourceIndex,
)


@runtime_checkable
class IngestService(Protocol):
    """C-1 · WO-102. Probe sources and build proxies. Read-only beneath media_root."""

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
    """C-2 · WO-103. Lossless project.json persistence with optimistic concurrency."""

    def save(self, project: Project) -> Project:
        """Persist and return the project with a bumped updated_at.

        Raises on an updated_at mismatch (HTTP maps this to 409, §6). Enforces the
        §4.1 invariants: origin on every mutation, proposals retained on override,
        disposition set, deleted never removes, order dense/unique.
        """
        ...

    def load(self, project_id: str) -> Project: ...


@runtime_checkable
class AnalysisService(Protocol):
    """C-7 · WO-111. Per-clip quality signals (facts, not decisions) → analysis.json."""

    def analyze(self, source: SourceIndex) -> Analysis: ...


@runtime_checkable
class TrimProposer(Protocol):
    """C-8 · WO-112. Deterministic, legible trim proposal per clip (ES-001 §5.2)."""

    def propose_trim(self, source: SourceIndex, analysis: Analysis) -> SegmentsProposal:
        """Return a proposal (disposition='pending') with one ReasonRecord per factor.

        Never returns an empty/silent result: if nothing clears the floors, proposes
        the full clip and says so (§5.2 rule 5). Honours the universal 1.0 s floor (G-9).
        """
        ...


@runtime_checkable
class Renderer(Protocol):
    """C-4/6 · WO-104. Draft render and per-audio-mode export (ES-001 §8)."""

    def render_draft(self, project: Project) -> str:
        """Render a draft from included, non-deleted clips in order; return its path."""
        ...

    def export(self, project: Project, audio_mode: AudioMode) -> RenderRecord:
        """Render and mux one audio mode (music | clip | silent); return its record."""
        ...


@runtime_checkable
class OutputQA(Protocol):
    """C-5 · WO-105. Output QA gate that blocks export on failure (ES-001 §8.3)."""

    def validate_render(
        self, render_path: str, project: Project, audio_mode: AudioMode
    ) -> QAReport:
        """Verdict for a rendered file against the mode's expectations. Never mutates."""
        ...
