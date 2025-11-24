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

# Initialize EasyOCR reader once (this takes time on first run)
print("Initializing EasyOCR...")
reader = easyocr.Reader(['en'], gpu=False)
print("EasyOCR ready!")

# --------------------------
# Helper functions
# --------------------------
def preprocess_image_for_ocr(img_path):
    """Preprocess image for better OCR results."""
    try:
        img = cv2.imread(img_path)
        if img is None:
            return None
        
        # Increase size for better text detection
        scale = 2
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        
        return binary
    except Exception as e:
        print(f"    [ERROR] Preprocessing failed: {e}")
        return None

def extract_qr_codes(img_path):
    """Detect QR codes and barcodes in the image."""
    links = []
    try:
        # Try with PIL
        image = Image.open(img_path)
        qr_results = decode(image)
        
        # If nothing found, try with OpenCV preprocessing
        if not qr_results:
            img_cv = cv2.imread(img_path)
            if img_cv is not None:
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                qr_results = decode(gray)
                
                if not qr_results:
                    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
                    qr_results = decode(binary)
        
        for qr in qr_results:
            try:
                content = qr.data.decode("utf-8").strip()
                if content:
                    links.append({
                        "type": f"{qr.type}",
                        "content": content,
                        "description": f"{qr.type} detected"
                    })
                    print(f"    ✓ Found {qr.type}: {content[:50]}...")
            except Exception as e:
                print(f"    [ERROR] Decoding QR: {e}")
    except Exception as e:
        print(f"    [ERROR] QR extraction: {e}")
    
    return links

def extract_text_and_urls(img_path):
    """Use EasyOCR to extract text and find URLs."""
    links = []
    
    try:
        print(f"    Running OCR on image...")
        
        # Read image
        image = Image.open(img_path)
        img_array = np.array(image)
        
        # Run OCR with bounding boxes
        ocr_results = reader.readtext(img_array, detail=1, paragraph=False)
        
        print(f"    Found {len(ocr_results)} text blocks")
        
        all_text = []
        
        # URL patterns
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        www_pattern = r'www\.[a-zA-Z0-9][a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
        
        for bbox, text, confidence in ocr_results:
            text = text.strip()
            
            if text and confidence > 0.25:  # Lower threshold to catch more text
                all_text.append(text)
                print(f"    OCR: '{text}' (confidence: {confidence:.2f})")
                
                # Find full URLs
                found_urls = re.findall(url_pattern, text, re.IGNORECASE)
                for url in found_urls:
                    url = url.rstrip('.,;:!?)')
                    if len(url) > 10:  # Filter out noise
                        links.append({
                            "type": "url",
                            "content": url,
                            "description": "URL found in image text",
                            "confidence": round(confidence, 2)
                        })
                        print(f"    ✓ Found URL: {url}")
                
                # Find www URLs
                found_www = re.findall(www_pattern, text, re.IGNORECASE)
                for url in found_www:
                    url = url.rstrip('.,;:!?)')
                    full_url = f"https://{url}"
                    links.append({
                        "type": "url",
                        "content": full_url,
                        "description": "URL found in image text",
                        "confidence": round(confidence, 2)
                    })
                    print(f"    ✓ Found www URL: {full_url}")
        
        # If no links found, try with preprocessed image
        if not links and len(all_text) == 0:
            print(f"    No text found, trying preprocessed image...")
            preprocessed = preprocess_image_for_ocr(img_path)
            
            if preprocessed is not None:
                ocr_results = reader.readtext(preprocessed, detail=1, paragraph=False)
                print(f"    Preprocessed OCR found {len(ocr_results)} text blocks")
                
                for bbox, text, confidence in ocr_results:
                    text = text.strip()
                    
                    if text and confidence > 0.25:
                        all_text.append(text)
                        print(f"    OCR (enhanced): '{text}' (confidence: {confidence:.2f})")
                        
                        found_urls = re.findall(url_pattern, text, re.IGNORECASE)
                        for url in found_urls:
                            url = url.rstrip('.,;:!?)')
                            if len(url) > 10:
                                links.append({
                                    "type": "url",
                                    "content": url,
                                    "description": "URL found (enhanced scan)",
                                    "confidence": round(confidence, 2)
                                })
                                print(f"    ✓ Found URL (enhanced): {url}")
        
        # If we found text but no URLs, include text content
        if not links and all_text:
            combined = " ".join(all_text[:3])
            # MODIFIED: Removed the length filter entirely to capture any detected text
            links.append({
                "type": "text",
                "content": combined[:250],
                "description": "Text detected (no URLs found)"
            })
            print(f"    ℹ No URLs found, returning text content: {combined}")
    
    except Exception as e:
        print(f"    [ERROR] OCR extraction: {e}")
        import traceback
        traceback.print_exc()
    
    return links

