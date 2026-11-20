"""Визуализация удачных и неудачных примеров U-Net."""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

from common import ROOT, load_manifest, load_pair
from run_unet import UNet, evaluate, PairDataset

OUT = ROOT / "docs" / "kt3" / "figures"
SIZE = 256
GOOD = [("ostrava", "02"), ("vt", "36"), ("ostrava", "01")]
BAD = [("vt", "11"), ("vt", "21"), ("vt", "19")]


def overlay(img, mask, color):
    out = img.astype(np.float32) / 255.0
    m = mask.astype(bool)
    out[m] = out[m] * 0.45 + np.array(color) * 0.55
    return np.clip(out, 0, 1)


def error_map(img, gt, pred):
    out = img.astype(np.float32) / 255.0 * 0.65
    tp = gt & pred
    fp = pred & ~gt
    fn = ~pred & gt
    out[tp] = out[tp] * 0.2 + np.array([0.1, 0.9, 0.2]) * 0.8
    out[fp] = out[fp] * 0.2 + np.array([0.95, 0.1, 0.1]) * 0.8
    out[fn] = out[fn] * 0.2 + np.array([0.1, 0.3, 1.0]) * 0.8
    return np.clip(out, 0, 1)


def draw(records, probs, keys, path, title):
    fig, axes = plt.subplots(len(keys), 4, figsize=(12, 3.1 * len(keys)))
    if len(keys) == 1:
        axes = axes[None, :]
    for row, (source, name) in enumerate(keys):
        idx = next(i for i, r in enumerate(records) if r["name"] == name and r["source"] == source)
        rec = records[idx]
        img, gt = load_pair(rec, SIZE)
        pred = probs[idx] >= 0.5
        tp = int(np.logical_and(pred, gt).sum())
        fp = int(np.logical_and(pred, ~gt).sum())
        fn = int(np.logical_and(~pred, gt).sum())
        dice = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 1.0
        panels = [
            (img, f"{rec['source']} / {name}"),
            (overlay(img, gt, [0.1, 0.9, 0.2]), "эталон"),
            (overlay(img, pred, [0.95, 0.1, 0.1]), f"U-Net, Dice={dice:.2f}"),
            (error_map(img, gt, pred), "TP зелёный / FP красный / FN синий"),
        ]
        for col, (arr, subtitle) in enumerate(panels):
            ax = axes[row, col]
            ax.imshow(arr)
            ax.set_title(subtitle, fontsize=9)
            ax.axis("off")
    fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    records = [r for r in manifest["records"] if r["split"] == "test"]
    ckpt = torch.load(ROOT / "dataset" / "processed" / "kt3" / "unet.pt", map_location="cpu", weights_only=False)
    model = UNet(channels=ckpt["channels"], bottleneck=ckpt["bottleneck"])
    model.load_state_dict(ckpt["state_dict"])
    probs = evaluate(model, PairDataset(records))

    draw(records, probs, GOOD, OUT / "examples_good.png", "Удачные примеры U-Net")
    draw(records, probs, BAD, OUT / "examples_bad.png", "Неудачные примеры U-Net")
    (OUT / "examples.json").write_text(json.dumps({"good": GOOD, "bad": BAD}, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
    print("saved", OUT)


if __name__ == "__main__":
    main()
