#!/usr/bin/env python3
"""
Meesho Label Enhancer
---------------------
Reads the original Meesho shipping label PDF, extracts the customer name from
each page, and generates a new PDF with a personalized thank-you message and
a QR code linking to the Meesho store below each label page.

Usage:
    python3 add_message_to_label.py <input_pdf> [output_pdf]

If output_pdf is not specified, it defaults to <input_pdf_name>_with_message.pdf
"""

import sys
import os
import io
import tempfile

import pymupdf  # PyMuPDF
import qrcode
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from PyPDF2 import PdfReader, PdfWriter


# ── Configuration ──────────────────────────────────────────────────────────
MEESHO_STORE_URL = "https://www.meesho.com/jumjumenterprise"

# Page dimensions (A4 in points: 595 x 842)
PAGE_WIDTH, PAGE_HEIGHT = A4  # 595.27 × 841.89

# Message template – $User is replaced with the customer name
MESSAGE_TEMPLATE = (
    "Dear $User,\n"
    "Thank you for shopping with us! We are so happy to have you as our customer.\n"
    "If you loved your purchase, please follow our store on Meesho! "
    "Scan the QR code below to stay updated on our latest collections.\n"
    "Keep visiting and supporting!"
)


def extract_customer_name(page):
    """
    Extract the customer name from a Meesho label page.
    The customer name is in the first text block, second line
    (first line is 'Customer Address').
    """
    blocks = page.get_text("blocks")
    if not blocks:
        return "Customer"

    first_block_text = blocks[0][4].strip()
    lines = first_block_text.split('\n')

    # First line is "Customer Address", second line is the name
    if len(lines) > 1:
        return lines[1].strip()
    return lines[0].strip()


def get_content_bottom(page):
    """
    Find the bottom-most y coordinate of content on the page.
    Returns the y position (from top of page) where content ends.
    """
    blocks = page.get_text("blocks")
    max_y = 0
    for block in blocks:
        # block[3] is y1 (bottom of block, from top)
        if block[3] > max_y:
            max_y = block[3]
    
    # Also check for image blocks
    image_list = page.get_images()
    # Add a small buffer
    return max_y + 10


def generate_qr_code(url, size=120):
    """Generate a QR code image for the given URL."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img


def create_message_overlay(customer_name, page_width, page_height, content_bottom_y, qr_image_path):
    """
    Create a PDF overlay with the personalized message and QR code.
    Returns the overlay as bytes.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_width, page_height))

    # ── Position calculation ───────────────────────────────────────────
    # ReportLab uses bottom-left origin, so y increases upward
    # content_bottom_y is from the top of the page
    start_y_from_bottom = page_height - content_bottom_y

    # Margins
    left_margin = 25
    right_margin = page_width - 25
    usable_width = right_margin - left_margin

    # ── Draw a subtle separator line ───────────────────────────────────
    c.setStrokeColor(HexColor("#CCCCCC"))
    c.setLineWidth(0.5)
    separator_y = start_y_from_bottom - 2
    c.line(left_margin, separator_y, right_margin, separator_y)

    # ── Personalized message ───────────────────────────────────────────
    message = MESSAGE_TEMPLATE.replace("$User", customer_name)

    # QR code dimensions
    qr_size = 80  # points
    qr_x = right_margin - qr_size - 5
    
    # Text area (left of QR code)
    text_right = qr_x - 15
    text_width = text_right - left_margin

    # Split message into paragraphs
    paragraphs = message.split('\n')

    current_y = separator_y - 18

    # "Dear $User," - bold greeting
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(HexColor("#333333"))
    c.drawString(left_margin, current_y, paragraphs[0])
    current_y -= 14

    # Rest of the message in regular font
    c.setFont("Helvetica", 7.5)
    c.setFillColor(HexColor("#444444"))
    
    for para in paragraphs[1:]:
        # Word-wrap each paragraph
        words = para.split()
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if c.stringWidth(test_line, "Helvetica", 7.5) < text_width:
                line = test_line
            else:
                c.drawString(left_margin, current_y, line)
                current_y -= 11
                line = word
        if line:
            c.drawString(left_margin, current_y, line)
            current_y -= 11
        current_y -= 3  # paragraph spacing

    # ── QR Code ────────────────────────────────────────────────────────
    qr_y = separator_y - qr_size - 10
    c.drawImage(qr_image_path, qr_x, qr_y, width=qr_size, height=qr_size)

    # Label under QR code
    c.setFont("Helvetica", 5.5)
    c.setFillColor(HexColor("#666666"))
    qr_label = "Scan to follow our store"
    label_width = c.stringWidth(qr_label, "Helvetica", 5.5)
    c.drawString(qr_x + (qr_size - label_width) / 2, qr_y - 9, qr_label)

    c.save()
    buf.seek(0)
    return buf


def process_pdf(input_path, output_path=None):
    """
    Main function: reads the Meesho label PDF, adds personalized message
    and QR code below each label, and saves the result.
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_with_message{ext}"

    # Generate QR code image and save to temp file
    qr_img = generate_qr_code(MEESHO_STORE_URL)
    qr_temp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    qr_img.save(qr_temp.name)
    qr_temp_path = qr_temp.name
    qr_temp.close()

    try:
        # Open with PyMuPDF to extract customer names and content positions
        mu_doc = pymupdf.open(input_path)
        page_info = []
        for page in mu_doc:
            name = extract_customer_name(page)
            bottom = get_content_bottom(page)
            page_info.append((name, bottom))
        mu_doc.close()

        print(f"Found {len(page_info)} pages:")
        for i, (name, bottom) in enumerate(page_info):
            print(f"  Page {i+1}: {name} (content ends at y={bottom:.1f})")

        # Read original PDF
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            customer_name, content_bottom = page_info[i]

            # Create overlay with message + QR
            overlay_buf = create_message_overlay(
                customer_name,
                float(page.mediabox.width),
                float(page.mediabox.height),
                content_bottom,
                qr_temp_path,
            )

            # Merge overlay onto the original page
            overlay_reader = PdfReader(overlay_buf)
            overlay_page = overlay_reader.pages[0]

            page.merge_page(overlay_page)
            writer.add_page(page)

        # Write output
        with open(output_path, "wb") as f:
            writer.write(f)

        print(f"\n✅ Output saved to: {output_path}")

    finally:
        # Clean up temp QR image
        os.unlink(qr_temp_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default: look for the Meesho label PDF in the current directory
        pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf') and 'Sub_Order' in f]
        if pdf_files:
            input_pdf = pdf_files[0]
        else:
            print("Usage: python3 add_message_to_label.py <input.pdf> [output.pdf]")
            sys.exit(1)
    else:
        input_pdf = sys.argv[1]

    output_pdf = sys.argv[2] if len(sys.argv) > 2 else None
    process_pdf(input_pdf, output_pdf)
