"""C-3 HTTP surface (WO-106). FastAPI app + ADR-011 local delivery security.

`create_app(services, config)` wires the ES-001 §6 routes to the WO-101 service
interfaces. Bind to 127.0.0.1 only (run.py).
"""

from backend.api.app import ApiConfig, SecurityMiddleware, create_app
from backend.api.services import Services

__all__ = ["create_app", "ApiConfig", "Services", "SecurityMiddleware"]
