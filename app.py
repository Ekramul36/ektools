from flask import Flask, render_template, request, send_file, send_from_directory, redirect
from pypdf import PdfReader, PdfWriter
import fitz
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ──────────────────────────────────────────
# HOME
# ──────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")


# ──────────────────────────────────────────
# PDF TOOLS
# ──────────────────────────────────────────

@app.route("/unlock-pdf", methods=["GET", "POST"])
def unlock_pdf():
    if request.method == "POST":
        try:
            pdf = request.files.get("pdf")
            password = request.form.get("password", "")

            if not pdf or pdf.filename == "":
                return render_template("pdf.html", error="Please select a PDF file.")

            input_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
            output_path = os.path.join(OUTPUT_FOLDER, "Unlocked_" + pdf.filename)

            pdf.save(input_path)
            reader = PdfReader(input_path)

            if reader.is_encrypted:
                result = reader.decrypt(password)
                if result == 0:
                    return render_template("pdf.html", error="Wrong PDF Password!")

            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)

            with open(output_path, "wb") as output_file:
                writer.write(output_file)

            return send_file(output_path, as_attachment=True, download_name="Unlocked_" + pdf.filename)

        except Exception as e:
            return render_template("pdf.html", error=f"Error: {str(e)}")

    return render_template("pdf.html")


@app.route("/merge-pdf", methods=["GET", "POST"])
def merge_pdf():
    if request.method == "POST":
        try:
            pdf_files = request.files.getlist("pdfs")

            if len(pdf_files) < 2:
                return render_template("merge_pdf.html", error="Please select at least 2 PDF files.")

            writer = PdfWriter()
            for pdf in pdf_files:
                reader = PdfReader(pdf)
                for page in reader.pages:
                    writer.add_page(page)

            output_path = os.path.join(OUTPUT_FOLDER, "Merged_PDF.pdf")
            with open(output_path, "wb") as output_file:
                writer.write(output_file)

            return send_file(output_path, as_attachment=True, download_name="Merged_PDF.pdf")

        except Exception as e:
            return render_template("merge_pdf.html", error=f"{str(e)}")

    return render_template("merge_pdf.html")


@app.route("/split-pdf", methods=["GET", "POST"])
def split_pdf():
    if request.method == "POST":
        try:
            pdf = request.files.get("pdf")
            pages = request.form.get("pages", "").strip()

            if not pdf or pdf.filename == "":
                return render_template("split_pdf.html", error="Please select a PDF file.")

            reader = PdfReader(pdf)
            writer = PdfWriter()

            if "-" in pages:
                start, end = pages.split("-")
                start = int(start)
                end = int(end)
                if start < 1 or end > len(reader.pages) or start > end:
                    return render_template("split_pdf.html", error="Invalid page range.")
                for i in range(start - 1, end):
                    writer.add_page(reader.pages[i])
            else:
                page = int(pages)
                if page < 1 or page > len(reader.pages):
                    return render_template("split_pdf.html", error="Invalid page number.")
                writer.add_page(reader.pages[page - 1])

            output_path = os.path.join(OUTPUT_FOLDER, "Split_PDF.pdf")
            with open(output_path, "wb") as output_file:
                writer.write(output_file)

            return send_file(output_path, as_attachment=True, download_name="Split_PDF.pdf")

        except Exception as e:
            return render_template("split_pdf.html", error=f"{str(e)}")

    return render_template("split_pdf.html")


@app.route("/compress-pdf", methods=["GET", "POST"])
def compress_pdf():
    if request.method == "POST":
        pdf = request.files.get("pdf")

        if not pdf or pdf.filename == "":
            return render_template("compress_pdf.html", error="Please select a PDF.")

        input_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
        output_path = os.path.join(OUTPUT_FOLDER, "Compressed_" + pdf.filename)
        pdf.save(input_path)

        try:
            doc = fitz.open(input_path)
            doc.save(output_path, garbage=4, deflate=True, clean=True)
            doc.close()
            return send_file(output_path, as_attachment=True, download_name="Compressed_" + pdf.filename)

        except Exception as e:
            return render_template("compress_pdf.html", error=str(e))

    return render_template("compress_pdf.html")


