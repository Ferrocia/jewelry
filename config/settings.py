"""Настройки парсера."""

BASE_URL = "https://www.585zolotoy.ru"
SHOP_NAME = "585zolotoy"

CATALOG_URLS = [
    # "https://www.585zolotoy.ru/catalog/sergi-kongo-s-kamnyami/",
    # "https://www.585zolotoy.ru/catalog/sergi-kongo-s-zhemchugom/",
    "https://www.585zolotoy.ru/catalog/sergi-kresty/",
    # "https://www.585zolotoy.ru/catalog/sergi-pusety-s-sapfirami/",
    # "https://www.585zolotoy.ru/catalog/sergi-s-kruglymi-kamnyami/",
    # "https://www.585zolotoy.ru/catalog/sergi-s-tantsuyushhimi-brilliantami/",
    # "https://www.585zolotoy.ru/catalog/sergi-s-tantsuyushhimi-kamnyami/",
    # "https://www.585zolotoy.ru/catalog/sergi-s-zheltymi-brilliantami/",
    # "https://www.585zolotoy.ru/catalog/sergi-tsepochki-iz-serebra/",
    # "https://www.585zolotoy.ru/catalog/sergi-zmeyi-iz-serebra/",
    # "https://www.585zolotoy.ru/catalog/sergi-zmeyi-iz-zolota/",
    # "https://www.585zolotoy.ru/catalog/sergi-zmeyi/",
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

