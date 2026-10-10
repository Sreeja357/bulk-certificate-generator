import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

# Professional navy-blue and gold theme
NAVY = colors.HexColor("#10234F")
GOLD = colors.HexColor("#C8952E")
PALE_GOLD = colors.HexColor("#F5EBD4")
DARK_TEXT = colors.HexColor("#18233A")
MUTED_TEXT = colors.HexColor("#5E687A")

def generate_certificate(
    certificate_id,
    recipient_name,
    certificate_title,
    event_name,
    certificate_date,
):
    """
    Generate a professional PDF certificate and return its absolute file path.

    Args:
        certificate_id: Unique ID for this certificate.
        recipient_name: Name printed on the certificate.
        certificate_title: Certificate heading/type, e.g. "Certificate of Completion".
        event_name: Course, workshop, or event name.
        certificate_date: Date string, preferably YYYY-MM-DD.

    Returns:
        Absolute path to the generated PDF.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_directory = os.path.join(
        project_root, "certificates", "generated"
    )
    os.makedirs(output_directory, exist_ok=True)

    output_path = os.path.abspath(
        os.path.join(output_directory, f"certificate_{certificate_id}.pdf")
    )

    page_width, page_height = landscape(A4)
    pdf = canvas.Canvas(output_path, pagesize=(page_width, page_height))

    # Background
    pdf.setFillColor(colors.white)
    pdf.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    # Soft inset panel
    margin = 28
    pdf.setFillColor(colors.HexColor("#FFFEFA"))
    pdf.roundRect(
        margin, margin,
        page_width - 2 * margin, page_height - 2 * margin,
        8, fill=1, stroke=0
    )

    # Double border
    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(3)
    pdf.rect(18, 18, page_width - 36, page_height - 36, fill=0, stroke=1)

    pdf.setStrokeColor(NAVY)
    pdf.setLineWidth(1.5)
    pdf.rect(29, 29, page_width - 58, page_height - 58, fill=0, stroke=1)

    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(0.8)
    pdf.rect(38, 38, page_width - 76, page_height - 76, fill=0, stroke=1)

    # Decorative corner accents
    corner = 58
    for x, y, sx, sy in [
        (43, page_height - 43, 1, -1),
        (page_width - 43, page_height - 43, -1, -1),
        (43, 43, 1, 1),
        (page_width - 43, 43, -1, 1),
    ]:
        pdf.setStrokeColor(NAVY)
        pdf.setLineWidth(3)
        pdf.line(x, y, x + sx * corner, y)
        pdf.line(x, y, x, y + sy * corner)
        pdf.setStrokeColor(GOLD)
        pdf.setLineWidth(1.8)
        pdf.line(x + sx * 8, y + sy * 8, x + sx * (corner + 7), y + sy * 8)
        pdf.line(x + sx * 8, y + sy * 8, x + sx * 8, y + sy * (corner + 7))

    center_x = page_width / 2

    # Main heading
    pdf.setFillColor(NAVY)
    pdf.setFont("Times-Bold", 31)
    pdf.drawCentredString(
        center_x, page_height - 112, "Certificate of Completion"
    )

    # Gold divider with a small diamond ornament
    divider_y = page_height - 133
    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(1.4)
    pdf.line(center_x - 170, divider_y, center_x - 16, divider_y)
    pdf.line(center_x + 16, divider_y, center_x + 170, divider_y)
    pdf.setFillColor(GOLD)
    pdf.saveState()
    pdf.translate(center_x, divider_y)
    path = pdf.beginPath()
    path.moveTo(0, 7)
    path.lineTo(7, 0)
    path.lineTo(0, -7)
    path.lineTo(-7, 0)
    path.close()
    pdf.drawPath(path, fill=1, stroke=0)
    pdf.restoreState()

    # Introductory line
    pdf.setFillColor(MUTED_TEXT)
    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(center_x, page_height - 165, "This certifies that")

    # Recipient name (fit long names into available width)
    name = str(recipient_name).strip()
    max_name_width = page_width - 150
    font_size = 27
    while font_size > 16 and pdf.stringWidth(name, "Times-BoldItalic", font_size) > max_name_width:
        font_size -= 1

    pdf.setFillColor(NAVY)
    pdf.setFont("Times-BoldItalic", font_size)
    pdf.drawCentredString(center_x, page_height - 207, name)

    # Underline below recipient
    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(1)
    pdf.line(center_x - 190, page_height - 218, center_x + 190, page_height - 218)

    pdf.setFillColor(DARK_TEXT)
    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(
        center_x, page_height - 244, "has successfully completed"
    )

    # Event/course name
    event = str(event_name).strip()
    event_font_size = 21
    max_event_width = page_width - 130
    while event_font_size > 13 and pdf.stringWidth(event, "Helvetica-Bold", event_font_size) > max_event_width:
        event_font_size -= 1

    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", event_font_size)
    pdf.drawCentredString(center_x, page_height - 278, event)

    # Certificate title / description
    title = str(certificate_title).strip()
    title_font_size = 12
    while title_font_size > 9 and pdf.stringWidth(title, "Helvetica", title_font_size) > page_width - 160:
        title_font_size -= 1
    pdf.setFillColor(MUTED_TEXT)
    pdf.setFont("Helvetica", title_font_size)
    pdf.drawCentredString(center_x, page_height - 301, title)

    # Date and certificate ID
    date_text = str(certificate_date).strip()
    try:
        date_text = datetime.strptime(date_text, "%Y-%m-%d").strftime("%B %d, %Y")
    except ValueError:
        pass

    details_y = 79
    pdf.setFillColor(DARK_TEXT)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(76, details_y, f"Date: {date_text}")
    pdf.drawRightString(page_width - 76, details_y, f"Certificate ID: {certificate_id}")

    # Signature placeholders (no fictitious signature)
    signature_y = 111
    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(0.8)
    pdf.line(100, signature_y, 245, signature_y)
    pdf.line(page_width - 245, signature_y, page_width - 100, signature_y)
    pdf.setFillColor(MUTED_TEXT)
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(172.5, signature_y - 14, "Authorized Signature")
    pdf.drawCentredString(page_width - 172.5, signature_y - 14, "Organization / Institution")

    pdf.showPage()
    pdf.save()
    return output_path