# ──────────────────────────────────────────
# IMAGE TOOLS
# ──────────────────────────────────────────

@app.route("/image", methods=["GET", "POST"])
def image():
    if request.method == "POST":
        try:
            from PIL import Image as PILImage
            images = request.files.getlist("images")
            if not images or images[0].filename == "":
                return render_template("image.html", error="Please select image files.")
            pdf_images = []
            for img_file in images:
                img = PILImage.open(img_file).convert("RGB")
                pdf_images.append(img)
            output_path = os.path.join(OUTPUT_FOLDER, "Images_to_PDF.pdf")
            if len(pdf_images) == 1:
                pdf_images[0].save(output_path, "PDF")
            else:
                pdf_images[0].save(output_path, "PDF", save_all=True, append_images=pdf_images[1:])
            return send_file(output_path, as_attachment=True, download_name="Images_to_PDF.pdf")
        except Exception as e:
            return render_template("image.html", error=f"Error: {str(e)}")
    return render_template("image.html")


# ──────────────────────────────────────────
# CALCULATORS
# ──────────────────────────────────────────

@app.route("/calculators/age")
def age_calculator():
    return render_template("age.html")

@app.route("/calculators/bmi")
def bmi_calculator():
    return render_template("bmi.html")

@app.route("/calculators/gst")
def gst_calculator():
    return render_template("gst.html")

@app.route("/calculators/emi")
def emi_calculator():
    return render_template("emi.html")

@app.route("/calculators/percentage")
def percentage_calculator():
    return render_template("percentage.html")


# ──────────────────────────────────────────
# TEXT & OTHER TOOLS
# ──────────────────────────────────────────

@app.route("/tools/word-counter")
def word_counter():
    return render_template("word_counter.html")

@app.route("/tools/case-converter")
def case_converter():
    return render_template("case_converter.html")

@app.route("/tools/mb-converter")
def mb_converter():
    return render_template("mb_converter.html")

@app.route("/tools/lorem")
def lorem_generator():
    return render_template("lorem.html")

@app.route("/pdf-editor")
def pdf_editor():
    return render_template("pdf_editor.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")


# ──────────────────────────────────────────
# STATIC FILES
# ──────────────────────────────────────────

@app.route("/robots.txt")
def robots():
    return send_from_directory("static", "robots.txt")

@app.route("/sitemap.xml")
def sitemap():
    return send_from_directory("static", "sitemap.xml")

@app.route("/google1b7c2f73edcb5802.html")
def google_verification():
    return send_from_directory("static", "google1b7c2f73edcb5802.html")


import zipfile
import io

# ──────────────────────────────────────────
# PDF TO JPG
# ──────────────────────────────────────────

@app.route("/pdf-to-jpg", methods=["GET", "POST"])
def pdf_to_jpg():
    if request.method == "POST":
        try:
            pdf = request.files.get("pdf")
            quality = int(request.form.get("quality", 200))

            if not pdf or pdf.filename == "":
                return render_template("pdf_to_jpg.html", error="Please select a PDF file.")

            input_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
            pdf.save(input_path)

            doc = fitz.open(input_path)

            if doc.page_count == 1:
                page = doc[0]
                mat = fitz.Matrix(quality/72, quality/72)
                pix = page.get_pixmap(matrix=mat)
                output_path = os.path.join(OUTPUT_FOLDER, "page_1.jpg")
                pix.save(output_path)
                doc.close()
                return send_file(output_path, as_attachment=True, download_name="page_1.jpg")
            else:
                zip_path = os.path.join(OUTPUT_FOLDER, "PDF_to_JPG.zip")
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for i, page in enumerate(doc):
                        mat = fitz.Matrix(quality/72, quality/72)
                        pix = page.get_pixmap(matrix=mat)
                        img_path = os.path.join(OUTPUT_FOLDER, f"page_{i+1}.jpg")
                        pix.save(img_path)
                        zipf.write(img_path, f"page_{i+1}.jpg")
                doc.close()
                return send_file(zip_path, as_attachment=True, download_name="PDF_to_JPG.zip")

        except Exception as e:
            return render_template("pdf_to_jpg.html", error=f"Error: {str(e)}")

    return render_template("pdf_to_jpg.html")


