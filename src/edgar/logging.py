import logging
import logging.config

import structlog
from structlog.contextvars import get_contextvars, merge_contextvars
from structlog.dev import ConsoleRenderer, RichTracebackFormatter
from structlog.processors import StackInfoRenderer, TimeStamper
from structlog.stdlib import (
    BoundLogger,
    ExtraAdder,
    LoggerFactory,
    PositionalArgumentsFormatter,
    ProcessorFormatter,
    add_log_level,
    add_logger_name,
)
from structlog.typing import EventDict, WrappedLogger

Level = str | int


def get_logger(name: str | None = None) -> BoundLogger:
    return structlog.stdlib.get_logger(name)


def configure_logging(level: Level) -> None:
    shared_processors = [
        add_log_level,
        add_logger_name,
        merge_contextvars,
        reorder_contextvars,
        TimeStamper(fmt="iso"),
        StackInfoRenderer(),
    ]

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "colors": {
                    "()": ProcessorFormatter,
                    "foreign_pre_chain": [
                        ExtraAdder(),
                        shared_processors,
                    ],
                    "processors": [
                        ProcessorFormatter.remove_processors_meta,
                        ConsoleRenderer(
                            pad_event=60,
                            colors=True,
                            sort_keys=False,
                            exception_formatter=RichTracebackFormatter(
                                show_locals=True
                            ),
                        ),
                    ],
                }
            },
            "handlers": {
                "console": {
                    "level": level,
                    "class": "logging.StreamHandler",
                    "formatter": "colors",
                }
            },
            "loggers": {
                "__main__": {
                    "level": level,
                    "handlers": ["console"],
                    "propagate": True,
                },
                "edgar": {
                    "level": level,
                    "handlers": ["console"],
                    "propagate": True,
                },
            },
        },
    )

    structlog.configure(
        processors=[
            *shared_processors,
            PositionalArgumentsFormatter(),
            ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=BoundLogger,
        cache_logger_on_first_use=True,
    )


def reorder_contextvars(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    context_keys = get_contextvars().keys()
    context_data = {k: event_dict.pop(k) for k in context_keys if k in event_dict}
    return {**context_data, **event_dict}


configure_logging("DEBUG")
