"""WO-113 · the remaining privacy guards (ES-001 §9).

  * the frontend references no remote assets (no CDN scripts/styles/fonts/images,
    no remote imports or fetches) — everything ships bundled locally
  * the media-handling backend imports no network libraries — originals never
    leave the device

Each test also asserts its detector flags a synthetic violation, so the guard
provably *can* fail (WO-113 gate). XML/SVG namespace URIs (xmlns="http://…") are
identifiers, never fetched, and are correctly not matched.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Remote *asset loads* — things a browser or bundler would actually fetch.
_REMOTE_ASSET = re.compile(
    r"""(?:src|href)\s*=\s*["']https?://"""      # <script src="http…">, <link href="http…">
    r"""|@import\s+["']?https?://"""             # css @import "http…"
    r"""|url\(\s*["']?https?://"""               # css url(http…) — remote font/image
    r"""|\bfrom\s+["']https?://"""               # remote ES module import
    r"""|\bimport\s*\(\s*["']https?://"""        # dynamic remote import
    r"""|\bfetch\s*\(\s*["']https?://""",        # remote fetch
    re.IGNORECASE,
)

# Outbound-network imports / calls in media code.
_NETWORK = re.compile(
    r"""^\s*(?:import|from)\s+(?:socket|urllib|urllib\.\w+|http\.client|"""
    r"""requests|httpx|aiohttp|ftplib|smtplib)\b"""
    r"""|\burlopen\s*\(|\bsocket\.socket\s*\(|\brequests\.\w|\bhttpx\.\w""",
    re.MULTILINE,
)


def _frontend_sources() -> list[Path]:
    src = REPO_ROOT / "frontend" / "src"
    files = [p for ext in ("*.ts", "*.tsx", "*.css") for p in src.rglob(ext)]
    files.append(REPO_ROOT / "frontend" / "index.html")
    return [p for p in files if p.exists()]


def test_frontend_references_no_remote_assets() -> None:
    offenders = []
    for f in _frontend_sources():
        for m in _REMOTE_ASSET.finditer(f.read_text(encoding="utf-8")):
            offenders.append(f"{f.relative_to(REPO_ROOT)}: {m.group(0)!r}")
    assert not offenders, f"remote assets referenced (ES-001 §9): {offenders}"
    # the guard can fail:
    assert _REMOTE_ASSET.search('<script src="https://cdn.example.com/x.js">')
    assert _REMOTE_ASSET.search("@import url(https://fonts.googleapis.com/css)")
    # …and does not flag an xmlns namespace identifier:
    assert not _REMOTE_ASSET.search('xmlns="http://www.w3.org/2000/svg"')


def test_media_backend_imports_no_network_libraries() -> None:
    files = [p for d in ("ingest", "analysis", "render", "qa") for p in (REPO_ROOT / "backend" / d).rglob("*.py")]
    offenders = []
    for f in files:
        if _NETWORK.search(f.read_text(encoding="utf-8")):
            offenders.append(str(f.relative_to(REPO_ROOT)))
    assert not offenders, f"media code imports/uses the network (ES-001 §9): {offenders}"
    # the guard can fail:
    assert _NETWORK.search("import requests")
    assert _NETWORK.search("from urllib.request import urlopen")
