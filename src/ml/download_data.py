"""Скачивание, проверка и распаковка открытых датасетов коррозии."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import urllib.request
import zipfile
from glob import glob

CHUNK = 1 << 20

SOURCES = [
    {
        "name": "pipelines",
        "file": "Corrosion_Pipelines.zip",
        "url": "https://ndownloader.figshare.com/files/59311992",
        "sha256": "3ce05636b67932d6be86df3fb643cc5ab95b84e8d717c165502aae7343072803",
        "md5": None,
        "dir": "pipelines",
    },
    {
        "name": "ostrava",
        "file": "ostrava.zip",
        "url": "https://zenodo.org/records/11235637/files/ostrava.zip?download=1",
        "sha256": "874a60cd8e9e92476c2314bd6acfcac7dc0f64eb797ea220a091a96681de50c5",
        "md5": "e30f1f62eb85018c2faee44909e69a06",
        "dir": "ostrava",
    },
    {
        "name": "vt",
        "file": "vt_corrosion.zip",
        "url": "https://ndownloader.figshare.com/files/48406757",
        "sha256": "45f0ec8b26f1c09d707f3010af359a28e0985d385d2bf6d98b5d4dd308e9dbe5",
        "md5": None,
        "dir": "vt",
    },
]


def digest(path: str, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: str) -> None:
    part = dest + ".part"
    if os.path.exists(part):
        os.remove(part)
    print(f"  загрузка: {url}")
    with urllib.request.urlopen(url, timeout=120) as response, open(part, "wb") as out:
        total = int(response.headers.get("Content-Length") or 0)
        done = 0
        last = -1
        while True:
            chunk = response.read(CHUNK)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            mb = done // CHUNK
            if mb != last and mb % 10 == 0:
                if total:
                    print(f"    {done / CHUNK:.0f} / {total / CHUNK:.0f} МБ")
                else:
                    print(f"    {done / CHUNK:.0f} МБ")
                last = mb
    os.replace(part, dest)


def check_archive(meta: dict, dest_dir: str) -> bool:
    path = os.path.join(dest_dir, meta["file"])
    if not os.path.exists(path):
        print(f"[{meta['name']}] файла нет: {path}")
        return False
    size = os.path.getsize(path)
    sha = digest(path, "sha256")
    ok = sha == meta["sha256"]
    print(f"[{meta['name']}] {size / CHUNK:.1f} МБ, sha256 {'OK' if ok else 'НЕ СОВПАЛ'}")
    if not ok:
        print(f"  ожидалось: {meta['sha256']}")
        print(f"  получено:  {sha}")
    if meta.get("md5"):
        md5_ok = digest(path, "md5") == meta["md5"]
        print(f"  md5 {'OK' if md5_ok else 'НЕ СОВПАЛ'}")
        ok = ok and md5_ok
    return ok


def extract(meta: dict, dest_dir: str, force: bool) -> str:
    target = os.path.join(dest_dir, meta["dir"])
    if os.path.isdir(target):
        if not force:
            print(f"[{meta['name']}] уже распакован: {target}")
            return target
        shutil.rmtree(target)
    os.makedirs(target, exist_ok=True)
    with zipfile.ZipFile(os.path.join(dest_dir, meta["file"])) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"повреждён файл в архиве: {bad}")
        archive.extractall(target)
    print(f"[{meta['name']}] распакован: {target}")
    return target


def count_dataset(name: str, target: str) -> None:
    if name == "pipelines":
        images = glob(os.path.join(target, "**", "images", "**", "*.jpg"), recursive=True)
        images += glob(os.path.join(target, "**", "images", "**", "*.jpeg"), recursive=True)
        images += glob(os.path.join(target, "**", "images", "**", "*.png"), recursive=True)
        anns = glob(os.path.join(target, "**", "annotations", "*.json"), recursive=True)
        boxes = 0
        for path in anns:
            with open(path, encoding="utf-8") as fh:
                boxes += len(json.load(fh).get("annotations", []))
        print(f"[pipelines] изображений: {len(images)}, аннотаций: {boxes}")
    elif name == "ostrava":
        images = glob(os.path.join(target, "**", "images", "*"), recursive=True)
        masks = glob(os.path.join(target, "**", "masks", "*"), recursive=True)
        print(f"[ostrava] изображений: {len(images)}, масок: {len(masks)}")
    elif name == "vt":
        images = glob(os.path.join(target, "**", "original", "*", "images", "*"), recursive=True)
        masks = glob(os.path.join(target, "**", "original", "*", "masks", "*"), recursive=True)
        labels = glob(os.path.join(target, "**", "original", "*", "json", "*.json"), recursive=True)
        print(f"[vt] изображений: {len(images)}, масок: {len(masks)}, JSON: {len(labels)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Скачать датасеты коррозии и проверить целостность")
    parser.add_argument("--dest", default=os.path.join("dataset", "raw"), help="каталог для архивов")
    parser.add_argument("--check-only", action="store_true", help="только проверить архивы и распаковку")
    parser.add_argument("--force", action="store_true", help="скачать и распаковать заново")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(args.dest, exist_ok=True)
    failed = []
    for meta in SOURCES:
        path = os.path.join(args.dest, meta["file"])
        needs_download = args.force or not os.path.exists(path)
        if not args.check_only and needs_download:
            download(meta["url"], path)
        if not os.path.exists(path):
            failed.append(meta["name"])
            continue
        if not check_archive(meta, args.dest):
            if args.check_only:
                failed.append(meta["name"])
                continue
            download(meta["url"], path)
            if not check_archive(meta, args.dest):
                failed.append(meta["name"])
                continue
        if not args.check_only or os.path.isdir(os.path.join(args.dest, meta["dir"])):
            target = extract(meta, args.dest, args.force)
            count_dataset(meta["name"], target)

    if failed:
        print("Ошибка: " + ", ".join(failed))
        return 1
    print("Все датасеты проверены.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
