"""Unit-тесты калибровки площади и resize маски."""

import math

import numpy as np
import pytest

from src.ml.calibration import area_mm2_from_pixels, resize_mask_to_original


def test_resize_mask_scales_area_with_original_pixels():
    mask = np.zeros((4, 4), dtype=np.uint8)
    mask[1:3, 1:3] = 1

    resized = resize_mask_to_original(mask, (16, 16))

    assert resized.shape == (16, 16)
    assert resized.dtype == np.bool_
    assert int(resized.sum()) == 64


def test_resize_mask_is_binary_and_uses_nearest():
    mask = np.array([[0, 1], [1, 0]], dtype=np.uint8)

    resized = resize_mask_to_original(mask, (4, 4))

    assert set(np.unique(resized)).issubset({False, True})
    assert int(resized.sum()) == 8


@pytest.mark.parametrize("size", [(0, 10), (10, 0), (-1, 10)])
def test_resize_mask_rejects_invalid_size(size):
    with pytest.raises(ValueError):
        resize_mask_to_original(np.zeros((4, 4), dtype=np.uint8), size)


def test_resize_mask_rejects_non_2d():
    with pytest.raises(ValueError):
        resize_mask_to_original(np.zeros((4, 4, 3), dtype=np.uint8), (16, 16))


def test_area_mm2_uses_original_image_scale():
    area_mm2, calibrated = area_mm2_from_pixels(619904, 0.1)

    assert calibrated is True
    assert area_mm2 == 6199.04


def test_area_mm2_is_none_without_calibration():
    area_mm2, calibrated = area_mm2_from_pixels(1000, None)

    assert area_mm2 is None
    assert calibrated is False


@pytest.mark.parametrize("scale", [0, -0.1, math.nan, math.inf, "bad"])
def test_area_mm2_rejects_invalid_scale(scale):
    area_mm2, calibrated = area_mm2_from_pixels(1000, scale)

    assert area_mm2 is None
    assert calibrated is False


def test_area_mm2_rejects_negative_pixels():
    with pytest.raises(ValueError):
        area_mm2_from_pixels(-1, 0.1)
