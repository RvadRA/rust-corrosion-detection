#!/usr/bin/env python3
"""Скрипт проверки и скачивания предобученных весов модели U-Net (КТ 3/4)."""

import argparse
import hashlib
import os
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEST = ROOT / "dataset" / "processed" / "kt3" / "unet.pt"
EXPECTED_SHA256 = "3900ef9023e22c5580666c37d9c4c5194a1f63fe057104bfad73f34a47dbdaa0"
DEFAULT_URL = os.getenv(
    "WEIGHTS_URL",
    "https://github.com/RvadRA/rust-corrosion-detection/releases/download/v1.0.0-kt3/unet.pt",
)


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest().lower()


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp_dest = dest.with_suffix(".tmp")

    print(f"Скачивание весов U-Net из: {url}")
    print(f"Целевой файл: {dest}")

    def reporthook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100.0, downloaded * 100 / total_size)
            mb = downloaded / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            sys.stdout.write(f"\r  Прогресс: {mb:.1f}/{total_mb:.1f} МБ ({percent:.1f}%)")
        else:
            sys.stdout.write(f"\r  Скачано: {downloaded / (1024 * 1024):.1f} МБ")
        sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, temp_dest, reporthook=reporthook)
        print("\nЗагрузка завершена, проверка контрольной суммы...")
    except Exception as e:
        if temp_dest.exists():
            temp_dest.unlink()
        raise RuntimeError(f"Ошибка скачивания весов: {e}")

    actual_hash = compute_sha256(temp_dest)
    if actual_hash != EXPECTED_SHA256:
        temp_dest.unlink()
        raise ValueError(
            f"Контрольная сумма SHA-256 не совпадает!\n"
            f"  Ожидалось: {EXPECTED_SHA256}\n"
            f"  Получено:  {actual_hash}"
        )

    temp_dest.replace(dest)
    print(f"Веса успешно верифицированы (SHA-256 OK) и сохранены в {dest}")


def main():
    parser = argparse.ArgumentParser(description="Скачивание и проверка весов модели U-Net")
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST, help="Путь для сохранения чекпоинта")
    parser.add_argument("--url", type=str, default=DEFAULT_URL, help="URL для скачивания unet.pt")
    parser.add_argument("--check-only", action="store_true", help="Только проверить локальный файл без скачивания")
    parser.add_argument("--force", action="store_true", help="Перекачать файл, даже если он уже существует")
    args = parser.parse_args()

    dest = args.dest.resolve()

    if dest.exists() and not args.force:
        print(f"Файл {dest} уже существует. Проверка контрольной суммы...")
        actual_hash = compute_sha256(dest)
        if actual_hash == EXPECTED_SHA256:
            print(f"OK: Контрольная сумма совпадает ({EXPECTED_SHA256}). Скачивание не требуется.")
            sys.exit(0)
        else:
            print(f"ВНИМАНИЕ: Контрольная сумма не совпадает!\n  Ожидалось: {EXPECTED_SHA256}\n  Фактически: {actual_hash}")
            if args.check_only:
                sys.exit(1)
            print("Перекачиваем файл...")

    if args.check_only:
        print(f"Файл {dest} не найден.")
        sys.exit(1)

    try:
        download_file(args.url, dest)
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        print(
            "\nЕсли файл ещё не опубликован в GitHub Releases, вы можете скопировать unet.pt вручную в:\n"
            f"  {dest}\n"
            f"Ожидаемый SHA256: {EXPECTED_SHA256}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
