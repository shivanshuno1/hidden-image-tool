from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import fitz  # PyMuPDF
from PIL import Image
from pyzbar.pyzbar import decode
import easyocr
import re
import io

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "pdf_uploads")
EXTRACT_FOLDER = os.path.join(BASE_DIR, "extracted_images")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACT_FOLDER, exist_ok=True)

BACKEND_URL = "https://hidden-backend-1.onrender.com"

# Initialize EasyOCR reader once
reader = easyocr.Reader(['en'], gpu=False)

# --------------------------
# Helper functions
# --------------------------
def extract_qr_codes(img_path):
    """Detect QR codes in the image."""
    image = Image.open(img_path)
    qr_results = decode(image)
    qr_links = []
    for qr in qr_results:
        content = qr.data.decode("utf-8").strip()
        if content:
            qr_links.append({
                "type": "qr",
                "content": content,
                "description": "QR code detected in image"
            })
    return qr_links

def extract_urls_from_image(img_path):
    """Use EasyOCR to extract URLs from images."""
    image = Image.open(img_path)
    # EasyOCR works on PIL images
    ocr_results = reader.readtext(image, detail=0)
    ocr_links = []
    for text in ocr_results:
        urls = re.findall(r'https?://[^\s]+', text)
        for url in urls:
            ocr_links.append({
                "type": "ocr_text",
                "content": url.strip(),
                "description": "URL detected from text in image"
            })
    print(f"OCR Text for {img_path}: {ocr_results}")
    return ocr_links

# --------------------------
# Routes
# --------------------------
@app.route("/images/<filename>")
def serve_image(filename):
    try:
        return send_from_directory(EXTRACT_FOLDER, filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Clear previous images
    for f in os.listdir(EXTRACT_FOLDER):
        os.remove(os.path.join(EXTRACT_FOLDER, f))

    pdf = fitz.open(filepath)
    report = []

    for page_num, page in enumerate(pdf, start=1):
        images = page.get_images(full=True)
        page_info = {"page": page_num, "images": []}

        for img_index, img in enumerate(images):
            xref = img[0]
            try:
                base_image = pdf.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image["ext"]
                base_name = os.path.splitext(file.filename)[0].replace(" ", "_")
                filename = f"{base_name}_page{page_num}_img{img_index}.{ext}"
                img_path = os.path.join(EXTRACT_FOLDER, filename)

                # Save image
                with open(img_path, "wb") as f:
                    f.write(image_bytes)

                # --------------------------
                # Extract links from image
                # --------------------------
                extracted_links = []
                extracted_links.extend(extract_qr_codes(img_path))
                extracted_links.extend(extract_urls_from_image(img_path))

                # Remove duplicates
                extracted_links = [dict(t) for t in {tuple(d.items()) for d in extracted_links}]

                page_info["images"].append({
                    "filename": filename,
                    "url": f"{BACKEND_URL}/images/{filename}",
                    "clickable_link_found": len(extracted_links) > 0,
                    "extracted_links": extracted_links
                })

            except Exception as e:
                print(f"Error processing image: {e}")
                continue

        report.append(page_info)
    pdf.close()

    return jsonify(report)

@app.route("/")
def home():
    return jsonify({"message": "PDF Image Scanner is running", "status": "ok"})

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
