"""WO-113 repo-hygiene build gates — the hard constraints, made executable.

  * project.json is gitignored everywhere (ADR-002: never commit a project file)
  * only fixtures/synthetic/ is tracked (ADR-013: no real footage/thumbnails)
  * no forbidden/distribution-restrictive dependency, e.g. madmom (ADR-003)

The frontend-bundle asset guard (no CDN/remote assets) and the media-path egress
guard are deferred until the real frontend exists (WO-107+).
"""

from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True)


def test_project_json_is_gitignored_anywhere() -> None:
    for candidate in ("project.json", "backend/store/data/x/project.json", "anywhere/project.json"):
        assert _git("check-ignore", candidate).returncode == 0, f"{candidate} is NOT gitignored"


def test_only_synthetic_fixtures_are_tracked() -> None:
    tracked = _git("ls-files", "fixtures/").stdout.split()
    assert tracked, "expected at least the synthetic fixtures README to be tracked"
    offenders = [p for p in tracked if not p.startswith("fixtures/synthetic/")]
    assert not offenders, f"non-synthetic fixtures are tracked (ADR-013 violation): {offenders}"


def test_no_forbidden_dependencies() -> None:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    deps = list(data["project"].get("dependencies", []))
    for group in data["project"].get("optional-dependencies", {}).values():
        deps.extend(group)
    names = {re.split(r"[<>=!~;\s\[]", d, 1)[0].strip().lower() for d in deps}
    assert "madmom" not in names, "madmom is distribution-restrictive (ADR-003)"
