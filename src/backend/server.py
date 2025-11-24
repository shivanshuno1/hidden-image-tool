from flask import Flask, request, jsonify, send_file
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
CORS(app, resources={r"/*": {"origins": "*"}})

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
def preprocess_image_for_ocr(img_path):
    """Preprocess image for better OCR results."""
    try:
        img = cv2.imread(img_path)
        if img is None:
            return None
        
        # Increase image size for better OCR
        scale_factor = 2
        width = int(img.shape[1] * scale_factor)
        height = int(img.shape[0] * scale_factor)
        img = cv2.resize(img, (width, height), interpolation=cv2.INTER_CUBIC)
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding for better text detection
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        
        return binary
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None

def extract_qr_codes(img_path):
    """Detect QR codes and barcodes in the image."""
    qr_links = []
    try:
        # Try original image
        image = Image.open(img_path)
        qr_results = decode(image)
        
        # Try with different preprocessing
        if not qr_results:
            img_cv = cv2.imread(img_path)
            if img_cv is not None:
                # Try grayscale
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                qr_results = decode(gray)
                
                # Try with thresholding
                if not qr_results:
                    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
                    qr_results = decode(binary)
        
        for qr in qr_results:
            try:
                content = qr.data.decode("utf-8").strip()
                if content:
                    qr_type = qr.type
                    qr_links.append({
                        "type": "qr_code" if qr_type == "QRCODE" else "barcode",
                        "content": content,
                        "description": f"{qr_type} detected in image"
                    })
                    print(f"  Found {qr_type}: {content}")
            except Exception as e:
                print(f"  Error decoding QR/barcode: {e}")
                continue
    except Exception as e:
        print(f"  Error extracting QR codes: {e}")
    
    return qr_links

def extract_text_and_urls(img_path):
    """Use EasyOCR to extract all text and URLs from images."""
    extracted_data = []
    
    try:
        # Read original image
        image = Image.open(img_path)
        img_array = np.array(image)
        
        # Get detailed OCR results with bounding boxes
        ocr_results = reader.readtext(img_array, detail=1)
        
        print(f"  Found {len(ocr_results)} text blocks")
        
        all_text_blocks = []
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        partial_url_pattern = r'www\.[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[^\s<>"{}|\\^`\[\]]+'
        
        for bbox, text, confidence in ocr_results:
            text = text.strip()
            if text and confidence > 0.3:  # Filter low confidence results
                all_text_blocks.append(text)
                print(f"  OCR Text (conf: {confidence:.2f}): {text}")
                
                # Check for URLs in this text block
                urls = re.findall(url_pattern, text, re.IGNORECASE)
                for url in urls:
                    url = url.rstrip('.,;:!?)')
                    extracted_data.append({
                        "type": "url",
                        "content": url,
                        "description": "URL found in image text",
                        "confidence": round(confidence, 2)
                    })
                
                # Check for partial URLs
                partial_urls = re.findall(partial_url_pattern, text, re.IGNORECASE)
                for url in partial_urls:
                    url = url.rstrip('.,;:!?)')
                    full_url = f"https://{url}" if not url.startswith('http') else url
                    extracted_data.append({
                        "type": "url",
                        "content": full_url,
                        "description": "URL found in image text",
                        "confidence": round(confidence, 2)
                    })
        
        # If no URLs found, try with preprocessed image
        if not extracted_data:
            print("  No URLs in original, trying preprocessed image...")
            preprocessed = preprocess_image_for_ocr(img_path)
            if preprocessed is not None:
                ocr_results_preprocessed = reader.readtext(preprocessed, detail=1)
                
                for bbox, text, confidence in ocr_results_preprocessed:
                    text = text.strip()
                    if text and confidence > 0.3:
                        all_text_blocks.append(text)
                        
                        urls = re.findall(url_pattern, text, re.IGNORECASE)
                        for url in urls:
                            url = url.rstrip('.,;:!?)')
                            extracted_data.append({
                                "type": "url",
                                "content": url,
                                "description": "URL found in image text (enhanced)",
                                "confidence": round(confidence, 2)
                            })
                        
                        partial_urls = re.findall(partial_url_pattern, text, re.IGNORECASE)
                        for url in partial_urls:
                            url = url.rstrip('.,;:!?)')
                            full_url = f"https://{url}" if not url.startswith('http') else url
                            extracted_data.append({
                                "type": "url",
                                "content": full_url,
                                "description": "URL found in image text (enhanced)",
                                "confidence": round(confidence, 2)
                            })
        
        # If still no URLs but we have text, include some text content
        if not extracted_data and all_text_blocks:
            combined_text = " ".join(all_text_blocks[:5])  # First 5 blocks
            if len(combined_text) > 15:
                extracted_data.append({
                    "type": "text_content",
                    "content": combined_text[:300],
                    "description": "Text content in image (no links found)",
                    "confidence": 0.8
                })
    
    except Exception as e:
        print(f"  Error extracting text/URLs: {e}")
        import traceback
        traceback.print_exc()
    
    return extracted_data

