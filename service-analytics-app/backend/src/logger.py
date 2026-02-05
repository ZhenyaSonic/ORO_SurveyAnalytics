"""Модуль для настройки логирования"""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from .settings import settings


class JsonFormatter(logging.Formatter):
    """JSON форматтер для логов"""
    def format(self, record: logging.LogRecord) -> str:
        log_object: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if hasattr(record, "extra"):
            log_object.update(record.extra)

        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_object, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Текстовый форматтер для логов"""
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-settings.MILLISECONDS_TO_TRIM]
        level = record.levelname
        message = record.getMessage()
        logger_name = record.name

        log_message = f"{timestamp} [{level}] {logger_name}: {message}"

        if record.exc_info:
            log_message += f"\n{self.formatException(record.exc_info)}"

        return log_message


def setup_logger() -> logging.Logger:
    """Настройка логгера приложения"""
    logger = logging.getLogger("notification_service")

    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)

    if settings.LOG_FORMAT.lower() == "json":
        formatter = JsonFormatter()
    else:
        formatter = TextFormatter(
            fmt=settings.LOG_TEXT_FORMAT,
            datefmt=settings.LOG_DATE_FORMAT
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logging.getLogger("uvicorn").handlers = []
    logging.getLogger("uvicorn.access").handlers = []

    return logger


logger = setup_logger()
