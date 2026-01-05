import os
import re
import json
import time
import base64
import random
import tempfile
import requests
from typing import Optional, Dict, List
from urllib.parse import urljoin, urlparse

import psycopg2
import psycopg2.extras
from minio import Minio

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup


# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

BASE = "https://www.585zolotoy.ru"
SHOP = "585zolotoy"

CATALOG_URLS = [
    "https://www.585zolotoy.ru/catalog/sergi-kongo-s-kamnyami/",
    "https://www.585zolotoy.ru/catalog/sergi-kongo-s-zhemchugom/",
    "https://www.585zolotoy.ru/catalog/sergi-kresty/",
    "https://www.585zolotoy.ru/catalog/sergi-pusety-s-sapfirami/",
    "https://www.585zolotoy.ru/catalog/sergi-s-kruglymi-kamnyami/",
    "https://www.585zolotoy.ru/catalog/sergi-s-tantsuyushhimi-brilliantami/",
    "https://www.585zolotoy.ru/catalog/sergi-s-tantsuyushhimi-kamnyami/",
    "https://www.585zolotoy.ru/catalog/sergi-s-zheltymi-brilliantami/",
    "https://www.585zolotoy.ru/catalog/sergi-tsepochki-iz-serebra/",
    "https://www.585zolotoy.ru/catalog/sergi-zmeyi-iz-serebra/",
    "https://www.585zolotoy.ru/catalog/sergi-zmeyi-iz-zolota/",
    "https://www.585zolotoy.ru/catalog/sergi-zmeyi/",
]

DB_CONFIG = {
    "dbname": "jewelry",
    "user": "jewelry_user",
    "password": "qqqwww12!",
    "host": "127.0.0.1",
    "port": 5432,
}

MINIO_CONFIG = {
    "endpoint": "127.0.0.1:9000",
    "access_key": "admin",
    "secret_key": "password",
    "secure": False,
}

MINIO_BUCKET = "jewelry-images"

PAUSE_CARD = (3, 6)
PAUSE_CATALOG = (6, 10)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def sleep_rand(a, b):
    time.sleep(random.uniform(a, b))


def normalize_text(v):
    if v is None:
        return None
    return v.encode("utf-8", errors="ignore").decode("utf-8")


def normalize_image_url(url: Optional[str]) -> Optional[str]:
    if not url or "/aHR0cHM6" not in url:
        return url
    try:
        encoded = url.split("/")[-1].split(".jpg")[0]
        return base64.b64decode(encoded).decode("utf-8")
    except Exception:
        return url


def download_temp_image(url: str) -> str:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    fd, path = tempfile.mkstemp(suffix=".jpg")
    with os.fdopen(fd, "wb") as f:
        f.write(r.content)
    return path


# ---------------------------------------------------------------------
# Selenium
# ---------------------------------------------------------------------

def setup_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )


# ---------------------------------------------------------------------
# DB + MinIO
# ---------------------------------------------------------------------

def init_db():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    return conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def init_minio():
    client = Minio(**MINIO_CONFIG)
    if not client.bucket_exists(MINIO_BUCKET):
        client.make_bucket(MINIO_BUCKET)
    return client


def save_product(cur, p: dict) -> int:
    cur.execute("""
        INSERT INTO products (
            shop, product_url, title, price, description, characteristics
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (product_url) DO UPDATE SET
            price = EXCLUDED.price,
            description = EXCLUDED.description,
            characteristics = EXCLUDED.characteristics
        RETURNING id;
    """, (
        SHOP,
        p["url"],
        p["title"],
        p["price"],
        p["description"],
        json.dumps(p["characteristics"], ensure_ascii=False)
    ))
    return cur.fetchone()["id"]


def save_image(cur, product_id, image_url, storage_path):
    cur.execute("""
        INSERT INTO product_images (
            product_id, image_url, storage_path, is_main
        )
        VALUES (%s, %s, %s, true)
        ON CONFLICT DO NOTHING;
    """, (product_id, image_url, storage_path))


# ---------------------------------------------------------------------
# Extractors
# ---------------------------------------------------------------------

def extract_price(soup) -> Optional[int]:
    for s in soup.select("script[type='application/ld+json']"):
        try:
            d = json.loads(s.string)
            if isinstance(d, dict) and "offers" in d:
                return int(float(d["offers"]["price"]))
        except Exception:
            pass
    txt = soup.get_text(" ", strip=True)
    m = re.search(r"(\d[\d\s\u202f]+)\s*₽", txt)
    if m:
        return int(m.group(1).replace(" ", "").replace("\u202f", ""))
    return None


def extract_characteristics(soup) -> Dict[str, str]:
    data = {}
    for row in soup.select("div.grid.grid-cols-2"):
        cols = row.find_all("div", recursive=False)
        if len(cols) == 2:
            data[
                normalize_text(cols[0].get_text(strip=True))
            ] = normalize_text(cols[1].get_text(strip=True))
    return data


def extract_description(soup) -> Optional[str]:
    h = soup.find("h2", string=lambda s: s and "О товаре" in s)
    if not h:
        return None
    for d in h.find_all_next("div"):
        t = d.get_text(" ", strip=True)
        if t and len(t) > 120:
            return normalize_text(t)
    return None


def extract_image_url(soup) -> Optional[str]:
    img = soup.select_one("img[src]")
    return img["src"] if img else None


# ---------------------------------------------------------------------
# Product page
# ---------------------------------------------------------------------

def parse_product_page(driver, url: str) -> Dict:
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


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    driver = setup_driver()
    conn, cur = init_db()
    minio_client = init_minio()

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
            urljoin(BASE, a["href"])
            for a in soup.select("a.product-card[href]")
        ]

        print(f"     найдено: {len(links)}")
        all_links.update(links)
        sleep_rand(*PAUSE_CATALOG)

    print(f"\n🧮 Всего уникальных товаров: {len(all_links)}")

    for i, link in enumerate(all_links, 1):
        print(f"🔍 [{i}/{len(all_links)}] {link}")
        product = parse_product_page(driver, link)
        pid = save_product(cur, product)

        if product["image_url"]:
            tmp = download_temp_image(product["image_url"])
            obj = f"{SHOP}/products/{pid}/main.jpg"
            minio_client.fput_object(
                MINIO_BUCKET, obj, tmp, content_type="image/jpeg"
            )
            save_image(cur, pid, product["image_url"], f"{MINIO_BUCKET}/{obj}")
            os.remove(tmp)

        sleep_rand(*PAUSE_CARD)

    driver.quit()
    cur.close()
    conn.close()
    print("\n🎉 Парсинг завершён успешно")


if __name__ == "__main__":
    main()