# FINAL MODIFIED HELPER FUNCTION TO EXTRACT ALL PDF STRUCTURAL ACTIONS
def extract_pdf_links_for_area(page, image_area_rect):
    """Detects ALL PDF Annotations that overlap with the image's area using page.get_links()."""
    links = []
    
    from fitz import Rect 
    image_rect = Rect(image_area_rect)

    print(f"      Scanning for structural PDF links using page.get_links() over area: {image_rect.x0:.0f}, {image_rect.y0:.0f}...")
    
    # Use the highly optimized method to get all link annotations
    pdf_links = page.get_links()

    for link_data in pdf_links:
        link_rect = link_data['rect']
        
        # We only check for intersection (most permissive bounding box match)
        if link_rect.intersects(image_rect):
            
            content = None
            link_type = None

            uri = link_data.get('uri')
            dest = link_data.get('dest')
            file = link_data.get('file') 
            
            if uri:
                content = uri
                link_type = "pdf_uri_link"
            elif file:
                # Type 3 is LINK_LAUNCH or LINK_GOTOR (remote file)
                content = f"PDF File Launch: {file}"
                link_type = "pdf_file_launch_link"
            elif dest:
                # dest is used for internal links (GoTo)
                # Check that it's not just a self-reference to the current page/view before logging
                if not (isinstance(dest, list) and dest[0] == page.number and dest[1] == 'xyz'):
                    content = f"Internal PDF Destination: {dest}"
                    link_type = "pdf_internal_link"
                else:
                    continue # Skip link to current page

            # Check for deeper actions (JS/Widget) using the underlying annotation object
            if content:
                # Find the actual annotation object for rich properties
                annot = page.find_annot(link_rect)
                if annot:
                    if annot.script:
                        # Overwrite content with script for clarity if available
                        content = f"JavaScript Action: {annot.script.strip()[:100]}..."
                        link_type = "pdf_js_action"
                    elif annot.field_name and annot.a:
                        # Check for Widget Actions
                        action = annot.a
                        if action.n == "/URI" and action.uri:
                            content = action.uri
                            link_type = "pdf_widget_uri_action"
                        elif action.n == "/JavaScript" and action.js:
                            content = f"Widget JS Action: {action.js.strip()[:100]}..."
                            link_type = "pdf_widget_js_action"
            
            # Use annot.url as a final fallback for non-URI/non-dest links if 'content' is still empty
            if not content and annot and annot.url:
                content = annot.url
                link_type = "pdf_generic_action"


            if content and link_type:
                links.append({
                    "type": link_type,
                    "content": content,
                    "description": f"Structural {link_type} found on PDF page",
                    "confidence": 1.0 
                })
                print(f"      ✅ Found Structural Link: {content[:50]}...")
    
    return links
    
# --------------------------
# Routes
# --------------------------
@app.route("/images/<filename>")
def serve_image(filename):
    """Serve extracted images"""
    try:
        img_path = os.path.join(EXTRACT_FOLDER, filename)
        
        if not os.path.exists(img_path):
            return jsonify({"error": "Image not found"}), 404
        
        return send_file(img_path, mimetype='image/png')
    except Exception as e:
        print(f"[ERROR] Serving image: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/upload", methods=["POST"])
def upload_file():
    print("\n" + "="*70)
    print("NEW PDF UPLOAD REQUEST")
    print("="*70)
    
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files allowed"}), 400

    # Save PDF
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    print(f"\n✓ Saved PDF: {file.filename}")

    # Clear old images
    for f in os.listdir(EXTRACT_FOLDER):
        try:
            os.remove(os.path.join(EXTRACT_FOLDER, f))
        except:
            pass

    # Process PDF
    pdf = fitz.open(filepath)
    report = []
    total_images = 0
    total_links = 0

    for page_num, page in enumerate(pdf, start=1):
        images = page.get_images(full=True)
        page_info = {"page": page_num, "images": []}
        
        print(f"\n📄 PAGE {page_num}: {len(images)} image(s)")

        for img_index, img in enumerate(images):
            xref = img[0]
            try:
                # Extract image
                base_image = pdf.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Save as PNG
                base_name = os.path.splitext(file.filename)[0].replace(" ", "_")
                filename = f"{base_name}_page{page_num}_img{img_index}.png"
                img_path = os.path.join(EXTRACT_FOLDER, filename)

                img_pil = Image.open(io.BytesIO(image_bytes))
                img_pil.save(img_path, 'PNG')
                total_images += 1
                
                print(f"\n  🖼️  Image {img_index}: {filename}")
                print(f"      Size: {img_pil.size[0]}x{img_pil.size[1]}px")
                
                # Get image position on page
                image_rects = page.get_image_rects(xref)
                image_area = [0, 0, 0, 0]
                if image_rects:
                    rect = image_rects[0]
                    # Store image area as [x0, y0, x1, y1] for fitz.Rect comparison
                    image_area = [rect.x0, rect.y0, rect.x1, rect.y1]

                # SCAN FOR LINKS
                all_links = []
                
                # 1. STRUCTURAL PDF LINKS (COMPREHENSIVE)
                print(f"      Scanning for structural PDF links...")
                pdf_links = extract_pdf_links_for_area(page, image_area)
                all_links.extend(pdf_links)
                
                # 2. QR Codes (Existing)
                print(f"      Scanning for QR codes...")
                qr_links = extract_qr_codes(img_path)
                all_links.extend(qr_links)
                
                # 3. Text & URLs (Existing - Highly Aggressive OCR)
                print(f"      Scanning for text and URLs...")
                text_links = extract_text_and_urls(img_path)
                all_links.extend(text_links)

                # Remove duplicates
                seen = set()
                unique_links = []
                for link in all_links:
                    content = link['content']
                    if content not in seen:
                        seen.add(content)
                        unique_links.append(link)

                total_links += len(unique_links)
                
                if len(unique_links) > 0:
                    print(f"      ✅ FOUND {len(unique_links)} LINK(S)!")
                else:
                    print(f"      ❌ No links detected")

                page_info["images"].append({
                    "filename": filename,
                    "url": f"{BACKEND_URL}/images/{filename}",
                    "image_area": image_area,
                    "clickable_links_found": len(unique_links) > 0,
                    "extracted_links": unique_links
                })

            except Exception as e:
                print(f"  [ERROR] Processing image: {e}")
                import traceback
                traceback.print_exc()

        report.append(page_info)
    
    pdf.close()
    
    print("\n" + "="*70)
    print(f"COMPLETED: {total_images} images, {total_links} links found")
    print("="*70 + "\n")

    return jsonify(report)

@app.route("/")
def home():
    return jsonify({"message": "PDF Image Scanner Active", "status": "ok"})

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)