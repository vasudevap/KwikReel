"""Deterministic dull-stretch speed proposals (SPEC.md §4.2)."""
from __future__ import annotations
from datetime import datetime, timezone
from backend.contracts.models import Analysis, ReasonRecord, SourceIndex, SpeedProposal, SpeedRange


class SpeedRuleProposer:
    def propose_speed(self, source: SourceIndex, analysis: Analysis) -> SpeedProposal:
        sig = analysis.signals
        dull = [m <= .25 and a <= .25 for m, a in zip(sig.motion_energy, sig.audio_rms)]
        values: list[SpeedRange] = []
        reasons: list[ReasonRecord] = []
        start: int | None = None
        for i, yes in enumerate(dull + [False]):
            if yes and start is None:
                start = i
            elif not yes and start is not None:
                end = min(float(i), source.duration_s)
                if end - start >= 1.5:
                    scores = [1 - max(sig.motion_energy[j], sig.audio_rms[j]) / .25 for j in range(start, i)]
                    score = max(0., min(1., sum(scores) / len(scores)))
                    rate = 1.5 + .5 * score
                    values.append(SpeedRange(from_s=float(start), to_s=end, rate=rate))
                    reasons.append(ReasonRecord(code="DULL_STRETCH", human_text=f"Sped up {end - start:.1f} s of quiet, low-motion footage to {rate:.2f}×.", evidence_refs=[f"signals.motion_energy[{start}:{i}]", f"signals.audio_rms[{start}:{i}]"], score=round(score, 3), confidence="med"))
                start = None
        return SpeedProposal(value=values, at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), reasons=reasons, disposition="pending")
