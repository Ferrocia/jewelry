"""Валидация данных продуктов."""

from typing import Optional, Dict, List, Tuple


class ValidationError(Exception):
    """Ошибка валидации данных."""

    pass


def validate_url(url: Optional[str]) -> bool:
    """Валидация URL."""
    if not url:
        return False
    return url.startswith("http://") or url.startswith("https://")


def validate_price(price: Optional[int]) -> bool:
    """Валидация цены."""
    if price is None:
        return False
    return price > 0 and price < 10_000_000  # Разумные пределы


def validate_title(title: Optional[str]) -> bool:
    """Валидация названия товара."""
    if not title:
        return False
    title = title.strip()
    return len(title) >= 3 and len(title) <= 500


def validate_description(description: Optional[str]) -> bool:
    """Валидация описания товара."""
    if description is None:
        return True  # Описание необязательно
    description = description.strip()
    return len(description) <= 10000  # Максимальная длина


def validate_image_url(image_url: Optional[str]) -> bool:
    """Валидация URL изображения."""
    if image_url is None:
        return True  # Изображение необязательно
    return validate_url(image_url)


def validate_characteristics(characteristics: Dict[str, str]) -> bool:
    """Валидация характеристик."""
    if not isinstance(characteristics, dict):
        return False
    # Проверка на пустые ключи или значения
    for key, value in characteristics.items():
        if not key or not key.strip():
            return False
        if not value or not value.strip():
            return False
    return True


def validate_product(product: Dict) -> Tuple[bool, List[str]]:
    """
    Комплексная валидация продукта.
    
    Returns:
        Tuple[bool, List[str]]: (валиден ли продукт, список ошибок)
    """
    errors = []
    
    if not validate_url(product.get("url")):
        errors.append("Неверный или отсутствующий URL товара")
    
    if not validate_title(product.get("title")):
        errors.append("Неверное или отсутствующее название товара")
    
    if not validate_price(product.get("price")):
        errors.append("Неверная или отсутствующая цена")
    
    if not validate_description(product.get("description")):
        errors.append("Описание слишком длинное")
    
    if not validate_image_url(product.get("image_url")):
        errors.append("Неверный URL изображения")
    
    if not validate_characteristics(product.get("characteristics", {})):
        errors.append("Неверные характеристики товара")
    
    return len(errors) == 0, errors


def validate_product_strict(product: Dict) -> None:
    """
    Строгая валидация продукта (бросает исключение при ошибке).
    
    Raises:
        ValidationError: Если продукт не прошел валидацию
    """
    is_valid, errors = validate_product(product)
    if not is_valid:
        raise ValidationError(f"Ошибки валидации: {', '.join(errors)}")

