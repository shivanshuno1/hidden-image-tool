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
import signal
import sys

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "pdf_uploads")
EXTRACT_FOLDER = os.path.join(BASE_DIR, "extracted_images")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACT_FOLDER, exist_ok=True)

BACKEND_URL = "https://hidden-backend-1.onrender.com"

print("Initializing EasyOCR...")
reader = easyocr.Reader(['en'], gpu=False)
print("EasyOCR ready!")

def handle_sigint(sig, frame):
    print("Shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_sigint)

def preprocess_image_for_ocr(img_path):
    try:
        img = cv2.imread(img_path)
        if img is None:
            return None
        scale = 2
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        return binary
    except Exception as e:
        print(f"Preprocessing failed: {e}")
        return None

def extract_qr_codes(img_path):
    links = []
    try:
        image = Image.open(img_path)
        qr_results = decode(image)
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
                    print(f"Found {qr.type}: {content[:50]}...")
            except Exception as e:
                print(f"Decoding QR: {e}")
    except Exception as e:
        print(f"QR extraction: {e}")
    return links

def extract_text_and_urls(img_path):
    links = []
    all_text = []
    try:
        print("Running OCR on image...")
        image = Image.open(img_path).convert("RGB")
        img_array = np.array(image)
        ocr_results = reader.readtext(img_array, detail=1, paragraph=False)
        print(f"Found {len(ocr_results)} text blocks")
        
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        www_pattern = r'www\.[a-zA-Z0-9][a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
        
        def clean_url(u):
            return u.strip().rstrip('.,;:!?)"]\'')
        
        for bbox, text, confidence in ocr_results:
            text = text.strip()
            if text and confidence > 0.3:
                all_text.append(text)
                print(f"OCR: '{text}' (confidence: {confidence:.2f})")
                
                for url in re.findall(url_pattern, text, re.IGNORECASE):
                    url = clean_url(url)
                    if len(url) > 10:
                        links.append({
                            "type": "url",
                            "content": url,
                            "description": "URL found in image text",
                            "confidence": round(confidence, 2)
                        })
                        print(f"Found URL: {url}")
                
                for url in re.findall(www_pattern, text, re.IGNORECASE):
                    url = clean_url(url)
                    full_url = f"https://{url}"
                    links.append({
                        "type": "url",
                        "content": full_url,
                        "description": "URL found in image text",
                        "confidence": round(confidence, 2)
                    })
                    print(f"Found www URL: {full_url}")
        
        if not links and not all_text:
            print("No text found, trying preprocessed image...")
            preprocessed = preprocess_image_for_ocr(img_path)
            if preprocessed is not None:
                ocr_results = reader.readtext(preprocessed, detail=1, paragraph=False)
                print(f"Preprocessed OCR found {len(ocr_results)} text blocks")
                for bbox, text, confidence in ocr_results:
                    text = text.strip()
                    if text and confidence > 0.3:
                        all_text.append(text)
                        print(f"OCR (enhanced): '{text}' (confidence: {confidence:.2f})")
                        for url in re.findall(url_pattern, text, re.IGNORECASE):
                            url = clean_url(url)
                            if len(url) > 10:
                                links.append({
                                    "type": "url",
                                    "content": url,
                                    "description": "URL found (enhanced scan)",
                                    "confidence": round(confidence, 2)
                                })
                                print(f"Found URL (enhanced): {url}")
        
        if not links and all_text:
            combined = " ".join(all_text[:3])
            links.append({
                "type": "text",
                "content": combined[:250],
                "description": "Text detected (no URLs found)"
            })
            print(f"No URLs found, returning text content: {combined}")
        
        seen = set()
        unique_links = []
        for link in links:
            if link["content"] not in seen:
                seen.add(link["content"])
                unique_links.append(link)
        return unique_links
    except Exception as e:
        print(f"OCR extraction: {e}")
        import traceback
        traceback.print_exc()
        return []

def extract_pdf_links_for_area(page, image_area, slice_index):
    links = []
    link_dicts = page.get_links()
    
    print(f"Slice {slice_index} area: {image_area}")
    print(f"Found {len(link_dicts)} total links on page")
    
    def overlaps(a, b):
        return not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])
    
    for i, ld in enumerate(link_dicts):
        rect = ld.get("from")
        uri = ld.get("uri")
        kind = ld.get("kind")
        
        if rect and uri and kind == 2:
            bbox = [rect.x0, rect.y0, rect.x1, rect.y1]
            print(f"Link {i}: {uri} at {bbox}")
            print(f"Comparing with image area: {image_area}")
            
            if overlaps(bbox, image_area):
                links.append({
                    "content": uri,
                    "type": "pdf_structural",
                    "bbox": bbox,
                    "description": "PDF structural link"
                })
                print(f"✅ Matched link: {uri}")
            else:
                print(f"❌ No overlap - Link: {bbox} vs Image: {image_area}")
    
    print(f"Found {len(links)} matching links for slice {slice_index}")
    return links

