import psycopg2
from minio import Minio


# -------- CONFIG --------

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

BUCKET = "jewelry-images"


def main():
    print("🧨 ПОЛНЫЙ RESET данных")

    # ---------- PostgreSQL ----------
    print("🗑 Очистка PostgreSQL...")

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("""
        TRUNCATE product_images, products
        RESTART IDENTITY CASCADE;
    """)

    cur.close()
    conn.close()
    print("✅ PostgreSQL очищен")

    # ---------- MinIO ----------
    print("🗑 Очистка MinIO...")

    client = Minio(**MINIO_CONFIG)

    if not client.bucket_exists(BUCKET):
        print("ℹ️ Bucket не существует, пропускаем")
        return

    objects = client.list_objects(BUCKET, recursive=True)

    deleted = False
    for obj in objects:
        client.remove_object(BUCKET, obj.object_name)
        deleted = True

    if deleted:
        print("✅ Все объекты в MinIO удалены")
    else:
        print("ℹ️ MinIO уже пуст")


if __name__ == "__main__":
    main()
