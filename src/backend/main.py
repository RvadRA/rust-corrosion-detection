"""FastAPI бэкенд системы контроля коррозии и ржавчины."""

import asyncio
from contextlib import asynccontextmanager
import csv
from datetime import datetime, timedelta, timezone
import io
import math
import os
from pathlib import Path
import re
import uuid

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
import httpx
from PIL import Image
from sqlalchemy import desc, text
from sqlalchemy.orm import Session

from src.backend.db import SessionLocal, get_db, init_db
from src.backend.models import Inspection
from src.backend.schemas import HealthResponse, InspectionListResponse, InspectionResponse

DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
UPLOADS_DIR = DATA_DIR / "uploads"
MASKS_DIR = DATA_DIR / "masks"
OVERLAYS_DIR = DATA_DIR / "overlays"

for d in (UPLOADS_DIR, MASKS_DIR, OVERLAYS_DIR):
    d.mkdir(parents=True, exist_ok=True)

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ml:8001").rstrip("/")
MM_PER_PX_ENV = os.getenv("MM_PER_PX")
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "30"))
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE_MB", "32")) * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}

_retention_task: asyncio.Task | None = None


def cleanup_old_inspections(db: Session, days: int = RETENTION_DAYS) -> int:
    """Удаление записей и связанных файлов старше заданного количества дней."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    old_records = db.query(Inspection).filter(Inspection.created_at < cutoff).all()
    deleted_count = 0

    for rec in old_records:
        for fpath_str in (rec.upload_path, rec.mask_path, rec.overlay_path):
            if fpath_str:
                p = Path(fpath_str)
                try:
                    if p.is_file():
                        p.unlink(missing_ok=True)
                except Exception as e:
                    print(f"[Cleanup] Ошибка удаления файла {p}: {e}", flush=True)

        db.delete(rec)
        deleted_count += 1

    if deleted_count > 0:
        db.commit()
        print(f"[Retention] Удалено {deleted_count} записей и файлов старше {days} дней.", flush=True)

    return deleted_count


async def periodic_retention_task():
    """Фоновая задача очистки архива раз в 12 часов."""
    try:
        while True:
            await asyncio.sleep(12 * 3600)
            try:
                with SessionLocal() as db:
                    cleanup_old_inspections(db, RETENTION_DAYS)
            except Exception as e:
                print(f"[Retention Error] Ошибка в periodic_retention_task: {e}", flush=True)
    except asyncio.CancelledError:
        print("[Retention] Фоновая задача ротации остановлена.", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _retention_task
    init_db()
    # Запуск очистки устаревших записей при старте
    try:
        with SessionLocal() as db:
            cleanup_old_inspections(db, RETENTION_DAYS)
    except Exception as e:
        print(f"[Startup Cleanup] Ошибка при очистке: {e}", flush=True)

    _retention_task = asyncio.create_task(periodic_retention_task())
    try:
        yield
    finally:
        if _retention_task and not _retention_task.done():
            _retention_task.cancel()
            try:
                await _retention_task
            except asyncio.CancelledError:
                pass


app = FastAPI(
    title="Rust & Corrosion Inspection System Backend",
    description="Backend API для автоматического контроля коррозии цилиндров (ПАО ЧКПЗ, КТ 4)",
    version="1.2.0",
    lifespan=lifespan,
)

# Корректная конфигурация CORS без wildcard при allow_credentials=True
raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [o.strip() for o in raw_cors.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Раздача медиафайлов
app.mount("/media", StaticFiles(directory=str(DATA_DIR)), name="media")


def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r"[^\w\.\-]", "_", Path(filename).name)
    return cleaned or "image.jpg"


def compute_verdict_and_message(area_px: int, area_mm2: float | None, calibrated: bool):
    if area_px < 0:
        return "ОШИБКА СИСТЕМЫ", "Некорректная площадь маски: отрицательное значение."

    if area_px == 0:
        if calibrated:
            return "НОРМА", "Коррозия не обнаружена."
        return (
            "НОРМА",
            "Коррозия не обнаружена. MM_PER_PX не задан; для нулевой площади вердикт не зависит "
            "от калибровки, но приёмочность проверки не подтверждена.",
        )

    if not calibrated:
        return (
            "ВНИМАНИЕ",
            "Внимание: масштаб не откалиброван (MM_PER_PX не задан). Площадь в мм² не рассчитана. "
            "Классификатор степени «лёгкая/глубокая» не реализован. Вердикт не является приёмочным, "
            "требуется калибровка.",
        )

    if area_mm2 is None or not math.isfinite(area_mm2) or area_mm2 < 0:
        return (
            "ОШИБКА СИСТЕМЫ",
            "Калибровка заявлена, но площадь в мм² не рассчитана или содержит некорректное значение.",
        )

    if area_mm2 <= 20.0:
        return (
            "ВНИМАНИЕ",
            f"Обнаружена ржавчина площадью {area_mm2:.2f} мм² (допустимый предел ≤ 20 мм²). "
            "Степень коррозии не классифицируется.",
        )
    else:
        return (
            "БРАК",
            f"Площадь поражения {area_mm2:.2f} мм² превышает допустимый предел 20 мм². "
            "Степень коррозии не классифицируется.",
        )


async def read_and_validate_upload(file: UploadFile, filename: str) -> bytes:
    """Потоковое чтение загружаемого файла с контролем лимита памяти и валидацией."""
    chunks = []
    total_size = 0
    chunk_size = 1024 * 1024  # 1 МБ

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_UPLOAD_SIZE:
            max_mb = MAX_UPLOAD_SIZE // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Размер файла превышает допустимый лимит {max_mb} МБ",
            )
        chunks.append(chunk)

    if total_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Передан пустой файл",
        )

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Неподдерживаемый формат файла: '{ext}'. Ожидается одно из: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    content = b"".join(chunks)

    try:
        with Image.open(io.BytesIO(content)) as img:
            img.verify()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл не является валидным изображением или повреждён",
        )

    return content


def model_to_response(item: Inspection) -> InspectionResponse:
    # Определение относительного пути для original_url с fallback для старых записей
    if item.upload_path:
        upload_rel = Path(item.upload_path).name
    else:
        upload_rel = f"{item.id}_{item.filename}"

    mask_rel = Path(item.mask_path).name
    overlay_rel = Path(item.overlay_path).name

    return InspectionResponse(
        id=item.id,
        created_at=item.created_at,
        filename=item.filename,
        verdict=item.verdict,
        area_px=item.area_px,
        area_mm2=item.area_mm2,
        confidence=item.confidence,
        calibrated=item.calibrated,
        original_url=f"/media/uploads/{upload_rel}",
        mask_url=f"/media/masks/{mask_rel}",
        overlay_url=f"/media/overlays/{overlay_rel}",
        message=item.message,
    )


@app.get("/health", response_model=HealthResponse)
async def health_endpoint(db: Session = Depends(get_db)):
    db_status = "error"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    ml_status = "error"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{ML_SERVICE_URL}/health")
            if resp.status_code == 200 and resp.json().get("status") == "ok":
                ml_status = "ready"
            else:
                ml_status = f"unhealthy ({resp.status_code})"
    except Exception as e:
        ml_status = f"unavailable: {str(e)}"

    overall_status = "ok" if (db_status == "connected" and ml_status == "ready") else "degraded"

    return HealthResponse(
        status=overall_status,
        db=db_status,
        ml=ml_status,
        retention_days=RETENTION_DAYS,
        timestamp=datetime.now(timezone.utc),
    )


@app.post("/api/v1/inspect", response_model=InspectionResponse)
async def inspect_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    safe_name = sanitize_filename(file.filename or "image.jpg")

    # 1. Потоковое чтение с защитой от переполнения памяти и валидация
    content = await read_and_validate_upload(file, safe_name)

    inspection_id = str(uuid.uuid4())
    upload_file_path = UPLOADS_DIR / f"{inspection_id}_{safe_name}"

    try:
        with open(upload_file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Не удалось сохранить загруженный файл: {e}")

    # 2. Асинхронный вызов ML-сервиса через httpx без блокировки event loop
    data_payload = {"inspection_id": inspection_id}
    if MM_PER_PX_ENV:
        try:
            data_payload["mm_per_px"] = str(float(MM_PER_PX_ENV))
        except ValueError:
            pass

    files_payload = {
        "file": (safe_name, content, file.content_type or "image/jpeg"),
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{ML_SERVICE_URL}/inspect",
                files=files_payload,
                data=data_payload,
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML-сервис сегментации U-Net недоступен: {str(e)}",
        )

    if resp.status_code != 200:
        err_msg = resp.text
        try:
            err_msg = resp.json().get("detail", err_msg)
        except Exception:
            pass
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Ошибка инференса ML-сервиса: {err_msg}",
        )

    ml_res = resp.json()
    area_px = int(ml_res["area_px"])
    area_mm2 = ml_res.get("area_mm2")
    confidence = float(ml_res["confidence"])
    calibrated = bool(ml_res["calibrated"])
    verdict, message = compute_verdict_and_message(area_px, area_mm2, calibrated)

    mask_path = ml_res["mask_png_path"]
    overlay_path = ml_res["overlay_png_path"]

    # 3. Запись в PostgreSQL с сохранением исходного upload_path и message
    record = Inspection(
        id=inspection_id,
        filename=safe_name,
        verdict=verdict,
        area_px=area_px,
        area_mm2=area_mm2,
        confidence=confidence,
        calibrated=calibrated,
        upload_path=str(upload_file_path),
        mask_path=str(mask_path),
        overlay_path=str(overlay_path),
        message=message,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return model_to_response(record)


@app.get("/api/v1/results", response_model=InspectionListResponse)
def get_results_endpoint(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * limit
    total = db.query(Inspection).count()
    items = (
        db.query(Inspection)
        .order_by(desc(Inspection.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    return InspectionListResponse(
        items=[model_to_response(it) for it in items],
        total=total,
        page=page,
        limit=limit,
    )


@app.get("/api/v1/results.csv")
def get_results_csv_endpoint(db: Session = Depends(get_db)):
    items = db.query(Inspection).order_by(desc(Inspection.created_at)).all()

    output = io.StringIO()
    # UTF-8 BOM для корректного открытия в Excel на русском языке
    output.write("\ufeff")

    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        "id",
        "created_at",
        "filename",
        "verdict",
        "area_px",
        "area_mm2",
        "confidence",
        "calibrated",
    ])

    for it in items:
        writer.writerow([
            it.id,
            it.created_at.isoformat() if it.created_at else "",
            it.filename,
            it.verdict,
            it.area_px,
            f"{it.area_mm2:.2f}" if it.area_mm2 is not None else "",
            f"{it.confidence:.4f}",
            "true" if it.calibrated else "false",
        ])

    csv_data = output.getvalue().encode("utf-8")
    return Response(
        content=csv_data,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="results.csv"',
        },
    )


@app.get("/api/v1/results/{inspection_id}", response_model=InspectionResponse)
def get_result_by_id_endpoint(inspection_id: str, db: Session = Depends(get_db)):
    record = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Запись проверки не найдена")
    return model_to_response(record)
