"""API-тесты backend на SQLite и замоканном ML-сервисе."""

from src.backend.models import Inspection

from .conftest import make_jpeg_bytes


def _payload(area_px=1000, area_mm2=None, calibrated=False, confidence=0.75):
    return {
        "area_px": area_px,
        "area_mm2": area_mm2,
        "confidence": confidence,
        "calibrated": calibrated,
        "mask_png_path": "/tmp/mask.png",
        "overlay_png_path": "/tmp/overlay.png",
    }


def _inspect(client, data=None):
    if data is None:
        data = make_jpeg_bytes()
    return client.post(
        "/api/v1/inspect",
        files={"file": ("part.jpg", data, "image/jpeg")},
    )


def test_health_ok(api):
    client, _, _ = api
    import src.backend.main as main

    # fake_ml already returns status=ok by default
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] == "connected"
    assert body["ml"] == "ready"
    assert body["retention_days"] == main.RETENTION_DAYS


def test_health_degraded_when_ml_unavailable(api, fake_ml):
    client, _, _ = api
    fake_ml.health_exception = RuntimeError("ml down")

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["db"] == "connected"
    assert body["ml"].startswith("unavailable:")


def test_inspect_without_calibration_returns_warning(api, fake_ml):
    client, _, _ = api
    fake_ml.inspect_payload = _payload(area_px=1000, area_mm2=None, calibrated=False)

    response = _inspect(client)

    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "ВНИМАНИЕ"
    assert body["area_px"] == 1000
    assert body["area_mm2"] is None
    assert body["calibrated"] is False
    assert "MM_PER_PX" in body["message"]
    assert "не является приёмочным" in body["message"]
    assert body["original_url"].endswith("_part.jpg")
    assert "mm_per_px" not in fake_ml.last_post_data


def test_inspect_with_zero_calibration_is_uncalibrated(api, fake_ml, monkeypatch):
    client, _, main = api
    monkeypatch.setattr(main, "MM_PER_PX_ENV", "0")
    fake_ml.inspect_payload = _payload(area_px=1000, area_mm2=None, calibrated=False)

    response = _inspect(client)

    assert response.status_code == 200
    body = response.json()
    assert fake_ml.last_post_data["mm_per_px"] == "0.0"
    assert body["area_mm2"] is None
    assert body["calibrated"] is False
    assert body["verdict"] == "ВНИМАНИЕ"
    assert "требуется калибровка" in body["message"]


def test_inspect_with_calibration_and_large_area_is_reject(api, fake_ml, monkeypatch):
    client, _, main = api
    monkeypatch.setattr(main, "MM_PER_PX_ENV", "0.1")
    fake_ml.inspect_payload = _payload(
        area_px=619904,
        area_mm2=6199.04,
        calibrated=True,
        confidence=0.7307,
    )

    response = _inspect(client)

    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "БРАК"
    assert body["area_mm2"] == 6199.04
    assert body["calibrated"] is True
    assert "не классифицируется" in body["message"]


def test_inspect_ml_error_returns_503(api, fake_ml):
    client, _, _ = api
    fake_ml.inspect_exception = RuntimeError("connection refused")

    response = _inspect(client)

    assert response.status_code == 503
    assert "ML-сервис" in response.json()["detail"]


def test_inspect_rejects_unsupported_extension(api):
    client, _, _ = api

    response = client.post(
        "/api/v1/inspect",
        files={"file": ("README.md", b"# not an image", "text/markdown")},
    )

    assert response.status_code == 415


def test_inspect_rejects_corrupt_image(api):
    client, _, _ = api

    response = _inspect(client, b"not a real jpeg")

    assert response.status_code == 400
    assert "поврежд" in response.json()["detail"]


def test_inspect_rejects_empty_file(api):
    client, _, _ = api

    response = _inspect(client, b"")

    assert response.status_code == 400
    assert "пустой" in response.json()["detail"]


def test_inspect_rejects_oversized_file(api, monkeypatch):
    client, _, main = api
    monkeypatch.setattr(main, "MAX_UPLOAD_SIZE", 8)

    response = _inspect(client, b"0123456789")

    assert response.status_code == 413


def test_results_and_single_result(api, fake_ml):
    client, _, _ = api
    fake_ml.inspect_payload = _payload(area_px=1000, area_mm2=None, calibrated=False)
    created = _inspect(client).json()

    listed = client.get("/api/v1/results")
    single = client.get(f"/api/v1/results/{created['id']}")

    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == created["id"]
    assert single.status_code == 200
    assert single.json()["id"] == created["id"]


def test_result_not_found(api):
    client, _, _ = api

    response = client.get("/api/v1/results/missing")

    assert response.status_code == 404


def test_results_pagination(api):
    client, session_factory, _ = api
    with session_factory() as session:
        for index in range(3):
            session.add(
                Inspection(
                    id=f"item-{index}",
                    filename=f"part-{index}.jpg",
                    verdict="НОРМА",
                    area_px=0,
                    area_mm2=None,
                    confidence=0.0,
                    calibrated=False,
                    upload_path=f"/tmp/upload-{index}.jpg",
                    mask_path=f"/tmp/mask-{index}.png",
                    overlay_path=f"/tmp/overlay-{index}.png",
                    message="Коррозия не обнаружена.",
                )
            )
        session.commit()

    response = client.get("/api/v1/results?page=1&limit=2")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["limit"] == 2
    assert len(body["items"]) == 2


def test_csv_has_bom_semicolon_and_real_row(api):
    client, session_factory, _ = api
    with session_factory() as session:
        session.add(
            Inspection(
                id="csv-id",
                filename="csv-part.jpg",
                verdict="БРАК",
                area_px=1000,
                area_mm2=10.0,
                confidence=0.75,
                calibrated=True,
                upload_path="/tmp/upload.jpg",
                mask_path="/tmp/mask.png",
                overlay_path="/tmp/overlay.png",
                message="Тестовая запись",
            )
        )
        session.commit()

    response = client.get("/api/v1/results.csv")

    assert response.status_code == 200
    assert response.content.startswith(b"\xef\xbb\xbf")
    text = response.content.decode("utf-8-sig")
    assert "id;created_at;filename;verdict;area_px;area_mm2;confidence;calibrated" in text
    assert "csv-id;" in text
    assert "csv-part.jpg;БРАК;1000;10.00;0.7500;true" in text
