# API key, rate-limit (прод-хуки)

from fastapi import Header, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

from .settings import settings

# Глобальный in-memory лимитер запросов на основе IP клиента.
limiter = Limiter(key_func=get_remote_address)


def require_api_key(x_api_key: str = Header(default="")) -> None:
    """
    Проверяет наличие и корректность API-ключа в заголовке X-API-Key.
    Если ключ не задан в настройках (пустая строка) — dev-режим, пропускаем всех.
    В продакшене ключ обязательно должен быть установлен через переменную окружения API_KEY.
    """
    if not settings.api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="invalid API key")
