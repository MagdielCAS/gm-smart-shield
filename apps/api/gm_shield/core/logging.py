"""
Structured logging setup for GM Smart Shield.

Provides a single ``configure_logging()`` function that wires up structlog with
the appropriate renderer for the current environment, and a ``get_logger()``
factory used by every module in the application.

Configuration is controlled by two optional environment variables:

- ``LOG_LEVEL`` — minimum level to emit (default: ``"INFO"``).  Accepted values:
  ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, ``CRITICAL``.
- ``LOG_FORMAT`` — output format (default: ``"console"``).  Accepted values:

  - ``"console"`` — coloured, human-readable output via
    :class:`structlog.dev.ConsoleRenderer` (ideal for local development).
  - ``"json"`` — newline-delimited JSON via
    :class:`structlog.processors.JSONRenderer` (ideal for production / log
    aggregators).

Call :func:`configure_logging` **once** at application startup (``main.py``)
before any loggers are obtained.  Every other module should only call
:func:`get_logger`.

Example::

    # main.py
    from gm_shield.core.logging import configure_logging, get_logger
    configure_logging()
    logger = get_logger(__name__)
    logger.info("app_started", version="0.1.0")
"""

import logging
import os
import sys

import structlog

# ── Public API ────────────────────────────────────────────────────────────────


def configure_logging(
    log_level: str | None = None,
    json_logs: bool | None = None,
) -> None:
    """
    Configure structlog and the stdlib ``logging`` root logger.

    Should be called **once** at application startup before any loggers are
    created.  Subsequent calls are safe but will re-configure the processors.

    Args:
        log_level: Minimum log level to emit.  Defaults to the ``LOG_LEVEL``
            environment variable, or ``"INFO"`` when unset.
        json_logs: When ``True``, emit newline-delimited JSON; when ``False``
            (the default for local development), use the coloured
            ``ConsoleRenderer``.  Defaults to ``True`` when the ``LOG_FORMAT``
            environment variable is set to ``"json"``, ``False`` otherwise.
    """
    # ── Resolve configuration from env when callers pass None ────────────────
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    if json_logs is None:
        json_logs = os.getenv("LOG_FORMAT", "console").lower() == "json"

    numeric_level = getattr(logging, log_level, logging.INFO)

    # ── Shared pre-chain processors ───────────────────────────────────────────
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # ── Final renderer ────────────────────────────────────────────────────────
    if json_logs:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        # stdlib.LoggerFactory() creates real stdlib loggers under the hood so
        # that stdlib.add_logger_name can read the ``.name`` attribute.
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # ── Stdlib root logger ────────────────────────────────────────────────────
    # Ensure stdlib messages (from third-party libraries) flow through structlog.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Return a structlog bound logger for the given module name.

    This is the **only** way to obtain a logger in the application.  Never
    call ``logging.getLogger`` or ``print`` in production code.

    Args:
        name: Typically ``__name__`` of the calling module.  Used as the
            ``logger`` field in every log record emitted by the returned logger.

    Returns:
        A :class:`structlog.BoundLogger` instance pre-bound with ``name``.

    Example::

        from gm_shield.core.logging import get_logger
        logger = get_logger(__name__)
        logger.info("ingestion_started", file_path="/data/book.pdf")
    """
    return structlog.get_logger(name)
