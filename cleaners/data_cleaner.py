"""Очистка и нормализация данных продуктов."""

import re
from typing import Optional, Dict

from utils.helpers import normalize_text


def clean_text(text: Optional[str]) -> Optional[str]:
    """
    Очистка текста от лишних пробелов и символов.
    
    Удаляет:
    - Множественные пробелы
    - Переносы строк и табуляции
    - Специальные невидимые символы
    """
    if not text:
        return None
    
    # Нормализация кодировки
    text = normalize_text(text)
    
    # Замена переносов и табуляций на пробелы
    text = re.sub(r'[\n\r\t]+', ' ', text)
    
    # Удаление множественных пробелов
    text = re.sub(r'\s+', ' ', text)
    
    # Удаление пробелов в начале и конце
    text = text.strip()
    
    # Удаление невидимых символов (кроме обычных пробелов)
    text = re.sub(r'[\u200b-\u200f\u202a-\u202e\u2060-\u206f]', '', text)
    
    return text if text else None


def clean_price(price: Optional[int]) -> Optional[int]:
    """Очистка и нормализация цены."""
    if price is None:
        return None
    
    # Убеждаемся, что цена положительная
    if price < 0:
        return None
    
    return price


def clean_title(title: Optional[str]) -> Optional[str]:
    """Очистка названия товара."""
    if not title:
        return None
    
    title = clean_text(title)
    
    if not title:
        return None
    
    # Обрезка слишком длинных названий
    if len(title) > 500:
        title = title[:497] + "..."
    
    return title


def clean_description(description: Optional[str]) -> Optional[str]:
    """Очистка описания товара."""
    if not description:
        return None
    
    description = clean_text(description)
    
    if not description:
        return None
    
    # Обрезка слишком длинных описаний
    if len(description) > 10000:
        description = description[:9997] + "..."
    
    return description


def clean_characteristics(characteristics: Dict[str, str]) -> Dict[str, str]:
    """Очистка характеристик товара."""
    if not isinstance(characteristics, dict):
        return {}
    
    cleaned = {}
    for key, value in characteristics.items():
        # Очистка ключа и значения
        clean_key = clean_text(key)
        clean_value = clean_text(value)
        
        # Пропускаем пустые ключи или значения
        if not clean_key or not clean_value:
            continue
        
        # Нормализация ключа (первая буква заглавная)
        clean_key = clean_key.strip()
        if clean_key:
            clean_key = clean_key[0].upper() + clean_key[1:] if len(clean_key) > 1 else clean_key.upper()
        
        cleaned[clean_key] = clean_value
    
    return cleaned


def clean_product(product: Dict) -> Dict:
    """
    Комплексная очистка данных продукта.
    
    Применяет все функции очистки к полям продукта.
    """
    cleaned = {
        "url": product.get("url"),
        "title": clean_title(product.get("title")),
        "price": clean_price(product.get("price")),
        "description": clean_description(product.get("description")),
        "characteristics": clean_characteristics(product.get("characteristics", {})),
        "image_url": product.get("image_url"),  # URL обычно не требует очистки
    }
    
    return cleaned

