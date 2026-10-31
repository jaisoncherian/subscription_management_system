"""Structured JSON logs, with a request id on every line logged during a request."""
import json
import logging
import re
import sys
import time
import uuid
from datetime import datetime, timezone

from flask import Flask, g, has_request_context, request

REQUEST_ID_HEADER = "X-Request-ID"
# A caller-supplied id ends up in logs and response headers, so it must be plain.
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }
        # logger.info("...", extra={"context": {...}}) adds structured fields.
        entry.update(getattr(record, "context", {}))
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def get_request_id() -> str | None:
    return g.get("request_id") if has_request_context() else None


def configure_logging(app: Flask) -> None:
    # Under pytest, leave logging to pytest: a stream handler would keep a
    # reference to its captured stdout after that stream has been closed.
    if app.testing:
        return

    root = logging.getLogger()
    root.setLevel(logging.DEBUG if app.debug else logging.INFO)
    if not any(isinstance(h.formatter, JsonFormatter) for h in root.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        root.addHandler(handler)


def register_request_logging(app: Flask) -> None:
    @app.before_request
    def start_request():
        supplied = request.headers.get(REQUEST_ID_HEADER, "")
        g.request_id = (
            supplied if _SAFE_REQUEST_ID.fullmatch(supplied) else uuid.uuid4().hex
        )
        g.request_started_at = time.perf_counter()

    @app.after_request
    def finish_request(response):
        response.headers[REQUEST_ID_HEADER] = g.request_id
        duration_ms = (time.perf_counter() - g.request_started_at) * 1000
        app.logger.info(
            "request completed",
            extra={
                "context": {
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                }
            },
        )
        return response
