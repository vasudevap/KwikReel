"""A complete, valid `project.json` matching SPEC.md §3.2.

This is the canonical example the round-trip gate runs against. Built in code so
it is type-checked by the models themselves; serialised to
`fixtures/project_v2_example.json` (the committed byte-for-byte reference) by
running this module: `python -m tests.contracts.canonical_example`.

It deliberately exercises the parts of §3 that are easy to get wrong:

  s1  a clip carrying a **pending trim proposal** and no user edit — so
      `segment` is null and `origin.segments` is "proposed". What renders is
      derived from the proposal, not from the clip. (§3.1)
  s2  a clip the user **trimmed by hand on top of a proposal** — `segment` is
      set, `origin.segments` is "user", the proposal is **retained** with
      `disposition: "adjusted"`, and no assist may touch it again. This is the
      stickiness case (§4.4) and the retention case (§3.1) in one clip.
  s3  a clip **binned**: its effective trim is zero-length (`out_s <= in_s`, so
      it is out of the reel per §3.4) with `stashed_segment` holding what
      pressing bin again restores. (§4.3)
  s4  a **damaged** source — `readable: false`, out of the reel for a completely
      different reason and fixed a completely different way. Untouched
      otherwise: every `origin` still "default", no proposal. (§3.4)

It also carries a user speed ramp in **source time** (s2), one export record
rather than a per-mode map, and a music track with an in-point.
"""

from __future__ import annotations

from pathlib import Path

from backend.contracts.models import (
    AudioMix,
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
    SpeedProposal,
    SpeedRange,
)

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "project_v2_example.json"


