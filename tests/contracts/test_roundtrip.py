"""WO-101 gate · the §4.1 example validates and round-trips byte-equivalently.

ES-001 §10 exit-gate 2 ("save → reopen → byte-equivalent project.json") proven
here at the model layer; WO-103 proves it again through the on-disk store.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from backend.contracts.models import Project
from tests.contracts.canonical_example import FIXTURE_PATH, build_example, canonical_json


def test_example_validates_and_carries_the_amendments() -> None:
    p = build_example()
    assert p.schema_version == 1
    assert p.name == "Beach Day"  # G-2

    # G-1: an untouched clip keeps every origin at "default", with no proposal.
    c2 = next(c for c in p.clips if c.source_id == "s2")
    assert c2.origin.segments == "default"
    assert c2.proposals.segments is None

    # a proposed clip carries origin "proposed" and a pending disposition.
    c1 = next(c for c in p.clips if c.source_id == "s1")
    assert c1.origin.segments == "proposed"
    assert c1.proposals.segments is not None
    assert c1.proposals.segments.disposition == "pending"

    # G-4: an unreadable source is excluded, origin.included "default".
    s3 = next(s for s in p.sources if s.source_id == "s3")
    assert s3.readable is False
    c3 = next(c for c in p.clips if c.source_id == "s3")
    assert c3.included is False and c3.origin.included == "default"

    # G-5: last_render is a map keyed by audio_mode.
    assert set(p.export.last_render) <= {"music", "clip", "silent"}
    assert "music" in p.export.last_render


def test_committed_fixture_is_byte_equivalent_to_the_model() -> None:
    # The fixture must be exactly what the model serialises; regenerate on drift:
    #   python -m tests.contracts.canonical_example
    assert FIXTURE_PATH.read_text(encoding="utf-8") == canonical_json()


def test_load_reopen_is_byte_equivalent() -> None:
    text = FIXTURE_PATH.read_text(encoding="utf-8")
    loaded = Project.model_validate_json(text)
    redumped = loaded.model_dump_json(indent=2) + "\n"
    assert redumped == text
    # second round trip is a fixed point
    assert Project.model_validate_json(redumped).model_dump_json(indent=2) + "\n" == text


def test_unknown_fields_are_rejected() -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    data["surprise"] = 1
    with pytest.raises(ValidationError):
        Project.model_validate(data)
