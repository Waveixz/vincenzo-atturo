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
OUTPUT = OUTPUT_DIR / "biglietto-da-visita-vincenzo-atturo-verticale-stampa.pdf"
SOURCE = TMP_DIR / "business-card-vertical-source.pdf"
QR_IMAGE = ROOT / "assets" / "vincenzo-atturo-qr.png"

PAGE_W = 61 * mm
PAGE_H = 91 * mm
BLEED = 3 * mm
TRIM_W = 55 * mm
TRIM_H = 85 * mm
SAFE = 4 * mm

CHARCOAL = CMYKColor(0.72, 0.58, 0.46, 0.72)
CHARCOAL_DEEP = CMYKColor(0.82, 0.66, 0.50, 0.82)
PANEL = CMYKColor(0.38, 0.30, 0.27, 0.28)
BLUE = CMYKColor(0.86, 0.34, 0.0, 0.0)
CYAN = CMYKColor(0.72, 0.03, 0.0, 0.0)
WHITE = CMYKColor(0.0, 0.0, 0.0, 0.0)
SOFT_WHITE = CMYKColor(0.06, 0.03, 0.0, 0.03)


def register_fonts():
    pdfmetrics.registerFont(TTFont("VA-Display", r"C:\Windows\Fonts\bahnschrift.ttf"))
    pdfmetrics.registerFont(TTFont("VA-Text", r"C:\Windows\Fonts\calibri.ttf"))
    pdfmetrics.registerFont(TTFont("VA-Text-Bold", r"C:\Windows\Fonts\calibrib.ttf"))


def fill_page(c, color):
    c.setFillColor(color)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)


def draw_front(c):
    fill_page(c, BLUE)

    c.setFillColor(CHARCOAL_DEEP)
    c.rect(0, 0, PAGE_W, 13 * mm, fill=1, stroke=0)
    c.setFillColor(CHARCOAL)
    c.rect(0, 13 * mm, PAGE_W, 2.2 * mm, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.rect(0, 15.2 * mm, PAGE_W, 1.2 * mm, fill=1, stroke=0)

    center = PAGE_W / 2
    c.setFillColor(WHITE)
    c.setFont("VA-Display", 31)
    c.drawCentredString(center, 50.5 * mm, "VA")
    c.setFont("VA-Text-Bold", 10)
    c.drawCentredString(center, 44.8 * mm, "VA DIGITAL")

    c.setStrokeColor(WHITE)
    c.setLineWidth(0.45)
    c.line(center - 11 * mm, 41.2 * mm, center + 11 * mm, 41.2 * mm)

    c.setFont("VA-Text", 7.3)
    c.setFillColor(SOFT_WHITE)
    c.drawCentredString(center, 36.3 * mm, "SOFTWARE  /  DATI  /  GIS")

    c.setFont("VA-Text", 6.5)
    c.setFillColor(WHITE)
    c.drawCentredString(center, 7.5 * mm, "va-digital.it")
    c.showPage()


def draw_contact_row(c, label, value, y):
    c.setFillColor(CYAN)
    c.setFont("VA-Text-Bold", 6.4)
    c.drawString(20 * mm, y, label)
    c.setFillColor(WHITE)
    c.setFont("VA-Text", 7.2)
    c.drawString(25.2 * mm, y, value)


def draw_back(c):
    fill_page(c, CHARCOAL_DEEP)

    c.setFillColor(CYAN)
    c.rect(BLEED, 0, 1.6 * mm, PAGE_H, fill=1, stroke=0)

    panel = c.beginPath()
    panel.moveTo(15 * mm, 0)
    panel.lineTo(PAGE_W, 0)
    panel.lineTo(PAGE_W, PAGE_H)
    panel.lineTo(9 * mm, PAGE_H)
    panel.close()
    c.setFillColor(PANEL)
    c.drawPath(panel, fill=1, stroke=0)

    c.setFillColor(WHITE)
    c.setFont("VA-Display", 14.6)
    c.drawString(19 * mm, 72.5 * mm, "Vincenzo Atturo")
    c.setFillColor(CYAN)
    c.setFont("VA-Text-Bold", 7.4)
    c.drawString(19 * mm, 67.5 * mm, "IT Manager")
    c.drawString(19 * mm, 63.8 * mm, "Digital Solutions Developer")

    c.setStrokeColor(CYAN)
    c.setLineWidth(0.5)
    c.line(19 * mm, 59.8 * mm, PAGE_W - BLEED - SAFE, 59.8 * mm)

    draw_contact_row(c, "T", "+39 334 991 6514", 54.0 * mm)
    draw_contact_row(c, "E", "atturo.vincenzo@gmail.com", 48.7 * mm)
    draw_contact_row(c, "W", "va-digital.it", 43.4 * mm)

    c.setFillColor(SOFT_WHITE)
    c.setFont("VA-Text", 6.6)
    c.drawString(20 * mm, 37.0 * mm, "Software su misura / Automazioni")
    c.drawString(20 * mm, 32.9 * mm, "Dashboard / Dati / GIS")

    qr_size = 19.5 * mm
    qr_x = PAGE_W - BLEED - SAFE - qr_size - 1.2 * mm
    qr_y = 9.5 * mm
    c.setFillColor(WHITE)
    c.rect(qr_x - 1.2 * mm, qr_y - 1.2 * mm, qr_size + 2.4 * mm, qr_size + 2.4 * mm, fill=1, stroke=0)
    c.drawImage(str(QR_IMAGE), qr_x, qr_y, qr_size, qr_size, preserveAspectRatio=True, mask="auto")

    c.setFillColor(WHITE)
    c.setFont("VA-Text-Bold", 7.0)
    c.drawString(20 * mm, 25.3 * mm, "APRI IL")
    c.drawString(20 * mm, 21.4 * mm, "BIGLIETTO")
    c.drawString(20 * mm, 17.5 * mm, "DIGITALE")
    c.setFillColor(CYAN)
    c.rect(20 * mm, 13.7 * mm, 8.5 * mm, 0.9 * mm, fill=1, stroke=0)
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
            "/Title": "Biglietto verticale - Vincenzo Atturo",
            "/Author": "VA Digital",
            "/Subject": "Biglietto verticale fronte e retro, 55 x 85 mm con abbondanza da 3 mm",
        }
    )
    with output.open("wb") as stream:
        writer.write(stream)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    register_fonts()
    pdf = canvas.Canvas(str(SOURCE), pagesize=(PAGE_W, PAGE_H), pdfVersion=(1, 6))
    pdf.setTitle("Biglietto verticale - Vincenzo Atturo")
    pdf.setAuthor("VA Digital")
    draw_front(pdf)
    draw_back(pdf)
    pdf.save()
    add_print_boxes(SOURCE, OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
