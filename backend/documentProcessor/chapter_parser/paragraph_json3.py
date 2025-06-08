# """
# metadata_to_paragraphs.py
# =========================

# Flatten the combined-chapter metadata JSON into a single
# <*_paragraphs.json> file.  Works with the new structure:

# {
#   "<chapter_key-1>": {                     # ← file-stem
#       "Chapter 2 JURISDICTION": { … },
#       ...
#   },
#   "<chapter_key-2>": { … },
#   ...
# }

# Key function
# ------------
# full_metadata_to_paragraphs(metadata_json_path, output_directory) → Path
# """

# from __future__ import annotations

# import json, re, hashlib, itertools
# from pathlib import Path
# from typing import Union, List, Dict, Generator

# # ── helpers ──────────────────────────────────────────────────────────────
# CLEAN_RX  = re.compile(r"[^\w\s]")
# SPLIT_HR  = re.compile(r"\s*---\s*", flags=re.MULTILINE)

# def _norm(txt: str) -> str:
#     return CLEAN_RX.sub(" ", txt.lower()).strip()

# def _extract_chapter_meta(chapter_heading: str):
#     """
#     "Chapter 2 JURISDICTION" -> ("2", "JURISDICTION")
#     If no match, returns (None, heading)
#     """
#     m = re.match(r"Chapter (\d+)\s+(.*)", chapter_heading, re.I)
#     return (m.group(1), m.group(2).strip()) if m else (None, chapter_heading.strip())

# def _walk_content(
#     current_path: List[str],
#     content_dict: Dict,
# ) -> Generator[tuple[List[str], Dict], None, None]:
#     """Yield (heading_path, leaf_dict) for every nested leaf containing section_text."""
#     if "section_text" in content_dict:
#         yield current_path, content_dict

#     for key, val in content_dict.items():
#         if key in {"section_text", "page_number", "bounding_box", "bounding_box_page_numbers"}:
#             continue
#         if isinstance(val, dict):
#             yield from _walk_content(current_path + [key], val)


# # ── main transformer ─────────────────────────────────────────────────────
# def full_metadata_to_paragraphs(
#     metadata_json_path: Union[str, Path],
#     output_directory: Union[str, Path],
# ) -> Path:
#     metadata_json_path = Path(metadata_json_path)
#     output_directory   = Path(output_directory)
#     output_directory.mkdir(parents=True, exist_ok=True)

#     metadata      = json.loads(metadata_json_path.read_text(encoding="utf-8"))
#     out_json_path = output_directory / f"{metadata_json_path.stem}_paragraphs.json"

#     records: List[Dict] = []
#     pid = itertools.count(1)

#     # ── FIRST level = chapter_key (file-stem) ────────────────────────────
#     for chapter_key, chapter_dict in metadata.items():
#         # SECOND level = real 'Chapter X …' heading
#         for chapter_heading, parts in chapter_dict.items():
#             chap_num, chap_title = _extract_chapter_meta(chapter_heading)

#             for part_title, sections in parts.items():
#                 for section_title, section_dict in sections.items():
#                     for heading_path, leaf in _walk_content(
#                         [chapter_heading, part_title, section_title], section_dict
#                     ):
#                         text_blob = leaf.get("section_text", "")
#                         page_num  = leaf.get("page_number")
#                         bbox      = leaf.get("bounding_box")
#                         bbox_pages= leaf.get("bounding_box_page_numbers")

#                         for piece in filter(None, SPLIT_HR.split(text_blob)):
#                             paragraph = piece.strip()
#                             if not paragraph:
#                                 continue
#                             rid = next(pid)
#                             records.append(
#                                 {
#                                     "id": rid,
#                                     "chapter_key": chapter_key,          # NEW
#                                     "chapter_number": chap_num,
#                                     "chapter_title": chap_title,
#                                     "part_title": part_title,
#                                     "section_title": section_title,
#                                     "heading_path": heading_path,
#                                     "page_number": page_num,
#                                     "bounding_box": bbox,
#                                     "bounding_box_page_numbers": bbox_pages,
#                                     "text": paragraph,
#                                     "norm_text": _norm(paragraph),
#                                     "sha1": hashlib.sha1(_norm(paragraph).encode()).hexdigest(),
#                                 }
#                             )

