# worker/app/comfy_client.py
# HTTP-клиент для общения с ComfyUI API.

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .settings import settings


class ComfyError(RuntimeError):
    """Ошибка при взаимодействии с ComfyUI API."""


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
    retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
    reraise=True,
)
def submit_prompt(workflow: dict) -> str:
    """POST /prompt → prompt_id. Пятикратный ретрай на сетевые ошибки."""
    with httpx.Client(base_url=settings.comfy_url, timeout=30.0) as client:
        response = client.post("/prompt", json={"prompt": workflow})
        response.raise_for_status()
        data = response.json()
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            raise ComfyError(f"no prompt_id in response: {data}")
        return prompt_id


def fetch_history(prompt_id: str) -> dict | None:
    """GET /history/{prompt_id} → запись о задаче или None, пока она выполняется."""
    with httpx.Client(base_url=settings.comfy_url, timeout=15.0) as client:
        response = client.get(f"/history/{prompt_id}")
        response.raise_for_status()
        return response.json().get(prompt_id)


def extract_filename(history_entry: dict, save_node_id: str) -> str | None:
    """Извлечь имя первого изображения из output заданного ComfyUI node."""
    outputs = history_entry.get("outputs") or {}
    node = outputs.get(save_node_id) or {}
    images = node.get("images") or []
    if not images:
        return None
    return images[0].get("filename")
