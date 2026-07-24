"""In-memory async job runner for the long operations (scan, finalize, export).

Reports `{state, progress, error}` (ES-001 §6). A failing job surfaces its error
rather than hanging, and the error is path-scrubbed before it is ever readable.
"""

from __future__ import annotations

import secrets
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable, Optional

ProgressFn = Callable[[float], None]


@dataclass
class Job:
    state: str = "queued"   # queued | running | done | error
    progress: float = 0.0
    error: Optional[str] = None


class JobRunner:
    def __init__(self, scrub: Callable[[str], str], max_workers: int = 2) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="reel-job")
        self._scrub = scrub

    def submit(self, work: Callable[[ProgressFn], None]) -> str:
        job_id = secrets.token_urlsafe(8)
        with self._lock:
            self._jobs[job_id] = Job()
        self._pool.submit(self._run, job_id, work)
        return job_id

    def _run(self, job_id: str, work: Callable[[ProgressFn], None]) -> None:
        self._update(job_id, state="running")
        try:
            work(lambda p: self._update(job_id, progress=max(0.0, min(1.0, p))))
            self._update(job_id, state="done", progress=1.0)
        except Exception as exc:  # noqa: BLE001 - surfaced to the client, scrubbed
            self._update(job_id, state="error", error=self._scrub(str(exc)))

    def _update(self, job_id: str, **fields) -> None:
        with self._lock:
            job = self._jobs[job_id]
            for key, value in fields.items():
                setattr(job, key, value)

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)
