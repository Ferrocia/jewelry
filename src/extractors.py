"""Извлечение данных из HTML."""

import json
import re
from typing import Optional, Dict

from bs4 import BeautifulSoup

from utils.helpers import normalize_text


def extract_price(soup: BeautifulSoup) -> Optional[int]:
    """Извлечение цены из страницы товара."""
    # Попытка извлечь цену из JSON-LD
    for s in soup.select("script[type='application/ld+json']"):
        try:
            d = json.loads(s.string)
            if isinstance(d, dict) and "offers" in d:
                return int(float(d["offers"]["price"]))
        except Exception:
            pass
    
    # Поиск цены в тексте страницы
    txt = soup.get_text(" ", strip=True)
    m = re.search(r"(\d[\d\s\u202f]+)\s*₽", txt)
    if m:
        return int(m.group(1).replace(" ", "").replace("\u202f", ""))
    return None


def extract_characteristics(soup: BeautifulSoup) -> Dict[str, str]:
    """Извлечение характеристик товара."""
    data = {}
    for row in soup.select("div.grid.grid-cols-2"):
        cols = row.find_all("div", recursive=False)
        if len(cols) == 2:
            data[
                normalize_text(cols[0].get_text(strip=True))
            ] = normalize_text(cols[1].get_text(strip=True))
    return data


def extract_description(soup: BeautifulSoup) -> Optional[str]:
    """Извлечение описания товара."""
    h = soup.find("h2", string=lambda s: s and "О товаре" in s)
    if not h:
        return None
    for d in h.find_all_next("div"):
        t = d.get_text(" ", strip=True)
        if t and len(t) > 120:
            return normalize_text(t)
    return None


def extract_image_url(soup: BeautifulSoup) -> Optional[str]:
    """Извлечение URL основного изображения."""
    img = soup.select_one("img[src]")
    return img["src"] if img else None

