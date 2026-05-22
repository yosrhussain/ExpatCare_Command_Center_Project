#!/usr/bin/env python3

import re
import json
import io
from pathlib import Path
import fitz
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

DATA_DIR = Path("data")
OUTPUT_DIR = Path("output")
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

def is_garbage(text):
    if not text.strip():
        return True
    letters = re.sub(r"[^A-Za-z]", "", text)
    if letters.isupper() and not any(v in letters.lower() for v in "aeiou"):
        return True
    if re.search(r"[\uF000-\uF8FF]", text):
        return True
    return False

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"(\w)[\-–—]\n\s*(\w)", r"\1\2", text)
    return text.replace("\r", "").strip()

def extract_page_text(page):
    raw = page.get_text("text") or ""
    if not is_garbage(raw):
        return clean_text(raw)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    try:
        ocr_text = pytesseract.image_to_string(img, lang="ara+eng")
    except:
        ocr_text = pytesseract.image_to_string(img, lang="eng")
    return clean_text(ocr_text)

def process_pdf(pdf_path):
    doc = fitz.open(pdf_path.as_posix())
    out_pages = []
    for i, page in enumerate(doc):
        text = extract_page_text(page)
        out_pages.append({
            "file": pdf_path.name,
            "page_number": i + 1,
            "cleaned_text": text
        })
    doc.close()
    return out_pages

def main():
    pdf_files = sorted([p for p in DATA_DIR.iterdir() if p.suffix.lower() == ".pdf"])
    if not pdf_files:
        print("No PDF files found in ./data/")
        return
    for pdf in pdf_files:
        print(f"Processing: {pdf.name}")
        pages = process_pdf(pdf)
        outname = OUTPUT_DIR / (pdf.stem + "_clean_by_page.json")
        with open(outname, "w", encoding="utf-8") as fh:
            json.dump({"file": pdf.name, "pages": pages}, fh, ensure_ascii=False, indent=2)
        print(f"Saved: {outname}")
    print("\nALL PDFs PROCESSED SUCCESSFULLY ✔")

if __name__ == "__main__":
    main()
