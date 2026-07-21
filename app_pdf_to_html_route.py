"""
PDF to HTML Converter — Flask Blueprint
Converts PDF pages to a single HTML file using PyMuPDF's built-in
page.get_text("html"), which already handles fonts, text positions,
and embeds images as base64 — no custom layout-preservation engine needed.

IMPORTANT — verified against installed PyMuPDF 1.28.0:
get_text("html") in current versions does NOT include "position:absolute"
on <p> tags or "position:relative" on the page <div> (older PyMuPDF docs
show these, but the current library omits them). Without adding that CSS
back ourselves, text renders left-aligned top-to-bottom instead of in its
original position. The _PAGE_CSS block below patches this. Confirmed by
testing locally — don't remove it.

Requires: PyMuPDF (already used by the PDF Editor tool, no new dependency)

Register in app.py:
    from app_pdf_to_html_route import pdf_to_html_bp
    app.register_blueprint(pdf_to_html_bp)
"""

import io
import re

import fitz  # PyMuPDF
from flask import Blueprint, render_template, request, send_file, jsonify

pdf_to_html_bp = Blueprint('pdf_to_html', __name__)

MAX_PAGES = 200          # same safety valve used by the PDF Editor tool for Render free-tier RAM
MAX_FILE_SIZE_MB = 30

_PAGE_CSS = """
.ekz-pdf-page { position: relative; margin: 24px auto; background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.15); overflow: hidden; }
.ekz-pdf-page p { position: absolute; white-space: pre; margin: 0; padding: 0; }
"""


@pdf_to_html_bp.route('/pdf-to-html')
def pdf_to_html_page():
    return render_template('pdf_to_html.html')


@pdf_to_html_bp.route('/pdf-to-html/convert', methods=['POST'])
def pdf_to_html_convert():
    file = request.files.get('file')

    if not file or file.filename == '':
        return jsonify({'error': 'No file uploaded'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are supported'}), 400

    file.seek(0, io.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)
    if size_mb > MAX_FILE_SIZE_MB:
        return jsonify({'error': f'File exceeds {MAX_FILE_SIZE_MB}MB limit'}), 400

    try:
        pdf_bytes = file.read()
        doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    except Exception:
        return jsonify({'error': 'Could not open PDF — file may be corrupted or password-protected'}), 400

    if doc.page_count == 0:
        doc.close()
        return jsonify({'error': 'PDF has no pages'}), 400

    if doc.page_count > MAX_PAGES:
        doc.close()
        return jsonify({'error': f'PDF exceeds the {MAX_PAGES} page limit on the free tier'}), 400

    page_blocks = []
    try:
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            raw_html = page.get_text("html")

            # get_text("html") always emits id="page0" regardless of actual
            # page number — duplicate ids across pages are invalid HTML, so
            # make each one unique and pull the width/height it computed
            # into our own wrapper div.
            width_match = re.search(r'width:([\d.]+)pt', raw_html)
            height_match = re.search(r'height:([\d.]+)pt', raw_html)
            width = width_match.group(1) if width_match else '595'
            height = height_match.group(1) if height_match else '842'

            inner = re.sub(r'^<div id="page0"[^>]*>', '', raw_html.strip())
            inner = re.sub(r'</div>\s*$', '', inner)

            page_blocks.append(
                f'<div class="ekz-pdf-page" id="ekz-page-{page_num + 1}" '
                f'data-page="{page_num + 1}" style="width:{width}pt;height:{height}pt">'
                f'{inner}</div>'
            )
    except Exception as e:
        doc.close()
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500
    finally:
        doc.close()

    base_name = file.filename.rsplit('.', 1)[0]
    full_html = _wrap_html(base_name, page_blocks)

    out_buffer = io.BytesIO(full_html.encode('utf-8'))
    return send_file(
        out_buffer,
        mimetype='text/html',
        as_attachment=True,
        download_name=f'{base_name}.html'
    )


def _wrap_html(title, page_blocks):
    pages_joined = '\n'.join(page_blocks)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
body {{ margin: 0; padding: 20px 0; background: #f1f5f9; font-family: Arial, sans-serif; }}
{_PAGE_CSS}
</style>
</head>
<body>
{pages_joined}
</body>
</html>'''