"""
EkZapp PDF Editor — "Apply changes" backend route.

Paste this into app.py (or import it and register the blueprint).
Requires: pip install pymupdf --break-system-packages

This route receives:
  - pdfBase64: the original uploaded PDF, base64-encoded
  - scale:     the render scale used in the browser (1 CSS px == 1/scale PDF points)
  - edits:     a list of edit objects collected from the editor's overlays

...and returns the flattened PDF as a file download.

NOTE on "forms": these are drawn as flattened marks (typed text / an X for a
checked box / a filled dot for a selected radio), not real interactive
AcroForm fields. Building actual fillable form fields is a separate,
larger feature (needs page.add_widget / fitz.Widget) — flagged in the
FAQ as "coming next" rather than promised here.
"""

import base64
import io
import re

import fitz  # PyMuPDF
from flask import Blueprint, request, send_file, abort

pdf_editor_bp = Blueprint("pdf_editor", __name__)

# ---------------------------------------------------------------------------
# Font mapping: the browser only ever sends a handful of font-family values
# from the editor's dropdown, so a small lookup table is enough — PyMuPDF's
# base14 fonts don't include "Inter", so everything maps to the closest
# built-in equivalent.
# ---------------------------------------------------------------------------
FONT_MAP = {
    "inter": "helv",
    "sans-serif": "helv",
    "georgia": "tiro",
    "serif": "tiro",
    "times new roman": "tiro",
    "courier new": "cour",
    "monospace": "cour",
}


def map_font(font_family_css):
    if not font_family_css:
        return "helv"
    first = font_family_css.split(",")[0].strip().strip("'").strip('"').lower()
    return FONT_MAP.get(first, FONT_MAP.get(font_family_css.lower(), "helv"))


def parse_color(css_color, fallback=(0, 0, 0)):
    """Accepts '#RRGGBB' or 'rgb(r, g, b)' and returns an (r,g,b) tuple in 0..1."""
    if not css_color:
        return fallback
    css_color = css_color.strip()
    if css_color.startswith("#"):
        hexs = css_color.lstrip("#")
        if len(hexs) == 3:
            hexs = "".join(c * 2 for c in hexs)
        try:
            r = int(hexs[0:2], 16) / 255
            g = int(hexs[2:4], 16) / 255
            b = int(hexs[4:6], 16) / 255
            return (r, g, b)
        except (ValueError, IndexError):
            return fallback
    m = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", css_color)
    if m:
        r, g, b = (int(m.group(i)) / 255 for i in (1, 2, 3))
        return (r, g, b)
    return fallback


def px_to_pt(px, scale):
    """Editor renders at `scale` CSS-px-per-PDF-point, so this just divides it back out."""
    return px / scale