def build_example() -> Project:
    return Project(
        schema_version=2,
        project_id="6f9619ff-8b86-d011-b42d-00cf4fc964ff",
        created_at="2026-07-28T18:55:02Z",
        updated_at="2026-07-28T19:10:44Z",
        app_version="0.2.0",
        name="Beach Day",
        media_root="/Users/example/Movies/BeachDay",
        target_duration_s=75.0,
        output_resolution="1080p",
        trim_assist_on=True,
        speed_assist_on=False,
        audio=AudioMix(music_level=0.62, clip_level=0.78),
        music=Music(
            track_ref="/Users/example/Music/summer.m4a",
            content_hash="sha256:1f0a…track",
            duration_s=191.4,
            in_s=12.5,
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
                duration_s=20.0,
                captured_at="2026-07-20T09:18:30-07:00",
                orientation="landscape",
                codec="h264",
                fps=30.0,
                width=1920,
                height=1080,
                has_audio=True,
                has_gps=False,
                readable=True,
                proxy_path="/Users/example/Movies/BeachDay/.proxies/s2.mp4",
            ),
            SourceIndex(
                source_id="s3",
                content_hash="sha256:cc33…s3",
                path="/Users/example/Movies/BeachDay/IMG_0003.mov",
                duration_s=8.0,
                captured_at="2026-07-20T09:22:05-07:00",
                orientation="portrait",
                codec="h264",
                fps=30.0,
                width=1080,
                height=1920,
                has_audio=False,
                has_gps=False,
                readable=True,
                proxy_path="/Users/example/Movies/BeachDay/.proxies/s3.mp4",
            ),
            SourceIndex(
                source_id="s4",
                content_hash="sha256:dd44…s4",
                path="/Users/example/Movies/BeachDay/IMG_0004.mov",
                duration_s=5.0,
                captured_at=None,
                orientation="portrait",
                codec="h264",
                fps=30.0,
                width=1080,
                height=1920,
                has_audio=True,
                has_gps=False,
                readable=False,  # damaged: out of the reel, surfaced, never dropped
                proxy_path=None,
            ),
        ],
        clips=[
            # s1 · the assist proposed a trim and the user has not acted on it.
            # `segment` stays null: the proposal is not copied into the clip, it
            # is read through at render time while trim_assist_on (§3.1).
            Clip(
                source_id="s1",
                order=1,
                segment=None,
                speed_ranges=[],
                stashed_segment=None,
                audio=AudioSettings(retain=True, gain_db=0.0),
                origin=Origin(segments="proposed"),
                proposals=Proposals(
                    segments=SegmentsProposal(
                        value=Segment(in_s=2.4, out_s=9.1),
                        at="2026-07-28T19:05:00Z",
                        reasons=[
                            ReasonRecord(
                                code="LEADING_BLUR",
                                human_text="Trimmed the first 2.4 s — too blurry to keep (sharpness 0.12 against a 0.35 floor)",
                                evidence_refs=["signals.blur[0:2]"],
                                score=0.12,
                                confidence="high",
                            ),
                            ReasonRecord(
                                code="TRAILING_STATIC",
                                human_text="Trimmed the last 3.3 s — nothing moving and nothing audible",
                                evidence_refs=["signals.motion_energy[9:12]", "signals.audio_rms[9:12]"],
                                score=0.04,
                                confidence="med",
                            ),
                        ],
                        disposition="pending",
                    )
                ),
            ),
            # s2 · the user moved a handle on a clip that carried a proposal, and
            # set a ramp by hand. Both origins are "user", so no assist reaches
            # either field again (§4.4) — and both proposals are RETAINED, which
            # is what makes switching the toggles off lossless (§3.1).
            # The ramp is in SOURCE time: 6.0–11.0 s from the clip's start, not a
            # fraction of the kept region, so moving the in-handle leaves it on
            # the content it was computed for (§3.2).
            Clip(
                source_id="s2",
                order=2,
                segment=Segment(in_s=1.5, out_s=16.0),
                speed_ranges=[SpeedRange(from_s=6.0, to_s=11.0, rate=1.75)],
                stashed_segment=None,
                audio=AudioSettings(retain=False, gain_db=0.0),  # muted on the row
                origin=Origin(segments="user", speed="user", audio="user"),
                proposals=Proposals(
                    segments=SegmentsProposal(
                        value=Segment(in_s=0.8, out_s=17.2),
                        at="2026-07-28T19:05:00Z",
                        reasons=[
                            ReasonRecord(
                                code="TRAILING_SHAKE",
                                human_text="Trimmed the last 2.8 s — the camera was moving too much to hold",
                                evidence_refs=["signals.shake[17:20]"],
                                score=0.71,
                                confidence="high",
                            )
                        ],
                        disposition="adjusted",  # written when the handle moved
                    ),
                    speed=SpeedProposal(
                        value=[SpeedRange(from_s=5.5, to_s=12.0, rate=1.6)],
                        at="2026-07-28T19:06:12Z",
                        reasons=[
                            ReasonRecord(
                                code="DULL_STRETCH",
                                human_text="Sped the middle 6.5 s to 1.6× — very little movement or sound through it",
                                evidence_refs=["signals.motion_energy[5:12]", "signals.audio_rms[5:12]"],
                                score=0.08,
                                confidence="med",
                            )
                        ],
                        disposition="adjusted",
                    ),
                ),
            ),
            # s3 · binned. The effective trim is zero-length, so the clip is out
            # of the reel (§3.4) — and `stashed_segment` is what pressing bin a
            # second time restores, which is what makes removal reversible (§4.3).
            Clip(
                source_id="s3",
                order=3,
                segment=Segment(in_s=0.0, out_s=0.0),
                speed_ranges=[],
                stashed_segment=Segment(in_s=0.0, out_s=8.0),
                audio=AudioSettings(),
                origin=Origin(segments="user"),
                proposals=Proposals(),
            ),
            # s4 · damaged source. Out of the reel because `readable` is false —
            # a different cause from s3's, fixed a different way, and shown in a
            # different colour (§3.4). Nothing about the clip itself is touched.
            Clip(
                source_id="s4",
                order=4,
                segment=None,
                speed_ranges=[],
                stashed_segment=None,
                audio=AudioSettings(),
                origin=Origin(),
                proposals=Proposals(),
            ),
        ],
        export=Export(
            last_render=RenderRecord(
                path="/Users/example/Movies/BeachDay/.out/beach-day.mp4",
                rendered_at="2026-07-28T19:10:40Z",
                qa=QAReport(
                    passed=True,
                    not_black=True,
                    audio_ok=True,
                    duration_ok=True,
                    resolution_ok=True,
                    codec_ok=True,
                    safe_margins_ok=True,
                    frame_count_ok=True,
                    duration_s=21.0,
                    width=1080,
                    height=1920,
                    reasons=[],
                ),
            )
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
