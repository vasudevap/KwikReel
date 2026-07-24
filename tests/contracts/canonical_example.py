"""A complete, valid `project.json` matching ES-001 §4.1 (as amended, §4.5).

This is the canonical example the round-trip gate runs against. Built in code so
it is type-checked by the models themselves; serialised to
`fixtures/project_v1_example.json` (the committed byte-for-byte reference) by
running this module: `python -m tests.contracts.canonical_example`.

It deliberately exercises the WO-100 amendments:
  G-1  a pure-"default" untouched clip (s2) alongside a "proposed" one (s1)
  G-2  a display `name`
  G-4  an unreadable source (s3), excluded, origin.included = "default"
  G-5  `export.last_render` as a map keyed by audio_mode
"""

from __future__ import annotations

from pathlib import Path

from backend.contracts.models import (
    AudioSettings,
    Clip,
    Export,
    Music,
    Origin,
    Project,
    Proposals,
    QAReport,
    ReasonRecord,
    RenderRecord,
    Segment,
    SegmentsProposal,
    SourceIndex,
    SpeedRange,
    StageApprovals,
)

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "project_v1_example.json"


def build_example() -> Project:
    return Project(
        schema_version=1,
        project_id="6f9619ff-8b86-d011-b42d-00cf4fc964ff",
        created_at="2026-07-24T18:55:02Z",
        updated_at="2026-07-24T19:10:44Z",
        app_version="0.1.0",
        name="Beach Day",
        media_root="/Users/example/Movies/BeachDay",
        target_duration_s=75.0,
        music=Music(
            track_ref="/Users/example/Music/summer.m4a",
            content_hash="sha256:1f0a…track",
            duration_s=191.4,
            beats_s=[],
            sections=[],
        ),
        sources=[
            SourceIndex(
                source_id="s1",
                content_hash="sha256:aa11…s1",
                path="/Users/example/Movies/BeachDay/IMG_0001.mov",
                duration_s=12.4,
                captured_at="2026-07-20T09:15:00-07:00",
                orientation="portrait",
                codec="hevc",
                fps=29.97,
                width=1080,
                height=1920,
                has_audio=True,
                has_gps=True,
                readable=True,
                proxy_path="/Users/example/Movies/BeachDay/.proxies/s1.mp4",
            ),
            SourceIndex(
                source_id="s2",
                content_hash="sha256:bb22…s2",
                path="/Users/example/Movies/BeachDay/IMG_0002.mov",
                duration_s=8.0,
                captured_at="2026-07-20T09:18:30-07:00",
                orientation="landscape",
                codec="h264",
                fps=30.0,
                width=1920,
                height=1080,
                has_audio=False,
                has_gps=False,
                readable=True,
                proxy_path="/Users/example/Movies/BeachDay/.proxies/s2.mp4",
            ),
            SourceIndex(
                source_id="s3",
                content_hash="sha256:cc33…s3",
                path="/Users/example/Movies/BeachDay/IMG_0003.mov",
                duration_s=5.0,
                captured_at=None,
                orientation="portrait",
                codec="h264",
                fps=30.0,
                width=1080,
                height=1920,
                has_audio=True,
                has_gps=False,
                readable=False,  # G-4: decode failed; surfaced, never dropped
                proxy_path=None,
            ),
        ],
        clips=[
            # s1: the machine proposed a trim, not yet acted on (pending).
            Clip(
                source_id="s1",
                included=True,
                order=1,
                deleted=False,
                segments=[Segment(in_s=3.0, out_s=8.0, speed=[SpeedRange(from_s=0.0, to_s=5.0, rate=1.0)])],
                audio=AudioSettings(retain=False, gain_db=0.0),
                origin=Origin(included="default", order="default", segments="proposed", speed="default", audio="default"),
                proposals=Proposals(
                    segments=SegmentsProposal(
                        value=[Segment(in_s=3.0, out_s=8.0, speed=[SpeedRange(from_s=0.0, to_s=5.0, rate=1.0)])],
                        at="2026-07-24T19:05:00Z",
                        reasons=[
                            ReasonRecord(
                                code="LEADING_BLUR",
                                human_text="Trimmed the first 2.4 s — too blurry to keep (sharpness 0.12 vs 0.35 floor)",
                                evidence_refs=["signals.blur[0:2]"],
                                score=0.12,
                                confidence="high",
                            )
                        ],
                        disposition="pending",
                    )
                ),
            ),
            # s2: untouched — full clip, every origin still "default" (G-1), no proposal.
            Clip(
                source_id="s2",
                included=True,
                order=2,
                deleted=False,
                segments=[Segment(in_s=0.0, out_s=8.0, speed=[])],
                audio=AudioSettings(),
                origin=Origin(),
                proposals=Proposals(),
            ),
            # s3: unreadable source — excluded, origin.included "default" (G-4).
            Clip(
                source_id="s3",
                included=False,
                order=3,
                deleted=False,
                segments=[Segment(in_s=0.0, out_s=5.0, speed=[])],
                audio=AudioSettings(),
                origin=Origin(),
                proposals=Proposals(),
            ),
        ],
        stage_approvals=StageApprovals(ingest="2026-07-24T19:02:11Z"),
        export=Export(
            audio_modes=["music", "clip", "silent"],
            last_render={
                "music": RenderRecord(
                    path="/Users/example/Movies/BeachDay/.out/beach-day-music.mp4",
                    rendered_at="2026-07-24T19:10:40Z",
                    qa=QAReport(
                        passed=True,
                        not_black=True,
                        audio_ok=True,
                        duration_ok=True,
                        resolution_ok=True,
                        codec_ok=True,
                        safe_margins_ok=True,
                        frame_count_ok=True,
                        duration_s=74.8,
                        width=1080,
                        height=1920,
                        reasons=[],
                    ),
                )
            },
        ),
    )


def canonical_json() -> str:
    """The byte-for-byte canonical serialisation (with a trailing newline)."""
    return build_example().model_dump_json(indent=2) + "\n"


def main() -> None:
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_PATH.write_text(canonical_json(), encoding="utf-8")
    print(f"wrote {FIXTURE_PATH}")


if __name__ == "__main__":
    main()
