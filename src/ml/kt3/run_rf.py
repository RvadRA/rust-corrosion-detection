"""M3: попиксельный классификатор цвет+текстура (RandomForest)."""

import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import psutil
from scipy import ndimage
from sklearn.ensemble import RandomForestClassifier

from common import ROOT, image_metrics, load_manifest, load_pair, rgb_to_hsv, rgb_to_lab, summarize

OUT = ROOT / "docs" / "kt3" / "results"
SIZE = 256
SEED = 42
FEATURES = [
    "r", "g", "b", "h_cos", "h_sin", "sat", "val",
    "lab_l", "lab_a", "lab_b", "r_mean9", "g_mean9", "b_mean9",
    "gray_std9", "grad", "red_excess", "sat_x_val",
]


def features(img):
    x = img.astype(np.float32) / 255.0
    h, s, v = rgb_to_hsv(img)
    lab = rgb_to_lab(img)
    gray = x @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    mean = ndimage.uniform_filter(gray, size=9)
    sq = ndimage.uniform_filter(gray * gray, size=9)
    std = np.sqrt(np.maximum(sq - mean * mean, 0))
    gx = ndimage.sobel(gray, axis=1)
    gy = ndimage.sobel(gray, axis=0)
    grad = np.hypot(gx, gy)
    r_mean = ndimage.uniform_filter(x[..., 0], size=9)
    g_mean = ndimage.uniform_filter(x[..., 1], size=9)
    b_mean = ndimage.uniform_filter(x[..., 2], size=9)
    return np.stack([
        x[..., 0], x[..., 1], x[..., 2],
        np.cos(2 * np.pi * h), np.sin(2 * np.pi * h), s, v,
        lab[..., 0] / 100.0, lab[..., 1] / 128.0, lab[..., 2] / 128.0,
        r_mean, g_mean, b_mean, std, grad,
        x[..., 0] - x[..., 1], s * v,
    ], axis=2).astype(np.float32)


def predict_proba(model, img):
    f = features(img)
    shape = f.shape[:2]
    prob = model.predict_proba(f.reshape(-1, f.shape[2]))[:, 1]
    return prob.reshape(shape)


def postprocess(prob, thr, morph):
    pred = prob >= thr
    if morph:
        pred = ndimage.binary_opening(pred, structure=np.ones((3, 3)))
        pred = ndimage.binary_closing(pred, structure=np.ones((3, 3)))
        lab, n = ndimage.label(pred)
        if n:
            sizes = ndimage.sum(pred, lab, range(1, n + 1))
            keep = np.zeros(n + 1, dtype=bool)
            keep[1:] = sizes >= 24
            pred = keep[lab]
    return pred


def make_rows(records, probs, thr, morph):
    rows = []
    for rec, prob in zip(records, probs):
        gt = load_pair(rec, SIZE)[1]
        pred = postprocess(prob, thr, morph)
        m = image_metrics(pred, gt)
        m.update({
            "id": rec["id"], "name": rec["name"], "source": rec["source"],
            "tp": int(np.logical_and(pred, gt).sum()),
            "fp": int(np.logical_and(pred, ~gt).sum()),
            "fn": int(np.logical_and(~pred, gt).sum()),
        })
        rows.append(m)
    return rows


def tune(records, probs):
    best = None
    for thr in (0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65):
        for morph in (False, True):
            rows = make_rows(records, probs, thr, morph)
            tp = sum(r["tp"] for r in rows)
            fp = sum(r["fp"] for r in rows)
            fn = sum(r["fn"] for r in rows)
            f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 1.0
            dice = float(np.mean([r["dice"] for r in rows]))
            if best is None or (f1, dice) > best[0]:
                best = ((f1, dice), thr, morph, rows)
    return best


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    records = {s: [r for r in manifest["records"] if r["split"] == s] for s in ("train", "val", "test")}
    rng = np.random.default_rng(SEED)

    t0 = time.perf_counter()
    xs, ys = [], []
    for rec in records["train"]:
        img, gt = load_pair(rec, SIZE)
        f = features(img).reshape(-1, len(FEATURES))
        y = gt.reshape(-1)
        pos = np.flatnonzero(y)
        neg = np.flatnonzero(~y)
        n_pos = min(1500, len(pos))
        n_neg = min(1500, len(neg))
        take = np.concatenate([
            rng.choice(pos, n_pos, replace=False),
            rng.choice(neg, n_neg, replace=False),
        ])
        xs.append(f[take])
        ys.append(y[take])
    x = np.concatenate(xs)
    y = np.concatenate(ys)
    print(f"train pixels: {len(y)} pos={y.mean():.3f}", flush=True)

    model = RandomForestClassifier(
        n_estimators=80, max_depth=16, min_samples_leaf=5,
        class_weight="balanced_subsample", n_jobs=-1, random_state=SEED,
    )
    model.fit(x, y)
    train_seconds = time.perf_counter() - t0
    rss_mb = round(psutil.Process().memory_info().rss / 1024**2, 1)
    joblib.dump(model, ROOT / "dataset" / "processed" / "kt3" / "rf.joblib")
    print(f"trained in {train_seconds:.1f}s", flush=True)

    t1 = time.perf_counter()
    val_probs = [predict_proba(model, load_pair(r, SIZE)[0]) for r in records["val"]]
    infer_val = time.perf_counter() - t1
    (_, thr, morph, val_rows) = tune(records["val"], val_probs)
    print(f"best thr={thr} morph={morph}", flush=True)

    t2 = time.perf_counter()
    test_probs = [predict_proba(model, load_pair(r, SIZE)[0]) for r in records["test"]]
    infer_test = time.perf_counter() - t2
    test_rows = make_rows(records["test"], test_probs, thr, morph)

    result = {
        "size": SIZE,
        "features": FEATURES,
        "train_pixels": int(len(y)),
        "train_positive_fraction": round(float(y.mean()), 4),
        "train_seconds": round(train_seconds, 2),
        "rss_mb": rss_mb,
        "infer_seconds_val": round(infer_val, 2),
        "infer_seconds_test": round(infer_test, 2),
        "fps_test": round(len(records["test"]) / infer_test, 2),
        "params": {"n_estimators": 80, "max_depth": 16, "min_samples_leaf": 5,
                   "threshold": thr, "morphology": morph},
        "val": summarize(val_rows),
        "test": summarize(test_rows),
        "rows": test_rows,
        "importance": {k: round(float(v), 4) for k, v in zip(FEATURES, model.feature_importances_)},
    }
    (OUT / "rf.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("RF test", result["test"]["all"])
    for s, m in result["test"].items():
        print(" ", s, m)
    print("saved", OUT / "rf.json")


if __name__ == "__main__":
    main()
