from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import fitz  # PyMuPDF for PDF image extraction

app = Flask(__name__)
CORS(app)

# Use absolute paths outside the Next.js project structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))  # Go up two levels from src/backend

# Create data folders at project root level
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "pdf_uploads")
EXTRACT_FOLDER = os.path.join(PROJECT_ROOT, "extracted_images")
REPORT_FILE = os.path.join(PROJECT_ROOT, "report.json")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACT_FOLDER, exist_ok=True)

print(f"Upload folder: {UPLOAD_FOLDER}")
print(f"Extract folder: {EXTRACT_FOLDER}")

# Serve extracted images
@app.route("/images/<filename>")
def serve_image(filename):
    return send_from_directory(EXTRACT_FOLDER, filename)

# Upload PDF and extract images
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Clear previous extracted images
    for f in os.listdir(EXTRACT_FOLDER):
        os.remove(os.path.join(EXTRACT_FOLDER, f))

    pdf = fitz.open(filepath)
    report = []

    for page_num, page in enumerate(pdf, start=1):
        images = page.get_images(full=True)
        page_info = {"page": page_num, "images": []}

        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = pdf.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            filename = f"{os.path.splitext(file.filename)[0]}_page{page_num}_img{img_index}.{ext}"
            img_path = os.path.join(EXTRACT_FOLDER, filename)

            with open(img_path, "wb") as f:
                f.write(image_bytes)

            page_info["images"].append({
                "filename": filename,
                "url": f"http://localhost:8000/images/{filename}",
                "clickable_link_found": False
            })

        report.append(page_info)

    pdf.close()

    # Save report.json
    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=4)

    return jsonify(report)

# Optional: download JSON report
@app.route("/download_report")
def download_report():
    return send_from_directory(PROJECT_ROOT, "report.json", as_attachment=True)

@app.route("/")
def home():
    return "Flask server is running!"

if __name__ == "__main__":
    app.run(port=8000, debug=True)