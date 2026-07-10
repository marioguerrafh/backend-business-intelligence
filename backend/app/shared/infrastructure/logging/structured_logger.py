import logging
from typing import Any


class StructuredLogger:
    def __init__(self, logger_name: str, base_context: dict[str, Any] | None = None) -> None:
        self._logger = logging.getLogger(logger_name)
        self._base_context = base_context or {}

    def with_context(self, **context: Any) -> "StructuredLogger":
        merged = dict(self._base_context)
        merged.update(context)
        return StructuredLogger(logger_name=self._logger.name, base_context=merged)

    def info(self, message: str, extra: dict[str, Any] | None = None) -> None:
        payload = dict(self._base_context)
        if extra:
            payload.update(extra)
        self._logger.info(message, extra=payload)

    def warning(self, message: str, extra: dict[str, Any] | None = None) -> None:
        payload = dict(self._base_context)
        if extra:
            payload.update(extra)
        self._logger.warning(message, extra=payload)

    def error(self, message: str, extra: dict[str, Any] | None = None) -> None:
        payload = dict(self._base_context)
        if extra:
            payload.update(extra)
        self._logger.error(message, extra=payload)
