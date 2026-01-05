"""Работа с базой данных и MinIO."""

import json
import psycopg2
import psycopg2.extras
from minio import Minio
from typing import Tuple

from config.settings import DB_CONFIG, MINIO_CONFIG, MINIO_BUCKET, SHOP_NAME


def init_db() -> Tuple[psycopg2.extensions.connection, psycopg2.extras.RealDictCursor]:
    """Инициализация подключения к базе данных."""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    return conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def init_minio() -> Minio:
    """Инициализация клиента MinIO."""
    client = Minio(**MINIO_CONFIG)
    if not client.bucket_exists(MINIO_BUCKET):
        client.make_bucket(MINIO_BUCKET)
    return client


def save_product(cur: psycopg2.extras.RealDictCursor, p: dict) -> int:
    """Сохранение продукта в базу данных."""
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
        SHOP_NAME,
        p["url"],
        p["title"],
        p["price"],
        p["description"],
        json.dumps(p["characteristics"], ensure_ascii=False)
    ))
    return cur.fetchone()["id"]


def save_image(
    cur: psycopg2.extras.RealDictCursor,
    product_id: int,
    image_url: str,
    storage_path: str
) -> None:
    """Сохранение информации об изображении в базу данных."""
    cur.execute("""
        INSERT INTO product_images (
            product_id, image_url, storage_path, is_main
        )
        VALUES (%s, %s, %s, true)
        ON CONFLICT DO NOTHING;
    """, (product_id, image_url, storage_path))

