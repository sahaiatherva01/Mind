"""
Structured Logging with Secret/PII Masking
"""
import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class SafeJSONFormatter(logging.Formatter):
    SENSITIVE_KEYS = {
        "password", "secret", "token", "authorization", "api_key",
        "gemini_api_key", "cookie", "session", "answer_key", "raw_secret"
    }

    def _sanitize(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                k: ("[REDACTED]" if k.lower() in self.SENSITIVE_KEYS else self._sanitize(v))
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [self._sanitize(i) for i in obj]
        return obj

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "props"):
            log_entry["props"] = self._sanitize(getattr(record, "props"))

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def get_logger(name: str = "mind") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(SafeJSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