@pdf_editor_bp.route("/api/apply-pdf-edits", methods=["POST"])
def apply_pdf_edits():
    data = request.get_json(silent=True)
    if not data or "pdfBase64" not in data or "edits" not in data:
        abort(400, "Missing pdfBase64 or edits in request body.")

    scale = float(data.get("scale") or 1.4)
    edits = data["edits"]

    try:
        pdf_bytes = base64.b64decode(data["pdfBase64"])
    except Exception:
        abort(400, "pdfBase64 could not be decoded.")

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        abort(400, "Could not open the uploaded file as a PDF.")

    # Cheap safety valve for the free tier — mirrors the other tools' page limits.
    MAX_PAGES = 200
    if doc.page_count > MAX_PAGES:
        doc.close()
        abort(400, f"This free tier supports PDFs up to {MAX_PAGES} pages.")

    for edit in edits:
        page_index = edit.get("pageIndex", 0)
        if page_index < 0 or page_index >= doc.page_count:
            continue
        page = doc[page_index]

        etype = edit.get("type")

        if etype == "text":
            x = px_to_pt(edit.get("xPx", 0), scale)
            y = px_to_pt(edit.get("yPx", 0), scale)
            font_size = px_to_pt(edit.get("fontSizePx", 16), scale)
            color = parse_color(edit.get("color"))
            fontname = map_font(edit.get("fontFamily"))
            baseline_y = y + font_size * 0.82  # approximate ascent offset
            page.insert_text(
                (x, baseline_y),
                edit.get("text", ""),
                fontsize=max(font_size, 1),
                fontname=fontname,
                color=color,
            )

        elif etype == "text-replace":
            # This is the "click existing text to edit" path: whiteout the
            # ORIGINAL detected text box first (erasing the old glyphs),
            # then — if the user left new text in place — draw it at the
            # (possibly dragged-to) new position. If the box was cleared
            # entirely, this just erases the original line.
            ox = px_to_pt(edit.get("origXPx", 0), scale)
            oy = px_to_pt(edit.get("origYPx", 0), scale)
            ow = px_to_pt(edit.get("origWPx", 0), scale)
            oh = px_to_pt(edit.get("origHPx", 0), scale)
            orig_rect = fitz.Rect(ox, oy, ox + ow, oy + oh)
            cover_color = parse_color(edit.get("bgColor"), fallback=(1, 1, 1))
            page.draw_rect(orig_rect, color=cover_color, fill=cover_color, width=0)

            new_text = edit.get("text", "")
            if new_text:
                x = px_to_pt(edit.get("xPx", 0), scale)
                y = px_to_pt(edit.get("yPx", 0), scale)
                font_size = px_to_pt(edit.get("fontSizePx", 16), scale)
                color = parse_color(edit.get("color"))
                fontname = map_font(edit.get("fontFamily"))
                baseline_y = y + font_size * 0.82
                page.insert_text(
                    (x, baseline_y),
                    new_text,
                    fontsize=max(font_size, 1),
                    fontname=fontname,
                    color=color,
                )

        elif etype in ("image", "signature"):
            data_url = edit.get("dataUrl", "")
            if "," not in data_url:
                continue
            img_bytes = base64.b64decode(data_url.split(",", 1)[1])
            x = px_to_pt(edit.get("xPx", 0), scale)
            y = px_to_pt(edit.get("yPx", 0), scale)
            w = px_to_pt(edit.get("wPx", 0), scale)
            h = px_to_pt(edit.get("hPx", 0), scale)
            rect = fitz.Rect(x, y, x + w, y + h)
            try:
                page.insert_image(rect, stream=img_bytes)
            except Exception:
                continue  # skip a malformed image rather than failing the whole export

        elif etype == "whiteout":
            x = px_to_pt(edit.get("xPx", 0), scale)
            y = px_to_pt(edit.get("yPx", 0), scale)
            w = px_to_pt(edit.get("wPx", 0), scale)
            h = px_to_pt(edit.get("hPx", 0), scale)
            rect = fitz.Rect(x, y, x + w, y + h)
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), width=0)

        elif etype == "shape":
            x = px_to_pt(edit.get("xPx", 0), scale)
            y = px_to_pt(edit.get("yPx", 0), scale)
            w = px_to_pt(edit.get("wPx", 0), scale)
            h = px_to_pt(edit.get("hPx", 0), scale)
            color = parse_color(edit.get("color"))
            stroke = max(px_to_pt(edit.get("stroke", 2), scale), 0.5)
            shape_type = edit.get("shapeType", "rectangle")
            rect = fitz.Rect(x, y, x + w, y + h)

            if shape_type == "rectangle":
                page.draw_rect(rect, color=color, width=stroke)
            elif shape_type == "ellipse":
                page.draw_oval(rect, color=color, width=stroke)
            elif shape_type == "line":
                mid_y = y + h / 2
                page.draw_line((x, mid_y), (x + w, mid_y), color=color, width=stroke)
            elif shape_type == "arrow":
                mid_y = y + h / 2
                shaft_end = (x + w - 10, mid_y)
                page.draw_line((x, mid_y), shaft_end, color=color, width=stroke)
                page.draw_polyline(
                    [(x + w - 14, mid_y - 8), (x + w, mid_y), (x + w - 14, mid_y + 8)],
                    color=color,
                    fill=color,
                    closePath=True,
                )

        elif etype == "formfield":
            x = px_to_pt(edit.get("xPx", 0), scale)
            y = px_to_pt(edit.get("yPx", 0), scale)
            w = px_to_pt(edit.get("wPx", 0), scale)
            h = px_to_pt(edit.get("hPx", 0), scale)
            kind = edit.get("fieldKind")

            if kind == "text":
                value = edit.get("value", "")
                if value:
                    font_size = max(h * 0.6, 8)
                    page.insert_text(
                        (x + 2, y + h * 0.72),
                        value,
                        fontsize=font_size,
                        fontname="helv",
                        color=(0, 0, 0),
                    )
            elif kind == "checkbox":
                rect = fitz.Rect(x, y, x + w, y + h)
                page.draw_rect(rect, color=(0, 0, 0), width=1)
                if edit.get("value") is True:
                    page.draw_line((x + 2, y + 2), (x + w - 2, y + h - 2), color=(0, 0, 0), width=1.5)
                    page.draw_line((x + w - 2, y + 2), (x + 2, y + h - 2), color=(0, 0, 0), width=1.5)
            elif kind == "radio":
                center = (x + w / 2, y + h / 2)
                radius = min(w, h) / 2
                page.draw_circle(center, radius, color=(0, 0, 0), width=1)
                if edit.get("value") is True:
                    page.draw_circle(center, radius * 0.5, color=(0, 0, 0), fill=(0, 0, 0), width=0)

    output_buffer = io.BytesIO()
    doc.save(output_buffer)
    doc.close()
    output_buffer.seek(0)

    return send_file(
        output_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="edited.pdf",
    )


# ---------------------------------------------------------------------------
# Registration example — add this to your main app.py:
#
#   from app_pdf_editor_route import pdf_editor_bp
#   app.register_blueprint(pdf_editor_bp)
#
# ---------------------------------------------------------------------------