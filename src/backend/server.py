from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import fitz  # PyMuPDF for PDF image extraction

app = Flask(__name__)
CORS(app)

# Use absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "pdf_uploads")
EXTRACT_FOLDER = os.path.join(BASE_DIR, "extracted_images")
REPORT_FILE = os.path.join(BASE_DIR, "report.json")

# ✅ CRITICAL FIX: Use your actual Render URL
BACKEND_URL = "https://hidden-backend-1.onrender.com"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACT_FOLDER, exist_ok=True)

print("🚀 PDF Image Scanner Backend - RENDER FIXED VERSION")
print(f"✅ Backend URL: {BACKEND_URL}")
print(f"✅ Upload folder: {UPLOAD_FOLDER}")

def count_links_in_pdf(pdf_path):
    """Count total links in PDF"""
    try:
        pdf_document = fitz.open(pdf_path)
        total_links = 0
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            links = page.get_links()
            total_links += len(links)
            print(f"Page {page_num + 1}: {len(links)} links")
        
        pdf_document.close()
        return total_links
    except Exception as e:
        print(f"Error counting links: {e}")
        return 0

@app.route("/images/<filename>")
def serve_image(filename):
    """Serve extracted images"""
    try:
        return send_from_directory(EXTRACT_FOLDER, filename)
    except Exception as e:
        print(f"Error serving image {filename}: {e}")
        return jsonify({"error": "Image not found"}), 404

@app.route("/upload", methods=["POST"])
def upload_file():
    print("=== UPLOAD CALLED - WITH REAL LINK EXTRACTION ===")
    
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    print(f"Processing file: {file.filename}")

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Clear previous extracted images
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

        print(f"Page {page_num}: Processing {len(images)} images")
        
        # Extract ALL links from this page with their positions
        page_links = page.get_links()
        print(f"Page {page_num}: {len(page_links)} links found")
        
        # Print all links for debugging
        for link_idx, link in enumerate(page_links):
            if 'uri' in link:
                print(f"  🔗 Link {link_idx}: URI = {link['uri']}")
            elif 'file' in link:
                print(f"  📁 Link {link_idx}: FILE = {link['file']}")
            elif 'page' in link:
                print(f"  📄 Link {link_idx}: INTERNAL_PAGE = {link['page']}")

        for img_index, img in enumerate(images):
            xref = img[0]
            try:
                base_image = pdf.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image["ext"]
                
                base_name = os.path.splitext(file.filename)[0].replace(' ', '_')
                filename = f"{base_name}_page{page_num}_img{img_index}.{ext}"
                img_path = os.path.join(EXTRACT_FOLDER, filename)

                print(f"Saving image to: {img_path}")
                with open(img_path, "wb") as f:
                    f.write(image_bytes)

                # ✅ REAL LINK EXTRACTION LOGIC
                extracted_links = []
                
                # Try to match this image with links
                # Since we don't have exact image positions, we'll associate by order
                if img_index < len(page_links):
                    link = page_links[img_index]
                    link_info = {}
                    
                    if 'uri' in link:
                        link_info = {
                            "type": "uri",
                            "content": link['uri'],
                            "description": "Web URL"
                        }
                    elif 'file' in link:
                        link_info = {
                            "type": "file", 
                            "content": link['file'],
                            "description": "Local file path"
                        }
                    elif 'page' in link:
                        link_info = {
                            "type": "internal",
                            "content": f"Page {link['page']}",
                            "description": "Internal page reference"
                        }
                    
                    if link_info:
                        extracted_links.append(link_info)
                        print(f"✅ Extracted link: {link_info}")

                # ✅ CRITICAL FIX: Use Render URL instead of localhost
                image_url = f"{BACKEND_URL}/images/{filename}"
                
                page_info["images"].append({
                    "filename": filename,
                    "url": image_url,
                    "clickable_link_found": len(extracted_links) > 0,
                    "extracted_links": extracted_links,  # ✅ THIS IS WHAT YOU NEED!
                    "total_links_on_page": len(page_links)
                })
                
                print(f"✅ Image {img_index}: URL = {image_url}")
                if extracted_links:
                    print(f"   🔗 Extracted: {extracted_links}")
                
            except Exception as e:
                print(f"❌ Image error: {e}")
                continue

        report.append(page_info)

    pdf.close()

    # Final verification
    if report and report[0]['images']:
        first_image = report[0]['images'][0]
        print(f"✅ VERIFIED: First image URL = {first_image['url']}")
        if first_image['extracted_links']:
            print(f"✅ EXTRACTED LINKS: {first_image['extracted_links']}")

    return jsonify(report)
@app.route("/")
def home():
    return jsonify({
        "message": "PDF Image Scanner - RENDER FIXED",
        "status": "running",
        "backend_url": BACKEND_URL,
        "version": "render-fixed-v2"
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "backend_url": BACKEND_URL,
        "version": "render-fixed-v2",
        "image_urls": "pointing_to_render"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🎯 Starting RENDER-FIXED server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)