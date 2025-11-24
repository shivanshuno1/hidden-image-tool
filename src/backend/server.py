from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import fitz  # PyMuPDF
from PIL import Image
import numpy as np
from pyzbar.pyzbar import decode
import easyocr
import re
import io
import cv2

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
def preprocess_image(img_path):
    """Preprocess image for better OCR results."""
    try:
        # Read image with OpenCV
        img = cv2.imread(img_path)
        if img is None:
            return None
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to get better contrast
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh)
        
        return denoised
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None

def extract_qr_codes(img_path):
    """Detect QR codes in the image."""
    qr_links = []
    try:
        # Try with original image
        image = Image.open(img_path)
        qr_results = decode(image)
        
        # If no QR codes found, try with preprocessed image
        if not qr_results:
            preprocessed = preprocess_image(img_path)
            if preprocessed is not None:
                qr_results = decode(preprocessed)
        
        for qr in qr_results:
            try:
                content = qr.data.decode("utf-8").strip()
                if content:
                    qr_links.append({
                        "type": "qr",
                        "content": content,
                        "description": "QR code detected in image"
                    })
            except Exception as e:
                print(f"Error decoding QR: {e}")
                continue
    except Exception as e:
        print(f"Error extracting QR codes: {e}")
    
    return qr_links

def extract_urls_from_image(img_path):
    """Use EasyOCR to extract URLs from images."""
    ocr_links = []
    try:
        # Try OCR on original image
        image = Image.open(img_path)
        ocr_results = reader.readtext(np.array(image), detail=0, paragraph=False)
        
        print(f"OCR Results for {img_path}: {ocr_results}")
        
        # If no text found, try with preprocessed image
        if not ocr_results:
            preprocessed = preprocess_image(img_path)
            if preprocessed is not None:
                ocr_results = reader.readtext(preprocessed, detail=0, paragraph=False)
                print(f"OCR Results (preprocessed) for {img_path}: {ocr_results}")
        
        # Extract URLs and other useful text
        all_text = " ".join(ocr_results)
        
        # Find URLs
        url_pattern = r'https?://[^\s,;)"\']+'
        urls = re.findall(url_pattern, all_text, re.IGNORECASE)
        
        for url in urls:
            # Clean up URL
            url = url.strip('.,;:!?')
            if url:
                ocr_links.append({
                    "type": "ocr_url",
                    "content": url,
                    "description": "URL detected from text in image"
                })
        
        # Also look for partial URLs without protocol
        partial_url_pattern = r'www\.[^\s,;)"\']+'
        partial_urls = re.findall(partial_url_pattern, all_text, re.IGNORECASE)
        for url in partial_urls:
            url = url.strip('.,;:!?')
            if url and url not in [link['content'] for link in ocr_links]:
                ocr_links.append({
                    "type": "ocr_url",
                    "content": f"https://{url}",
                    "description": "Partial URL detected from text in image"
                })
        
        # If we found text but no URLs, include some text content
        if ocr_results and not ocr_links:
            combined_text = " ".join(ocr_results[:3])  # First 3 text blocks
            if len(combined_text) > 10:
                ocr_links.append({
                    "type": "ocr_text",
                    "content": combined_text[:200],  # Limit to 200 chars
                    "description": "Text content detected in image"
                })
    
    except Exception as e:
        print(f"Error extracting URLs from image: {e}")
    
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
        try:
            os.remove(os.path.join(EXTRACT_FOLDER, f))
        except Exception as e:
            print(f"Error removing file: {e}")

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

                print(f"Processing image: {filename}")

                # --------------------------
                # Extract links from image
                # --------------------------
                extracted_links = []
                
                # Try QR code extraction
                qr_links = extract_qr_codes(img_path)
                print(f"QR links found: {len(qr_links)}")
                extracted_links.extend(qr_links)
                
                # Try OCR extraction
                ocr_links = extract_urls_from_image(img_path)
                print(f"OCR links found: {len(ocr_links)}")
                extracted_links.extend(ocr_links)

                # Remove duplicates based on content
                seen = set()
                unique_links = []
                for link in extracted_links:
                    content = link['content']
                    if content not in seen:
                        seen.add(content)
                        unique_links.append(link)

                page_info["images"].append({
                    "filename": filename,
                    "url": f"{BACKEND_URL}/images/{filename}",
                    "clickable_link_found": len(unique_links) > 0,
                    "extracted_links": unique_links
                })

            except Exception as e:
                print(f"Error processing image on page {page_num}, img {img_index}: {e}")
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