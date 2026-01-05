"""Вспомогательные функции."""

import os
import base64
import random
import tempfile
import time
import requests
from typing import Optional


def sleep_rand(a: float, b: float) -> None:
    """Случайная пауза между запросами."""
    time.sleep(random.uniform(a, b))


def normalize_text(v: Optional[str]) -> Optional[str]:
    """Нормализация текста (обработка кодировки)."""
    if v is None:
        return None
    return v.encode("utf-8", errors="ignore").decode("utf-8")


def normalize_image_url(url: Optional[str]) -> Optional[str]:
    """Декодирование base64 URL изображений."""
    if not url or "/aHR0cHM6" not in url:
        return url
    try:
        encoded = url.split("/")[-1].split(".jpg")[0]
        return base64.b64decode(encoded).decode("utf-8")
    except Exception:
        return url


def download_temp_image(url: str) -> str:
    """Скачивание изображения во временный файл."""
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    fd, path = tempfile.mkstemp(suffix=".jpg")
    with os.fdopen(fd, "wb") as f:
        f.write(r.content)
    return path

