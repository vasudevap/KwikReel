"""Error envelope + absolute-path scrubbing (ES-001 §6 / §9, ADR-011).

Every error response is `{error_code, human_text, remediation}` with **no absolute
media paths** — not in the body, and (via `scrub`) not in any surfaced string or
job error. Handlers return fixed, path-free copy; `scrub` is the belt-and-braces
pass for anything derived from an exception message.
"""

from __future__ import annotations

import re

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from backend.ingest import ProbeError
from backend.qa import QAError
from backend.render import RenderError
from backend.store import (
    ConflictError,
    InvariantError,
    ProjectNotFoundError,
    SchemaVersionError,
)

# Any absolute POSIX path -> "<path>". Deliberately greedy on non-space, non-quote.
_ABS_PATH = re.compile(r"/[^\s'\"]+")


def scrub(text: str | None) -> str:
    return _ABS_PATH.sub("<path>", text or "")


def envelope(error_code: str, human_text: str, remediation: str, status: int) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error_code": error_code, "human_text": scrub(human_text), "remediation": remediation},
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProjectNotFoundError)
    async def _not_found(_r: Request, _e: Exception) -> JSONResponse:
        return envelope("not_found", "No such project or resource.", "Check the id and retry.", 404)

    @app.exception_handler(ConflictError)
    async def _conflict(_r: Request, _e: Exception) -> JSONResponse:
        return envelope("conflict", "The project changed since you loaded it.", "Reload, reapply your edit, and save again.", 409)

    @app.exception_handler(SchemaVersionError)
    async def _schema(_r: Request, _e: Exception) -> JSONResponse:
        return envelope("unsupported_schema", "This project uses an unsupported schema version.", "Open it with a matching app version.", 422)

    @app.exception_handler(InvariantError)  # also catches OriginProtectionError (subclass)
    async def _invariant(_r: Request, _e: Exception) -> JSONResponse:
        return envelope("invariant_violation", "That change breaks a project rule.", "Reload and try a smaller edit.", 422)

    @app.exception_handler(ProbeError)
    async def _probe(_r: Request, _e: Exception) -> JSONResponse:
        return envelope("probe_failed", "A media file could not be read.", "Confirm it is a valid, supported video.", 422)

    @app.exception_handler(RenderError)
    async def _render(_r: Request, _e: Exception) -> JSONResponse:
        return envelope("render_failed", "The render could not be produced.", "See the local server log for detail.", 500)

    @app.exception_handler(QAError)
    async def _qa(_r: Request, _e: Exception) -> JSONResponse:
        return envelope("qa_failed", "The output could not be checked.", "See the local server log for detail.", 500)

    @app.exception_handler(RequestValidationError)
    async def _validation(_r: Request, _e: Exception) -> JSONResponse:
        # Do NOT echo FastAPI's default detail — it includes the input, which may
        # contain absolute media paths.
        return envelope("validation_error", "The request body was not valid.", "Check the fields and retry.", 422)

    @app.exception_handler(Exception)
    async def _unexpected(_r: Request, _e: Exception) -> JSONResponse:
        return envelope("internal_error", "Something went wrong.", "See the local server log for detail.", 500)
