"""Сервис начальных настроек """
from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn
from typing import Optional
import os


class Settings(BaseSettings):
    """Настройки приложения через переменные окружения"""
    APP_NAME: str = "Smart Notification System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="Режим отладки")

    APP_HOST: str = Field(default="0.0.0.0", description="Хост приложения")
    APP_PORT: int = Field(default=8000, description="Порт приложения")

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/survey_db"
    )

    LOG_LEVEL: str = Field(default="INFO", description="Уровень логирования")
    LOG_FORMAT: str = Field(
        default="json",
        description="Формат логов (json или text)"
    )

    # Форматирование времени
    TIME_FORMAT_DECIMAL_PLACES: int = Field(
        default=3, description="Количество знаков после запятой для времени"
    )
    MILLISECONDS_TO_TRIM: int = Field(
        default=3, description="Количество символов для обрезки строки миллисекунд"
    )

    # Форматы логирования
    LOG_TEXT_FORMAT: str = Field(
        default="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        description="Формат текстового лога"
    )
    LOG_DATE_FORMAT: str = Field(
        default="%Y-%m-%d %H:%M:%S",
        description="Формат даты в логах"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