# ──────────────────────────────────────────
# ROTATE PDF
# ──────────────────────────────────────────

@app.route("/rotate-pdf", methods=["GET", "POST"])
def rotate_pdf():
    if request.method == "POST":
        try:
            pdf = request.files.get("pdf")
            rotation = int(request.form.get("rotation", 90))

            if not pdf or pdf.filename == "":
                return render_template("rotate_pdf.html", error="Please select a PDF file.")

            reader = PdfReader(pdf)
            writer = PdfWriter()

            for page in reader.pages:
                page.rotate(rotation)
                writer.add_page(page)

            output_path = os.path.join(OUTPUT_FOLDER, "Rotated_PDF.pdf")
            with open(output_path, "wb") as f:
                writer.write(f)

            return send_file(output_path, as_attachment=True, download_name="Rotated_PDF.pdf")

        except Exception as e:
            return render_template("rotate_pdf.html", error=f"Error: {str(e)}")

    return render_template("rotate_pdf.html")


# ──────────────────────────────────────────
# DELETE PAGES
# ──────────────────────────────────────────

@app.route("/delete-pages", methods=["GET", "POST"])
def delete_pages():
    if request.method == "POST":
        try:
            pdf = request.files.get("pdf")
            pages_input = request.form.get("pages", "").strip()

            if not pdf or pdf.filename == "":
                return render_template("delete_pages.html", error="Please select a PDF file.")

            reader = PdfReader(pdf)

            pages_to_delete = set()
            for part in pages_input.split(","):
                part = part.strip()
                if "-" in part:
                    s, e = part.split("-")
                    for p in range(int(s), int(e)+1):
                        pages_to_delete.add(p)
                else:
                    pages_to_delete.add(int(part))

            writer = PdfWriter()
            for i, page in enumerate(reader.pages):
                if (i+1) not in pages_to_delete:
                    writer.add_page(page)

            if len(writer.pages) == 0:
                return render_template("delete_pages.html", error="Cannot delete all pages!")

            output_path = os.path.join(OUTPUT_FOLDER, "Deleted_Pages.pdf")
            with open(output_path, "wb") as f:
                writer.write(f)

            return send_file(output_path, as_attachment=True, download_name="Deleted_Pages.pdf")

        except Exception as e:
            return render_template("delete_pages.html", error=f"Error: {str(e)}")

    return render_template("delete_pages.html")


# ──────────────────────────────────────────
# PDF TO WORD
# ──────────────────────────────────────────

@app.route("/pdf-to-word", methods=["GET", "POST"])
def pdf_to_word():
    if request.method == "POST":
        try:
            from pdf2docx import Converter

            pdf = request.files.get("pdf")

            if not pdf or pdf.filename == "":
                return render_template("pdf_to_word.html", error="Please select a PDF file.")

            input_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
            output_path = os.path.join(OUTPUT_FOLDER, "Converted.docx")
            pdf.save(input_path)

            cv = Converter(input_path)
            cv.convert(output_path, start=0, end=None)
            cv.close()

            return send_file(output_path, as_attachment=True, download_name="Converted.docx")

        except Exception as e:
            return render_template("pdf_to_word.html", error=f"Error: {str(e)}")

    return render_template("pdf_to_word.html")


@app.route("/tools/qr-generator")
def qr_generator():
    return render_template("qr_generator.html")

@app.route("/tools/password-generator")
def password_generator():
    return render_template("password_generator.html")

@app.route("/tools/currency-converter")
def currency_converter():
    return render_template("currency_converter.html")

@app.route("/tools/unit-converter")
def unit_converter():
    return render_template("unit_converter.html")

@app.route("/calculators/sip")
def sip_calculator():
    return render_template("sip_calculator.html")

@app.route("/calculators/date")
def date_calculator():
    return render_template("date_calculator.html")


