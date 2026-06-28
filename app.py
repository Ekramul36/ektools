from flask import Flask, render_template, request, send_file, send_from_directory
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


# ──────────────────────────────────────────
# OTHER PAGES
# ──────────────────────────────────────────

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


# ──────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)