"""Build Redexa Social icon assets from the approved master PNG."""

from __future__ import annotations

import base64
import re
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def png_bytes(image: Image.Image, size: int) -> bytes:
    canvas = Image.new("RGB", (size, size), "white")
    source = image.convert("RGBA")
    source.thumbnail((round(size * 0.86), round(size * 0.86)), Image.Resampling.LANCZOS)
    offset = ((size - source.width) // 2, (size - source.height) // 2)
    canvas.paste(source, offset, source)
    output = BytesIO()
    canvas.save(output, format="PNG", optimize=True)
    return output.getvalue()


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: build_brand_assets.py MASTER_PNG")
    master = Image.open(sys.argv[1])
    png_1024 = png_bytes(master, 1024)
    png_512 = png_bytes(master, 512)
    png_64 = png_bytes(master, 64)
    (ROOT / "docs" / "app-icon-1024.png").write_bytes(png_1024)
    (ROOT / "icon_preview.png").write_bytes(png_512)
    (ROOT / "static" / "brand-mark.png").write_bytes(png_64)
    Image.open(BytesIO(png_512)).save(
        ROOT / "icon.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    assets_path = ROOT / "oauth-proxy" / "assets.js"
    assets = assets_path.read_text(encoding="utf-8")
    screenshot = (ROOT / "docs" / "screenshots" / "overview.png").read_bytes()
    for name, data in {
        "FAVICON_B64": png_64,
        "ICON_512_B64": png_512,
        "SCREENSHOT_B64": screenshot,
    }.items():
        value = base64.b64encode(data).decode("ascii")
        assets, count = re.subn(rf'export const {name} = "[^"]*";', f'export const {name} = "{value}";', assets, count=1)
        if count != 1:
            raise RuntimeError(f"Could not update {name}")
    assets_path.write_text(assets, encoding="utf-8")
    print("Built Redexa Social brand assets.")


if __name__ == "__main__":
    main()