@app.route("/images/<filename>")
def serve_image(filename):
    try:
        img_path = os.path.join(EXTRACT_FOLDER, filename)
        if not os.path.exists(img_path):
            return jsonify({"error": "Image not found"}), 404
        return send_file(img_path, mimetype='image/png')
    except Exception as e:
        print(f"Serving image: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/upload", methods=["POST"])
def upload_file():
    print("\n" + "="*60)
    print("🚀 NEW PDF UPLOAD REQUEST - FIXED VERSION")
    print("="*60)
    
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files allowed"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    print(f"📁 Saved PDF: {file.filename}")

    # Clear old images
    for f in os.listdir(EXTRACT_FOLDER):
        try:
            os.remove(os.path.join(EXTRACT_FOLDER, f))
        except:
            pass

    pdf = fitz.open(filepath)
    report = []
    total_images = 0
    total_links = 0

    for page_num, page in enumerate(pdf, start=1):
        page_info = {"page": page_num, "images": []}
        
        print(f"\n📄 PROCESSING PAGE {page_num}")
        print("-" * 40)
        
        # STEP 1: Get ALL PDF links (this works as your test shows)
        all_pdf_links = page.get_links()
        print(f"🔍 Found {len(all_pdf_links)} total links on page {page_num}")
        
        # Filter only URI links (kind 2)
        uri_links = [ld for ld in all_pdf_links if ld.get('kind') == 2 and ld.get('uri')]
        print(f"🌐 Found {len(uri_links)} URI links")
        
        # STEP 2: Process each URI link and create images from link areas
        for link_idx, ld in enumerate(uri_links):
            rect = ld.get("from")
            uri = ld.get("uri")
            
            print(f"\n  🔗 Processing URI Link {link_idx}:")
            print(f"     URL: {uri}")
            print(f"     Position: [{rect.x0:.1f}, {rect.y0:.1f}, {rect.x1:.1f}, {rect.y1:.1f}]")
            
            # Create image from link area
            base_name = os.path.splitext(file.filename)[0].replace(" ", "_")
            filename = f"{base_name}_page{page_num}_link{link_idx}.png"
            img_path = os.path.join(EXTRACT_FOLDER, filename)
            
            try:
                # Render the link area as high-quality image with padding
                padding = 5
                clip_rect = fitz.Rect(
                    max(0, rect.x0 - padding),
                    max(0, rect.y0 - padding),
                    min(page.rect.width, rect.x1 + padding),
                    min(page.rect.height, rect.y1 + padding)
                )
                
                # High quality rendering
                mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
                pix = page.get_pixmap(matrix=mat, clip=clip_rect)
                pix.save(img_path)
                total_images += 1
                
                print(f"     ✅ Saved link area image: {filename}")
                print(f"     📐 Image size: {pix.width} x {pix.height} pixels")
                
                # STEP 3: Create the PDF structural link entry (THIS IS WHAT WE NEED!)
                pdf_link = {
                    "content": uri,
                    "type": "pdf_structural",
                    "bbox": [rect.x0, rect.y0, rect.x1, rect.y1],
                    "description": f"PDF structural link"
                }
                
                # Also scan for QR codes and OCR (optional)
                qr_links = extract_qr_codes(img_path)
                ocr_links = extract_text_and_urls(img_path)
                
                # Combine all links - PDF structural link is MOST IMPORTANT
                all_links = [pdf_link] + qr_links + ocr_links
                
                # Deduplicate
                seen = set()
                unique_links = []
                for link in all_links:
                    content = link["content"]
                    if content not in seen:
                        seen.add(content)
                        unique_links.append(link)
                
                total_links += len(unique_links)
                
                # Log results
                if unique_links:
                    print(f"     ✅ FOUND {len(unique_links)} LINK(S)!")
                    for link in unique_links:
                        print(f"        - {link['type']}: {link['content'][:60]}...")
                else:
                    print(f"     ❌ No additional links detected")
                
                # Add to page results - THIS IS WHAT GOES TO FRONTEND
                page_info["images"].append({
                    "filename": filename,
                    "url": f"{BACKEND_URL}/images/{filename}",
                    "image_area": [rect.x0, rect.y0, rect.x1, rect.y1],
                    "clickable_links_found": len(unique_links) > 0,
                    "extracted_links": unique_links
                })
                
            except Exception as e:
                print(f"     💥 ERROR processing link area: {e}")
                import traceback
                traceback.print_exc()
        
        # STEP 4: Also process any actual embedded images (if they exist)
        images = page.get_images(full=True)
        print(f"\n  🖼️  Found {len(images)} embedded images on page")
        
        for img_index, img in enumerate(images):
            xref = img[0]
            try:
                base_image = pdf.extract_image(xref)
                image_bytes = base_image["image"]
                base_name = os.path.splitext(file.filename)[0].replace(" ", "_")
                filename = f"{base_name}_page{page_num}_img{img_index}.png"
                img_path = os.path.join(EXTRACT_FOLDER, filename)

                img_pil = Image.open(io.BytesIO(image_bytes))
                img_pil.save(img_path, "PNG")
                total_images += 1

                image_rects = page.get_image_rects(xref)
                image_area = [0, 0, 0, 0]
                if image_rects:
                    rect = image_rects[0]
                    image_area = [rect.x0, rect.y0, rect.x1, rect.y1]

                print(f"     Processing embedded image {img_index} at {image_area}")

                # Extract links from embedded image
                pdf_links = extract_pdf_links_for_area(page, image_area, img_index)
                qr_links = extract_qr_codes(img_path)
                ocr_links = extract_text_and_urls(img_path)

                all_links = pdf_links + qr_links + ocr_links
                
                seen = set()
                unique_links = []
                for link in all_links:
                    content = link["content"]
                    if content not in seen:
                        seen.add(content)
                        unique_links.append(link)

                total_links += len(unique_links)

                page_info["images"].append({
                    "filename": filename,
                    "url": f"{BACKEND_URL}/images/{filename}",
                    "image_area": image_area,
                    "clickable_links_found": len(unique_links) > 0,
                    "extracted_links": unique_links
                })

            except Exception as e:
                print(f"     💥 ERROR processing embedded image: {e}")

        report.append(page_info)

    pdf.close()
    
    print(f"\n" + "="*60)
    print(f"🎉 SCAN COMPLETED!")
    print(f"📊 Total Images Created: {total_images}")
    print(f"🔗 Total Links Found: {total_links}")
    print(f"📄 Total Pages Processed: {len(report)}")
    print("="*60)
    
    return jsonify(report)
