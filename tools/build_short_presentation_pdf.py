from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "commercial-kit" / "09_presentazione_breve_va_digital.pdf"
QR = ROOT / "assets" / "vincenzo-atturo-qr.png"

PAGE = (338.67 * mm, 190.5 * mm)
W, H = landscape((PAGE[1], PAGE[0])) if PAGE[0] < PAGE[1] else PAGE

NAVY = HexColor("#0B2C47")
INK = HexColor("#111820")
BLUE = HexColor("#168FF0")
CYAN = HexColor("#45C9F5")
PALE = HexColor("#EAF4FC")
LIGHT = HexColor("#F4F7FA")
MID = HexColor("#60748A")


def register_fonts():
    candidates = [
        ("Bahnschrift", Path(r"C:\Windows\Fonts\bahnschrift.ttf")),
        ("Arial", Path(r"C:\Windows\Fonts\arial.ttf")),
        ("Arial-Bold", Path(r"C:\Windows\Fonts\arialbd.ttf")),
    ]
    for name, path in candidates:
        if path.exists():
            pdfmetrics.registerFont(TTFont(name, str(path)))


register_fonts()
DISPLAY = "Bahnschrift" if "Bahnschrift" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
BODY = "Arial" if "Arial" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
BODY_BOLD = "Arial-Bold" if "Arial-Bold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"


def para(c, text, x, y, width, size=15, color=INK, font=BODY, leading=None, align=TA_LEFT):
    style = ParagraphStyle(
        "p", fontName=font, fontSize=size, leading=leading or size * 1.28,
        textColor=color, alignment=align, spaceAfter=0,
    )
    p = Paragraph(text, style)
    _, ph = p.wrap(width, H)
    p.drawOn(c, x, y - ph)
    return ph


def brand(c, dark=False):
    fg = white if dark else NAVY
    c.setFont(DISPLAY, 16)
    c.setFillColor(BLUE)
    c.drawString(18 * mm, H - 17 * mm, "VA")
    c.setFont(BODY_BOLD, 8.5)
    c.setFillColor(fg)
    c.drawString(31 * mm, H - 16.4 * mm, "VA DIGITAL")
    c.setStrokeColor(BLUE)
    c.setLineWidth(1.2)
    c.line(18 * mm, H - 21 * mm, W - 18 * mm, H - 21 * mm)


def footer(c, number, dark=False):
    c.setFillColor(white if dark else MID)
    c.setFont(BODY, 7.5)
    c.drawString(18 * mm, 9 * mm, "va-digital.it")
    c.drawRightString(W - 18 * mm, 9 * mm, f"{number:02d}")


def pill(c, text, x, y, width, fill=PALE, color=NAVY):
    c.setFillColor(fill)
    c.roundRect(x, y, width, 11 * mm, 2.5 * mm, fill=1, stroke=0)
    c.setFillColor(color)
    c.setFont(BODY_BOLD, 10)
    c.drawCentredString(x + width / 2, y + 3.7 * mm, text)


