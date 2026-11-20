"""Замер скорости и RSS для M1–M4. Качество (F1/Dice/IoU) здесь не считается; см. common.summarize."""

import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import psutil
import torch

from common import ROOT, hsv_mask, lab_mask, load_manifest, load_pair
from run_rf import features
from run_unet import UNet, evaluate, PairDataset

OUT = ROOT / "docs" / "kt3" / "results"
SIZE = 256


def rss():
    return round(psutil.Process().memory_info().rss / 1024**2, 1)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    manifest = load_manifest()
    records = [r for r in manifest["records"] if r["split"] == "test"]
    images = [load_pair(r, SIZE)[0] for r in records]
    thr = json.loads((OUT / "thresholds.json").read_text(encoding="utf-8"))
    out = {"size": SIZE, "n": len(records), "methods": {}}

    p = thr["methods"]["M1 HSV-порог"]["params"]
    t = time.perf_counter()
    for img in images:
        hsv_mask(img, p["s_min"], p["v_min"], p["v_max"], p["hue_max"], p["hue_wrap"])
    sec = time.perf_counter() - t
    out["methods"]["M1 HSV-порог"] = {"seconds": round(sec, 3), "fps": round(len(images) / sec, 2), "rss_mb": rss()}

    p = thr["methods"]["M2 Lab-порог"]["params"]
    t = time.perf_counter()
    for img in images:
        lab_mask(img, p["a_min"], p["b_min"], p["l_max"])
    sec = time.perf_counter() - t
    out["methods"]["M2 Lab-порог"] = {"seconds": round(sec, 3), "fps": round(len(images) / sec, 2), "rss_mb": rss()}

    model = joblib.load(ROOT / "dataset" / "processed" / "kt3" / "rf.joblib")
    t = time.perf_counter()
    for img in images:
        f = features(img)
        model.predict_proba(f.reshape(-1, f.shape[2]))[:, 1]
    sec = time.perf_counter() - t
    out["methods"]["M3 RandomForest"] = {"seconds": round(sec, 3), "fps": round(len(images) / sec, 2), "rss_mb": rss()}

    ckpt = torch.load(ROOT / "dataset" / "processed" / "kt3" / "unet.pt", map_location="cpu", weights_only=False)
    unet = UNet(channels=ckpt["channels"], bottleneck=ckpt["bottleneck"])
    unet.load_state_dict(ckpt["state_dict"])
    ds = PairDataset(records)
    t = time.perf_counter()
    evaluate(unet, ds)
    sec = time.perf_counter() - t
    out["methods"]["M4 U-Net"] = {"seconds": round(sec, 3), "fps": round(len(images) / sec, 2), "rss_mb": rss()}

    (OUT / "speed.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    for k, v in out["methods"].items():
        print(k, v)
    print("saved", OUT / "speed.json")


if __name__ == "__main__":
    main()
