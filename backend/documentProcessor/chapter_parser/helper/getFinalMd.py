import json
import os
import re


def getFinalMd(part_mapped_to_heading_path, parts_and_sections_path, preprocessed_markdown_path, output_directory):
    # Step 1: Load chapter title
    with open(part_mapped_to_heading_path, "r", encoding="utf-8") as f:
        chapter_title = json.load(f)[0]["title"]

    # Step 2: Load PARTS and SECTIONS
    with open(parts_and_sections_path, "r", encoding="utf-8") as f:
        parts = json.load(f)

    # Build section-to-part mapping
    section_to_part = {}
    for part in parts:
        for entry in part["sections"]:
            if isinstance(entry, str):
                section_to_part[entry] = part
            else:
                section_to_part[entry["section"]] = part
                for sub in entry.get("subsections", []):
                    section_to_part[sub] = part

    # Step 3: Read body markdown
    with open(preprocessed_markdown_path, "r", encoding="utf-8") as f:
        body_lines = f.read().splitlines()

    header_pat = re.compile(r"^(#+)\s+(.*)")
    final_lines = []
    inserted_parts = set()

    # Step 4: Process lines and inject PART headers
    for line in body_lines:
        m = header_pat.match(line)
        if not m:
            final_lines.append(line)
            continue

        old_hashes, title_text = m.groups()

        # 4a) Inject PART header before new section
        if title_text.startswith("§"):
            part = section_to_part.get(title_text)
            if part and part["part_number"] not in inserted_parts:
                final_lines.append("")
                final_lines.append(f"## PART {part['part_number']}: {part['part_title']}")
                final_lines.append("")
                inserted_parts.add(part["part_number"])

        # 4b) Bump heading level down by 2
        new_hashes = "#" * (len(old_hashes) + 2)
        final_lines.append(f"{new_hashes} {title_text}")

    # Step 5: Add chapter title at the top
    chapter_heading = f"# {chapter_title}"
    final_md_text = "\n".join([chapter_heading, ""] + final_lines)

    # Step 6: Write output file
    os.makedirs(output_directory, exist_ok=True)
    output_md_path = os.path.join(output_directory, "chapter_markdown.md")
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(final_md_text)

    print(f"✅ Final markdown written to: {os.path.abspath(output_md_path)}")
    return os.path.abspath(output_md_path)