@app.route("/debug-upload", methods=["POST"])
def debug_upload():
    """Debug endpoint to see exactly what's in the PDF"""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, "debug_" + file.filename)
    file.save(filepath)
    
    pdf = fitz.open(filepath)
    debug_info = {
        "file_info": {
            "name": file.filename,
            "size": os.path.getsize(filepath)
        },
        "pages": []
    }
    
    for page_num, page in enumerate(pdf, start=1):
        page_info = {
            "page_number": page_num,
            "page_size": {
                "width": page.rect.width,
                "height": page.rect.height
            },
            "links": [],
            "images_found": 0,
            "text_content": []
        }
        
        # Get ALL links
        links = page.get_links()
        print(f"\n=== PAGE {page_num} DEBUG ===")
        print(f"Total links found: {len(links)}")
        
        for i, link in enumerate(links):
            print(f"Link {i}: {link}")
            if link.get('kind') == 2 and link.get('uri'):  # URI links
                rect = link.get('from')
                page_info["links"].append({
                    "link_number": i,
                    "uri": link.get('uri'),
                    "position": {
                        "x0": rect.x0,
                        "y0": rect.y0,
                        "x1": rect.x1, 
                        "y1": rect.y1
                    },
                    "area": f"{rect.x0},{rect.y0} to {rect.x1},{rect.y1}"
                })
        
        # Check images
        images = page.get_images()
        page_info["images_found"] = len(images)
        print(f"Images found: {len(images)}")
        
        for img_index, img in enumerate(images):
            print(f"Image {img_index}: {img}")
        
        debug_info["pages"].append(page_info)
    
    pdf.close()
    return jsonify(debug_info)


