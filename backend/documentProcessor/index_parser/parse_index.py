from pathlib import Path
from docx import Document
import re, json

REF_RX = re.compile(r'(\d+\.\d+(?:\[\d+\])?)')  # e.g. 6.07  or 9.08[6]

def build_index_terms(
    docx_path: str | Path,
    output_directory: str | Path
) -> Path:
    """
    Convert a Word index into index_terms.json (single-level sub-entries).

    Parameters
    ----------
    docx_path : str | Path
        Full path to your index DOCX.
    output_directory : str | Path
        Directory to write the JSON output to.

    Returns
    -------
    Path
        Full path to the written JSON file.
    """
    docx_path = Path(docx_path)
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    out_json = output_directory / (docx_path.stem + ".json")

    doc = Document(docx_path)
    entries, current = [], None

    for p in doc.paragraphs:
        txt = p.text.strip()
        if not txt or (len(txt) == 1 and txt.isupper()):
            continue  # skip blank & A-Z dividers

        if txt.isupper() and len(txt.split()) <= 5:  # MAIN TERM (heuristic)
            current = {"term": txt, "subentries": []}
            entries.append(current)
            continue

        if current is None:
            continue  # safety guard

        refs = REF_RX.findall(txt)
        clean = REF_RX.sub("", txt).strip(" ,;–-")
        if clean or refs:
            current["subentries"].append({"text": clean, "refs": refs})

    out_json.write_text(json.dumps(entries, indent=2, ensure_ascii=False))
    print(f"✔ index terms written → {out_json}  (terms: {len(entries)})")
    return out_json

# ── Example call ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    output_path = build_index_terms(
        r"C:\Users\e430337\Desktop\GenAI-Powered-Indexing\input\indexPage\1744r2024.docx",
        r"C:\Users\e430337\Desktop\GenAI-Powered-Indexing\input\indexPage"
    )
    print(f"Output file path: {output_path}")
