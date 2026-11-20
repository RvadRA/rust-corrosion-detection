"""Сборка единого датасета KT3 из Ostrava, Virginia Tech и Pipelines."""

import json
import os
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "dataset" / "raw"
OUT = ROOT / "dataset" / "processed" / "kt3"
SIZE = 512
SEED = 42


def log(*args):
    print(*args, flush=True)


def decode_rle(counts, height, width):
    flat = np.zeros(height * width, dtype=np.uint8)
    pos = 0
    for i, value in enumerate(counts):
        if i % 2 == 1:
            flat[pos:pos + value] = 1
        pos += value
    return flat.reshape((width, height)).T


def save_pair(image_path, mask, out_image, out_mask):
    image = Image.open(image_path).convert("RGB").resize((SIZE, SIZE), Image.BILINEAR)
    mask_img = Image.fromarray((mask > 0).astype(np.uint8) * 255, mode="L")
    mask_img = mask_img.resize((SIZE, SIZE), Image.NEAREST)
    image.save(out_image, optimize=True)
    mask_img.save(out_mask, optimize=True)
    m = np.asarray(mask_img) > 0
    return float(m.mean())


def split_pipelines(images):
    ids = sorted(images, key=lambda x: x["id"])
    random.Random(SEED).shuffle(ids)
    n = len(ids)
    n_train = int(round(n * 0.64))
    n_val = int(round(n * 0.18))
    parts = {
        "train": ids[:n_train],
        "val": ids[n_train:n_train + n_val],
        "test": ids[n_train + n_val:],
    }
    return {k: {x["id"] for x in v} for k, v in parts.items()}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for sub in ("images", "masks"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)

    records = []
    index = 0

    def add(source, split, image_path, mask, name):
        nonlocal index
        idx = f"{index:04d}"
        pos = save_pair(image_path, mask, OUT / "images" / f"{idx}.png", OUT / "masks" / f"{idx}.png")
        records.append({
            "id": idx,
            "name": name,
            "source": source,
            "split": split,
            "image": str((OUT / "images" / f"{idx}.png").relative_to(ROOT)),
            "mask": str((OUT / "masks" / f"{idx}.png").relative_to(ROOT)),
            "positive_fraction": round(pos, 6),
        })
        index += 1

    ostrava = RAW / "ostrava" / "corrosion-in-industrial-complexes-in-ostrava"
    for split, folder in (("train", "train"), ("val", "validation"), ("test", "test")):
        img_dir = ostrava / folder / "images"
        mask_dir = ostrava / folder / "masks"
        for path in sorted(img_dir.glob("*")):
            mask_path = mask_dir / (path.stem + ".png")
            if not mask_path.exists():
                continue
            mask = np.asarray(Image.open(mask_path).convert("RGB")).max(axis=2)
            add("ostrava", split, path, mask, path.stem)

    vt = RAW / "vt" / "Corrosion Condition State Classification"
    for split, folder in (("train", "Train"), ("test", "Test")):
        img_dir = vt / "512x512" / folder / "images_512"
        mask_dir = vt / "512x512" / folder / "mask_512"
        for path in sorted(img_dir.glob("*")):
            mask_path = mask_dir / (path.stem + ".png")
            if not mask_path.exists():
                continue
            mask = np.asarray(Image.open(mask_path).convert("RGB")).max(axis=2)
            add("vt", split, path, mask, path.stem)

    pipe = RAW / "pipelines" / "job_100_dataset_2025_04_09_17_18_29_coco 1.0"
    coco = json.loads((pipe / "annotations" / "instances_default.json").read_text(encoding="utf-8"))
    by_id = {im["id"]: im for im in coco["images"]}
    masks = {}
    for ann in coco["annotations"]:
        im = by_id[ann["image_id"]]
        h, w = im["height"], im["width"]
        if ann["image_id"] not in masks:
            masks[ann["image_id"]] = np.zeros((h, w), dtype=np.uint8)
        masks[ann["image_id"]] |= decode_rle(ann["segmentation"]["counts"], h, w)
    pipe_split = split_pipelines(coco["images"])
    for im in sorted(coco["images"], key=lambda x: x["id"]):
        split = next((k for k, ids in pipe_split.items() if im["id"] in ids), None)
        if split is None:
            continue
        path = pipe / "images" / "default" / im["file_name"]
        mask = masks.get(im["id"], np.zeros((im["height"], im["width"]), dtype=np.uint8))
        add("pipelines", split, path, mask, Path(im["file_name"]).stem)

    manifest = {
        "seed": SEED,
        "size": SIZE,
        "count": len(records),
        "splits": {},
        "records": records,
    }
    for split in ("train", "val", "test"):
        rows = [r for r in records if r["split"] == split]
        manifest["splits"][split] = {
            "count": len(rows),
            "sources": {s: sum(1 for r in rows if r["source"] == s)
                        for s in sorted({r["source"] for r in rows})},
            "positive_fraction": round(float(np.mean([r["positive_fraction"] for r in rows])), 6) if rows else 0,
        }
    OUT.mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "kt3" / "results").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "kt3" / "results" / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    for split, info in manifest["splits"].items():
        log(f"{split:5s}: {info['count']:3d} {info['sources']} pos={info['positive_fraction']:.3f}")
    log(f"saved {len(records)} pairs to {OUT}")


if __name__ == "__main__":
    main()
