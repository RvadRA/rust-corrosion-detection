"""Spot-level метрики: компоненты, IoU >= 0.5, площадь >= 24 px."""

import json
import sys

import joblib
import numpy as np
import torch
from scipy import ndimage

from common import ROOT, hsv_mask, lab_mask, load_manifest, load_pair
from run_rf import features, postprocess
from run_unet import UNet, evaluate, PairDataset

OUT = ROOT / "docs" / "kt3" / "results"
SIZE = 256
MIN_AREA = 24


def components(mask, min_area=MIN_AREA):
    lab, n = ndimage.label(mask)
    out = []
    for i in range(1, n + 1):
        m = lab == i
        area = int(m.sum())
        if area >= min_area:
            out.append((m, area))
    return out


def match(gt_mask, pred_mask):
    gt = components(gt_mask)
    pr = components(pred_mask)
    used = set()
    hits = 0
    errors = []
    for gm, ga in gt:
        best = None
        for j, (pm, pa) in enumerate(pr):
            if j in used:
                continue
            inter = int(np.logical_and(gm, pm).sum())
            if inter == 0:
                continue
            iou = inter / (ga + pa - inter)
            if best is None or iou > best[0]:
                best = (iou, j, pa)
        if best is not None and best[0] >= 0.5:
            hits += 1
            used.add(best[1])
            errors.append(abs(best[2] - ga) / ga)
    return {
        "gt": len(gt),
        "pred": len(pr),
        "tp": hits,
        "fp": len(pr) - len(used),
        "fn": len(gt) - hits,
        "area_mae": float(np.mean(errors)) if errors else None,
    }


def aggregate(preds, gts):
    tp = fp = fn = 0
    errors = []
    for p, g in zip(preds, gts):
        m = match(g, p)
        tp += m["tp"]
        fp += m["fp"]
        fn += m["fn"]
        if m["area_mae"] is not None:
            errors.append(m["area_mae"])
    return {
        "gt": tp + fn,
        "pred": tp + fp,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "recall": round(tp / (tp + fn), 4) if (tp + fn) else 1.0,
        "precision": round(tp / (tp + fp), 4) if (tp + fp) else 1.0,
        "f1": round(2 * tp / (2 * tp + fp + fn), 4) if (2 * tp + fp + fn) else 1.0,
        "area_mae": round(float(np.mean(errors)), 4) if errors else None,
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    manifest = load_manifest()
    test = [r for r in manifest["records"] if r["split"] == "test"]
    images = [load_pair(r, SIZE)[0] for r in test]
    gts = [load_pair(r, SIZE)[1] for r in test]
    thr = json.loads((OUT / "thresholds.json").read_text(encoding="utf-8"))

    p = thr["methods"]["M1 HSV-порог"]["params"]
    hsv = [hsv_mask(im, p["s_min"], p["v_min"], p["v_max"], p["hue_max"], p["hue_wrap"]) for im in images]
    p = thr["methods"]["M2 Lab-порог"]["params"]
    lab = [lab_mask(im, p["a_min"], p["b_min"], p["l_max"]) for im in images]

    rf = joblib.load(ROOT / "dataset" / "processed" / "kt3" / "rf.joblib")
    params = json.loads((OUT / "rf.json").read_text(encoding="utf-8"))["params"]
    rf_pred = []
    for im in images:
        f = features(im)
        prob = rf.predict_proba(f.reshape(-1, f.shape[2]))[:, 1].reshape(im.shape[:2])
        rf_pred.append(postprocess(prob, params["threshold"], params["morphology"]))

    ckpt = torch.load(ROOT / "dataset" / "processed" / "kt3" / "unet.pt", map_location="cpu", weights_only=False)
    unet = UNet(channels=ckpt["channels"], bottleneck=ckpt["bottleneck"])
    unet.load_state_dict(ckpt["state_dict"])
    params = json.loads((OUT / "unet.json").read_text(encoding="utf-8"))["params"]
    probs = evaluate(unet, PairDataset(test))
    unet_pred = [postprocess(p, params["threshold"], params["morphology"]) for p in probs]

    out = {
        "min_area_px": MIN_AREA,
        "iou_threshold": 0.5,
        "size": SIZE,
        "methods": {
            "M1 HSV-порог": aggregate(hsv, gts),
            "M2 Lab-порог": aggregate(lab, gts),
            "M3 RandomForest": aggregate(rf_pred, gts),
            "M4 U-Net": aggregate(unet_pred, gts),
        },
    }
    (OUT / "spots.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    for k, v in out["methods"].items():
        print(k, v)
    print("saved", OUT / "spots.json")


if __name__ == "__main__":
    main()
