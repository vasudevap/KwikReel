"""C-7 · Per-clip analysis (WO-111). Quality signals for the trim proposer.

`OpenCVAnalysis` satisfies the `AnalysisService` interface (WO-101): it reads the
proxy (video) and the original (audio, read-only) and emits normalised per-second
signals as `analysis.json` (ES-001 §4.3 / §5.1). `FileAnalysisStore` persists
them so `propose` can read what `analyze` computed. Facts, not decisions.
"""

from backend.analysis.analysis_store import FileAnalysisStore
from backend.analysis.opencv_analysis import AnalysisConfig, AnalysisError, OpenCVAnalysis

__all__ = ["OpenCVAnalysis", "AnalysisConfig", "AnalysisError", "FileAnalysisStore"]
