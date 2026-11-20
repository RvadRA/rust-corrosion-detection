"""Unit-тесты бизнес-логики вердиктов."""

import pytest

from src.backend.main import compute_verdict_and_message


def test_no_rust_is_norm():
    verdict, message = compute_verdict_and_message(0, None, False)
    assert verdict == "НОРМА"
    assert "Коррозия не обнаружена" in message
    assert "приёмочность" in message


def test_calibrated_zero_area_is_norm_without_warning():
    verdict, message = compute_verdict_and_message(0, None, True)
    assert verdict == "НОРМА"
    assert message == "Коррозия не обнаружена."


def test_uncalibrated_nonzero_area_is_attention_with_warning():
    verdict, message = compute_verdict_and_message(1000, None, False)
    assert verdict == "ВНИМАНИЕ"
    assert "MM_PER_PX" in message
    assert "не является приёмочным" in message
    assert "«лёгкая/глубокая»" in message


@pytest.mark.parametrize("area_mm2", [0.01, 10.0, 20.0])
def test_calibrated_area_up_to_limit_is_attention(area_mm2):
    verdict, message = compute_verdict_and_message(1000, area_mm2, True)
    assert verdict == "ВНИМАНИЕ"
    assert "20" in message
    assert "Степень коррозии не классифицируется" in message


@pytest.mark.parametrize("area_mm2", [20.01, 100.0, 6199.04])
def test_calibrated_area_above_limit_is_reject(area_mm2):
    verdict, message = compute_verdict_and_message(1000, area_mm2, True)
    assert verdict == "БРАК"
    assert "20" in message
    assert "Степень коррозии не классифицируется" in message


def test_negative_area_is_system_error():
    verdict, _ = compute_verdict_and_message(-1, None, False)
    assert verdict == "ОШИБКА СИСТЕМЫ"


@pytest.mark.parametrize("area_mm2", [None, float("nan"), float("inf"), -1.0])
def test_invalid_area_with_calibration_is_system_error(area_mm2):
    verdict, _ = compute_verdict_and_message(1000, area_mm2, True)
    assert verdict == "ОШИБКА СИСТЕМЫ"