# ──────────────────────────────────────────
# IMAGE COMPRESS / RESIZE / CONVERT
# ──────────────────────────────────────────

@app.route("/image/compress", methods=["GET", "POST"])
def image_compress():
    if request.method == "POST":
        try:
            from PIL import Image as PILImage
            img_file = request.files.get("image")
            quality = int(request.form.get("quality", 80))
            if not img_file or img_file.filename == "":
                return render_template("image_compress.html", error="Please select an image.")
            img = PILImage.open(img_file)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            output_path = os.path.join(OUTPUT_FOLDER, "Compressed_" + img_file.filename.rsplit(".",1)[0] + ".jpg")
            img.save(output_path, "JPEG", quality=quality, optimize=True)
            return send_file(output_path, as_attachment=True, download_name="Compressed.jpg")
        except Exception as e:
            return render_template("image_compress.html", error=str(e))
    return render_template("image_compress.html")

@app.route("/image/resize", methods=["GET", "POST"])
def image_resize():
    if request.method == "POST":
        try:
            from PIL import Image as PILImage
            img_file = request.files.get("image")
            width = request.form.get("width")
            height = request.form.get("height")
            keep_ratio = request.form.get("keep_ratio")
            if not img_file or img_file.filename == "":
                return render_template("image_resize.html", error="Please select an image.")
            img = PILImage.open(img_file)
            w = int(width) if width else None
            h = int(height) if height else None
            if keep_ratio and w and not h:
                ratio = w / img.width
                h = int(img.height * ratio)
            elif keep_ratio and h and not w:
                ratio = h / img.height
                w = int(img.width * ratio)
            if w and h:
                img = img.resize((w, h), PILImage.LANCZOS)
            output_path = os.path.join(OUTPUT_FOLDER, "Resized.jpg")
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(output_path, "JPEG", quality=95)
            return send_file(output_path, as_attachment=True, download_name="Resized.jpg")
        except Exception as e:
            return render_template("image_resize.html", error=str(e))
    return render_template("image_resize.html")

@app.route("/image/convert", methods=["GET", "POST"])
def image_convert():
    if request.method == "POST":
        try:
            from PIL import Image as PILImage
            img_file = request.files.get("image")
            fmt = request.form.get("format", "jpg").upper()
            if not img_file or img_file.filename == "":
                return render_template("image_convert.html", error="Please select an image.")
            img = PILImage.open(img_file)
            if fmt == "JPG":
                fmt = "JPEG"
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
            ext = "jpg" if fmt == "JPEG" else fmt.lower()
            output_path = os.path.join(OUTPUT_FOLDER, f"Converted.{ext}")
            img.save(output_path, fmt)
            return send_file(output_path, as_attachment=True, download_name=f"Converted.{ext}")
        except Exception as e:
            return render_template("image_convert.html", error=str(e))
    return render_template("image_convert.html")


# ──────────────────────────────────────────
# WATERMARK PDF
# ──────────────────────────────────────────

@app.route("/watermark-pdf", methods=["GET", "POST"])
def watermark_pdf():
    if request.method == "POST":
        try:
            pdf = request.files.get("pdf")
            watermark = request.form.get("watermark", "CONFIDENTIAL")
            font_size = int(request.form.get("font_size", 50))
            opacity = float(request.form.get("opacity", 30)) / 100
            if not pdf or pdf.filename == "":
                return render_template("watermark_pdf.html", error="Please select a PDF.")
            input_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
            output_path = os.path.join(OUTPUT_FOLDER, "Watermarked.pdf")
            pdf.save(input_path)
            doc = fitz.open(input_path)
            for page in doc:
                page.insert_text(
                    (page.rect.width/2 - len(watermark)*font_size/4, page.rect.height/2),
                    watermark, fontsize=font_size,
                    color=(0.5, 0.5, 0.5), rotate=45
                )
            doc.save(output_path)
            doc.close()
            return send_file(output_path, as_attachment=True, download_name="Watermarked.pdf")
        except Exception as e:
            return render_template("watermark_pdf.html", error=str(e))
    return render_template("watermark_pdf.html")


