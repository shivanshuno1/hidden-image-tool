from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import fitz  # PyMuPDF for PDF image extraction
from urllib.parse import unquote

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

print("🚀 PDF Image Scanner Backend - WITH LINK EXTRACTION")
print(f"✅ Backend URL: {BACKEND_URL}")
print(f"✅ Upload folder: {UPLOAD_FOLDER}")

def extract_links_with_positions(pdf_path):
    """Extract all links with their positions from PDF"""
    try:
        pdf_document = fitz.open(pdf_path)
        all_links = []
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            links = page.get_links()
            
            for link in links:
                link_info = {
                    'page': page_num + 1,
                    'rect': link.get('rect', []),  # The clickable area
                    'link_type': 'unknown'
                }
                
                # Extract the actual link content
                if 'uri' in link:
                    link_info['link_type'] = 'uri'
                    link_info['content'] = link['uri']
                elif 'file' in link:
                    link_info['link_type'] = 'file'
                    link_info['content'] = link['file']
                elif 'page' in link:
                    link_info['link_type'] = 'internal_page'
                    link_info['content'] = f"Page {link['page']}"
                else:
                    link_info['content'] = str(link)
                
                all_links.append(link_info)
                print(f"📎 Found {link_info['link_type']} link: {link_info['content']}")
        
        pdf_document.close()
        return all_links
    except Exception as e:
        print(f"Error extracting links: {e}")
        return []

def find_links_for_image_area(page_links, image_area, tolerance=5):
    """Find links that overlap with image area"""
    matching_links = []
    
    for link in page_links:
        link_rect = link.get('rect', [])
        if rects_overlap(link_rect, image_area, tolerance):
            matching_links.append(link)
    
    return matching_links

def rects_overlap(rect1, rect2, tolerance=5):
    """Check if two rectangles overlap within tolerance"""
    if not rect1 or not rect2 or len(rect1) < 4 or len(rect2) < 4:
        return False
    
    # Simple rectangle overlap detection
    # rect format: [x0, y0, x1, y1]
    overlap_x = not (rect1[2] < rect2[0] - tolerance or rect1[0] > rect2[2] + tolerance)
    overlap_y = not (rect1[3] < rect2[1] - tolerance or rect1[1] > rect2[3] + tolerance)
    
    return overlap_x and overlap_y

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
    print("=== UPLOAD CALLED - WITH LINK EXTRACTION ===")
    
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

    # Extract all links from PDF first
    all_links = extract_links_with_positions(filepath)
    print(f"📊 Total links found in PDF: {len(all_links)}")

    pdf = fitz.open(filepath)
    report = []

    for page_num, page in enumerate(pdf, start=1):
        images = page.get_images(full=True)
        page_info = {"page": page_num, "images": []}

        print(f"Page {page_num}: Processing {len(images)} images")
        
        # Get links for this specific page
        page_links = [link for link in all_links if link['page'] == page_num]
        print(f"Page {page_num}: {len(page_links)} links on this page")

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

                # Get image position (approximate)
                # In PyMuPDF, we need to find where images are drawn on the page
                image_areas = []
                
                # Try to find image position by searching for rectangles that might contain images
                drawing_areas = page.get_drawings()
                for drawing in drawing_areas:
                    if 'rect' in drawing and drawing.get('type') == 'image':
                        image_areas.append(drawing['rect'])
                
                # If we can't find exact position, use a heuristic based on image order
                image_area = None
                if image_areas and img_index < len(image_areas):
                    image_area = image_areas[img_index]
                else:
                    # Fallback: divide page into sections for images
                    page_rect = page.rect
                    section_height = page_rect.height / max(1, len(images))
                    image_area = [
                        page_rect.x0, 
                        page_rect.y0 + (section_height * img_index),
                        page_rect.x1, 
                        page_rect.y0 + (section_height * (img_index + 1))
                    ]

                # Find links that overlap with this image area
                matching_links = find_links_for_image_area(page_links, image_area)
                
                # Extract the actual link content
                extracted_links = []
                for link in matching_links:
                    link_content = link.get('content', '')
                    link_type = link.get('link_type', 'unknown')
                    
                    # Decode URL if needed
                    if link_type in ['uri', 'file']:
                        try:
                            link_content = unquote(link_content)
                        except:
                            pass
                    
                    extracted_links.append({
                        'type': link_type,
                        'content': link_content,
                        'area': link.get('rect', [])
                    })
                
                print(f"🖼️ Image {img_index}: Found {len(extracted_links)} linked URLs")

                # ✅ CRITICAL FIX: Use Render URL instead of localhost
                image_url = f"{BACKEND_URL}/images/{filename}"
                
                page_info["images"].append({
                    "filename": filename,
                    "url": image_url,  # ✅ This now points to Render
                    "clickable_links_found": len(extracted_links) > 0,
                    "extracted_links": extracted_links,  # ✅ THIS IS WHAT YOU NEED!
                    "image_area": image_area
                })
                
                print(f"✅ Image {img_index}: URL = {image_url}")
                for link in extracted_links:
                    print(f"   🔗 {link['type']}: {link['content']}")
                
            except Exception as e:
                print(f"❌ Image error: {e}")
                continue

        report.append(page_info)

    pdf.close()

    # Save detailed report
    try:
        with open(REPORT_FILE, 'w') as f:
            json.dump({
                'pdf_name': file.filename,
                'total_pages': len(report),
                'total_links_found': len(all_links),
                'pages': report,
                'all_links': all_links
            }, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save report: {e}")

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
        "message": "PDF Image Scanner - WITH LINK EXTRACTION",
        "status": "running",
        "backend_url": BACKEND_URL,
        "version": "link-extraction-v1"
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "backend_url": BACKEND_URL,
        "version": "link-extraction-v1"
    })

@app.route("/report")
def get_report():
    """Endpoint to get the detailed report"""
    try:
        with open(REPORT_FILE, 'r') as f:
            report_data = json.load(f)
        return jsonify(report_data)
    except:
        return jsonify({"error": "No report available"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🎯 Starting LINK-EXTRACTION server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)