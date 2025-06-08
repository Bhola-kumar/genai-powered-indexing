from pathlib import Path
from typing import Union, List, Dict
import json, re, hashlib, itertools

# ------------------------------------------------------------------------
# normaliser and helpers
CLEAN_RX = re.compile(r"[^\w\s]")  # strip punctuation

def _norm(txt: str) -> str:
    return CLEAN_RX.sub(" ", txt.lower()).strip()

SPLIT_HR = re.compile(r"\s*---\s*", flags=re.MULTILINE)  # “---”  → paragraph break

# ------------------------------------------------------------------------
def nested_json_to_paragraphs(
    nested_json_path: Union[str, Path],      # your existing nested JSON
    output_directory: Union[str, Path]       # directory to save the output file
) -> Path:
    """
    Flatten nested-heading JSON into audit-ready paragraphs.

    Parameters:
    - nested_json_path: Input nested JSON file path
    - output_directory: Directory where the output file will be saved

    Returns:
    - Path to the generated paragraph JSON file
    """
    nested_json_path = Path(nested_json_path)
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    nested = json.loads(nested_json_path.read_text(encoding="utf8"))

    output_filename = nested_json_path.stem + "_paragraphs.json"
    out_json_path = output_directory / output_filename

    records: List[Dict] = []
    pid = itertools.count(1)  # running id counter

    def recurse(node, heading_stack: List[str]):
        if isinstance(node, dict):
            for key, child in node.items():
                recurse(child, heading_stack + [key])
        else:
            raw = str(node)
            for piece in filter(None, SPLIT_HR.split(raw)):
                paragraph = piece.strip()
                if not paragraph:
                    continue
                rid = next(pid)
                records.append({
                    "id": rid,
                    "heading_path": heading_stack,
                    "text": paragraph,
                    "norm_text": _norm(paragraph),
                    "sha1": hashlib.sha1(_norm(paragraph).encode()).hexdigest(),
                })

    recurse(nested, [])
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


    print(f"✔ paragraph JSON written → {out_json_path}  (paragraphs: {len(records)})")
    
    
    return out_json_path

# ------------------------------------------------------------------------
# Example usage — will return output path
if __name__ == "__main__":
    output_path = nested_json_to_paragraphs(
        r"C:\Users\e430272.SPI-GLOBAL\Desktop\Straive-Work\GenAI Powered Indexing\GenAI-Powered-Indexing\backend\documentProcessor\chapter_parser\temp\markdown_to_json.json",
        r"C:\Users\e430272.SPI-GLOBAL\Desktop\Straive-Work\GenAI Powered Indexing\GenAI-Powered-Indexing\backend\documentProcessor\chapter_parser\temp"
    )
    print(f"Output file path: {output_path}")
