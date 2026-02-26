import os
import json
import requests
import psycopg2
from fastapi import FastAPI, HTTPException
from psycopg2.extras import Json

app = FastAPI()

# Получаем настройки из переменных окружения (Docker передаст их)
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "db") # "db" - это имя контейнера в docker-compose

def get_db_connection():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    return conn

@app.get("/")
def read_root():
    return {"status": "Backend is running", "message": "Go to /docs to see API"}

@app.post("/sync/anime")
def sync_anime_data():
    """
    Скачивает Топ-25 аниме с Jikan API и сохраняет в БД.
    """
    jikan_url = "https://api.jikan.moe/v4/top/anime"
    
    try:
        response = requests.get(jikan_url)
        data = response.json().get("data", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching from Jikan: {e}")

    conn = get_db_connection()
    cursor = conn.cursor()

    added_count = 0

    try:
        for item in data:
            # 1. Формируем данные
            title_name = item.get("title_english") or item.get("title") # Если нет английского, берем обычное
            description = item.get("synopsis")
            rating = item.get("score")
            year = item.get("year")
            
            # 2. Собираем JSONB (всё остальное, что не влезло в колонки)
            # Мы кладем туда количество эпизодов, студию, статус и картинку!
            metadata = {
                "episodes": item.get("episodes"),
                "status": item.get("status"),
                "duration": item.get("duration"),
                "image_url": item.get("images", {}).get("jpg", {}).get("image_url"),
                "studio": item.get("studios", [{}])[0].get("name") if item.get("studios") else None
            }

            # 3. SQL запрос (Upsert - вставляем, если нет ошибок)
            # Предполагаем, что type_id=1 это Аниме (как в твоем скрипте media_types)
            sql = """
                INSERT INTO titles (type_id, title_name, description, rating, metadata)
                VALUES (1, %s, %s, %s, %s)
            """
            
            # Json(metadata) сам превратит словарь Python в JSON для Postgres
            cursor.execute(sql, (title_name, description, rating, Json(metadata)))
            added_count += 1

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()

    return {"status": "success", "added": added_count}
