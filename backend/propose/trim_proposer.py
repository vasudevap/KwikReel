"""Deterministic trim proposal from analysis signals (ES-001 §5.2).

Signals are per-second and normalised to 0..1 by the analysis lane:
  blur      = sharpness (higher = sharper) — must clear `sharpness_floor`
  exposure  = clipping  (higher = worse)   — must stay under `exposure_ceiling`
  shake     = instability (higher = worse) — must stay under `shake_ceiling`
  motion_energy, audio_rms — used to spot static "dead air" at head/tail

Rules: score each second against the floors; take the longest contiguous good run
that does not cross a scene cut; trim leading/trailing static; enforce a 1.0 s
universal floor (G-9); if nothing clears the floors, keep the whole clip and say
so. Every trimmed span emits one ReasonRecord citing the signal range that drove
it. Thresholds are config, surfaced in the UI, and tunable (not pre-registered).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone

from backend.contracts.models import (
    Analysis,
    Confidence,
    ReasonRecord,
    Segment,
    SegmentsProposal,
    SourceIndex,
)


@dataclass(frozen=True)
class TrimConfig:
    sharpness_floor: float = 0.35      # §4.4 example floor
    exposure_ceiling: float = 0.50     # fraction of clipped pixels
    shake_ceiling: float = 0.50
    static_motion_ceiling: float = 0.10
    static_audio_ceiling: float = 0.10
    min_window_s: float = 1.0          # universal timeline floor (G-9)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _confidence(fail_fraction: float) -> Confidence:
    if fail_fraction >= 0.75:
        return "high"
    if fail_fraction >= 0.4:
        return "med"
    return "low"


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


class TrimRuleProposer:
    def __init__(self, config: TrimConfig | None = None) -> None:
        self.config = config or TrimConfig()

    def propose_trim(self, source: SourceIndex, analysis: Analysis) -> SegmentsProposal:
        c = self.config
        sig = analysis.signals
        n = len(sig.blur)
        dur = source.duration_s if source.duration_s > 0 else float(n)

        if n == 0:
            return self._fallback(dur, "NO_SIGNALS", "No analysis signals were available, so the whole clip is kept.", [], 0.0)

        good = [
            sig.blur[s] >= c.sharpness_floor
            and sig.exposure[s] <= c.exposure_ceiling
            and sig.shake[s] <= c.shake_ceiling
            for s in range(n)
        ]
        static = [
            sig.motion_energy[s] <= c.static_motion_ceiling and sig.audio_rms[s] <= c.static_audio_ceiling
            for s in range(n)
        ]
        cut_starts = {int(math.floor(t)) for t in analysis.scene_cuts_s if 0 < t < n}

        best = self._longest_good_run(good, cut_starts, n)
        if best is None:  # rule 5 fallback — nothing cleared the floors
            best_second = max(range(n), key=lambda s: sig.blur[s])
            return self._fallback(
                dur, "NO_CLEAR_WINDOW",
                "No section clearly cleared the quality floors, so the whole clip is kept for you to judge.",
                [f"signals.blur[0:{n}]"], round(sig.blur[best_second], 3),
            )

        start, end = best
        core_start, core_end = start, end
        while core_start <= core_end and static[core_start]:
            core_start += 1
        while core_end >= core_start and static[core_end]:
            core_end -= 1
        if core_end < core_start:  # would trim everything — keep the good run
            core_start, core_end = start, end

        in_s = float(core_start)
        out_s = min(float(core_end + 1), dur)
        if out_s - in_s < c.min_window_s:  # honour the 1.0 s floor
            out_s = min(in_s + c.min_window_s, dur)
            in_s = max(0.0, out_s - c.min_window_s)

        reasons: list[ReasonRecord] = []
        if start > 0:
            reasons.append(self._quality_reason("LEADING", 0, start, sig))
        if end < n - 1:
            reasons.append(self._quality_reason("TRAILING", end + 1, n, sig))
        if core_start > start:
            reasons.append(self._static_reason("LEADING_STATIC", start, core_start, sig, "lead-in"))
        if core_end < end:
            reasons.append(self._static_reason("TRAILING_STATIC", core_end + 1, end + 1, sig, "tail"))
        if not reasons:
            reasons.append(ReasonRecord(
                code="WHOLE_CLIP_GOOD",
                human_text="The whole clip cleared the quality floors — nothing needed trimming.",
                evidence_refs=[f"signals.blur[0:{n}]"],
                score=round(_mean(sig.blur), 3),
                confidence="high",
            ))

        return SegmentsProposal(
            value=[Segment(in_s=in_s, out_s=out_s, speed=[])],
            at=_now_iso(),
            reasons=reasons,
            disposition="pending",
        )

    # --- internals --------------------------------------------------------

    def _longest_good_run(self, good: list[bool], cut_starts: set[int], n: int):
        best = None
        s = 0
        while s < n:
            if not good[s]:
                s += 1
                continue
            e = s
            while e + 1 < n and good[e + 1] and (e + 1) not in cut_starts:
                e += 1
            if best is None or (e - s) > (best[1] - best[0]):
                best = (s, e)
            s = e + 1
        return best

    def _quality_reason(self, prefix: str, a: int, b: int, sig) -> ReasonRecord:
        c = self.config
        span = b - a
        blur_fail = sum(1 for s in range(a, b) if sig.blur[s] < c.sharpness_floor)
        shake_fail = sum(1 for s in range(a, b) if sig.shake[s] > c.shake_ceiling)
        exp_fail = sum(1 for s in range(a, b) if sig.exposure[s] > c.exposure_ceiling)
        factor, count = max(
            [("BLUR", blur_fail), ("SHAKE", shake_fail), ("OVEREXPOSED", exp_fail)],
            key=lambda kv: kv[1],
        )
        where = "first" if prefix == "LEADING" else "last"
        field, value, floor_txt = {
            "BLUR": ("blur", _mean([sig.blur[s] for s in range(a, b)]), f"vs {c.sharpness_floor:.2f} floor"),
            "SHAKE": ("shake", _mean([sig.shake[s] for s in range(a, b)]), f"vs {c.shake_ceiling:.2f} limit"),
            "OVEREXPOSED": ("exposure", _mean([sig.exposure[s] for s in range(a, b)]), f"vs {c.exposure_ceiling:.2f} limit"),
        }[factor]
        adjective = {"BLUR": "too blurry", "SHAKE": "too shaky", "OVEREXPOSED": "badly exposed"}[factor]
        return ReasonRecord(
            code=f"{prefix}_{factor}",
            human_text=f"Trimmed the {where} {span} s — {adjective} to keep ({field} {value:.2f} {floor_txt}).",
            evidence_refs=[f"signals.{field}[{a}:{b}]"],
            score=round(value, 3),
            confidence=_confidence(count / span if span else 0.0),
        )

    def _static_reason(self, code: str, a: int, b: int, sig, where: str) -> ReasonRecord:
        span = b - a
        motion = _mean([sig.motion_energy[s] for s in range(a, b)])
        return ReasonRecord(
            code=code,
            human_text=f"Trimmed {span} s of still, quiet footage at the {where} — low motion and near-silence.",
            evidence_refs=[f"signals.motion_energy[{a}:{b}]", f"signals.audio_rms[{a}:{b}]"],
            score=round(motion, 3),
            confidence="med",
        )

    def _fallback(self, dur: float, code: str, text: str, evidence: list[str], score: float) -> SegmentsProposal:
        return SegmentsProposal(
            value=[Segment(in_s=0.0, out_s=dur, speed=[])],
            at=_now_iso(),
            reasons=[ReasonRecord(code=code, human_text=text, evidence_refs=evidence, score=score, confidence="low")],
            disposition="pending",
        )