# ──────────────────────────────────────────
# PROTECT PDF
# ──────────────────────────────────────────

@app.route("/protect-pdf", methods=["GET", "POST"])
def protect_pdf():
    if request.method == "POST":
        try:
            pdf = request.files.get("pdf")
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")
            if not pdf or pdf.filename == "":
                return render_template("protect_pdf.html", error="Please select a PDF.")
            if password != confirm:
                return render_template("protect_pdf.html", error="Passwords do not match!")
            if not password:
                return render_template("protect_pdf.html", error="Please enter a password.")
            reader = PdfReader(pdf)
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            writer.encrypt(password)
            output_path = os.path.join(OUTPUT_FOLDER, "Protected.pdf")
            with open(output_path, "wb") as f:
                writer.write(f)
            return send_file(output_path, as_attachment=True, download_name="Protected.pdf")
        except Exception as e:
            return render_template("protect_pdf.html", error=str(e))
    return render_template("protect_pdf.html")


@app.route("/tools/tip-calculator")
def tip_calculator():
    return render_template("tip_calculator.html")

@app.route("/calculators/calorie")
def calorie_calculator():
    return render_template("calorie_calculator.html")


# ──────────────────────────────────────────
# WORD TO PDF
# ──────────────────────────────────────────

@app.route("/word-to-pdf", methods=["GET", "POST"])
def word_to_pdf():
    if request.method == "POST":
        try:
            from docx2pdf import convert
            doc = request.files.get("file")
            if not doc or doc.filename == "":
                return render_template("word_to_pdf.html", error="Please select a Word file.")
            input_path = os.path.join(UPLOAD_FOLDER, doc.filename)
            output_path = os.path.join(OUTPUT_FOLDER, "Converted.pdf")
            doc.save(input_path)
            convert(input_path, output_path)
            return send_file(output_path, as_attachment=True, download_name="Converted.pdf")
        except Exception as e:
            return render_template("word_to_pdf.html", error=f"Error: {str(e)}")
    return render_template("word_to_pdf.html")


# ──────────────────────────────────────────
# EXCEL TO PDF
# ──────────────────────────────────────────

@app.route("/excel-to-pdf", methods=["GET", "POST"])
def excel_to_pdf():
    if request.method == "POST":
        try:
            import openpyxl
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
            from reportlab.lib import colors

            xl = request.files.get("file")
            if not xl or xl.filename == "":
                return render_template("excel_to_pdf.html", error="Please select an Excel file.")

            input_path = os.path.join(UPLOAD_FOLDER, xl.filename)
            output_path = os.path.join(OUTPUT_FOLDER, "Converted.pdf")
            xl.save(input_path)

            wb = openpyxl.load_workbook(input_path, data_only=True)
            ws = wb.active

            data = []
            for row in ws.iter_rows(values_only=True):
                data.append([str(cell) if cell is not None else "" for cell in row])

            if not data:
                return render_template("excel_to_pdf.html", error="Excel file is empty.")

            doc = SimpleDocTemplate(output_path, pagesize=landscape(A4))
            col_count = len(data[0])
            col_width = (landscape(A4)[0] - 40) / col_count if col_count > 0 else 100

            table = Table(data, colWidths=[col_width] * col_count)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9FAFB')]),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('PADDING', (0,0), (-1,-1), 4),
            ]))

            doc.build([table])
            return send_file(output_path, as_attachment=True, download_name="Converted.pdf")
        except Exception as e:
            return render_template("excel_to_pdf.html", error=f"Error: {str(e)}")
    return render_template("excel_to_pdf.html")


# ──────────────────────────────────────────
# PDF TO EXCEL
# ──────────────────────────────────────────

