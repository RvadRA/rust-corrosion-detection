"""Общие фикстуры для unit/API-тестов без PostgreSQL и реального ML."""

import io
import json
import os
from pathlib import Path
import sys
import tempfile

import pytest
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_DATA_DIR = Path(tempfile.mkdtemp(prefix="rust-corrosion-tests-"))
os.environ.setdefault("DATABASE_URL", f"sqlite:///{(TEST_DATA_DIR / 'test.db').as_posix()}")
os.environ.setdefault("DATA_DIR", str(TEST_DATA_DIR))
os.environ.setdefault("ML_SERVICE_URL", "http://ml.test:8001")
os.environ.setdefault("RETENTION_DAYS", "30")
os.environ.setdefault("MAX_UPLOAD_SIZE_MB", "32")
os.environ.setdefault("CORS_ORIGINS", "http://testserver")
os.environ.setdefault("MM_PER_PX", "")


def make_jpeg_bytes(width: int = 64, height: int = 48) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (120, 80, 40)).save(buffer, format="JPEG")
    return buffer.getvalue()


class FakeResponse:
    def __init__(self, status_code: int = 200, payload=None, text: str | None = None):
        self.status_code = status_code
        self._payload = payload
        self._text = text if text is not None else json.dumps(payload, ensure_ascii=False)

    def json(self):
        if self._payload is None:
            raise ValueError("JSON payload is not set")
        return self._payload

    @property
    def text(self) -> str:
        return self._text


class FakeAsyncClient:
    health_payload = {"status": "ok", "model_loaded": True, "device": "cpu"}
    health_exception = None
    inspect_payload = None
    inspect_exception = None
    last_post_data = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url):
        if self.health_exception is not None:
            raise self.health_exception
        return FakeResponse(payload=self.health_payload)

    async def post(self, url, **kwargs):
        type(self).last_post_data = kwargs.get("data")
        if self.inspect_exception is not None:
            raise self.inspect_exception
        return FakeResponse(payload=self.inspect_payload)


@pytest.fixture()
def fake_ml(monkeypatch):
    import src.backend.main as main

    FakeAsyncClient.health_payload = {"status": "ok", "model_loaded": True, "device": "cpu"}
    FakeAsyncClient.health_exception = None
    FakeAsyncClient.inspect_payload = None
    FakeAsyncClient.inspect_exception = None
    FakeAsyncClient.last_post_data = None
    monkeypatch.setattr(main.httpx, "AsyncClient", FakeAsyncClient)
    return FakeAsyncClient


@pytest.fixture()
def api(monkeypatch, tmp_path, fake_ml):
    from fastapi.testclient import TestClient
    from src.backend.db import Base
    import src.backend.main as main

    engine = create_engine(
        f"sqlite:///{(tmp_path / 'api.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    uploads = tmp_path / "uploads"
    masks = tmp_path / "masks"
    overlays = tmp_path / "overlays"
    for directory in (uploads, masks, overlays):
        directory.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(main, "init_db", lambda: None)
    monkeypatch.setattr(main, "SessionLocal", testing_session)
    monkeypatch.setattr(main, "UPLOADS_DIR", uploads)
    monkeypatch.setattr(main, "MASKS_DIR", masks)
    monkeypatch.setattr(main, "OVERLAYS_DIR", overlays)
    monkeypatch.setattr(main, "MM_PER_PX_ENV", None)
    main.app.dependency_overrides[main.get_db] = override_get_db

    with TestClient(main.app) as client:
        yield client, testing_session, main

    main.app.dependency_overrides.clear()
