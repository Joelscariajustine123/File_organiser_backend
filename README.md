# File Organiser

A web-based application to upload, organize, scan, extract, and transfer files efficiently. Users can create downloadable links with QR codes for easy file sharing across devices. Built with **Flask** (backend) and **React** (frontend).

---

## 🚀 Hosted Links

- **Frontend:** [https://fileorganizerfrontend.netlify.app/transfer](https://fileorganizerfrontend.netlify.app/transfer)  
- **Backend:** [https://file-organiser-backend.onrender.com](https://file-organiser-backend.onrender.com)

---

## 📂 Frontend Repository

- GitHub: [https://github.com/Joelscariajustine123/File_organiser_frontend.git](https://github.com/Joelscariajustine123/File_organiser_frontend.git)

---

## 🔧 Features

- **File Upload:** Upload multiple files at once with support for images, videos, documents, codes, and more.
- **Organize Files:** Automatically categorize files into folders such as `images`, `videos`, `documents`, `codes`, etc.
- **Extract ZIP:** Extract files from uploaded ZIP archives.
- **Scan Files:** Simulated virus/malware scan with clean/infected status.
- **File Transfer:** Generate downloadable ZIP links and QR codes to easily share files across devices.
- **Database Integration:** Tracks file transfers and metadata for better management.

---

## 🛠️ Tech Stack

**Backend:**  
- Python 3.12+  
- Flask 3.0  
- Flask-CORS  
- Flask-SQLAlchemy  
- QRCode  
- Pillow  

**Frontend:**  
- React.js  
- Tailwind CSS  
- React-QRCode  

---

## ⚡ Usage

1. **Frontend:** Visit the hosted link or run locally:
 ``` bash
 cd frontend
 npm install
 npm start
```
Backend: Clone the repository and run:

```bash
git clone https://github.com/Joelscariajustine123/File_organiser_backend.git
cd File_organiser_backend
pip install -r requirements.txt
python app.py
```

File Transfer:

Upload files via the frontend.

Select files to transfer.

Optional: provide an email for notifications.

Click Create Transfer to generate a ZIP download link and QR code.
```
📂 Directory Structure (Backend)
File_organiser_backend/
│
├─ app.py
├─ requirements.txt
├─ uploads/             # Uploaded and organized files
└─ database.db          # SQLite database for transfers
```
```
📂 Directory Structure (Frontend)
frontend/
│
├─ src/
│  ├─ pages/
│  │  └─ Transfer.jsx
│  ├─ components/
│  └─ App.jsx
├─ package.json
└─ vite.config.js
```
📌 Notes

The backend must run and be publicly accessible for the frontend to function correctly.

The QR code and download link will always point to the backend deployment URL.

Old file transfers should be cleaned regularly to save storage space.
