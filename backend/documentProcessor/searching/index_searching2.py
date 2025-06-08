import json, difflib, re
from pathlib import Path
from typing import List, Dict, Tuple, Generator
from openai import OpenAI
import chardet
import os

# ── paths ─────────────────────────────────────────────────────
IDX_PATH   = Path(r"C:\Users\e430272.SPI-GLOBAL\Desktop\Straive-Work\GenAI Powered Indexing\demo\backend\temp\1744r2024.json")
PARA_PATH  = Path(r"C:\Users\e430272.SPI-GLOBAL\Desktop\Straive-Work\GenAI Powered Indexing\demo\backend\temp\combined_json_with_metadata_paragraphs.json")
OUT_PATH   = Path("index_audit_result4.json")

# ── OpenAI Proxy Setup ────────────────────────────────────────
client = OpenAI(
    base_url="https://llmfoundry.straive.com/openai/v1",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImJob2xhLmt1bWFyQHN0cmFpdmUuY29tIn0.jq66OE-OrTGreCoN6-ED8LqO5qVo0g4qRWm5S2SG8UE"
)

# ── Helpers ───────────────────────────────────────────────────
def load_json(p: Path):
    with open(p, "rb") as f:
        raw = f.read()
        enc = chardet.detect(raw)["encoding"] or "utf-8"
    with open(p, "r", encoding=enc) as f:
        return json.load(f)

def iter_index_terms(idx) -> Generator[Tuple[str, str, str], None, None]:
    """
    Yield (main_term, subentry_text, section_ref) for every ref in the index.
    Supports both dict and list structures.
    """
    if isinstance(idx, dict):
        for main, subs in idx.items():
            for sub, refs in subs.items():
                for ref in refs:
                    yield main, sub, ref
    elif isinstance(idx, list):
        for entry in idx:
            term = entry.get("term")
            for sub in entry.get("subentries", []):
                text = sub.get("text")
                for ref in sub.get("refs", []):
                    yield term, text, ref
    else:
        raise TypeError("Unknown index structure")

def exact_match(t, s):           return t.lower() in s.lower()
def fuzzy_match(t, s, c=0.85):   return bool(difflib.get_close_matches(t.lower(), s.split(), 1, c))

SEC_RX = re.compile(r"(\d+\.\d+)(\[\d+\])?")
def sec_match(path, sec):
    """
    Does this heading_path correspond to section-ref '2.05[1]'?
    """
    m = SEC_RX.match(sec)
    if not m:
        return False
    base, sub = m.group(1), m.group(2)
    if not any(base in h for h in path):
        return False
    return True if not sub else any(h.strip().startswith(sub) for h in path)

def llm_match(term, heading, body):
    """
    Last-resort semantic check via GPT.
    """
    try:
        prompt = (
            "Decide whether the following section is about "
            f"the legal term '{term}'. Answer Yes or No.\n\n"
            f"{' > '.join(heading)}\n{body}"
        )
        rsp = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return rsp.choices[0].message.content.strip().lower().startswith("y")
    except Exception:
        return False

# ── Main Search Logic ────────────────────────────────────────
def search(index_data, paras):
    result = {}
    for main, sub, ref in iter_index_terms(index_data):
        key = f"{sub}::{ref}"
        result[key] = {"status": "❌ Section not found"}

        # 1️⃣ restrict paragraphs to matching section numbers
        cands = [p for p in paras if sec_match(p["heading_path"], ref)]
        if not cands:
            continue

        # 2️⃣ exact heading/paragraph text match
        for p in cands:
            if exact_match(sub, " ".join(p["heading_path"]) + p["text"]):
                result[key] = match_payload(p, "Exact match")
                break
        if result[key]["status"].startswith("✅"):
            continue

        # 3️⃣ fuzzy
        for p in cands:
            if fuzzy_match(sub, " ".join(p["heading_path"]) + p["text"]):
                result[key] = match_payload(p, "Fuzzy match")
                break
        if result[key]["status"].startswith("✅"):
            continue

        # 4️⃣ LLM
        for p in cands:
            if llm_match(sub, p["heading_path"], p["text"]):
                result[key] = match_payload(p, "LLM")
                break

    return result

def match_payload(p, matched_by):
    """
    Build the dict stored in result_map[key]
    Now includes chapter_key.
    """
    return {
        "status": f"✅ Found [{matched_by}]",
        "match_details": {
            "chapter_key":   p.get("chapter_key"),      # NEW
            "chapter_number": p.get("chapter_number"),
            "chapter_title":  p.get("chapter_title"),
            "part_title":     p.get("part_title"),
            "section_title":  p.get("section_title"),
            "page_number":    p.get("page_number"),
            "bounding_box":   p.get("bounding_box"),
            "bounding_box_page_numbers": p.get("bounding_box_page_numbers"),
            "paragraph_id": p.get("id"),
            "sha1":         p.get("sha1"),
            "matched_by":   matched_by
        }
    }

# ── Structured Report Builder ─────────────────────────────────
def build_structured_report(index_data, result_map):
    """
    Convert the flat {sub::ref: {status, match_details}} map back into
    the tree/list structure the frontend expects.
    """
    def unpack(res):
        return res["status"], res["status"].startswith("✅"), res.get("match_details")

    out = []

    if isinstance(index_data, dict):          # dict-style index
        for term, subs in index_data.items():
            block = {"term": term, "subentries": []}
            for sub, refs in subs.items():
                for ref in refs:
                    key = f"{sub}::{ref}"
                    st, hl, md = unpack(result_map.get(key, {"status": "❌ Section not found"}))
                    entry = {"text": sub, "refs": [ref], "status": st, "highlight": hl}
                    if md: entry["match_details"] = md
                    block["subentries"].append(entry)
            out.append(block)

    else:                                     # list-style index
        for entry in index_data:
            block = {"term": entry["term"], "subentries": []}
            for sub in entry.get("subentries", []):
                text = sub["text"]
                for ref in sub.get("refs", []):
                    key = f"{text}::{ref}"
                    st, hl, md = unpack(result_map.get(key, {"status": "❌ Section not found"}))
                    itm = {"text": text, "refs": [ref], "status": st, "highlight": hl}
                    if md: itm["match_details"] = md
                    block["subentries"].append(itm)
            out.append(block)
    return out


def generate_search_report(paragraphs_path: str,index_path: str, output_dir: str):
    output_path = Path(output_dir) / "index_audit_result.json"
    idx = load_json(Path(index_path))
    paras = load_json(Path(paragraphs_path))
    result_map = search(idx,paras)
    report = build_structured_report(idx,result_map)

    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"✅ index_audit_result.json written to {output_path.resolve()}")
    return output_path

# ── Entry Point ──────────────────────────────────────────────
if __name__ == "__main__":
    index_data = load_json(IDX_PATH)
    paras      = load_json(PARA_PATH)

    result_map = search(index_data, paras)
    audit      = build_structured_report(index_data, result_map)

    OUT_PATH.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✔ Done: {len(audit)} index terms processed → {OUT_PATH}")
