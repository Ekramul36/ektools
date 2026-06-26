from flask import Flask, render_template, request, send_file
from pypdf import PdfReader, PdfWriter
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/unlock-pdf", methods=["GET", "POST"])
def unlock_pdf():

    if request.method == "POST":

        try:
            pdf = request.files.get("pdf")
            password = request.form.get("password", "")

            if not pdf or pdf.filename == "":
                return render_template(
                    "pdf.html",
                    error="Please select a PDF file."
                )

            input_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
            output_path = os.path.join(
                OUTPUT_FOLDER,
                "Unlocked_" + pdf.filename
            )

            pdf.save(input_path)

            reader = PdfReader(input_path)

            if reader.is_encrypted:
                result = reader.decrypt(password)

                if result == 0:
                    return render_template(
                        "pdf.html",
                        error="❌ Wrong PDF Password!"
                    )

            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            with open(output_path, "wb") as output_file:
                writer.write(output_file)

            return send_file(
                output_path,
                as_attachment=True,
                download_name="Unlocked_" + pdf.filename
            )

        except Exception as e:
            return render_template(
                "pdf.html",
                error=f"❌ Error: {str(e)}"
            )

    return render_template("pdf.html")


@app.route("/image")
def image():
    return render_template("image.html")


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)