"""Калибровка площади маски по масштабу исходного изображения."""

import math
from typing import Optional, Tuple

import numpy as np
from PIL import Image


def resize_mask_to_original(
    mask: np.ndarray,
    original_size: Tuple[int, int],
) -> np.ndarray:
    """Возвращает бинарную маску в размере исходного изображения.

    ``original_size`` задаётся в формате Pillow ``(width, height)``.
    Используется nearest resize, чтобы не размывать границы маски.
    """
    width, height = original_size
    if width <= 0 or height <= 0:
        raise ValueError("Размер исходного изображения должен быть положительным")

    arr = np.asarray(mask)
    if arr.ndim != 2:
        raise ValueError("Маска должна быть двумерным массивом")

    binary = (arr > 0).astype(np.uint8) * 255
    resized = Image.fromarray(binary).resize((width, height), Image.Resampling.NEAREST)
    return np.asarray(resized) > 0


def area_mm2_from_pixels(
    area_px: int,
    mm_per_px: Optional[float],
) -> Tuple[Optional[float], bool]:
    """Пересчитывает площадь в пикселях исходника в мм².

    ``mm_per_px`` — масштаб исходного изображения (мм на пиксель), а не
    уменьшенного входа U-Net 256×256. Возвращает ``(площадь, calibrated)``.
    """
    if area_px < 0:
        raise ValueError("Площадь в пикселях не может быть отрицательной")

    if mm_per_px is None:
        return None, False

    try:
        scale = float(mm_per_px)
    except (TypeError, ValueError):
        return None, False

    if not math.isfinite(scale) or scale <= 0:
        return None, False

    return round(float(area_px) * scale * scale, 2), True
