"""Rebuild the Windows icon from the approved Redexa Social master asset."""

from pathlib import Path

from PIL import Image

root = Path(__file__).resolve().parent
source = Image.open(root / "icon_preview.png").convert("RGB")
source.save(
    root / "icon.ico",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
print("Built icon.ico")
