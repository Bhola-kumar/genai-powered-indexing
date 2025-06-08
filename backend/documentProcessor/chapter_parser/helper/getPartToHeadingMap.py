import fitz  # PyMuPDF
import json
import re
import os


def getPartToHeadingMap(pdf_path, ocr_json_path, output_directory):
    # Step 1: Read headings from the PDF TOC
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()  # [level, title, page]

    # Build headings list
    headings = []
    for level, title, page in toc:
        if level >= 1:
            headings.append({
                "title": title.strip(),
                "page": page
            })

    if len(headings) < 2:
        raise ValueError("PDF TOC must have at least a chapter heading and one more heading")

    # Step 2: Load OCR bounding box JSON
    with open(ocr_json_path, 'r', encoding='utf-8') as f:
        response_data = json.load(f)

    # Step 3: Create page number to text map
    page_text_map = {}
    for page in response_data.get("pages", []):
        page_num = page.get("page_number")
        lines = [line.get("content", "") for line in page.get("lines", [])]
        page_text_map[page_num] = "\n".join(lines)

    # Step 4: Extract only the first section (likely the chapter + index listing)
    chapter_heading_title = headings[0]["title"]
    start_page = headings[0]["page"]
    end_page = headings[1]["page"]  # Stop *before* next heading

    combined_text = ""
    for page_num in range(start_page, end_page + 1):
        if page_num in page_text_map:
            combined_text += page_text_map[page_num] + "\n"

    chapter_data = [{
        "title": chapter_heading_title,
        "start_page": start_page,
        "end_page": end_page,
        "content": combined_text
    }]

    # Step 5: Save output in the given directory
    os.makedirs(output_directory, exist_ok=True)
    output_path = os.path.join(output_directory, "part_mapped_to_heading.json")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chapter_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Chapter index saved to: {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)
