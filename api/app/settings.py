# чтение env-переменных

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Все настройки приложения
    """

    database_url: str
    comfy_output_dir: str = "/comfy_output"
    api_key: str = "dev-local-key-change-me"
    rate_limit_per_min: int = 30
    allowed_origins: str = "http://localhost:3000"

    # Настройки поведения pydantic-settings
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


# Синглтон — создаём ОДИН экземпляр и импортируем везде
settings = Settings()
