"""The service container the API codes against — interfaces, not implementations.

WO-106 depends only on the WO-101 `Protocol`s. `analysis` and `proposer` are
optional because their lanes (WO-111/112) are not built yet; routes that need
them return a clear 501 until they are injected.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.contracts.interfaces import (
    AnalysisService,
    IngestService,
    OutputQA,
    ProjectStore,
    Renderer,
    TrimProposer,
)


@dataclass
class Services:
    store: ProjectStore
    ingest: IngestService
    renderer: Renderer
    qa: OutputQA
    analysis: Optional[AnalysisService] = None   # WO-111
    proposer: Optional[TrimProposer] = None      # WO-112
