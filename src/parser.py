"""Основной модуль парсера."""

from typing import Dict, Set
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config.settings import BASE_URL, CATALOG_URLS, PAUSE_CATALOG
from src.selenium_utils import setup_driver
from src.extractors import (
    extract_price,
    extract_characteristics,
    extract_description,
    extract_image_url,
)
from utils.helpers import (
    normalize_text,
    normalize_image_url,
    sleep_rand,
)


def parse_product_page(driver, url: str) -> Dict:
    """Парсинг страницы товара."""
    driver.get(url)
    WebDriverWait(driver, 25).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    sleep_rand(1.5, 2.5)

    soup = BeautifulSoup(driver.page_source, "lxml")
    title_el = soup.select_one("h1")

    return {
        "url": url,
        "title": normalize_text(title_el.get_text(strip=True)) if title_el else None,
        "price": extract_price(soup),
        "description": extract_description(soup),
        "characteristics": extract_characteristics(soup),
        "image_url": normalize_image_url(extract_image_url(soup)),
    }


def collect_product_links(driver) -> Set[str]:
    """Сбор ссылок на товары из каталогов."""
    all_links = set()

    print("📂 Сбор карточек из каталогов")
    for cat in CATALOG_URLS:
        print(f"   → {cat}")
        driver.get(cat)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.product-card"))
        )
        sleep_rand(2, 3)

        soup = BeautifulSoup(driver.page_source, "lxml")
        links = [
            urljoin(BASE_URL, a["href"])
            for a in soup.select("a.product-card[href]")
        ]

        print(f"     найдено: {len(links)}")
        all_links.update(links)
        sleep_rand(*PAUSE_CATALOG)

    return all_links

