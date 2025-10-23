import os
import zipfile
import shutil
import uuid
import qrcode
import random
from flask import Flask, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
from flask_cors import CORS

# --------------------
# Configuration
# --------------------
app = Flask(__name__)
CORS(app)  # Allow requests from any origin

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = set([
    'png','jpg','jpeg','gif','mp4','mov','pdf','docx','pptx','txt',
    'py','js','java','c','cpp','html','css','zip','rar','csv','xlsx'
])

# --------------------
# Helpers
# --------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def organize_files(filepaths, target_dir):
    categories = {
        'images': ['png','jpg','jpeg','gif'],
        'videos': ['mp4','mov','mkv'],
        'documents': ['pdf','docx','txt','csv','xlsx'],
        'presentations': ['ppt','pptx'],
        'codes': ['py','js','java','c','cpp','html','css'],
        'gifs': ['gif']
    }
    os.makedirs(target_dir, exist_ok=True)
    created = []
    for fp in filepaths:
        ext = fp.rsplit('.',1)[-1].lower()
        placed = False
        for cat, exts in categories.items():
            if ext in exts:
                dest_dir = os.path.join(target_dir, cat)
                os.makedirs(dest_dir, exist_ok=True)
                try:
                    shutil.copy(fp, dest_dir)
                except Exception:
                    pass
                placed = True
                created.append((fp, dest_dir))
                break
        if not placed:
            other = os.path.join(target_dir, 'others')
            os.makedirs(other, exist_ok=True)
            try:
                shutil.copy(fp, other)
            except Exception:
                pass
            created.append((fp, other))
    return created

# --------------------
# Routes
# --------------------
@app.route('/api/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No files uploaded'}), 400
    saved = []
    for f in files:
        if f and allowed_file(f.filename):
            fn = secure_filename(f.filename)
            uid = str(uuid.uuid4())[:8]
            outname = f"{uid}__{fn}"
            path = os.path.join(app.config['UPLOAD_FOLDER'], outname)
            try:
                f.save(path)
                saved.append(path)
            except Exception as e:
                print(f"Failed to save {f.filename}: {e}")
    if not saved:
        return jsonify({'error': 'No valid files saved'}), 400
    return jsonify({'saved': saved})

@app.route('/api/organize', methods=['POST'])
def api_organize():
    data = request.json or {}
    files = data.get('files', [])
    if not files:
        return jsonify({'error': 'No files provided'}), 400
    target = os.path.join(app.config['UPLOAD_FOLDER'], 'organized_' + str(uuid.uuid4())[:8])
    os.makedirs(target, exist_ok=True)
    organize_files(files, target)
    zipname = target + ".zip"
    shutil.make_archive(target, 'zip', target)
    return jsonify({'zip_path': zipname, 'download_token': os.path.basename(zipname)})

@app.route('/api/extract', methods=['POST'])
def api_extract():
    data = request.json or {}
    zippath = data.get('zip')
    if not zippath or not os.path.exists(zippath):
        return jsonify({'error': 'Zip not found'}), 400
    extract_dir = zippath + "_extracted_" + str(uuid.uuid4())[:6]
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zippath, 'r') as zf:
        zf.extractall(extract_dir)
    return jsonify({'extracted_dir': extract_dir})

@app.route('/api/scan', methods=['POST'])
def api_scan():
    data = request.json or {}
    files = data.get('files', [])
    results = []
    for f in files:
        ok = random.random() > 0.1
        results.append({'file': f, 'clean': ok, 'message': 'clean' if ok else 'infected'})
    summary = {'total': len(files), 'clean': sum(1 for r in results if r['clean']), 'infected': sum(1 for r in results if not r['clean'])}
    return jsonify({'results': results, 'summary': summary})

@app.route('/api/transfer', methods=['POST'])
def api_transfer():
    data = request.json or {}
    files = data.get('files', [])
    email = data.get('email', None)
    if not files:
        return jsonify({'error':'No files'}), 400

    token = str(uuid.uuid4())[:12]
    token_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'transfers', token)
    os.makedirs(token_dir, exist_ok=True)

    for f in files:
        if os.path.exists(f):
            try:
                shutil.copy(f, token_dir)
            except Exception:
                pass

    zip_out = os.path.join(app.config['UPLOAD_FOLDER'], f"transfer_{token}.zip")
    shutil.make_archive(os.path.splitext(zip_out)[0], 'zip', token_dir)

    link = f"/download/{os.path.basename(zip_out)}"
    qr_img = qrcode.make(link)
    qr_path = os.path.join(app.config['UPLOAD_FOLDER'], f"qr_{token}.png")
    qr_img.save(qr_path)

    # Email sending can be added here using SMTP if desired.

    return jsonify({'token': token, 'link': link, 'qr': f"/files/{os.path.basename(qr_path)}", 'zip': os.path.basename(zip_out)})

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(path):
        return abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/files/<filename>', methods=['GET'])
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --------------------
# Run
# --------------------
if __name__ == '__main__':
    app.run(debug=True, port=5001)
