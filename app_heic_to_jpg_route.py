"""
HEIC to JPG Converter — Flask Blueprint
Converts HEIC/HEIF images (iPhone photos) to JPG.

Fully in-memory (no disk writes) — same pattern as the Compress Image tool,
to stay safe within Render free tier's 512MB RAM.

New pip dependency required:
    pip install pillow-heif
    (add "pillow-heif==0.18.0" or latest to requirements.txt)

Register in app.py:
    from app_heic_to_jpg_route import heic_to_jpg_bp
    app.register_blueprint(heic_to_jpg_bp)
"""

import io
import zipfile

from flask import Blueprint, render_template, request, send_file, jsonify
from PIL import Image, ImageOps
import pillow_heif

# Registers pillow-heif as a Pillow plugin so Image.open() understands .heic/.heif
pillow_heif.register_heif_opener()

heic_to_jpg_bp = Blueprint('heic_to_jpg', __name__)

MAX_FILES = 20
MAX_FILE_SIZE_MB = 25
ALLOWED_EXTENSIONS = {'.heic', '.heif'}


def _allowed_file(filename):
    if '.' not in filename:
        return False
    return '.' + filename.rsplit('.', 1)[-1].lower() in ALLOWED_EXTENSIONS


@heic_to_jpg_bp.route('/heic-to-jpg')
def heic_to_jpg_page():
    return render_template('heic_to_jpg.html')


@heic_to_jpg_bp.route('/heic-to-jpg/convert', methods=['POST'])
def heic_to_jpg_convert():
    files = request.files.getlist('files')

    if not files or files[0].filename == '':
        return jsonify({'error': 'No files uploaded'}), 400

    if len(files) > MAX_FILES:
        return jsonify({'error': f'Max {MAX_FILES} files per batch'}), 400

    try:
        quality = int(request.form.get('quality', 90))
        quality = max(10, min(100, quality))
    except (TypeError, ValueError):
        quality = 90

    converted = []  # list of (filename, bytes)

    for f in files:
        if not f or f.filename == '':
            continue
        if not _allowed_file(f.filename):
            return jsonify({'error': f'{f.filename} is not a HEIC/HEIF file'}), 400

        f.stream.seek(0, io.SEEK_END)
        size_mb = f.stream.tell() / (1024 * 1024)
        f.stream.seek(0)
        if size_mb > MAX_FILE_SIZE_MB:
            return jsonify({'error': f'{f.filename} exceeds {MAX_FILE_SIZE_MB}MB limit'}), 400

        try:
            img = Image.open(f.stream)
            # iPhone HEIC photos carry EXIF orientation — without this,
            # portrait photos come out sideways after conversion
            img = ImageOps.exif_transpose(img)
            img = img.convert('RGB')  # drop alpha channel, HEIC-specific color info

            out_buffer = io.BytesIO()
            img.save(out_buffer, format='JPEG', quality=quality, optimize=True)
            out_buffer.seek(0)

            base_name = f.filename.rsplit('.', 1)[0]
            converted.append((f'{base_name}.jpg', out_buffer.read()))
        except Exception as e:
            return jsonify({'error': f'Failed to convert {f.filename}: {str(e)}'}), 400

    if not converted:
        return jsonify({'error': 'No valid HEIC/HEIF files found'}), 400

    if len(converted) == 1:
        name, data = converted[0]
        return send_file(
            io.BytesIO(data),
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=name
        )

    # Multiple files → zip them
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, data in converted:
            zf.writestr(name, data)
    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='converted_images.zip'
    )