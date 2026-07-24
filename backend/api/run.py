"""Local entrypoint — binds 127.0.0.1 ONLY (ES-001 §9 / ADR-005).

Binding beyond 127.0.0.1 is a stop-and-ask. Prints the per-launch capability
token; the frontend obtains it by being served with it injected (WO-107), never
from an unauthenticated endpoint.

    python -m backend.api.run --data ~/.reel-agent --port 8000
"""

from __future__ import annotations

import argparse
from pathlib import Path

from backend.api import ApiConfig, Services, create_app
from backend.ingest import FFmpegIngest
from backend.qa import FFmpegOutputQA
from backend.render import FFmpegRenderer
from backend.store import FileProjectStore


def build_app(data_root: Path):
    proxy_root = data_root / "proxies"
    output_root = data_root / "renders"
    services = Services(
        store=FileProjectStore(data_root / "projects"),
        ingest=FFmpegIngest(proxy_root=proxy_root),
        renderer=FFmpegRenderer(output_root=output_root),
        qa=FFmpegOutputQA(),
    )
    config = ApiConfig(proxy_root=proxy_root, output_root=output_root)
    app = create_app(services, config)
    print(f"capability token (this launch): {app.state.capability_token}")
    return app


def main() -> None:  # pragma: no cover - operational entrypoint
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(Path.home() / ".reel-agent"))
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    app = build_app(Path(args.data))
    # 127.0.0.1 ONLY. Do not change to 0.0.0.0 without an owner-authorized ADR change.
    uvicorn.run(app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":  # pragma: no cover
    main()