@app.route("/diagnostics")
def diagnostics():
    """Check what packages are installed"""
    import pkg_resources
    import sys
    
    installed_packages = []
    for package in pkg_resources.working_set:
        installed_packages.append(f"{package.project_name}=={package.version}")
    
    # Check specifically for PyMuPDF
    try:
        import fitz
        pymupdf_status = "✅ INSTALLED"
        pymupdf_version = fitz.__doc__.split(' ')[1] if fitz.__doc__ else "unknown"
    except ImportError as e:
        pymupdf_status = f"❌ NOT INSTALLED: {e}"
        pymupdf_version = "N/A"
    
    return jsonify({
        "python_version": sys.version,
        "pymupdf_status": pymupdf_status,
        "pymupdf_version": pymupdf_version,
        "installed_packages": installed_packages
    })

@app.route("/test-pymupdf")
def test_pymupdf():
    """Test if PyMuPDF is working"""
    try:
        import fitz
        # Create a simple PDF in memory to test
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "PyMuPDF Test - Working!")
        pdf_bytes = doc.write()
        doc.close()
        
        return jsonify({
            "status": "✅ PyMuPDF is working!",
            "version": fitz.__doc__.split(' ')[1] if fitz.__doc__ else "unknown"
        })
    except ImportError as e:
        return jsonify({
            "status": "❌ PyMuPDF not installed",
            "error": str(e)
        }), 500
    except Exception as e:
        return jsonify({
            "status": "⚠️ PyMuPDF installed but has issues",
            "error": str(e)
        }), 500

@app.route("/simple-test", methods=["POST"])
def simple_test():
    """Super simple test - just return the links as JSON"""
    print("🔍 SIMPLE-TEST: Starting...")
    
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    print(f"📁 File received: {file.filename}")
    
    # Save file temporarily
    filepath = os.path.join(UPLOAD_FOLDER, "test_file.pdf")
    file.save(filepath)
    print(f"💾 File saved: {filepath}")
    
    try:
        pdf = fitz.open(filepath)
        print(f"📄 PDF opened successfully, pages: {len(pdf)}")
        
        results = []
        
        for page_num, page in enumerate(pdf, start=1):
            print(f"🔍 Checking page {page_num}...")
            links = page.get_links()
            print(f"📊 Found {len(links)} links on page {page_num}")
            
            page_links = []
            for link in links:
                print(f"   Link: {link}")
                if link.get('kind') == 2 and link.get('uri'):
                    page_links.append({
                        "uri": link.get('uri'),
                        "position": {
                            "x0": link['from'].x0,
                            "y0": link['from'].y0,
                            "x1": link['from'].x1, 
                            "y1": link['from'].y1
                        }
                    })
            
            results.append({
                "page": page_num,
                "total_links": len(links),
                "uri_links": page_links
            })
        
        pdf.close()
        print(f"🎉 SIMPLE-TEST: Returning {sum(len(p['uri_links']) for p in results)} URI links")
        return jsonify({"success": True, "results": results})
        
    except Exception as e:
        print(f"💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@app.route("/")
def home():
    return jsonify({"message": "PDF Image Scanner Active", "status": "ok"})

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)