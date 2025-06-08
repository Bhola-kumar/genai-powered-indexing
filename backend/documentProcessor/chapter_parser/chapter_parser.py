"""
chapter_parser.py
-----------------

• convert_chapter_to_json(path, …)         – runs pipeline for one chapter
  ↳ NOW returns { <chapter_key>: <metadata-dict> }

• convert_chapters_to_single_json(paths…)  – merges many chapters into one
  big dict keyed by chapter file-stem.

Run directly:
    python -m documentProcessor.chapter_parser.chapter_parser
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Dict, Any, Union

# ── helper imports ────────────────────────────────────────────────────────
from .helper.convert_docx_to_pdf import convert_docx_to_pdf
from .helper.getBoundingBox import getBoundingBox
from .helper.getHeadingToPageMap import getHeadingToPageMap
from .helper.getHeadingToContentMap import getHeadingToContentMap
from .helper.getPreprocessMd import getPreprocessMd
from .helper.getPartToHeadingMap import getPartToHeadingMap
from .helper.getPartToHeadingMapCleaned import getPartToHeadingMapCleaned
from .helper.getFinalMd import getFinalMd
from .helper.getMarkdownToJson2 import getMarkdownToJson2

# ── centralised config ────────────────────────────────────────────────────
PATH_TO_LIBREOFFICE                 = r"C:\Users\e430272.SPI-GLOBAL\Downloads\LibreOfficePortable\App\libreoffice\program\soffice.exe"
TEMPORARY_DIRECTORY                 = r"C:\Users\e430272.SPI-GLOBAL\Desktop\Straive-Work\GenAI Powered Indexing\demo\backend\temp"
AZURE_ENDPOINT                      = "https://llmfoundry.straive.com/azureformrecognizer/analyze"
AZURE_API_KEY                       = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImJob2xhLmt1bWFyQHN0cmFpdmUuY29tIn0.jq66OE-OrTGreCoN6-ED8LqO5qVo0g4qRWm5S2SG8UE"
AZURE_DOCUMENT_AI_INTELLIGENCE_MODEL = "prebuilt-document"

# ──────────────────────────────────────────────────────────────────────────
# 1)  SINGLE-CHAPTER PIPELINE
# ──────────────────────────────────────────────────────────────────────────
def convert_chapter_to_json(
    chapter_path: Union[str, Path],
    *,
    PATH_TO_LIBREOFFICE: str = PATH_TO_LIBREOFFICE,
    TEMPORARY_DIRECTORY: str = TEMPORARY_DIRECTORY,
    AZURE_API_KEY: str = AZURE_API_KEY,
    AZURE_ENDPOINT: str = AZURE_ENDPOINT,
    AZURE_DOCUMENT_AI_INTELLIGENCE_MODEL: str = AZURE_DOCUMENT_AI_INTELLIGENCE_MODEL,
) -> Dict[str, Any] | None:
    """
    Return **{ <chapter_key>: <metadata-dict> }** for a single chapter file.
    where <chapter_key> = Path(chapter_path).stem
    """
    try:
        chapter_path = Path(chapter_path)
        chap_key     = chapter_path.stem
        print(f"\n=== Processing {chapter_path.name} ===")

        # 1️⃣  DOCX → PDF if needed
        if chapter_path.suffix.lower() == ".docx":
            print("📄 Converting DOCX → PDF …")
            chapter_path = convert_docx_to_pdf(
                str(chapter_path), PATH_TO_LIBREOFFICE, TEMPORARY_DIRECTORY
            )

        # 2️⃣  Bounding boxes
        print("📦 Extracting bounding boxes …")
        bbox_json = getBoundingBox(
            str(chapter_path),
            TEMPORARY_DIRECTORY,
            AZURE_ENDPOINT,
            AZURE_API_KEY,
            AZURE_DOCUMENT_AI_INTELLIGENCE_MODEL,
        )

        # 3️⃣  Heading → page map
        print("📍 Mapping headings to pages …")
        heading_to_page = getHeadingToPageMap(
            str(chapter_path), bbox_json, TEMPORARY_DIRECTORY
        )

        # 4️⃣  Heading → content markdown
        print("📝 Building heading/content markdown …")
        heading_to_content_md = getHeadingToContentMap(
            heading_to_page, TEMPORARY_DIRECTORY
        )

        # 5️⃣  Pre-process markdown
        print("🧹 Pre-processing markdown …")
        preprocess_md = getPreprocessMd(
            str(chapter_path), heading_to_content_md, TEMPORARY_DIRECTORY
        )

        # 6️⃣  Raw TOC map
        print("📘 Extracting raw TOC map …")
        part_to_heading = getPartToHeadingMap(
            str(chapter_path), bbox_json, TEMPORARY_DIRECTORY
        )

        # 7️⃣  Cleaned TOC map
        print("🧽 Cleaning TOC map …")
        part_to_heading_clean = getPartToHeadingMapCleaned(
            part_to_heading, TEMPORARY_DIRECTORY
        )

        # 8️⃣  Final markdown
        print("📐 Generating final markdown …")
        final_md = getFinalMd(
            part_to_heading,
            part_to_heading_clean,
            preprocess_md,
            TEMPORARY_DIRECTORY,
        )

        # 9️⃣  Markdown → JSON
        print("📊 Converting markdown → JSON …")
        inner_json = getMarkdownToJson2(
            final_md, chapter_path, bbox_json, TEMPORARY_DIRECTORY
        )

        # handle case where helper returned a path string
        if isinstance(inner_json, str) and Path(inner_json).is_file():
            inner_json = json.loads(Path(inner_json).read_text(encoding="utf-8"))

        if not isinstance(inner_json, dict):
            raise TypeError(f"getMarkdownToJson2 should yield dict; got {type(inner_json).__name__}")

        print("✅ Completed.")
        return {chap_key: inner_json}   # ← chapter key wrapper

    except Exception as exc:
        print(f"❌ Error while processing {chapter_path.name}: {exc}")
        return None


# ──────────────────────────────────────────────────────────────────────────
# 2)  MULTI-CHAPTER WRAPPER
# ──────────────────────────────────────────────────────────────────────────
def convert_chapters_to_single_json(
    chapter_paths: Union[Iterable[Union[str, Path]], str, Path],
    *,
    PATH_TO_LIBREOFFICE: str = PATH_TO_LIBREOFFICE,
    TEMPORARY_DIRECTORY: str = TEMPORARY_DIRECTORY,
    AZURE_API_KEY: str = AZURE_API_KEY,
    AZURE_ENDPOINT: str = AZURE_ENDPOINT,
    AZURE_DOCUMENT_AI_INTELLIGENCE_MODEL: str = AZURE_DOCUMENT_AI_INTELLIGENCE_MODEL,
    out_path: Union[str, Path] | None = None,
) -> Dict[str, Any]:
    """
    Return one dict:

        {
           "<chapter_key-1>": {...},
           "<chapter_key-2>": {...},
           ...
        }
    """
    chapter_iter = [chapter_paths] if isinstance(chapter_paths, (str, Path)) else list(chapter_paths)
    combined: Dict[str, Any] = {}

    for p in chapter_iter:
        result = convert_chapter_to_json(
            p,
            PATH_TO_LIBREOFFICE=PATH_TO_LIBREOFFICE,
            TEMPORARY_DIRECTORY=TEMPORARY_DIRECTORY,
            AZURE_API_KEY=AZURE_API_KEY,
            AZURE_ENDPOINT=AZURE_ENDPOINT,
            AZURE_DOCUMENT_AI_INTELLIGENCE_MODEL=AZURE_DOCUMENT_AI_INTELLIGENCE_MODEL,
        )
        if result:
            combined.update(result)

    # Persist to disk
    if out_path is None:
        out_path = Path(TEMPORARY_DIRECTORY) / "combined_json_with_metadata.json"
    else:
        out_path = Path(out_path)

    # out_path.write_text(json.dumps(combined, indent=2, ensure_ascii=False), encoding="utf-8")
    with open(out_path,"w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
    print(f"💾 Combined JSON written to {out_path.resolve()}")

    return out_path


# ──────────────────────────────────────────────────────────────────────────
# 3)  DEMO
# ──────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    all_paths = [
        r"C:\Users\bhola\Desktop\Straive-Work\modified app\input\manuscriptPdf\01744-ch0002_Release_2024_Jun-28-24-0931 - checked.pdf",
        r"C:\Users\bhola\Desktop\Straive-Work\modified app\input\manuscriptPdf\01744-ch0003_Release_2024_Jun-28-24-0931 - checked copy.pdf",
    ]

    convert_chapters_to_single_json(all_paths)
