"""WO-118 · The Log's sidecar — `SPEC.md` §7.2 and §7.3.

`log.json`, per project, beside `project.json`. Local, never committed.

The Log is the audit trail (DECISIONS A-2, A-3). SO-2 closed on 2026-07-29 with
four answers, and this module is three of them; the fourth — severity outranking
recency in the three visible lines — is a display rule and belongs to the
frontend (ADP-003), not here.

  * **It persists.** A session-only Log would discard A-3b's export summary the
    moment the app closed, and that summary is the only named measure for
    evidence claim C-03.
  * **It lives in a sidecar, not in `project.json`.** `project.json` is *state*;
    the Log is append-only *history*, and the contract is frozen — a sidecar
    closes SO-2 without amending §3, the way `analysis.json` already does.
  * **500 entries, evicted oldest-first, standing lines exempt.** A 50-clip
    reel's full trim and speed run writes on the order of 110 entries, so 500
    holds several such runs plus their summaries: deep enough to read a session
    back, small enough that this stays a document rather than a database.

## Shape and order on disk

A plain JSON array of §7.3 `LogEntry` objects, **oldest first** — the natural
order for an append-only file, and the reverse of how the Log reads them (three
lines of glass, newest first). Standing entries are held at the head, which is
§7.2's "foot of the scrollback": the oldest end of a newest-first display.

`LogEntry` is defined here rather than in `backend/contracts/` because it is not
part of the §3 contract WO-117 froze — §3 is `project.json`, and this is a
sidecar. Anything that changes §7.3's shape changes this file.

## What this module does not do

It does not decide *what* gets logged. §7.1's eight duties belong to the lanes
that do the work — ingest writes its summary, the proposers write their
`ReasonRecord.human_text` verbatim, the API writes save failures. One §7.2
convention is theirs too and worth restating where they will look for it: **a
bulk run writes its detail first and its summary last**, so newest-first shows
the headline and every reason is one scroll away.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Iterable, Literal, Optional

from pydantic import BaseModel, ConfigDict

from backend.store.project_store import atomic_write, now_iso

# §7.2. Counts standing entries, which are exempt from eviction but not from the
# ceiling — the flowing window shrinks by however many standing lines exist, so
# `log.json` holds 500 entries in total.
LOG_CAPACITY = 500


class LogEntry(BaseModel):
    """`SPEC.md` §7.3."""

    model_config = ConfigDict(extra="forbid")

    at: str                          # ISO-8601
    kind: Literal["info", "warn", "fault"]
    text: str                        # written to be read — a ReasonRecord's
                                     # human_text goes here verbatim
    code: Optional[str] = None       # stable machine code where one exists
    source_id: Optional[str] = None  # the clip it concerns, when it concerns one
    standing: bool = False           # exempt from eviction (§7.2)


# §7.1's two standing lines, verbatim in intent. They are the assurance A-7
# required, they are never evicted, and they are **what the three lines show
# when a project opens**, before anything has been logged.
STANDING_TEXTS: tuple[tuple[str, str], ...] = (
    ("ORIGINALS_READ_ONLY", "Originals are opened read-only and never changed."),
    ("LOCAL_ONLY", "Previews are made on this Mac. Nothing is uploaded and nobody is recognised."),
)


def standing_entries(at: Optional[str] = None) -> list[LogEntry]:
    """A fresh pair of §7.1 standing lines."""
    stamp = at or now_iso()
    return [
        LogEntry(at=stamp, kind="info", text=text, code=code, standing=True)
        for code, text in STANDING_TEXTS
    ]


def evict(entries: Iterable[LogEntry], capacity: int = LOG_CAPACITY) -> list[LogEntry]:
    """§7.2 retention: newest `capacity` entries, standing lines never dropped.

    Standing entries are returned first — §7.2's foot of the scrollback — and
    the flowing window takes whatever room is left. If standing entries alone
    ever exceeded `capacity` they would all still be kept: never-evicted means
    never, and the ceiling yields to it.
    """
    ordered = list(entries)
    standing = [e for e in ordered if e.standing]
    flowing = [e for e in ordered if not e.standing]
    room = max(0, capacity - len(standing))
    return standing + (flowing[-room:] if room else [])


class FileLogStore:
    """`log.json` beside `project.json`, one per project (§7.3)."""

    def __init__(self, root: str | os.PathLike) -> None:
        self.root = Path(root)
        self._lock = threading.RLock()

    def _path(self, project_id: str) -> Path:
        return self.root / project_id / "log.json"

    def exists(self, project_id: str) -> bool:
        return self._path(project_id).exists()

    def load(self, project_id: str) -> list[LogEntry]:
        """Every retained entry, oldest first. An absent log is an empty one."""
        path = self._path(project_id)
        if not path.exists():
            return []
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [LogEntry.model_validate(item) for item in raw]

    def append(self, project_id: str, entries: Iterable[LogEntry]) -> list[LogEntry]:
        """Append, evict per §7.2, and return the retained log."""
        with self._lock:
            retained = evict(self.load(project_id) + list(entries))
            self._write(project_id, retained)
            return retained

    def append_one(self, project_id: str, entry: LogEntry) -> LogEntry:
        """Append one entry and return the accepted value."""
        self.append(project_id, [entry])
        return entry

    def ensure_standing(self, project_id: str) -> list[LogEntry]:
        """Write §7.1's standing lines if this project has none yet.

        Called when a project is created. Idempotent, so reopening an existing
        project does not accumulate a second pair.
        """
        existing = self.load(project_id)
        present = {e.code for e in existing if e.standing}
        missing = [e for e in standing_entries() if e.code not in present]
        if not missing:
            return existing
        return self.append(project_id, missing)

    def standing_lines(self, project_id: str) -> list[LogEntry]:
        """What the three lines show when a project opens, before any event (§7.2)."""
        return [e for e in self.load(project_id) if e.standing]

    def _write(self, project_id: str, entries: list[LogEntry]) -> None:
        payload = [e.model_dump(mode="json") for e in entries]
        atomic_write(self._path(project_id), json.dumps(payload, indent=2) + "\n")


class SessionLogBuffer:
    """§7.3: entries logged before a project exists.

    A track may be chosen before there is a project to log against (§8's
    `GET /api/music/peaks` is keyed by content hash for exactly that reason).
    Those entries are held for the session and written on the project's first
    save, rather than being dropped on the floor.
    """

    def __init__(self) -> None:
        self._pending: list[LogEntry] = []

    def add(self, entry: LogEntry) -> None:
        self._pending.append(entry)

    @property
    def pending(self) -> list[LogEntry]:
        return list(self._pending)

    def flush_to(self, store: FileLogStore, project_id: str) -> list[LogEntry]:
        """Write the held entries into the project's log and clear the buffer."""
        held, self._pending = self._pending, []
        return store.append(project_id, held)
