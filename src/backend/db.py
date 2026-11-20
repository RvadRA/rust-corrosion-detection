"""Подключение к базе данных PostgreSQL и сессии SQLAlchemy."""

import os
import time
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "Переменная окружения DATABASE_URL не задана. Задайте ее в .env файле."
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(max_retries: int = 15, delay: float = 2.0) -> None:
    """Создание таблиц БД, миграция колонок и backfill путей для старых записей."""
    from src.backend.models import Inspection  # noqa: F401

    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE inspections ADD COLUMN IF NOT EXISTS upload_path VARCHAR(512);"))
                conn.execute(text("ALTER TABLE inspections ADD COLUMN IF NOT EXISTS message VARCHAR(512);"))
                # Backfill для старых записей, у которых upload_path был NULL или пуст
                conn.execute(text(
                    "UPDATE inspections "
                    "SET upload_path = '/app/data/uploads/' || id || '_' || filename "
                    "WHERE upload_path IS NULL OR upload_path = '' OR upload_path NOT LIKE '%/%';"
                ))
                conn.commit()
            print("[Backend DB] Таблицы базы данных успешно инициализированы и обновлены (с backfill).", flush=True)
            return
        except Exception as e:
            if attempt == max_retries:
                print(f"[Backend DB] Не удалось инициализировать БД после {max_retries} попыток: {e}", flush=True)
                raise
            print(f"[Backend DB] Ожидание БД (попытка {attempt}/{max_retries})... Ошибка: {e}", flush=True)
            time.sleep(delay)