# --------------------------
# Routes
# --------------------------
@app.route("/images/<filename>")
def serve_image(filename):
    """Serve extracted images with proper headers"""
    try:
        img_path = os.path.join(EXTRACT_FOLDER, filename)
        
        if not os.path.exists(img_path):
            print(f"Image not found: {img_path}")
            return jsonify({"error": "Image not found"}), 404
        
        ext = filename.split('.')[-1].lower()
        mimetype_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'bmp': 'image/bmp',
            'webp': 'image/webp'
        }
        mimetype = mimetype_map.get(ext, 'image/png')
        
        return send_file(img_path, mimetype=mimetype, as_attachment=False)
    except Exception as e:
        print(f"Error serving image {filename}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    # Save uploaded PDF
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    print(f"\n{'='*60}")
    print(f"Processing PDF: {file.filename}")
    print(f"{'='*60}")

    # Clear previous images
    for f in os.listdir(EXTRACT_FOLDER):
        try:
            os.remove(os.path.join(EXTRACT_FOLDER, f))
        except Exception as e:
            print(f"Error removing old file: {e}")

    # Open PDF
    pdf = fitz.open(filepath)
    report = []
    total_images = 0
    total_links_found = 0

    for page_num, page in enumerate(pdf, start=1):
        images = page.get_images(full=True)
        page_info = {"page": page_num, "images": []}
        print(f"\nPage {page_num}: Found {len(images)} images")

        for img_index, img in enumerate(images):
            xref = img[0]
            try:
                # Extract image
                base_image = pdf.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Save as PNG for compatibility
                base_name = os.path.splitext(file.filename)[0].replace(" ", "_")
                filename = f"{base_name}_page{page_num}_img{img_index}.png"
                img_path = os.path.join(EXTRACT_FOLDER, filename)

                # Convert and save
                img_pil = Image.open(io.BytesIO(image_bytes))
                img_pil.save(img_path, 'PNG')
                total_images += 1
                
                print(f"\nImage {img_index}: {filename}")
                print(f"  Size: {img_pil.size}")

                # Extract all types of links
                all_links = []
                
                # 1. Extract QR codes and barcodes
                print("  Scanning for QR codes...")
                qr_links = extract_qr_codes(img_path)
                all_links.extend(qr_links)
                
                # 2. Extract text and URLs
                print("  Scanning for text and URLs...")
                text_links = extract_text_and_urls(img_path)
                all_links.extend(text_links)

                # Remove duplicates based on content
                seen = set()
                unique_links = []
                for link in all_links:
                    content = link['content']
                    if content not in seen:
                        seen.add(content)
                        unique_links.append(link)
                        total_links_found += 1

                print(f"  Total unique links found: {len(unique_links)}")

                page_info["images"].append({
                    "filename": filename,
                    "url": f"{BACKEND_URL}/images/{filename}",
                    "has_links": len(unique_links) > 0,
                    "link_count": len(unique_links),
                    "links": unique_links
                })

            except Exception as e:
                print(f"  ERROR processing image: {e}")
                import traceback
                traceback.print_exc()
                continue

        report.append(page_info)
    
    pdf.close()
    
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  Total images extracted: {total_images}")
    print(f"  Total links found: {total_links_found}")
    print(f"{'='*60}\n")

    return jsonify({
        "success": True,
        "total_images": total_images,
        "total_links": total_links_found,
        "pages": report
    })

@app.route("/")
def home():
    return jsonify({"message": "PDF Image Scanner is running", "status": "ok"})

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/debug/images")
def debug_images():
    """Debug endpoint to list all extracted images"""
    try:
        images = os.listdir(EXTRACT_FOLDER)
        return jsonify({
            "total": len(images),
            "images": images,
            "folder_path": EXTRACT_FOLDER
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)