def page_cover(c):
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(BLUE)
    c.rect(W - 12 * mm, 0, 12 * mm, H, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.rect(W - 12 * mm, H * .62, 12 * mm, H * .12, fill=1, stroke=0)
    brand(c, True)
    para(c, "Strumenti digitali costruiti<br/>intorno al lavoro reale", 18 * mm, H - 48 * mm, 190 * mm, 30, white, DISPLAY, 34)
    para(c, "Software su misura, automazioni, dashboard e GIS per rendere processi e dati più semplici da usare.", 18 * mm, H - 116 * mm, 185 * mm, 14, HexColor("#D7E6F2"), BODY, 20)
    c.setFillColor(white)
    c.setFont(BODY_BOLD, 12)
    c.drawString(18 * mm, 28 * mm, "Vincenzo Atturo")
    c.setFont(BODY, 9.5)
    c.setFillColor(HexColor("#BFD4E4"))
    c.drawString(18 * mm, 22 * mm, "IT Manager & Digital Solutions Developer")
    footer(c, 1, True)
    c.showPage()


def page_problems(c):
    brand(c)
    para(c, "Da dove parte il lavoro", 18 * mm, H - 39 * mm, 200 * mm, 25, INK, DISPLAY, 29)
    para(c, "Il punto di partenza non è la tecnologia, ma un ostacolo operativo riconoscibile.", 18 * mm, H - 57 * mm, 250 * mm, 12, MID)
    cards = [
        ("Attività ripetitive", "Report, controlli e passaggi manuali che assorbono tempo."),
        ("Dati dispersi", "File, email e archivi che non restituiscono una visione unica."),
        ("Territorio difficile da leggere", "Mappe, particelle e informazioni tecniche non collegate."),
    ]
    card_w = 94 * mm
    gap = 8 * mm
    for i, (title, body) in enumerate(cards):
        x = 18 * mm + i * (card_w + gap)
        y = 39 * mm
        c.setFillColor(LIGHT if i != 1 else PALE)
        c.roundRect(x, y, card_w, 75 * mm, 2.5 * mm, fill=1, stroke=0)
        c.setFillColor(BLUE)
        c.rect(x, y + 68 * mm, card_w, 7 * mm, fill=1, stroke=0)
        para(c, title, x + 7 * mm, y + 58 * mm, card_w - 14 * mm, 15, NAVY, BODY_BOLD, 18)
        para(c, body, x + 7 * mm, y + 38 * mm, card_w - 14 * mm, 10.5, MID, BODY, 15)
    footer(c, 2)
    c.showPage()


def page_solutions(c):
    brand(c)
    para(c, "Quattro aree di intervento", 18 * mm, H - 39 * mm, 240 * mm, 25, INK, DISPLAY, 29)
    items = [
        ("01", "Software su misura", "Applicazioni web e strumenti operativi dedicati."),
        ("02", "Automazioni", "Workflow, script Python, report e integrazioni."),
        ("03", "Dati e dashboard", "KPI, database, processi ETL e viste operative."),
        ("04", "GIS e territorio", "WebGIS, cartografia e dati territoriali interrogabili."),
    ]
    for i, (num, title, body) in enumerate(items):
        col = i % 2
        row = i // 2
        x = 18 * mm + col * 155 * mm
        y = H - 79 * mm - row * 51 * mm
        c.setFillColor(PALE if i in (0, 3) else LIGHT)
        c.roundRect(x, y - 34 * mm, 145 * mm, 39 * mm, 2.5 * mm, fill=1, stroke=0)
        c.setFillColor(BLUE)
        c.setFont(DISPLAY, 19)
        c.drawString(x + 7 * mm, y - 8 * mm, num)
        para(c, title, x + 28 * mm, y, 105 * mm, 14, NAVY, BODY_BOLD, 17)
        para(c, body, x + 28 * mm, y - 14 * mm, 105 * mm, 9.8, MID, BODY, 13)
    footer(c, 3)
    c.showPage()


def page_method(c):
    brand(c)
    para(c, "Un percorso chiaro e verificabile", 18 * mm, H - 39 * mm, 250 * mm, 25, INK, DISPLAY, 29)
    steps = [
        ("1", "Analisi", "Processo, persone, dati e vincoli."),
        ("2", "Perimetro", "Obiettivi e prima versione verificabile."),
        ("3", "Realizzazione", "Sviluppo per fasi con confronti intermedi."),
        ("4", "Consegna", "Collaudo, documentazione e assistenza concordata."),
    ]
    y = 80 * mm
    c.setStrokeColor(HexColor("#B8D6EA"))
    c.setLineWidth(3)
    c.line(35 * mm, y + 14 * mm, W - 35 * mm, y + 14 * mm)
    for i, (num, title, body) in enumerate(steps):
        x = 35 * mm + i * 89 * mm
        c.setFillColor(BLUE)
        c.circle(x, y + 14 * mm, 8 * mm, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont(BODY_BOLD, 12)
        c.drawCentredString(x, y + 10.8 * mm, num)
        para(c, title, x - 30 * mm, y - 2 * mm, 60 * mm, 13, NAVY, BODY_BOLD, 16, TA_CENTER)
        para(c, body, x - 34 * mm, y - 21 * mm, 68 * mm, 9.5, MID, BODY, 13, TA_CENTER)
    para(c, "Ogni fase lascia un riferimento condiviso: requisiti, tempi, responsabilità, avanzamento e collaudo.", 40 * mm, 31 * mm, W - 80 * mm, 11.5, NAVY, BODY_BOLD, 16, TA_CENTER)
    footer(c, 4)
    c.showPage()


def page_contact(c):
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    brand(c, True)
    para(c, "Parliamo del processo<br/>che vuoi migliorare", 18 * mm, H - 48 * mm, 190 * mm, 29, white, DISPLAY, 34)
    para(c, "Un primo confronto serve a chiarire obiettivo, priorità e prossimo passo.", 18 * mm, H - 112 * mm, 170 * mm, 13, HexColor("#D7E6F2"), BODY, 18)
    pill(c, "+39 334 991 6514", 18 * mm, 30 * mm, 61 * mm, BLUE, white)
    pill(c, "atturo.vincenzo@gmail.com", 84 * mm, 30 * mm, 88 * mm, PALE, NAVY)
    pill(c, "va-digital.it", 177 * mm, 30 * mm, 54 * mm, PALE, NAVY)
    if QR.exists():
        c.setFillColor(white)
        c.roundRect(W - 84 * mm, 30 * mm, 57 * mm, 57 * mm, 3 * mm, fill=1, stroke=0)
        c.drawImage(str(QR), W - 78 * mm, 36 * mm, 45 * mm, 45 * mm, preserveAspectRatio=True, mask="auto")
        para(c, "Apri il biglietto digitale", W - 91 * mm, 25 * mm, 70 * mm, 8.5, HexColor("#C8DCEB"), BODY, 11, TA_CENTER)
    footer(c, 5, True)
    c.showPage()


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W, H), pageCompression=1)
    c.setTitle("VA Digital presentazione breve")
    c.setAuthor("Vincenzo Atturo - VA Digital")
    page_cover(c)
    page_problems(c)
    page_solutions(c)
    page_method(c)
    page_contact(c)
    c.save()
    print(OUT)


if __name__ == "__main__":
    main()
