"""Allowlisted server events; never format raw messages, args or tracebacks."""
from datetime import datetime, timezone
import json
import logging

_EVENTS = {
    "Started server process [%d]": "server_started",
    "Waiting for application startup.": "application_starting",
    "Application startup complete.": "application_started",
    "Shutting down": "server_stopping",
    "Waiting for application shutdown.": "application_stopping",
    "Application shutdown complete.": "application_stopped",
    "Finished server process [%d]": "server_stopped",
    "Exception in ASGI application": "request_failed",
    "Error loading ASGI app. %s": "application_load_failed",
    "ASGI 'lifespan' protocol appears unsupported.": "lifespan_unsupported",
}
_EXCEPTIONS = {kind: kind.__name__ for kind in (
    RuntimeError, ValueError, TypeError, KeyError, OSError, TimeoutError,
    ConnectionError, PermissionError, FileNotFoundError, ExceptionGroup,
)}


class ServerFormatter(logging.Formatter):
    def format(self, record):
        level = record.levelno if type(record.levelno) is int else logging.ERROR
        name = next((label for minimum, label in ((50, "CRITICAL"), (40, "ERROR"),
            (30, "WARNING"), (20, "INFO"), (10, "DEBUG")) if level >= minimum), "DEBUG")
        event = "server_error" if level >= 40 else "server_warning" if level >= 30 else "server_event"
        if type(record.msg) is str and len(record.msg) <= 200:
            event = _EVENTS.get(record.msg.strip(), event)
        source = record.name if type(record.name) is str and record.name in {
            "uvicorn", "uvicorn.error", "uvicorn.access", "asyncio"} else "server"
        result = {"format": "ami-server-event-v1", "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                  "level": name, "source": source, "event": event}
        if isinstance(record.exc_info, tuple) and len(record.exc_info) > 1:
            result["exception_type"] = _EXCEPTIONS.get(type(record.exc_info[1]), "Exception")
        # Do not call getMessage(), formatException(), repr() or the parent
        # formatter: each can copy arbitrary request/provider data into logs.
        return json.dumps(result, sort_keys=True)


def server_logging_config():
    """Applied only by the explicit launcher, leaving evaluation/root logs alone."""
    return {"version": 1, "disable_existing_loggers": False,
        "formatters": {"server": {"()": "src.pilot._server_logging.ServerFormatter"}},
        "handlers": {"server": {"class": "logging.StreamHandler", "formatter": "server", "stream": "ext://sys.stderr"}},
        "loggers": {
            "uvicorn": {"handlers": ["server"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"handlers": [], "level": "INFO", "propagate": True},
            "uvicorn.access": {"handlers": [], "level": "INFO", "propagate": False},
            "asyncio": {"handlers": ["server"], "level": "WARNING", "propagate": False},
        }}
