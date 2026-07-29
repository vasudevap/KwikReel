"""WO-118 gates · the `log.json` sidecar (`SPEC.md` §7.2, §7.3).

The ADP-002 §4 gate: **the Log survives close -> reopen, evicts at 500, and
never evicts a standing entry.** All three are here, plus the §7.3 clause about
entries logged before a project exists.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from backend.store import (
    LOG_CAPACITY,
    FileLogStore,
    LogEntry,
    SessionLogBuffer,
    STANDING_TEXTS,
    evict,
    standing_entries,
)

PROJECT_ID = "6f9619ff-8b86-d011-b42d-00cf4fc964ff"


def _entry(n: int, kind: str = "info") -> LogEntry:
    return LogEntry(at=f"2026-07-29T10:00:{n % 60:02d}Z", kind=kind, text=f"entry {n}")


# --- §7.3 · the entry shape -----------------------------------------------

def test_an_entry_carries_the_seven_three_fields() -> None:
    entry = LogEntry(
        at="2026-07-29T10:00:00Z",
        kind="warn",
        text="Trimmed to nothing — this clip is out of the reel",
        code="EMPTY_SEGMENT",
        source_id="s1",
    )
    assert entry.standing is False
    assert entry.model_dump(mode="json") == {
        "at": "2026-07-29T10:00:00Z",
        "kind": "warn",
        "text": "Trimmed to nothing — this clip is out of the reel",
        "code": "EMPTY_SEGMENT",
        "source_id": "s1",
        "standing": False,
    }


def test_an_unknown_field_or_kind_is_refused() -> None:
    with pytest.raises(ValidationError):
        LogEntry(at="2026-07-29T10:00:00Z", kind="info", text="x", level="debug")
    with pytest.raises(ValidationError):
        LogEntry(at="2026-07-29T10:00:00Z", kind="debug", text="x")


# --- §7.2 · it persists ---------------------------------------------------

def test_the_log_survives_close_and_reopen(tmp_path) -> None:
    # A session-only Log would discard A-3b's export summary the moment the app
    # closed, and that summary is the only named measure for claim C-03.
    FileLogStore(tmp_path).append(PROJECT_ID, [
        _entry(1),
        LogEntry(at="2026-07-29T10:05:00Z", kind="info", text="Kept 14 of 19 AI trims."),
    ])

    reopened = FileLogStore(tmp_path).load(PROJECT_ID)   # a fresh store, as on relaunch
    assert [e.text for e in reopened] == ["entry 1", "Kept 14 of 19 AI trims."]


def test_the_sidecar_sits_beside_project_json(tmp_path) -> None:
    store = FileLogStore(tmp_path)
    store.append(PROJECT_ID, [_entry(1)])
    path = tmp_path / PROJECT_ID / "log.json"
    assert path.exists()
    assert [item["text"] for item in json.loads(path.read_text(encoding="utf-8"))] == ["entry 1"]


def test_an_absent_log_reads_as_an_empty_one(tmp_path) -> None:
    assert FileLogStore(tmp_path).load("no-such-project") == []


def test_appending_keeps_oldest_first(tmp_path) -> None:
    store = FileLogStore(tmp_path)
    store.append(PROJECT_ID, [_entry(1), _entry(2)])
    store.append(PROJECT_ID, [_entry(3)])
    assert [e.text for e in store.load(PROJECT_ID)] == ["entry 1", "entry 2", "entry 3"]


# --- §7.2 · retention -----------------------------------------------------

def test_it_holds_five_hundred_entries_evicted_oldest_first(tmp_path) -> None:
    store = FileLogStore(tmp_path)
    store.append(PROJECT_ID, [_entry(n) for n in range(600)])

    kept = store.load(PROJECT_ID)
    assert len(kept) == LOG_CAPACITY == 500
    assert kept[0].text == "entry 100"      # the first hundred aged out
    assert kept[-1].text == "entry 599"


def test_a_standing_entry_is_never_evicted(tmp_path) -> None:
    store = FileLogStore(tmp_path)
    store.ensure_standing(PROJECT_ID)
    store.append(PROJECT_ID, [_entry(n) for n in range(600)])

    kept = store.load(PROJECT_ID)
    assert len(kept) == LOG_CAPACITY
    standing = [e for e in kept if e.standing]
    assert [e.code for e in standing] == [code for code, _ in STANDING_TEXTS]
    # The flowing window gives up the room instead.
    assert len(kept) - len(standing) == LOG_CAPACITY - len(STANDING_TEXTS)


def test_standing_entries_sit_at_the_foot_of_the_scrollback(tmp_path) -> None:
    # §7.2: the foot of a newest-first display is the oldest end of the file.
    store = FileLogStore(tmp_path)
    store.ensure_standing(PROJECT_ID)
    store.append(PROJECT_ID, [_entry(1)])
    kept = store.load(PROJECT_ID)
    assert [e.standing for e in kept] == [True, True, False]


def test_eviction_never_drops_a_standing_entry_even_past_capacity() -> None:
    # never-evicted means never: the ceiling yields, not the assurance.
    standing = [
        LogEntry(at="2026-07-29T10:00:00Z", kind="info", text=f"s{n}", standing=True)
        for n in range(12)
    ]
    kept = evict(standing + [_entry(n) for n in range(50)], capacity=10)
    assert len(kept) == 12
    assert all(e.standing for e in kept)


# --- §7.1 / §7.2 · the standing lines -------------------------------------

def test_the_two_standing_lines_are_what_a_project_opens_with(tmp_path) -> None:
    store = FileLogStore(tmp_path)
    store.ensure_standing(PROJECT_ID)

    opening = store.standing_lines(PROJECT_ID)
    assert [e.code for e in opening] == ["ORIGINALS_READ_ONLY", "LOCAL_ONLY"]
    assert "read-only" in opening[0].text
    assert "nobody is recognised" in opening[1].text     # A-7's assurance, verbatim
    assert all(e.kind == "info" and e.standing for e in opening)


def test_ensuring_the_standing_lines_twice_does_not_double_them(tmp_path) -> None:
    store = FileLogStore(tmp_path)
    store.ensure_standing(PROJECT_ID)
    store.append(PROJECT_ID, [_entry(1)])
    store.ensure_standing(PROJECT_ID)                    # reopening the project

    assert len(store.standing_lines(PROJECT_ID)) == len(STANDING_TEXTS)
    assert len(store.load(PROJECT_ID)) == len(STANDING_TEXTS) + 1


def test_standing_entries_are_stamped_when_they_are_written() -> None:
    assert [e.code for e in standing_entries("2026-07-29T10:00:00Z")] == [
        code for code, _ in STANDING_TEXTS
    ]
    assert standing_entries("2026-07-29T10:00:00Z")[0].at == "2026-07-29T10:00:00Z"


# --- §7.3 · entries logged before a project exists ------------------------

def test_entries_from_before_a_project_existed_land_on_its_first_save(tmp_path) -> None:
    # A track may be chosen before there is a project to log against (§8).
    buffer = SessionLogBuffer()
    buffer.add(LogEntry(at="2026-07-29T09:58:00Z", kind="info", text="Track chosen: summer.m4a"))
    buffer.add(LogEntry(at="2026-07-29T09:59:00Z", kind="warn", text="Track is shorter than the reel"))
    assert len(buffer.pending) == 2

    store = FileLogStore(tmp_path)
    buffer.flush_to(store, PROJECT_ID)

    assert [e.text for e in store.load(PROJECT_ID)] == [
        "Track chosen: summer.m4a",
        "Track is shorter than the reel",
    ]
    assert buffer.pending == []          # held for the session, written once
