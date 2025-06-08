import fitz  # PyMuPDF
import json
import re
import os


def getHeadingToPageMap(input_pdf_path, input_bounding_box_json_path, output_directory):
    # Step 1: Read headings from the PDF TOC
    doc = fitz.open(input_pdf_path)
    toc = doc.get_toc()  # [level, title, page]
    
    headings = []
    for level, title, page in toc:
        if level >= 1:
            headings.append({
                "title": title.strip(),
                "page": page
            })

    # Step 2: Load OCR bounding box JSON
    with open(input_bounding_box_json_path, 'r', encoding='utf-8') as f:
        response_data = json.load(f)

    # Step 3: Create page number to text map
    page_text_map = {}
    for page in response_data.get("pages", []):
        page_num = page.get("page_number")
        lines = [line.get("content", "") for line in page.get("lines", [])]
        page_text_map[page_num] = "\n".join(lines)

    # Step 4: Normalize text
    def normalize_text(text):
        if not text:
            return ""
        text = text.replace('\u00A0', ' ')  # Replace non-breaking spaces
        text = text.replace('\t', ' ')
        text = text.replace('\n', ' ')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    # Step 5: Combine text under each heading
    def combine_heading_contents(page_text_map, headings):
        results = []

        # Add dummy end heading
        headings_with_end = headings[1:] + [{"title": "END_OF_DOCUMENT", "page": max(page_text_map.keys())}]

        for i in range(len(headings)-1):
            current = headings_with_end[i]
            next_one = headings_with_end[i + 1]

            start_page = current["page"]
            end_page = next_one["page"]

            combined_text = ""
            for page_num in range(start_page, end_page + 1):
                if page_num in page_text_map:
                    combined_text += page_text_map[page_num] + "\n"

            combined_text = normalize_text(combined_text)

            results.append({
                "title": current["title"],
                "start_page": start_page,
                "end_page": end_page,
                "content": combined_text
            })

        return results

    # Step 6: Run the process
    final_contents = combine_heading_contents(page_text_map, headings)

    # Step 7: Save output
    output_path = os.path.join(output_directory, "heading_to_page_map.json")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_contents, f, ensure_ascii=False, indent=2)

    print(f"✅ Heading-wise combined text saved to {output_path}")
    return output_path

# getHeadingToPageMap(
#     input_pdf_path=r"C:\Users\e430272.SPI-GLOBAL\Desktop\Straive-Work\GenAI Powered Indexing\GenAI-Powered-Indexing\input\manuscriptPdf\01744-ch0003_Release_2024_Jun-28-24-0931 - checked copy.pdf",
#     input_bounding_box_json_path=r"C:\Users\e430272.SPI-GLOBAL\Desktop\Straive-Work\GenAI Powered Indexing\GenAI-Powered-Indexing\backend\documentProcessor\chapter_parser\temp\bounding_box.json"
# )