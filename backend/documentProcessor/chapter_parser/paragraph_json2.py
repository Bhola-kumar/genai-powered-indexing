from pathlib import Path
from typing import Union, List, Dict
import json, re, hashlib, itertools

# ------------------------------------------------------------------------
CLEAN_RX = re.compile(r"[^\w\s]")
SPLIT_HR = re.compile(r"\s*---\s*", flags=re.MULTILINE)


def _norm(txt: str) -> str:
    return CLEAN_RX.sub(" ", txt.lower()).strip()


def extract_chapter_metadata(chapter_heading: str):
    match = re.match(r"Chapter (\d+)\s+(.*)", chapter_heading, re.IGNORECASE)
    if match:
        return match.group(1), match.group(2).strip()
    return None, chapter_heading.strip()


def full_metadata_to_paragraphs(
    metadata_json_path: Union[str, Path],
    output_directory: Union[str, Path]
) -> Path:
    metadata_json_path = Path(metadata_json_path)
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    metadata = json.loads(metadata_json_path.read_text(encoding="utf8"))

    output_filename = metadata_json_path.stem + "_paragraphs.json"
    out_json_path = output_directory / output_filename

    records: List[Dict] = []
    pid = itertools.count(1)

    for chapter_heading, parts in metadata.items():
        chapter_number, chapter_title = extract_chapter_metadata(chapter_heading)

        for part_title, sections in parts.items():
            for section_title, content_dict in sections.items():
                section_text = content_dict.get("section_text", "")
                page_number = content_dict.get("page_number")
                bounding_box = content_dict.get("bounding_box")

                for piece in filter(None, SPLIT_HR.split(section_text)):
                    paragraph = piece.strip()
                    if not paragraph:
                        continue
                    rid = next(pid)
                    records.append({
                        "id": rid,
                        "chapter_number": chapter_number,
                        "chapter_title": chapter_title,
                        "part_title": part_title,
                        "section_title": section_title,
                        "heading_path": [chapter_heading, part_title, section_title],
                        "page_number": page_number,
                        "bounding_box": bounding_box,
                        "text": paragraph,
                        "norm_text": _norm(paragraph),
                        "sha1": hashlib.sha1(_norm(paragraph).encode()).hexdigest()
                    })

    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"✔ paragraph JSON written → {out_json_path}  (paragraphs: {len(records)})")
    return out_json_path


if __name__ == "__main__":
    output_path = full_metadata_to_paragraphs(
        r"C:\Users\bhola\Desktop\Straive-Work\modified app\backend\temp\final_markdown_with_full_metadata.json",
        r"C:\Users\bhola\Desktop\Straive-Work\modified app\backend\temp"
    )
    print(f"Output file path: {output_path}")
