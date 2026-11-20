"""Микросервис ML-инференса для системы обнаружения ржавчины и коррозии."""

import io
import os
from pathlib import Path
import tempfile
import uuid
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

from src.ml.inference import get_detector, inspect_image

app = FastAPI(
    title="Rust & Corrosion Detection ML Service",
    description="U-Net inference service for rust defect inspection",
    version="1.2.0",
)

DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
MASKS_DIR = DATA_DIR / "masks"
OVERLAYS_DIR = DATA_DIR / "overlays"

for d in (MASKS_DIR, OVERLAYS_DIR):
    d.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
def startup_event():
    try:
        detector = get_detector()
        print(f"[ML Service] Модель U-Net успешно загружена на устройстве: {detector.device}", flush=True)
    except Exception as e:
        print(f"[ML Service] Ошибка загрузки модели при старте: {e}", flush=True)


@app.get("/health")
def health_check():
    try:
        detector = get_detector()
        return {
            "status": "ok",
            "model_loaded": detector.model is not None,
            "device": str(detector.device),
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": f"ML model not ready: {str(e)}"},
        )


@app.post("/inspect")
async def inspect_endpoint(
    file: UploadFile = File(...),
    inspection_id: Optional[str] = Form(None),
    mm_per_px: Optional[float] = Form(None),
):
    """Строго multipart-эндпоинт инференса.

    Исходник обрабатывается через временный файл и сразу удаляется после инференса.
    ML не создает постоянных дубликатов файлов в uploads/.
    Маска и overlay сохраняются с ID инспекции.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Имя файла не указано")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Передан пустой файл")

    try:
        with Image.open(io.BytesIO(content)) as img:
            img.verify()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Переданный файл повреждён или не является допустимым изображением",
        )

    file_id = inspection_id or str(uuid.uuid4())
    ext = Path(file.filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"]:
        ext = ".jpg"

    mask_path = MASKS_DIR / f"{file_id}.png"
    overlay_path = OVERLAYS_DIR / f"{file_id}.png"

    # Обработка через временный файл с гарантированным удалением
    tmp_fd, tmp_path_str = tempfile.mkstemp(suffix=ext, prefix="ml_input_")
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(tmp_fd, "wb") as f:
            f.write(content)

        res = inspect_image(
            image_path=tmp_path,
            output_mask_path=mask_path,
            output_overlay_path=overlay_path,
            mm_per_px=mm_per_px,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка инференса U-Net: {str(e)}")
    finally:
        # Удаляем временный файл исходника сразу после инференса
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception as e:
            print(f"[ML Service] Ошибка удаления временного файла {tmp_path}: {e}", flush=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.ml.service:app", host="0.0.0.0", port=8001)