#     out_json_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
#     print(f"✔ paragraphs JSON written → {out_json_path}   (total: {len(records)})")
#     return out_json_path


# llm foundry version
from __future__ import annotations

import json, re, hashlib, itertools
from pathlib import Path
from typing import Union, List, Dict, Generator

# ── helpers ──────────────────────────────────────────────────────────────
CLEAN_RX  = re.compile(r"[^\w\s]")
SPLIT_HR  = re.compile(r"\s*---\s*", flags=re.MULTILINE)

def _norm(txt: str) -> str:
    return CLEAN_RX.sub(" ", txt.lower()).strip()

def _extract_chapter_meta(chapter_heading: str):
    """
    "Chapter 2 JURISDICTION" -> ("2", "JURISDICTION")
    If no match, returns (None, heading)
    """
    m = re.match(r"Chapter (\d+)\s+(.*)", chapter_heading, re.I)
    return (m.group(1), m.group(2).strip()) if m else (None, chapter_heading.strip())

def _walk_content(
    current_path: List[str],
    content_dict: Union[Dict, str],
) -> Generator[tuple[List[str], Dict], None, None]:
    """Yield (heading_path, leaf_dict) for every nested leaf containing section_text."""
    if isinstance(content_dict, dict) and "section_text" in content_dict:
        yield current_path, content_dict

    if isinstance(content_dict, dict):
        for key, val in content_dict.items():
            if key in {"section_text", "page_number", "bounding_box", "bounding_box_page_numbers"}:
                continue
            if isinstance(val, dict):
                yield from _walk_content(current_path + [key], val)
            elif isinstance(val, str):
                # Handle the case where a value is a string
                # This is crucial for the error you were encountering
                pass  # Skip string values


# ── main transformer ─────────────────────────────────────────────────────
def full_metadata_to_paragraphs(
    metadata_json_path: Union[str, Path],
    output_directory: Union[str, Path],
) -> Path:
    metadata_json_path = Path(metadata_json_path)
    output_directory   = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    try:
        metadata      = json.loads(metadata_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None  # Or handle the error in a more appropriate way

    out_json_path = output_directory / f"{metadata_json_path.stem}_paragraphs.json"

    records: List[Dict] = []
    pid = itertools.count(1)

    # ── FIRST level = chapter_key (file-stem) ────────────────────────────
    for chapter_key, chapter_dict in metadata.items():
        # SECOND level = real 'Chapter X …' heading
        for chapter_heading, parts in chapter_dict.items():
            chap_num, chap_title = _extract_chapter_meta(chapter_heading)

            for part_title, sections in parts.items():
                for section_title, section_dict in sections.items():
                    for heading_path, leaf in _walk_content(
                        [chapter_heading, part_title, section_title], section_dict
                    ):
                        text_blob = leaf.get("section_text", "")
                        page_num  = leaf.get("page_number")
                        bbox      = leaf.get("bounding_box")
                        bbox_pages= leaf.get("bounding_box_page_numbers")

                        for piece in filter(None, SPLIT_HR.split(text_blob)):
                            paragraph = piece.strip()
                            if not paragraph:
                                continue
                            rid = next(pid)
                            records.append(
                                {
                                    "id": rid,
                                    "chapter_key": chapter_key,
                                    "chapter_number": chap_num,
                                    "chapter_title": chap_title,
                                    "part_title": part_title,
                                    "section_title": section_title,
                                    "heading_path": heading_path,
                                    "page_number": page_num,
                                    "bounding_box": bbox,
                                    "bounding_box_page_numbers": bbox_pages,
                                    "text": paragraph,
                                    "norm_text": _norm(paragraph),
                                    "sha1": hashlib.sha1(_norm(paragraph).encode()).hexdigest(),
                                }
                            )

    try:
        out_json_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✔ paragraphs JSON written → {out_json_path}   (total: {len(records)})")
        return out_json_path
    except Exception as e:
        print(f"Error writing JSON: {e}")
        return None
# ── demo call ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    output_file = full_metadata_to_paragraphs(
        r"C:\Users\bhola\Desktop\ddmo\backend\temp\combined_json_with_metadata.json",
        r"C:\Users\bhola\Desktop\ddmo\backend\temp",
    )
    if output_file:
        print("Output file:", output_file)