@app.route("/pdf-to-excel", methods=["GET", "POST"])
def pdf_to_excel():
    if request.method == "POST":
        try:
            import pdfplumber
            import openpyxl

            pdf = request.files.get("pdf")
            if not pdf or pdf.filename == "":
                return render_template("pdf_to_excel.html", error="Please select a PDF file.")

            input_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
            output_path = os.path.join(OUTPUT_FOLDER, "Converted.xlsx")
            pdf.save(input_path)

            wb = openpyxl.Workbook()
            first = True

            with pdfplumber.open(input_path) as pdf_doc:
                for i, page in enumerate(pdf_doc.pages):
                    tables = page.extract_tables()
                    if tables:
                        for t_idx, table in enumerate(tables):
                            if first:
                                ws = wb.active
                                ws.title = f"Page{i+1}"
                                first = False
                            else:
                                ws = wb.create_sheet(f"Page{i+1}_T{t_idx+1}")
                            for row in table:
                                ws.append([cell if cell else "" for cell in row])
                    else:
                        text = page.extract_text()
                        if text:
                            if first:
                                ws = wb.active
                                ws.title = f"Page{i+1}"
                                first = False
                            else:
                                ws = wb.create_sheet(f"Page{i+1}")
                            for line in text.split('\n'):
                                ws.append([line])

            if first:
                return render_template("pdf_to_excel.html", error="No content found in PDF.")

            wb.save(output_path)
            return send_file(output_path, as_attachment=True, download_name="Converted.xlsx")
        except Exception as e:
            return render_template("pdf_to_excel.html", error=f"Error: {str(e)}")
    return render_template("pdf_to_excel.html")


# ──────────────────────────────────────────
# OCR — IMAGE TO TEXT
# ──────────────────────────────────────────

@app.route("/ocr", methods=["GET", "POST"])
def ocr_tool():
    if request.method == "POST":
        try:
            import pytesseract
            from PIL import Image as PILImage

            img_file = request.files.get("image")
            if not img_file or img_file.filename == "":
                return render_template("ocr.html", error="Please select an image.")

            img = PILImage.open(img_file)
            text = pytesseract.image_to_string(img, lang='eng')

            if not text.strip():
                return render_template("ocr.html", error="No text found in image.", result="")

            return render_template("ocr.html", result=text)
        except Exception as e:
            return render_template("ocr.html", error=f"Error: {str(e)}")
    return render_template("ocr.html")


# ──────────────────────────────────────────
# BACKGROUND REMOVER
# ──────────────────────────────────────────

@app.route("/remove-background", methods=["GET", "POST"])
def remove_background():
    if request.method == "POST":
        try:
            2qJ63NFCUXfz8q5Sn7j2JDGP
            from PIL import Image as PILImage
            import io

            img_file = request.files.get("image")
            if not img_file or img_file.filename == "":
                return render_template("remove_background.html", error="Please select an image.")

            input_bytes = img_file.read()
            output_bytes = remove(input_bytes)

            output_path = os.path.join(OUTPUT_FOLDER, "No_Background.png")
            with open(output_path, "wb") as f:
                f.write(output_bytes)

            return send_file(output_path, as_attachment=True, download_name="No_Background.png")
        except Exception as e:
            return render_template("remove_background.html", error=f"Error: {str(e)}")
    return render_template("remove_background.html")


# ──────────────────────────────────────────
# PASSPORT PHOTO MAKER
# ──────────────────────────────────────────

