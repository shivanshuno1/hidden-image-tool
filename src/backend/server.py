from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import fitz  # PyMuPDF
from pyzbar.pyzbar import decode
from PIL import Image
import pytesseract
import re

app = Flask(__name__)
CORS(app)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "pdf_uploads")
EXTRACT_FOLDER = os.path.join(BASE_DIR, "extracted_images")
REPORT_FILE = os.path.join(BASE_DIR, "report.json")

# Backend URL (replace with your Render URL)
BACKEND_URL = "https://hidden-backend-1.onrender.com"

# Create folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACT_FOLDER, exist_ok=True)

print("🚀 PDF Image Scanner Backend")
print(f"✅ Backend URL: {BACKEND_URL}")

# Helper: Count total links in PDF
def count_links_in_pdf(pdf_path):
    try:
        pdf_document = fitz.open(pdf_path)
        total_links = 0
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            links = page.get_links()
            total_links += len(links)
        pdf_document.close()
        return total_links
    except Exception as e:
        print(f"Error counting links: {e}")
        return 0

@app.route("/images/<filename>")
def serve_image(filename):
    try:
        return send_from_directory(EXTRACT_FOLDER, filename)
    except Exception as e:
        print(f"Error serving image {filename}: {e}")
        return jsonify({"error": "Image not found"}), 404

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Clear previous images
    for f in os.listdir(EXTRACT_FOLDER):
        try:
            os.remove(os.path.join(EXTRACT_FOLDER, f))
        except:
            pass

    pdf = fitz.open(filepath)
    report = []

    for page_num, page in enumerate(pdf, start=1):
        images = page.get_images(full=True)
        page_info = {"page": page_num, "images": []}

        page_links = page.get_links()  # PDF annotations

        for img_index, img in enumerate(images):
            xref = img[0]
            try:
                base_image = pdf.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image["ext"]
                base_name = os.path.splitext(file.filename)[0].replace(' ', '_')
                filename = f"{base_name}_page{page_num}_img{img_index}.{ext}"
                img_path = os.path.join(EXTRACT_FOLDER, filename)

                with open(img_path, "wb") as f_img:
                    f_img.write(image_bytes)

                extracted_links = []

                # --- PDF annotation link (if exists) ---
                if img_index < len(page_links):
                    link = page_links[img_index]
                    link_info = {}
                    if 'uri' in link:
                        link_info = {"type": "uri", "content": link['uri'], "description": "Web URL"}
                    elif 'file' in link:
                        link_info = {"type": "file", "content": link['file'], "description": "Local file path"}
                    elif 'page' in link:
                        link_info = {"type": "internal", "content": f"Page {link['page']}", "description": "Internal page"}
                    if link_info:
                        extracted_links.append(link_info)

                # --- QR code detection ---
                qr_results = decode(Image.open(img_path))
                for qr in qr_results:
                    extracted_links.append({
                        "type": "qr",
                        "content": qr.data.decode("utf-8"),
                        "description": "QR code detected in image"
                    })

                # --- OCR for text URLs ---
                text = pytesseract.image_to_string(Image.open(img_path))
                urls_in_text = re.findall(r'https?://\S+', text)
                for url in urls_in_text:
                    extracted_links.append({
                        "type": "ocr_text",
                        "content": url,
                        "description": "URL detected from text in image"
                    })

                # Remove duplicates
                extracted_links = [dict(t) for t in {tuple(d.items()) for d in extracted_links}]

                image_url = f"{BACKEND_URL}/images/{filename}"
                page_info["images"].append({
                    "filename": filename,
                    "url": image_url,
                    "clickable_link_found": len(extracted_links) > 0,
                    "extracted_links": extracted_links,
                    "total_links_on_page": len(page_links)
                })

            except Exception as e:
                print(f"❌ Error processing image {img_index} on page {page_num}: {e}")
                continue

        report.append(page_info)

    pdf.close()
    return jsonify(report)

@app.route("/")
def home():
    return jsonify({
        "message": "PDF Image Scanner",
        "status": "running",
        "backend_url": BACKEND_URL,
        "version": "v2"
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "backend_url": BACKEND_URL,
        "version": "v2"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
