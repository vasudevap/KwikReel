"""Put the repo root on sys.path so `backend.*` and `tests.*` import when running
pytest from the repo root, with or without an editable install."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