@app.route("/passport-photo", methods=["GET", "POST"])
def passport_photo():
    if request.method == "POST":
        try:
            from PIL import Image as PILImage
            import base64
            import io as BytesIO_io

            img_file    = request.files.get("image")
            size_preset = request.form.get("size", "35x45")
            bg_color    = request.form.get("bg_color", "#ffffff")
            copies      = int(request.form.get("copies", 8))

            if not img_file or img_file.filename == "":
                return render_template("passport_photo.html", error="Please select an image.")

            sizes = {
                "35x45": (413, 531),   # India passport (300 dpi)
                "51x51": (600, 600),   # US passport
                "35x35": (413, 413),   # UK passport
                "40x60": (472, 709),   # Schengen visa
            }
            w, h = sizes.get(size_preset, (413, 531))

            img = PILImage.open(img_file).convert("RGBA")

            # Center crop to target ratio
            img_ratio    = img.width / img.height
            target_ratio = w / h
            if img_ratio > target_ratio:
                new_h = h
                new_w = int(h * img_ratio)
            else:
                new_w = w
                new_h = int(w / img_ratio)

            img  = img.resize((new_w, new_h), PILImage.LANCZOS)
            left = (new_w - w) // 2
            top  = (new_h - h) // 2
            img  = img.crop((left, top, left + w, top + h))

            # Background color
            try:
                bg = PILImage.new("RGB", (w, h), bg_color)
            except Exception:
                bg = PILImage.new("RGB", (w, h), "white")

            if img.mode == "RGBA":
                bg.paste(img, mask=img.split()[3])
            else:
                bg.paste(img)

            # Build A4 print sheet @ 300 DPI
            dpi    = 300
            a4_w   = int(8.27 * dpi)
            a4_h   = int(11.69 * dpi)
            sheet  = PILImage.new("RGB", (a4_w, a4_h), "white")
            margin = int(0.3 * dpi)
            gap    = int(0.1 * dpi)

            placed = 0
            x_pos  = margin
            y_pos  = margin

            while placed < copies:
                if x_pos + w > a4_w - margin:
                    x_pos  = margin
                    y_pos += h + gap
                if y_pos + h > a4_h - margin:
                    break
                sheet.paste(bg, (x_pos, y_pos))
                x_pos += w + gap
                placed += 1

            # Save full-res file for download
            output_path = os.path.join(OUTPUT_FOLDER, "Passport_Photo.jpg")
            sheet.save(output_path, "JPEG", quality=95, dpi=(dpi, dpi))

            # Smaller preview (base64)
            preview = sheet.copy()
            preview.thumbnail((800, 1000), PILImage.LANCZOS)
            buf = BytesIO_io.BytesIO()
            preview.save(buf, format="JPEG", quality=75)
            img_b64 = base64.b64encode(buf.getvalue()).decode()

            return render_template("passport_photo.html",
                                   preview_image=img_b64,
                                   download_ready=True,
                                   copies=placed,
                                   size=size_preset)

        except Exception as e:
            return render_template("passport_photo.html", error=f"Error: {str(e)}")

    return render_template("passport_photo.html")


@app.route("/passport-photo/download")
def passport_photo_download():
    output_path = os.path.join(OUTPUT_FOLDER, "Passport_Photo.jpg")
    if os.path.exists(output_path):
        return send_file(output_path, as_attachment=True, download_name="Passport_Photo.jpg")
    return redirect("/passport-photo")


# ──────────────────────────────────────────
# INVOICE GENERATOR
# ──────────────────────────────────────────

