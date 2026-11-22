# API key, rate-limit (прод-хуки)

import hmac

from fastapi import Header, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

from .settings import settings

# Глобальный in-memory лимитер запросов на основе IP клиента.
limiter = Limiter(key_func=get_remote_address)


def require_api_key(x_api_key: str = Header(default="")) -> None:
    """
    Проверяет наличие и корректность API-ключа в заголовке X-API-Key.
    Ключ должен быть задан в настройках и совпадать с переданным значением.
    Если ключ в настройках пустой или не совпадает с заголовком, доступ запрещается (403).
    """
    if not settings.api_key or not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=403, detail="invalid API key")
