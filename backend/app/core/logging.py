import logging
import sys
import structlog
from structlog.types import Processor

def setup_logging():
    """
    Configures structlog for the application.
    - JSON logs in production (non-TTY).
    - Pretty colored logs in development (TTY).
    """
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if sys.stdout.isatty():
        # Development: Pretty print
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer()
        ]
    else:
        # Production: JSON print
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )

    # Re-route standard logging to structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

logger = structlog.get_logger()
