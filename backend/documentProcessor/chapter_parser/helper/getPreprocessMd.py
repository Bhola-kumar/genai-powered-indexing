import fitz  # PyMuPDF
import re
from pathlib import Path


def getPreprocessMd(chapter_path, heading_to_content_map_md_path, output_directory):
    # Step 1: Extract TOC and convert to Markdown-style headings
    doc = fitz.open(chapter_path)
    toc = doc.get_toc()  # returns [level, title, page]

    toc_list = []
    for level, title, page in toc:
        toc_list.append(f"{'#' * (level - 1)}# {title}")

    toc_list = toc_list[1:]  # Remove first dummy or unwanted heading if needed

    # Step 2: Prepare input/output paths
    md_path = Path(heading_to_content_map_md_path)
    out_path = Path(output_directory) / "preprocessed_markdown.md"

    md_lines = md_path.read_text(encoding="utf-8").splitlines()
    toc_iter = iter(toc_list)

    header_pat = re.compile(r"^(#+)\s+(.*)")  # capture heading hashes and title
    updated_lines: list[str] = []

    for line in md_lines:
        m = header_pat.match(line)
        if m:
            try:
                toc_heading = next(toc_iter)
            except StopIteration:
                # TOC exhausted, keep current heading as is
                updated_lines.append(line)
                continue

            desired_hashes = header_pat.match(toc_heading).group(1)
            title_text = m.group(2)
            updated_line = f"{desired_hashes} {title_text}"
            updated_lines.append(updated_line)
        else:
            updated_lines.append(line)

    # Step 3: Write updated markdown to file
    out_path.write_text("\n".join(updated_lines), encoding="utf-8")
    print(f"✅ Preprocessed markdown written to: {out_path.resolve()}")

    return str(out_path.resolve())
