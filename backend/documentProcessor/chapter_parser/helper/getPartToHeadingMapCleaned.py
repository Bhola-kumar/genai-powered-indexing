import json
import re
import os


def getPartToHeadingMapCleaned(input_json_path, output_directory):
    # ──────────────── 1) Load source JSON ────────────────
    with open(input_json_path, 'r', encoding='utf-8') as f:
        chapter_blob = json.load(f)[0]
    raw_text = chapter_blob["content"]

    # ──────────────── 2) Pre-split into lines ────────────────
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]

    # ──────────────── 3) Regex patterns ────────────────
    part_pat = re.compile(r"^PART\s+([IVXLCDM]+)\s*:\s*(.+)$", re.I)
    section_pat = re.compile(r"^§\s*\d+\.\d+\s+.+")
    subsec_pat = re.compile(r"^\[\d+\]\s+.+")  # e.g. [1] text

    # ──────────────── 4) Build the hierarchy ────────────────
    parts = []
    current_part = None
    seen_part_numbers = set()

    for ln in lines:
        if (m := part_pat.match(ln)):
            roman = m.group(1).upper()

            # Stop at repeated PART block (i.e., duplicate index page)
            if roman in seen_part_numbers:
                break
            seen_part_numbers.add(roman)

            if current_part:
                parts.append(current_part)

            current_part = {
                "part_number": roman,
                "part_title": m.group(2).strip(),
                "sections": []
            }
            continue

        if current_part is None:
            continue  # skip until first PART is found

        if section_pat.match(ln):
            current_part["sections"].append(ln)
            continue

        if subsec_pat.match(ln):
            if not current_part["sections"]:
                continue  # malformed input
            last = current_part["sections"][-1]
            if isinstance(last, str):
                last = {"section": last, "subsections": []}
                current_part["sections"][-1] = last
            last["subsections"].append(ln)
            continue

    if current_part:
        parts.append(current_part)

    # ──────────────── 5) Write Output ────────────────
    os.makedirs(output_directory, exist_ok=True)
    output_path = os.path.join(output_directory, "parts_and_sections.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(parts, f, indent=2, ensure_ascii=False)

    print(f"✅ Parts & sections written to {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)
