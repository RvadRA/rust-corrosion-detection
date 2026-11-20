"""Unit-тесты потоковой валидации загружаемых изображений."""

import asyncio
import io

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from src.backend.main import read_and_validate_upload

from .conftest import make_jpeg_bytes


def _upload(data: bytes, filename: str) -> UploadFile:
    return UploadFile(file=io.BytesIO(data), filename=filename)


def test_accepts_valid_jpeg():
    data = make_jpeg_bytes()

    result = asyncio.run(read_and_validate_upload(_upload(data, "part.jpg"), "part.jpg"))

    assert result == data


def test_rejects_unsupported_extension():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            read_and_validate_upload(
                _upload(b"# not an image", "README.md"),
                "README.md",
            )
        )

    assert exc.value.status_code == 415


def test_rejects_corrupt_image():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(read_and_validate_upload(_upload(b"broken", "part.jpg"), "part.jpg"))

    assert exc.value.status_code == 400


def test_rejects_empty_file():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(read_and_validate_upload(_upload(b"", "part.jpg"), "part.jpg"))

    assert exc.value.status_code == 400


def test_rejects_oversized_file(monkeypatch):
    import src.backend.main as main

    monkeypatch.setattr(main, "MAX_UPLOAD_SIZE", 8)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            read_and_validate_upload(
                _upload(b"0123456789", "part.jpg"),
                "part.jpg",
            )
        )

    assert exc.value.status_code == 413
