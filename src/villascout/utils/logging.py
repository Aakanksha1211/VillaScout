import json
import logging
import sys
from collections.abc import Mapping


def configure_logging(level: str) -> None:
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level.upper(), force=True)
    logging.getLogger("httpx").setLevel(logging.WARNING)


class StructuredLogger:
    def __init__(self, name: str, context: dict[str, object] | None = None) -> None:
        self._logger = logging.getLogger(name)
        self._context = context or {}

    def bind(self, **context: object) -> "StructuredLogger":
        return StructuredLogger(self._logger.name, {**self._context, **context})

    def info(self, event: str, **context: object) -> None:
        self._log(logging.INFO, event, context)

    def warning(self, event: str, **context: object) -> None:
        self._log(logging.WARNING, event, context)

    def _log(self, level: int, event: str, context: dict[str, object]) -> None:
        payload = {"event": event, "logger": self._logger.name, **self._context, **context}
        self._logger.log(level, json.dumps(payload, default=str, ensure_ascii=False))


def get_logger(name: str, **context: object) -> StructuredLogger:
    return StructuredLogger(name, context)


def redact_mapping(values: Mapping[str, object]) -> dict[str, object]:
    redacted: dict[str, object] = {}
    for key, value in values.items():
        if key.lower() in {"key", "api_key", "google_api_key", "token", "authorization"}:
            redacted[key] = "***REDACTED***"
        else:
            redacted[key] = value
    return redacted
