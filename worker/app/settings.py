# Чтение и валидация переменных окружения для Worker'а.
# Worker и API читают ОДИН .env файл, но используют разные переменные.

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    """
    Настройки Worker'а — фонового обработчика задач генерации.
    Читает переменные из .env и переменных окружения Docker.
    """

    database_url: str
    comfy_url: str = "http://host.docker.internal:8188"
    comfy_save_node_id: str = "9"
    worker_poll_interval_sec: float = 2.0
    worker_comfy_poll_interval_sec: float = 2.0
    worker_comfy_timeout_sec: int = 600

    # Настройки pydantic-settings
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


settings = WorkerSettings()
