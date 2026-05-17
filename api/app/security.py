# API key, rate-limit (прод-хуки)

from fastapi import Header, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

from .settings import settings

limiter = Limiter(key_func=get_remote_address)
# Limiter — глобальный счётчик запросов (in-memory).
# key_func=get_remote_address — считает запросы по IP клиента.


# TODO : Перед продом добавить ключ. раздел 10
# Если API_KEY пустой или не задан — dev-режим, пропускаем всех
def require_api_key(x_api_key: str = Header(default="")) -> None:
    if not settings.api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="invalid API key")
