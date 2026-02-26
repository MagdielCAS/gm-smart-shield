"""
Unit tests for the structured logging infrastructure.

Verifies that ``configure_logging`` and ``get_logger`` produce loggers whose
records carry the expected structured fields.
"""

import pytest
import structlog
from structlog.testing import capture_logs

from gm_shield.core.logging import configure_logging, get_logger


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_structlog():
    """Re-configure structlog in test mode before each test and restore afterwards."""
    # structlog.testing.capture_logs works best with the test processor chain.
    configure_logging(log_level="DEBUG", json_logs=False)
    yield
    # Reset to a clean state so each test is isolated.
    structlog.reset_defaults()


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_get_logger_returns_bound_logger():
    """get_logger should return a structlog BoundLogger-compatible object."""
    logger = get_logger("test.module")
    assert logger is not None
    assert hasattr(logger, "info")
    assert hasattr(logger, "warning")
    assert hasattr(logger, "error")
    assert hasattr(logger, "debug")


def test_log_event_name_captured():
    """
    Structured log records should carry the event name as the ``event`` key.
    """
    logger = get_logger("test.event")
    with capture_logs() as logs:
        logger.info("something_happened")

    assert len(logs) == 1
    assert logs[0]["event"] == "something_happened"


def test_log_keyword_fields_captured():
    """
    Keyword arguments passed to log calls should appear as top-level keys
    in the captured log record.
    """
    logger = get_logger("test.fields")
    with capture_logs() as logs:
        logger.info("ingestion_started", file_path="/data/book.pdf", chunk_count=42)

    assert len(logs) == 1
    record = logs[0]
    assert record["event"] == "ingestion_started"
    assert record["file_path"] == "/data/book.pdf"
    assert record["chunk_count"] == 42


def test_log_level_field_present():
    """
    Every captured record should expose a ``log_level`` field matching the
    method called.
    """
    logger = get_logger("test.level")
    with capture_logs() as logs:
        logger.warning("something_degraded", service="ollama")

    assert len(logs) == 1
    assert logs[0]["log_level"] == "warning"


def test_error_record_fields():
    """
    Error records should carry the expected event and context fields.
    """
    logger = get_logger("test.error")
    with capture_logs() as logs:
        logger.error(
            "text_extraction_failed",
            file_path="/bad/file.exe",
            error="Unsupported file type: .exe",
        )

    assert len(logs) == 1
    record = logs[0]
    assert record["event"] == "text_extraction_failed"
    assert record["file_path"] == "/bad/file.exe"
    assert "Unsupported" in record["error"]
    assert record["log_level"] == "error"


def test_configure_logging_console_mode():
    """configure_logging should not raise when json_logs=False."""
    configure_logging(log_level="DEBUG", json_logs=False)
    logger = get_logger("test.console")
    with capture_logs() as logs:
        logger.debug("debug_event", key="value")

    assert any(log["event"] == "debug_event" for log in logs)


def test_configure_logging_json_mode():
    """configure_logging should not raise when json_logs=True."""
    configure_logging(log_level="INFO", json_logs=True)
    logger = get_logger("test.json")
    with capture_logs() as logs:
        logger.info("json_event", key="value")

    assert any(log["event"] == "json_event" for log in logs)
