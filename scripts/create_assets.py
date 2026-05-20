"""Gera placeholders de logo e background em assets/."""

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Instale Pillow para gerar assets: pip install pillow")
    raise

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)


def create_logo() -> None:
    img = Image.new("RGBA", (320, 120), (28, 35, 51, 255))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((10, 10, 310, 110), radius=16, outline=(31, 111, 235), width=3)
    draw.text((40, 42), "DEVOLUÇÃO", fill=(230, 237, 243))
    draw.text((40, 68), "WMS", fill=(63, 185, 80))
    img.save(ASSETS / "logo.png")


def create_background() -> None:
    img = Image.new("RGB", (1920, 1080), (13, 17, 23))
    draw = ImageDraw.Draw(img)
    for i in range(0, 1920, 80):
        draw.line([(i, 0), (i, 1080)], fill=(22, 27, 34), width=1)
    for j in range(0, 1080, 80):
        draw.line([(0, j), (1920, j)], fill=(22, 27, 34), width=1)
    draw.ellipse((760, 340, 1160, 740), outline=(31, 111, 235, 80), width=2)
    img.save(ASSETS / "background.png")


if __name__ == "__main__":
    create_logo()
    create_background()
    print(f"Assets criados em {ASSETS}")
