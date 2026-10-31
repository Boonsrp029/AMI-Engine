"""Fixed server metadata, never private messages, locals, paths or traceback."""
import json
import logging
import sys

import pytest

from src.pilot._server_logging import ServerFormatter, server_logging_config

PRIVATE = "synthetic-private-provider-body"


@pytest.mark.parametrize("level,event", [(logging.INFO, "server_event"),
    (logging.WARNING, "server_warning"), (logging.ERROR, "server_error"), (logging.CRITICAL, "server_error")])
def test_unknown_messages_and_all_user_fields_are_omitted(level, event):
    record = logging.LogRecord("uvicorn.error", level, PRIVATE, 23, PRIVATE+" %s", (PRIVATE,), None)
    record.stack_info = PRIVATE; record.exc_text = PRIVATE; record.private = PRIVATE
    text = ServerFormatter().format(record)
    assert PRIVATE not in text
    value = json.loads(text)
    assert value["event"] == event and value["source"] == "uvicorn.error"
    assert set(value) == {"format", "timestamp_utc", "level", "source", "event"}


def test_known_events_retain_codes_without_message_arguments():
    record = logging.LogRecord("uvicorn.error", logging.INFO, PRIVATE, 1, "Started server process [%d]", (123456,), None)
    value = json.loads(ServerFormatter().format(record))
    assert value["event"] == "server_started" and "123456" not in json.dumps(value)


def test_exception_type_survives_without_raw_message_or_traceback():
    try:raise RuntimeError(PRIVATE)
    except RuntimeError:
        record = logging.LogRecord("uvicorn.error", logging.ERROR, PRIVATE, 1, "Exception in ASGI application\n", (), sys.exc_info())
    value = json.loads(ServerFormatter().format(record))
    assert value["event"] == "request_failed" and value["exception_type"] == "RuntimeError"
    assert PRIVATE not in json.dumps(value) and "Traceback" not in json.dumps(value)


def test_custom_exception_names_and_logger_names_are_not_reflected():
    custom = type(PRIVATE, (Exception,), {})
    record = logging.LogRecord(PRIVATE, logging.ERROR, PRIVATE, 1, PRIVATE, (), (custom, custom(PRIVATE), None))
    value = json.loads(ServerFormatter().format(record))
    assert value["exception_type"] == "Exception" and value["source"] == "server"
    assert PRIVATE not in json.dumps(value)


def test_formatter_does_not_stringify_hostile_objects():
    class Hostile:
        def __str__(self):raise AssertionError("Raw object formatted")
        def __repr__(self):raise AssertionError("Raw object represented")
    record = logging.LogRecord("uvicorn.error", logging.ERROR, PRIVATE, 1, Hostile(), (Hostile(),), None)
    assert json.loads(ServerFormatter().format(record))["event"] == "server_error"


def test_config_keeps_access_logs_off_and_root_unmodified():
    config = server_logging_config()
    assert "root" not in config and config["disable_existing_loggers"] is False
    assert config["loggers"]["uvicorn.access"] == {"handlers": [], "level": "INFO", "propagate": False}
    assert config["loggers"]["asyncio"]["propagate"] is False
    config["loggers"].clear()
    assert server_logging_config()["loggers"]
