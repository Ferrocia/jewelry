"""Главный файл для запуска парсера."""

import os

from src.selenium_utils import setup_driver
from src.storage import init_db, init_minio, save_product, save_image
from src.parser import parse_product_page, collect_product_links
from utils.helpers import download_temp_image, sleep_rand
from utils.validators import validate_product
from cleaners.data_cleaner import clean_product
from config.settings import SHOP_NAME, MINIO_BUCKET, PAUSE_CARD


def main():
    """Основная функция парсера."""
    driver = setup_driver()
    conn, cur = init_db()
    minio_client = init_minio()

    try:
        # Сбор ссылок на товары
        all_links = collect_product_links(driver)
        print(f"\n🧮 Всего уникальных товаров: {len(all_links)}")

        # Парсинг товаров
        for i, link in enumerate(all_links, 1):
            print(f"🔍 [{i}/{len(all_links)}] {link}")
            
            try:
                # Парсинг страницы товара
                product = parse_product_page(driver, link)
                
                # Очистка данных
                product = clean_product(product)
                
                # Валидация данных
                is_valid, errors = validate_product(product)
                if not is_valid:
                    print(f"   ⚠️  Пропущен из-за ошибок валидации: {', '.join(errors)}")
                    continue
                
                # Сохранение товара в БД
                pid = save_product(cur, product)
                
                # Сохранение изображения
                if product["image_url"]:
                    try:
                        tmp = download_temp_image(product["image_url"])
                        obj = f"{SHOP_NAME}/products/{pid}/main.jpg"
                        minio_client.fput_object(
                            MINIO_BUCKET, obj, tmp, content_type="image/jpeg"
                        )
                        save_image(cur, pid, product["image_url"], f"{MINIO_BUCKET}/{obj}")
                        os.remove(tmp)
                    except Exception as e:
                        print(f"   ⚠️  Ошибка при сохранении изображения: {e}")
                
                sleep_rand(*PAUSE_CARD)
                
            except Exception as e:
                print(f"   ❌ Ошибка при обработке товара: {e}")
                continue

        print("\n🎉 Парсинг завершён успешно")
        
    finally:
        driver.quit()
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()

