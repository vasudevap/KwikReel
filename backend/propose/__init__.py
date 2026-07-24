"""C-8 · Trim proposer (WO-112). Deterministic, legible in/out proposals.

`TrimRuleProposer` satisfies the `TrimProposer` interface (WO-101) and implements
the ES-001 §5.2 rules over the analysis signals. Every proposal carries one
plain-language `ReasonRecord` per contributing factor (ADR-006); nothing is a
black box. No media or ffmpeg here — pure logic over `Analysis`.
"""

from backend.propose.trim_proposer import TrimConfig, TrimRuleProposer

__all__ = ["TrimRuleProposer", "TrimConfig"]
