"""The v2 service container used by the HTTP layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.contracts.interfaces import (
    AnalysisService, IngestService, MediaService, OutputQA, ProjectStore,
    Renderer, SpeedProposer, TrimProposer,
)
from backend.store.log_store import FileLogStore


@dataclass
class Services:
    store: ProjectStore
    ingest: IngestService
    renderer: Renderer
    qa: OutputQA
    media: Optional[MediaService] = None
    analysis: Optional[AnalysisService] = None
    proposer: Optional[TrimProposer] = None
    speed_proposer: Optional[SpeedProposer] = None
    log: Optional[FileLogStore] = None
