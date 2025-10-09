import os
import subprocess
from pikepdf import Pdf, PdfImage

def analyze_pdf(pdf_path, output_dir="hidden_extracted"):
    os.makedirs(output_dir, exist_ok=True)
    pdf = Pdf.open(pdf_path)
    extracted_files = []

    for i, page in enumerate(pdf.pages, start=1):
        xobjects = getattr(page, "images", {})
        if not xobjects:
            continue

        for name, obj in xobjects.items():
            img = PdfImage(obj)
            out_name = os.path.join(output_dir, f"page{i}_{name[1:]}.bin")
            img.extract_to(fileprefix=out_name.replace('.bin', ''))
            extracted_files.append(out_name)
            print(f"Extracted: {out_name}")

    # Run Windows Defender scan if available
    try:
        for f in extracted_files:
            subprocess.run(["powershell", "Start-MpScan", "-ScanPath", f], check=True)
    except Exception as e:
        print("Windows Defender scan skipped:", e)

    return extracted_files
