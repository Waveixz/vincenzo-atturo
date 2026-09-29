from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "vincenzo-atturo-share-2026.jpg"
WIDTH, HEIGHT = 1200, 630

NAVY = "#06223d"
NAVY_DEEP = "#031726"
BLUE = "#159cff"
WHITE = "#ffffff"
MUTED = "#bcd0df"
LINE = "#16486f"


def font(name, size):
    return ImageFont.truetype(str(Path(r"C:\Windows\Fonts") / name), size)


image = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
draw = ImageDraw.Draw(image)

draw.rectangle((970, 0, WIDTH, HEIGHT), fill=NAVY_DEEP)
draw.rectangle((950, 0, 970, HEIGHT), fill=BLUE)

for y, length in ((92, 220), (152, 150), (478, 270), (538, 180)):
    draw.line((730, y, 730 + length, y), fill=LINE, width=2)
    draw.line((730 + length, y, 730 + length + 42, y - 42), fill=LINE, width=2)
for x, length in ((90, 165), (160, 110), (870, 90)):
    draw.line((x, 0, x, length), fill=LINE, width=2)

draw.text((78, 61), "VA", font=font("segoeuib.ttf", 54), fill=BLUE)
draw.text((180, 76), "VA DIGITAL", font=font("segoeuib.ttf", 25), fill=WHITE)

draw.text((78, 184), "BIGLIETTO DIGITALE", font=font("segoeuib.ttf", 20), fill=BLUE)
draw.text((74, 226), "Vincenzo Atturo", font=font("segoeuib.ttf", 72), fill=WHITE)
draw.text(
    (78, 326),
    "IT Manager & Digital Solutions Developer",
    font=font("segoeuib.ttf", 28),
    fill="#d7e9f7",
)

draw.text(
    (78, 390),
    "Software, automazioni, dashboard, dati e GIS su misura.",
    font=font("segoeui.ttf", 26),
    fill=MUTED,
)
draw.line((78, 466, 865, 466), fill=BLUE, width=3)
draw.text(
    (78, 500),
    "Apri per chiamare, scrivere o salvare il contatto",
    font=font("segoeui.ttf", 23),
    fill=MUTED,
)
draw.text((78, 552), "va-digital.it/vincenzo-atturo/", font=font("segoeuib.ttf", 25), fill=WHITE)

image.save(OUTPUT, "JPEG", quality=94, optimize=True, progressive=True, subsampling=0)
print(OUTPUT)
