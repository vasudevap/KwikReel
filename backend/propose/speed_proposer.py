"""Deterministic dull-stretch speed proposals (SPEC.md §4.2)."""
from __future__ import annotations
from datetime import datetime, timezone
from backend.contracts.models import Analysis, ReasonRecord, SourceIndex, SpeedProposal, SpeedRange

_DULL_CEILING = 0.25
_MIN_RANGE_S = 1.5
_MERGE_GAP_S = 0.5


def _merge_candidate_spans(
    spans: list[tuple[float, float]], *, gap_s: float = _MERGE_GAP_S
) -> list[tuple[float, float]]:
    """Merge §4.2 candidate spans whose separating gap is under `gap_s`.

    Current analysis signals are per-second, so two separately detected spans
    have an integral gap and cannot satisfy this rule in ordinary proposals.
    Keeping the rule explicit here means a future sub-second signal stream does
    not silently change the specified behaviour.
    """
    merged: list[tuple[float, float]] = []
    for start, end in spans:
        if merged and start - merged[-1][1] < gap_s:
            merged[-1] = (merged[-1][0], end)
        else:
            merged.append((start, end))
    return merged


class SpeedRuleProposer:
    def propose_speed(self, source: SourceIndex, analysis: Analysis) -> SpeedProposal:
        sig = analysis.signals
        dull = [
            motion <= _DULL_CEILING and audio <= _DULL_CEILING
            for motion, audio in zip(sig.motion_energy, sig.audio_rms)
        ]
        candidates: list[tuple[float, float]] = []
        start: int | None = None
        for i, yes in enumerate(dull + [False]):
            if yes and start is None:
                start = i
            elif not yes and start is not None:
                candidates.append((float(start), float(i)))
                start = None

        values: list[SpeedRange] = []
        reasons: list[ReasonRecord] = []
        for start_s, end_s in _merge_candidate_spans(candidates):
            start_i, end_i = int(start_s), int(end_s)
            end_s = min(end_s, source.duration_s)
            if end_s - start_s < _MIN_RANGE_S:
                continue
            scores = [
                1 - max(sig.motion_energy[j], sig.audio_rms[j]) / _DULL_CEILING
                for j in range(start_i, end_i)
            ]
            score = max(0.0, min(1.0, sum(scores) / len(scores)))
            rate = 1.5 + 0.5 * score
            values.append(SpeedRange(from_s=start_s, to_s=end_s, rate=rate))
            reasons.append(
                ReasonRecord(
                    code="DULL_STRETCH",
                    human_text=(
                        f"Sped up {end_s - start_s:.1f} s of quiet, low-motion footage "
                        f"to {rate:.2f}×."
                    ),
                    evidence_refs=[
                        f"signals.motion_energy[{start_i}:{end_i}]",
                        f"signals.audio_rms[{start_i}:{end_i}]",
                    ],
                    score=round(score, 3),
                    confidence="med",
                )
            )
        return SpeedProposal(
            value=values,
            at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            reasons=reasons,
            disposition="pending",
        )
