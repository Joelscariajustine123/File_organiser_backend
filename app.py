import os
import zipfile
import shutil
import uuid
import qrcode
import random
from flask import Flask, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# --------------------
# Configuration
# --------------------
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transfers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

ALLOWED_EXTENSIONS = set([
    'png','jpg','jpeg','gif','mp4','mov','pdf','docx','pptx','txt',
    'py','js','java','c','cpp','html','css','zip','rar','csv','xlsx'
])

# --------------------
# Database Models
# --------------------
class Transfer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(32), unique=True, nullable=False)
    zip_filename = db.Column(db.String(256), nullable=False)
    qr_filename = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

db.create_all()

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

    # Save transfer info in database
    transfer = Transfer(
        token=token,
        zip_filename=os.path.basename(zip_out),
        qr_filename=os.path.basename(qr_path),
        email=email
    )
    db.session.add(transfer)
    db.session.commit()

    return jsonify({
        'token': token,
        'link': link,
        'qr': f"/files/{os.path.basename(qr_path)}",
        'zip': os.path.basename(zip_out)
    })

@app.route('/api/transfers', methods=['GET'])
def list_transfers():
    transfers = Transfer.query.order_by(Transfer.created_at.desc()).all()
    data = [{
        'token': t.token,
        'zip': t.zip_filename,
        'qr': t.qr_filename,
        'email': t.email,
        'created_at': t.created_at.isoformat()
    } for t in transfers]
    return jsonify(data)

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
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
