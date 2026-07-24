"""C-5 · Output QA (WO-105). The gate that blocks export on a bad render.

`FFmpegOutputQA` satisfies the `OutputQA` interface (WO-101) and implements the
ES-001 §8.3 checks, emitting a `QAReport`. It never renders and never mutates —
it inspects a produced file against the mode's expectations.
"""

from backend.qa.output_qa import FFmpegOutputQA, QAError

__all__ = ["FFmpegOutputQA", "QAError"]
