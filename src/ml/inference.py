"""Инференс U-Net для обнаружения ржавчины и коррозии (КТ 4)."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np
from PIL import Image
from scipy import ndimage
import torch
from torch import nn

SIZE = 256
DEFAULT_THRESHOLD = 0.5
MIN_COMPONENT_SIZE = 24


class ConvBlock(nn.Module):
    def __init__(self, cin: int, cout: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(cin, cout, 3, padding=1, bias=False),
            nn.BatchNorm2d(cout),
            nn.ReLU(inplace=True),
            nn.Conv2d(cout, cout, 3, padding=1, bias=False),
            nn.BatchNorm2d(cout),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
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

    def forward(self, x: torch.Tensor) -> torch.Tensor:
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


def find_model_path() -> Path:
    env_path = os.getenv("MODEL_PATH")
    if env_path and Path(env_path).is_file():
        return Path(env_path)

    candidates = [
        Path("/models/unet.pt"),
        Path(__file__).resolve().parents[2] / "dataset" / "processed" / "kt3" / "unet.pt",
        Path("dataset/processed/kt3/unet.pt"),
    ]
    for cand in candidates:
        if cand.is_file():
            return cand
    raise FileNotFoundError(
        "Чекпоинт U-Net не найден. Укажите MODEL_PATH или запустите 'python scripts/fetch_weights.py'"
    )


class RustDetector:
    def __init__(self, checkpoint_path: Optional[Union[str, Path]] = None, device: Optional[str] = None):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        if checkpoint_path is None:
            self.checkpoint_path = find_model_path()
        else:
            self.checkpoint_path = Path(checkpoint_path)

        self.model = self._load_model()

    def _load_model(self) -> UNet:
        checkpoint = torch.load(self.checkpoint_path, map_location=self.device)
        channels = checkpoint.get("channels", [16, 32, 64, 128])
        bottleneck = checkpoint.get("bottleneck", 256)
        state_dict = checkpoint["state_dict"]

        model = UNet(channels=channels, bottleneck=bottleneck)
        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()
        return model

    def predict(
        self,
        image: Image.Image,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        orig_w, orig_h = image.size
        img_resized = image.resize((SIZE, SIZE), Image.BILINEAR)
        arr = np.asarray(img_resized, dtype=np.float32) / 255.0
        x = torch.from_numpy(arr.transpose(2, 0, 1)).unsqueeze(0).to(self.device)

        with torch.inference_mode():
            logits = self.model(x)
            probs = torch.sigmoid(logits).squeeze().cpu().numpy()

        pred = probs >= threshold

        # Морфологическая постобработка (КТ 3)
        pred = ndimage.binary_opening(pred, structure=np.ones((3, 3)))
        pred = ndimage.binary_closing(pred, structure=np.ones((3, 3)))
        lab, n = ndimage.label(pred)
        if n:
            sizes = ndimage.sum(pred, lab, range(1, n + 1))
            keep = np.zeros(n + 1, dtype=bool)
            keep[1:] = sizes >= MIN_COMPONENT_SIZE
            pred = keep[lab]

        # Расчет confidence: средняя sigmoid-вероятность по предсказанным пикселям дефекта
        if np.any(pred):
            confidence = float(np.mean(probs[pred]))
        else:
            confidence = 0.0

        # Маска в исходном размере изображения через nearest resize
        mask_orig_img = Image.fromarray((pred.astype(np.uint8) * 255)).resize(
            (orig_w, orig_h), Image.NEAREST
        )
        mask_orig = np.asarray(mask_orig_img) > 0

        return mask_orig, probs, confidence


_DETECTOR: Optional[RustDetector] = None


def get_detector() -> RustDetector:
    global _DETECTOR
    if _DETECTOR is None:
        _DETECTOR = RustDetector()
    return _DETECTOR


def inspect_image(
    image_path: Union[str, Path],
    output_mask_path: Optional[Union[str, Path]] = None,
    output_overlay_path: Optional[Union[str, Path]] = None,
    mm_per_px: Optional[float] = None,
) -> Dict[str, Any]:
    image_file = Path(image_path)
    if not image_file.is_file():
        raise FileNotFoundError(f"Изображение не найдено: {image_path}")

    img = Image.open(image_file).convert("RGB")
    orig_np = np.asarray(img, dtype=np.uint8)

    detector = get_detector()
    mask_orig, _, confidence = detector.predict(img)

    area_px = int(np.sum(mask_orig))

    # Калибровка MM_PER_PX
    if mm_per_px is None:
        env_val = os.getenv("MM_PER_PX")
        if env_val:
            try:
                val = float(env_val)
                if val > 0:
                    mm_per_px = val
            except ValueError:
                pass

    if mm_per_px is not None and mm_per_px > 0:
        calibrated = True
        area_mm2 = round(area_px * (float(mm_per_px) ** 2), 2)
    else:
        calibrated = False
        area_mm2 = None

    # Построение overlay: исходное изображение + красная полупрозрачная маска
    overlay_np = orig_np.copy()
    red = np.array([255, 0, 0], dtype=np.uint8)
    if np.any(mask_orig):
        overlay_np[mask_orig] = (0.5 * orig_np[mask_orig] + 0.5 * red).astype(np.uint8)

    data_dir = os.getenv("DATA_DIR")
    base_dir = Path(data_dir) if data_dir else image_file.parent

    if output_mask_path is None:
        mask_dir = base_dir / "masks"
        mask_dir.mkdir(parents=True, exist_ok=True)
        output_mask_path = mask_dir / f"{image_file.stem}_mask.png"
    else:
        output_mask_path = Path(output_mask_path)
        output_mask_path.parent.mkdir(parents=True, exist_ok=True)

    if output_overlay_path is None:
        overlay_dir = base_dir / "overlays"
        overlay_dir.mkdir(parents=True, exist_ok=True)
        output_overlay_path = overlay_dir / f"{image_file.stem}_overlay.png"
    else:
        output_overlay_path = Path(output_overlay_path)
        output_overlay_path.parent.mkdir(parents=True, exist_ok=True)

    mask_img = Image.fromarray((mask_orig.astype(np.uint8) * 255))
    mask_img.save(output_mask_path, format="PNG")

    overlay_img = Image.fromarray(overlay_np)
    overlay_img.save(output_overlay_path, format="PNG")

    return {
        "mask_png_path": str(output_mask_path),
        "overlay_png_path": str(output_overlay_path),
        "area_px": area_px,
        "area_mm2": area_mm2,
        "confidence": round(confidence, 4),
        "calibrated": calibrated,
    }
