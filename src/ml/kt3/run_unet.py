"""M4: небольшая U-Net, обучение на CPU."""

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
from torch import nn
from torch.utils.data import DataLoader, Dataset

import torch

from common import ROOT, image_metrics, load_manifest, load_pair, summarize

OUT = ROOT / "docs" / "kt3" / "results"
MODEL_DIR = ROOT / "dataset" / "processed" / "kt3"
SIZE = 256
SEED = 42


class PairDataset(Dataset):
    def __init__(self, records, train=False):
        self.records = records
        self.train = train
        self.images = []
        self.masks = []
        for rec in records:
            img, mask = load_pair(rec, SIZE)
            self.images.append(img)
            self.masks.append(mask.astype(np.float32))

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        img = self.images[idx].astype(np.float32) / 255.0
        mask = self.masks[idx]
        if self.train:
            k = random.randint(0, 3)
            if k:
                img = np.rot90(img, k).copy()
                mask = np.rot90(mask, k).copy()
            if random.random() < 0.5:
                img = img[:, ::-1].copy()
                mask = mask[:, ::-1].copy()
            if random.random() < 0.3:
                img = np.clip(img * random.uniform(0.85, 1.15) + random.uniform(-0.05, 0.05), 0, 1)
        x = torch.from_numpy(img.transpose(2, 0, 1))
        y = torch.from_numpy(mask[None, ...])
        return x, y


class ConvBlock(nn.Module):
    def __init__(self, cin, cout):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(cin, cout, 3, padding=1, bias=False),
            nn.BatchNorm2d(cout), nn.ReLU(inplace=True),
            nn.Conv2d(cout, cout, 3, padding=1, bias=False),
            nn.BatchNorm2d(cout), nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.net(x)


class UNet(nn.Module):
    def __init__(self, channels=(16, 32, 64, 128), bottleneck=256):
        super().__init__()
        self.down = nn.ModuleList()
        cin = 3
        for c in channels:
            self.down.append(ConvBlock(cin, c))
            cin = c
        self.pool = nn.MaxPool2d(2)
        self.mid = ConvBlock(cin, bottleneck)
        cin = bottleneck
        self.up = nn.ModuleList()
        self.upconv = nn.ModuleList()
        for c in reversed(channels):
            self.upconv.append(nn.ConvTranspose2d(cin, c, 2, stride=2))
            self.up.append(ConvBlock(c * 2, c))
            cin = c
        self.head = nn.Conv2d(cin, 1, 1)

    def forward(self, x):
        skips = []
        for block in self.down:
            x = block(x)
            skips.append(x)
            x = self.pool(x)
        x = self.mid(x)
        for upconv, block, skip in zip(self.upconv, self.up, reversed(skips)):
            x = upconv(x)
            x = torch.cat([x, skip], dim=1)
            x = block(x)
        return self.head(x)


def dice_loss(logits, target):
    prob = torch.sigmoid(logits)
    num = 2 * (prob * target).sum(dim=(1, 2, 3)) + 1.0
    den = prob.sum(dim=(1, 2, 3)) + target.sum(dim=(1, 2, 3)) + 1.0
    return 1 - (num / den).mean()


def evaluate(model, dataset, batch_size=4):
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    probs = []
    model.eval()
    with torch.inference_mode():
        for x, _ in loader:
            probs.append(torch.sigmoid(model(x)).squeeze(1).numpy())
    return np.concatenate(probs, axis=0)


def make_rows(records, probs, thr, morph=True):
    from scipy import ndimage
    rows = []
    for rec, prob in zip(records, probs):
        gt = load_pair(rec, SIZE)[1]
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-3)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.set_num_threads(min(12, os.cpu_count() or 1))
    torch.set_num_interop_threads(1)

    manifest = load_manifest()
    records = {s: [r for r in manifest["records"] if r["split"] == s] for s in ("train", "val", "test")}
    train_ds = PairDataset(records["train"], train=True)
    val_ds = PairDataset(records["val"])
    test_ds = PairDataset(records["test"])
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
    model = UNet()
    n_params = sum(p.numel() for p in model.parameters())
    print(f"model params: {n_params}", flush=True)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)
    bce = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(2.0))

    best_dice = -1
    best_state = None
    best_epoch = 0
    history = []
    t0 = time.perf_counter()
    for epoch in range(1, args.epochs + 1):
        model.train()
        total = 0.0
        for step, (x, y) in enumerate(train_loader, 1):
            opt.zero_grad(set_to_none=True)
            logits = model(x)
            loss = bce(logits, y) + dice_loss(logits, y)
            loss.backward()
            opt.step()
            total += float(loss)
            if step % 20 == 0 or step == len(train_loader):
                print(f" epoch {epoch:02d} step {step:03d}/{len(train_loader)} loss={total / step:.4f}", flush=True)
        sched.step()
        val_probs = evaluate(model, val_ds)
        val_rows = make_rows(records["val"], val_probs, 0.5, morph=False)
        dev_dice = float(np.mean([r["dice"] for r in val_rows]))
        history.append({"epoch": epoch, "loss": round(total / len(train_loader), 4), "val_dice": round(dev_dice, 4)})
        print(f"epoch {epoch:02d} loss={total / len(train_loader):.4f} val_dice={dev_dice:.4f} "
              f"elapsed={time.perf_counter() - t0:.0f}s", flush=True)
        if dev_dice > best_dice:
            best_dice = dev_dice
            best_epoch = epoch
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    assert best_state is not None
    model.load_state_dict(best_state)
    torch.save({"state_dict": best_state, "channels": [16, 32, 64, 128], "bottleneck": 256},
               MODEL_DIR / "unet.pt")

    val_probs = evaluate(model, val_ds)
    best = None
    for thr in (0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6):
        for morph in (False, True):
            rows = make_rows(records["val"], val_probs, thr, morph)
            tp = sum(r["tp"] for r in rows)
            fp = sum(r["fp"] for r in rows)
            fn = sum(r["fn"] for r in rows)
            f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 1.0
            dice = float(np.mean([r["dice"] for r in rows]))
            if best is None or (f1, dice) > best[0]:
                best = ((f1, dice), thr, morph, rows)
    _, thr, morph, val_rows = best

    t1 = time.perf_counter()
    test_probs = evaluate(model, test_ds)
    infer = time.perf_counter() - t1
    test_rows = make_rows(records["test"], test_probs, thr, morph)
    result = {
        "size": SIZE,
        "params": {"architecture": "UNet 16-32-64-128, bottleneck 256", "parameters": n_params,
                   "epochs": args.epochs, "batch_size": args.batch_size, "lr": args.lr,
                   "threshold": thr, "morphology": morph, "best_epoch": best_epoch},
        "train_seconds": round(time.perf_counter() - t0, 1),
        "infer_seconds_test": round(infer, 2),
        "fps_test": round(len(records["test"]) / infer, 2),
        "history": history,
        "val": summarize(val_rows),
        "test": summarize(test_rows),
        "rows": test_rows,
    }
    (OUT / "unet.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("U-Net test", result["test"]["all"], flush=True)
    for s, m in result["test"].items():
        print(" ", s, m)
    print(f"saved {OUT / 'unet.json'} in {result['train_seconds']}s")


if __name__ == "__main__":
    main()
