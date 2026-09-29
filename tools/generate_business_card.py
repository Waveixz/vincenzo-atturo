from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, FloatObject
from reportlab.lib.colors import CMYKColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "pdf"
TMP_DIR = ROOT / "tmp" / "pdfs"
OUTPUT = OUTPUT_DIR / "biglietto-da-visita-vincenzo-atturo-stampa.pdf"
SOURCE = TMP_DIR / "business-card-source.pdf"
QR_IMAGE = ROOT / "assets" / "vincenzo-atturo-qr.png"

PAGE_W = 91 * mm
PAGE_H = 61 * mm
BLEED = 3 * mm
TRIM_W = 85 * mm
TRIM_H = 55 * mm
SAFE = 4 * mm

NAVY = CMYKColor(1.0, 0.65, 0.30, 0.50)
NAVY_DEEP = CMYKColor(1.0, 0.72, 0.42, 0.68)
CHARCOAL = CMYKColor(0.72, 0.58, 0.46, 0.72)
GRAPHITE = CMYKColor(0.45, 0.36, 0.32, 0.38)
BLUE = CMYKColor(0.85, 0.35, 0.0, 0.0)
CYAN = CMYKColor(0.72, 0.03, 0.0, 0.0)
PALE_BLUE = CMYKColor(0.18, 0.06, 0.0, 0.0)
WHITE = CMYKColor(0.0, 0.0, 0.0, 0.0)
MUTED_WHITE = CMYKColor(0.12, 0.04, 0.0, 0.04)
INK = CMYKColor(0.85, 0.55, 0.30, 0.60)


def register_fonts():
    pdfmetrics.registerFont(TTFont("VA-Display", r"C:\Windows\Fonts\bahnschrift.ttf"))
    pdfmetrics.registerFont(TTFont("VA-Text", r"C:\Windows\Fonts\calibri.ttf"))
    pdfmetrics.registerFont(TTFont("VA-Text-Bold", r"C:\Windows\Fonts\calibrib.ttf"))
    pdfmetrics.registerFont(TTFont("VA-Text-Light", r"C:\Windows\Fonts\calibril.ttf"))


def draw_full_bleed_background(c, color):
    c.setFillColor(color)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)


def draw_brand(c, x, y, dark=False):
    c.setFont("VA-Display", 14)
    c.setFillColor(BLUE)
    c.drawString(x, y, "VA")
    c.setFont("VA-Text-Bold", 6.8)
    c.setFillColor(INK if dark else WHITE)
    c.drawString(x + 17 * mm, y + 1.1 * mm, "VA DIGITAL")


