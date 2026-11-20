"""Общие функции KT3: данные, цветовые пространства и метрики."""

import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "docs" / "kt3" / "results" / "manifest.json"


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def load_pair(record, size=256):
    image = Image.open(ROOT / record["image"]).convert("RGB").resize((size, size), Image.BILINEAR)
    mask = Image.open(ROOT / record["mask"]).convert("L").resize((size, size), Image.NEAREST)
    return np.asarray(image, dtype=np.uint8), np.asarray(mask) > 0


def rgb_to_hsv(rgb):
    x = rgb.astype(np.float32) / 255.0
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    maxc = x.max(axis=2)
    minc = x.min(axis=2)
    delta = maxc - minc
    h = np.zeros_like(maxc)
    mask = delta > 1e-6
    rmask = mask & (maxc == r)
    gmask = mask & (maxc == g)
    bmask = mask & (maxc == b)
    h[rmask] = ((g[rmask] - b[rmask]) / delta[rmask]) % 6
    h[gmask] = (b[gmask] - r[gmask]) / delta[gmask] + 2
    h[bmask] = (r[bmask] - g[bmask]) / delta[bmask] + 4
    h = h / 6.0
    s = np.where(maxc > 1e-6, delta / np.maximum(maxc, 1e-6), 0)
    return h.astype(np.float32), s.astype(np.float32), maxc.astype(np.float32)


def rgb_to_lab(rgb):
    x = rgb.astype(np.float32) / 255.0
    x = np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    X = (r * 0.4124564 + g * 0.3575761 + b * 0.1804375) / 0.95047
    Y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    Z = (r * 0.0193339 + g * 0.1191920 + b * 0.9503041) / 1.08883

    def f(t):
        return np.where(t > 0.008856, np.cbrt(t), 7.787 * t + 16.0 / 116.0)

    fx, fy, fz = f(X), f(Y), f(Z)
    return np.stack([116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)], axis=2).astype(np.float32)


def hsv_mask(rgb, s_min, v_min, v_max, hue_max=0.13, hue_wrap=0.0):
    h, s, v = rgb_to_hsv(rgb)
    hue = (h <= hue_max)
    if hue_wrap > 0:
        hue |= (h >= hue_wrap)
    return hue & (s >= s_min) & (v >= v_min) & (v <= v_max)


def lab_mask(rgb, a_min, b_min, l_max=100.0):
    _, a, b = np.moveaxis(rgb_to_lab(rgb), 2, 0)
    return (a >= a_min) & (b >= b_min) & (rgb_to_lab(rgb)[..., 0] <= l_max)


def image_metrics(pred, gt):
    pred = pred.astype(bool)
    gt = gt.astype(bool)
    tp = np.logical_and(pred, gt).sum(dtype=np.int64)
    fp = np.logical_and(pred, ~gt).sum(dtype=np.int64)
    fn = np.logical_and(~pred, gt).sum(dtype=np.int64)
    union = tp + fp + fn
    denom = 2 * tp + fp + fn
    precision = tp / (tp + fp) if (tp + fp) else (1.0 if not gt.any() else 0.0)
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    dice = 2 * tp / denom if denom else 1.0
    iou = tp / union if union else 1.0
    return {
        "precision": float(precision),
        "recall": float(recall),
        "dice": float(dice),
        "iou": float(iou),
        "gt_pixels": int(gt.sum()),
        "pred_pixels": int(pred.sum()),
        "area_rel_error": float(abs(pred.sum() - gt.sum()) / max(int(gt.sum()), 1)),
    }


def summarize(rows):
    out = {}
    for source in ("all", "ostrava", "vt", "pipelines"):
        subset = rows if source == "all" else [r for r in rows if r["source"] == source]
        if not subset:
            continue
        tp = sum(r["tp"] for r in subset)
        fp = sum(r["fp"] for r in subset)
        fn = sum(r["fn"] for r in subset)
        denom = 2 * tp + fp + fn
        out[source] = {
            "n": len(subset),
            "precision_micro": round(tp / (tp + fp), 4) if (tp + fp) else 0.0,
            "recall_micro": round(tp / (tp + fn), 4) if (tp + fn) else 0.0,
            "f1_micro": round(2 * tp / denom, 4) if denom else 1.0,
            "dice_micro": round(2 * tp / denom, 4) if denom else 1.0,
            "iou_micro": round(tp / (tp + fp + fn), 4) if (tp + fp + fn) else 1.0,
            "dice_macro": round(float(np.mean([r["dice"] for r in subset])), 4),
            "iou_macro": round(float(np.mean([r["iou"] for r in subset])), 4),
            "area_rel_error_macro": round(float(np.mean([r["area_rel_error"] for r in subset])), 4),
        }
    return out


def score_rows(preds, records, source=None):
    rows = []
    for pred, rec in zip(preds, records):
        if source and rec["source"] != source:
            continue
        gt = np.asarray(Image.open(ROOT / rec["mask"]).convert("L")) > 0
        if pred.shape != gt.shape:
            pred = np.asarray(Image.fromarray(pred.astype(np.uint8) * 255).resize(
                (gt.shape[1], gt.shape[0]), Image.NEAREST)) > 0
        m = image_metrics(pred, gt)
        m["source"] = rec["source"]
        m["tp"] = int(np.logical_and(pred, gt).sum())
        m["fp"] = int(np.logical_and(pred, ~gt).sum())
        m["fn"] = int(np.logical_and(~pred, gt).sum())
        m["name"] = rec["name"]
        m["id"] = rec["id"]
        rows.append(m)
    return rows
