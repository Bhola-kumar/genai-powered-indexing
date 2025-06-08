import json
import re
import os
from typing import Optional


def getHeadingToContentMap(input_json_path, output_directory):
    def canonical(s: str) -> str:
        return re.sub(r"\s+", " ", s.replace("\u00A0", " ")).strip()

    def build_regex(title: str) -> re.Pattern:
        pat = re.escape(title.replace("\u00A0", " "))
        pat = pat.replace(r"\ ", r"\s+")
        return re.compile(pat, re.MULTILINE)

    def extract_body(cur_block: dict, next_block: Optional[dict]) -> str:
        raw = cur_block["content"]
        cur_pat = build_regex(cur_block["title"])
        m_cur = cur_pat.search(raw)
        start = m_cur.end() if m_cur else 0

        if next_block:
            next_pat = build_regex(next_block["title"])
            m_next = next_pat.search(raw, pos=start)
            end = m_next.start() if m_next else len(raw)
        else:
            end = len(raw)

        return raw[start:end].lstrip()

    # Load JSON blocks
    with open(input_json_path, encoding="utf-8") as f:
        blocks = json.load(f)

    # Sort blocks by page order with original index tie-breaker
    blocks = sorted(enumerate(blocks), key=lambda t: (t[1]["start_page"], t[0]))
    blocks = [b for _, b in blocks]

    # Extract and format body text
    extracted = []
    for i, blk in enumerate(blocks):
        nxt = blocks[i + 1] if i + 1 < len(blocks) else None
        extracted.append({"title": blk["title"], "body": extract_body(blk, nxt)})

    # Construct output path and write to Markdown
    os.makedirs(output_directory, exist_ok=True)
    output_md_path = os.path.join(output_directory, "heading_to_content_map.md")

    with open(output_md_path, "w", encoding="utf-8") as md:
        for item in extracted:
            md.write(f"### {canonical(item['title'])}\n\n")
            md.write(item["body"].strip())
            md.write("\n\n---\n\n")

    print(f"✅ Markdown saved to {output_md_path}")
    return output_md_path