def draw_front(c):
    draw_full_bleed_background(c, BLUE)
    center = PAGE_W / 2
    c.setFillColor(WHITE)
    c.setFont("VA-Display", 27)
    c.drawCentredString(center, 34.2 * mm, "VA")
    c.setFont("VA-Text-Bold", 9.4)
    c.drawCentredString(center, 28.2 * mm, "VA DIGITAL")

    c.setStrokeColor(WHITE)
    c.setLineWidth(0.45)
    c.line(center - 15 * mm, 24.5 * mm, center + 15 * mm, 24.5 * mm)

    c.setFont("VA-Text", 7.0)
    c.setFillColor(MUTED_WHITE)
    c.drawCentredString(center, 19.8 * mm, "SOFTWARE  /  DATI  /  GIS")

    c.setFillColor(NAVY_DEEP)
    c.rect(0, 0, PAGE_W, 8.2 * mm, fill=1, stroke=0)
    c.setFillColor(CHARCOAL)
    c.rect(0, 8.2 * mm, PAGE_W, 1.8 * mm, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.rect(0, 10 * mm, PAGE_W, 1.1 * mm, fill=1, stroke=0)

    c.setFont("VA-Text", 6.5)
    c.setFillColor(WHITE)
    c.drawCentredString(center, 6.8 * mm, "va-digital.it")
    c.showPage()


def draw_back(c):
    draw_full_bleed_background(c, NAVY_DEEP)
    c.setFillColor(CYAN)
    c.rect(BLEED, 0, 1.4 * mm, PAGE_H, fill=1, stroke=0)

    panel = c.beginPath()
    panel.moveTo(31 * mm, 0)
    panel.lineTo(PAGE_W, 0)
    panel.lineTo(PAGE_W, PAGE_H)
    panel.lineTo(24 * mm, PAGE_H)
    panel.close()
    c.setFillColor(GRAPHITE)
    c.drawPath(panel, fill=1, stroke=0)

    left = BLEED + SAFE + 2 * mm
    right = PAGE_W - BLEED - SAFE
    c.setFillColor(WHITE)
    c.setFont("VA-Display", 18)
    c.drawString(left, 42 * mm, "VA")
    c.setFont("VA-Text-Bold", 7.2)
    c.drawString(left, 37.6 * mm, "VA DIGITAL")

    qr_size = 19 * mm
    qr_x = left
    qr_y = 14.5 * mm
    c.setFillColor(WHITE)
    c.rect(qr_x - 1.1 * mm, qr_y - 1.1 * mm, qr_size + 2.2 * mm, qr_size + 2.2 * mm, fill=1, stroke=0)
    c.drawImage(str(QR_IMAGE), qr_x, qr_y, qr_size, qr_size, preserveAspectRatio=True, mask="auto")
    c.setFont("VA-Text-Bold", 5.8)
    c.drawCentredString(qr_x + qr_size / 2, 10.4 * mm, "APRI IL BIGLIETTO")
    c.drawCentredString(qr_x + qr_size / 2, 7.5 * mm, "DIGITALE")

    info_x = 37 * mm
    c.setFillColor(WHITE)
    c.setFont("VA-Display", 15.2)
    c.drawString(info_x, 43.3 * mm, "Vincenzo Atturo")
    c.setFillColor(CYAN)
    c.setFont("VA-Text-Bold", 7.2)
    c.drawString(info_x, 38.5 * mm, "IT Manager")
    c.drawString(info_x, 34.8 * mm, "Digital Solutions Developer")

    c.setStrokeColor(CYAN)
    c.setLineWidth(0.45)
    c.line(info_x, 31.4 * mm, right, 31.4 * mm)

    rows = (
        ("T", "+39 334 991 6514"),
        ("E", "atturo.vincenzo@gmail.com"),
        ("W", "va-digital.it"),
    )
    y = 26.6 * mm
    for label, value in rows:
        c.setFillColor(CYAN)
        c.setFont("VA-Text-Bold", 6.2)
        c.drawString(info_x, y, label)
        c.setFillColor(WHITE)
        c.setFont("VA-Text", 6.9)
        c.drawString(info_x + 5.5 * mm, y, value)
        y -= 5.0 * mm

    c.setFillColor(MUTED_WHITE)
    c.setFont("VA-Text", 6.2)
    c.drawString(info_x, 8.6 * mm, "Software / Automazioni / Dati / GIS")
    c.showPage()


def add_print_boxes(source, output):
    reader = PdfReader(source)
    writer = PdfWriter()
    trim_box = ArrayObject(
        [
            FloatObject(BLEED),
            FloatObject(BLEED),
            FloatObject(BLEED + TRIM_W),
            FloatObject(BLEED + TRIM_H),
        ]
    )
    bleed_box = ArrayObject([FloatObject(0), FloatObject(0), FloatObject(PAGE_W), FloatObject(PAGE_H)])
    for page in reader.pages:
        page.trimbox = trim_box
        page.bleedbox = bleed_box
        writer.add_page(page)
    writer.add_metadata(
        {
            "/Title": "Biglietto da visita - Vincenzo Atturo",
            "/Author": "VA Digital",
            "/Subject": "Biglietto da visita fronte e retro, 85 x 55 mm con abbondanza da 3 mm",
        }
    )
    with output.open("wb") as stream:
        writer.write(stream)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    register_fonts()
    pdf = canvas.Canvas(str(SOURCE), pagesize=(PAGE_W, PAGE_H), pdfVersion=(1, 6))
    pdf.setTitle("Biglietto da visita - Vincenzo Atturo")
    pdf.setAuthor("VA Digital")
    draw_front(pdf)
    draw_back(pdf)
    pdf.save()
    add_print_boxes(SOURCE, OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
