"""Persist analysis.json per source so `propose` reads what `analyze` computed."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from backend.contracts.models import Analysis


class FileAnalysisStore:
    def __init__(self, root: str | os.PathLike) -> None:
        self.root = Path(root)

    def _path(self, project_id: str, source_id: str) -> Path:
        return self.root / project_id / f"{source_id}.json"

    def exists(self, project_id: str, source_id: str) -> bool:
        return self._path(project_id, source_id).exists()

    def save(self, project_id: str, analysis: Analysis) -> None:
        path = self._path(project_id, analysis.source_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(analysis.model_dump_json(indent=2) + "\n")
        os.replace(tmp, path)

    def load(self, project_id: str, source_id: str) -> Analysis:
        return Analysis.model_validate(json.loads(self._path(project_id, source_id).read_text(encoding="utf-8")))