@app.route("/invoice-generator", methods=["GET", "POST"])
def invoice_generator():
    if request.method == "POST":
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
            from reportlab.lib.units import mm
            from datetime import datetime

            from_name    = request.form.get("from_name", "")
            from_address = request.form.get("from_address", "")
            from_gst     = request.form.get("from_gst", "")
            to_name      = request.form.get("to_name", "")
            to_address   = request.form.get("to_address", "")
            invoice_no   = request.form.get("invoice_no", "INV-001")
            invoice_date = request.form.get("invoice_date", datetime.now().strftime("%d/%m/%Y"))
            due_date     = request.form.get("due_date", "")
            gst_rate     = float(request.form.get("gst_rate", 18))
            notes        = request.form.get("notes", "Thank you for your business!")

            items_desc = request.form.getlist("item_desc[]")
            items_qty  = request.form.getlist("item_qty[]")
            items_rate = request.form.getlist("item_rate[]")

            output_path = os.path.join(OUTPUT_FOLDER, "Invoice.pdf")
            doc = SimpleDocTemplate(output_path, pagesize=A4,
                                    leftMargin=15*mm, rightMargin=15*mm,
                                    topMargin=15*mm, bottomMargin=15*mm)

            styles = getSampleStyleSheet()
            blue  = colors.HexColor('#2563EB')
            light = colors.HexColor('#F9FAFB')

            elements = []

            header_data = [[
                Paragraph(f"<font size='20' color='#2563EB'><b>INVOICE</b></font>", styles['Normal']),
                Paragraph(f"<font size='9' color='#6B7280'>Invoice No: <b>{invoice_no}</b><br/>Date: {invoice_date}" +
                          (f"<br/>Due: {due_date}" if due_date else "") + "</font>", styles['Normal'])
            ]]
            header_table = Table(header_data, colWidths=[90*mm, 80*mm])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 8*mm))

            ft_data = [[
                Paragraph(f"<font size='8' color='#6B7280'>FROM</font><br/>"
                          f"<font size='10'><b>{from_name}</b></font><br/>"
                          f"<font size='8' color='#6B7280'>{from_address.replace(chr(10),'<br/>')}</font>" +
                          (f"<br/><font size='8' color='#6B7280'>GST: {from_gst}</font>" if from_gst else ""),
                          styles['Normal']),
                Paragraph(f"<font size='8' color='#6B7280'>BILL TO</font><br/>"
                          f"<font size='10'><b>{to_name}</b></font><br/>"
                          f"<font size='8' color='#6B7280'>{to_address.replace(chr(10),'<br/>')}</font>",
                          styles['Normal'])
            ]]
            ft_table = Table(ft_data, colWidths=[85*mm, 85*mm])
            ft_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BACKGROUND', (0,0), (-1,-1), light),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
                ('PADDING', (0,0), (-1,-1), 8),
                ('LINEAFTER', (0,0), (0,-1), 0.5, colors.HexColor('#E5E7EB')),
            ]))
            elements.append(ft_table)
            elements.append(Spacer(1, 8*mm))

            item_header = ['#', 'Description', 'Qty', 'Rate (₹)', 'Amount (₹)']
            item_rows = [item_header]
            subtotal = 0

            for i, (desc, qty, rate) in enumerate(zip(items_desc, items_qty, items_rate)):
                if desc.strip():
                    q = float(qty) if qty else 1
                    r = float(rate) if rate else 0
                    amount = q * r
                    subtotal += amount
                    item_rows.append([str(i+1), desc, f"{q:.0f}", f"₹{r:,.2f}", f"₹{amount:,.2f}"])

            gst_amount = subtotal * gst_rate / 100
            total = subtotal + gst_amount

            item_rows.append(['', '', '', 'Subtotal', f'₹{subtotal:,.2f}'])
            item_rows.append(['', '', '', f'GST ({gst_rate:.0f}%)', f'₹{gst_amount:,.2f}'])
            item_rows.append(['', '', '', Paragraph('<b>TOTAL</b>', styles['Normal']),
                              Paragraph(f'<b>₹{total:,.2f}</b>', styles['Normal'])])

            col_widths = [10*mm, 80*mm, 15*mm, 30*mm, 35*mm]
            items_table = Table(item_rows, colWidths=col_widths)
            last = len(item_rows) - 1
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), blue),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('ROWBACKGROUNDS', (0,1), (-1, last-3), [colors.white, light]),
                ('GRID', (0,0), (-1, last-3), 0.3, colors.HexColor('#E5E7EB')),
                ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('PADDING', (0,0), (-1,-1), 5),
                ('LINEABOVE', (3, last-2), (-1, last), 0.5, colors.HexColor('#E5E7EB')),
                ('BACKGROUND', (3, last), (-1, last), colors.HexColor('#EFF6FF')),
                ('FONTNAME', (3, last), (-1, last), 'Helvetica-Bold'),
            ]))
            elements.append(items_table)
            elements.append(Spacer(1, 8*mm))

            if notes:
                elements.append(Paragraph(
                    f"<font size='8' color='#6B7280'><b>Notes:</b> {notes}</font>",
                    styles['Normal']))

            doc.build(elements)
            return send_file(output_path, as_attachment=True,
                             download_name=f"Invoice_{invoice_no}.pdf")

        except Exception as e:
            return render_template("invoice_generator.html", error=f"Error: {str(e)}")
    return render_template("invoice_generator.html")


if __name__ == "__main__":
    app.run(debug=True)
