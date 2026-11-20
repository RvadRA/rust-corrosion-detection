"""M1/M2: пороговые сегментаторы HSV и Lab."""

import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

from common import ROOT, hsv_mask, image_metrics, lab_mask, load_manifest, load_pair, summarize

OUT = ROOT / "docs" / "kt3" / "results"
SIZE = 256


def collect(split):
    manifest = load_manifest()
    records = [r for r in manifest["records"] if r["split"] == split]
    images, masks = [], []
    for rec in records:
        img, mask = load_pair(rec, SIZE)
        images.append(img)
        masks.append(mask)
    return records, images, masks


def evaluate(images, masks, fn):
    tp = fp = fn_ = 0
    rows = []
    for img, gt in zip(images, masks):
        pred = fn(img)
        m = image_metrics(pred, gt)
        tp += int(np.logical_and(pred, gt).sum())
        fp += int(np.logical_and(pred, ~gt).sum())
        fn_ += int(np.logical_and(~pred, gt).sum())
        rows.append(m)
    denom = 2 * tp + fp + fn_
    return {
        "f1": 2 * tp / denom if denom else 1.0,
        "precision": tp / (tp + fp) if (tp + fp) else 0.0,
        "recall": tp / (tp + fn_) if (tp + fn_) else 0.0,
        "mean_dice": float(np.mean([r["dice"] for r in rows])),
        "rows": rows,
    }


def tune_hsv(images, masks):
    best = None
    for s_min, v_min, v_max, hue_max, hue_wrap in itertools.product(
        (0.2, 0.3, 0.4, 0.5), (0.0, 0.15, 0.3), (0.7, 0.85, 1.0), (0.10, 0.13, 0.16), (0.0, 0.92, 0.95)
    ):
        res = evaluate(images, masks, lambda im, a=s_min, b=v_min, c=v_max, d=hue_max, e=hue_wrap:
                       hsv_mask(im, a, b, c, d, e))
        key = (res["f1"], res["mean_dice"])
        if best is None or key > best[0]:
            best = (key, (s_min, v_min, v_max, hue_max, hue_wrap), res)
    return best


def tune_lab(images, masks):
    best = None
    for a_min, b_min, l_max in itertools.product((0, 5, 10, 15, 20), (0, 5, 10, 15, 20, 25), (70, 85, 100)):
        res = evaluate(images, masks, lambda im, a=a_min, b=b_min, c=l_max: lab_mask(im, a, b, c))
        key = (res["f1"], res["mean_dice"])
        if best is None or key > best[0]:
            best = (key, (a_min, b_min, l_max), res)
    return best


def test_with(records, images, masks, fn):
    rows = []
    for rec, img, gt in zip(records, images, masks):
        pred = fn(img)
        m = image_metrics(pred, gt)
        m.update({
            "id": rec["id"], "name": rec["name"], "source": rec["source"],
            "tp": int(np.logical_and(pred, gt).sum()),
            "fp": int(np.logical_and(pred, ~gt).sum()),
            "fn": int(np.logical_and(~pred, gt).sum()),
        })
        rows.append(m)
    return rows


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    val_records, val_images, val_masks = collect("val")
    test_records, test_images, test_masks = collect("test")
    results = {"size": SIZE, "val_n": len(val_records), "test_n": len(test_records), "methods": {}}

    t0 = time.perf_counter()
    best_hsv = tune_hsv(val_images, val_masks)
    _, hsv_params, hsv_val = best_hsv
    hsv_fn = lambda im: hsv_mask(im, *hsv_params)
    hsv_test = test_with(test_records, test_images, test_masks, hsv_fn)
    results["methods"]["M1 HSV-порог"] = {
        "params": {"s_min": hsv_params[0], "v_min": hsv_params[1], "v_max": hsv_params[2],
                   "hue_max": hsv_params[3], "hue_wrap": hsv_params[4]},
        "val": {k: round(v, 4) for k, v in hsv_val.items() if k != "rows"},
        "test": summarize(hsv_test),
        "rows": hsv_test,
    }
    print("HSV", hsv_params, results["methods"]["M1 HSV-порог"]["test"]["all"])

    best_lab = tune_lab(val_images, val_masks)
    _, lab_params, lab_val = best_lab
    lab_fn = lambda im: lab_mask(im, *lab_params)
    lab_test = test_with(test_records, test_images, test_masks, lab_fn)
    results["methods"]["M2 Lab-порог"] = {
        "params": {"a_min": lab_params[0], "b_min": lab_params[1], "l_max": lab_params[2]},
        "val": {k: round(v, 4) for k, v in lab_val.items() if k != "rows"},
        "test": summarize(lab_test),
        "rows": lab_test,
    }
    print("Lab", lab_params, results["methods"]["M2 Lab-порог"]["test"]["all"])

    results["tuning_seconds"] = round(time.perf_counter() - t0, 2)
    (OUT / "thresholds.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", OUT / "thresholds.json")


if __name__ == "__main__":
    main()
