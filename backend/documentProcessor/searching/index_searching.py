"""
searching.py  – produces a report identical in shape to structured_output.json

Input
-----
markdown_to_json_paragraphs.json   (paragraphs)
1744r2024.json                     (new-style index†)

Output
------
search_result.json                 (list; order == index order)

† The script still accepts the legacy dict index, too.
"""
import json, difflib, re, time
from pathlib import Path
from typing import List, Dict, Tuple, Generator
from openai import OpenAI
import chardet
import os

# ── paths ──────────────────────────────────────────────────────────────────
IDX_PATH   = Path(r"C:\Users\bhola\Desktop\Straive-Work\modified app\backend\temp\1744r2024.json")
PARA_PATH  = Path(r"C:\Users\bhola\Desktop\Straive-Work\modified app\backend\temp\final_markdown_with_full_metadata_paragraphs.json")
OUT_PATH   = Path("index_audit_result2.json")

# ── OpenAI proxy (same as before) ──────────────────────────────────────────
client = OpenAI(
    base_url="https://llmfoundry.straive.com/openai/v1",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImJob2xhLmt1bWFyQHN0cmFpdmUuY29tIn0.jq66OE-OrTGreCoN6-ED8LqO5qVo0g4qRWm5S2SG8UE"
)

# ── helpers (unchanged) ────────────────────────────────────────────────────
def load_json(p: Path):
    """Load JSON file with automatic encoding detection."""
    with open(p, "rb") as f:
        raw = f.read()
        result = chardet.detect(raw)
        encoding = result["encoding"] or "utf-8"  # fallback if None
    with open(p, "r", encoding=encoding) as f:
        return json.load(f)

# iterator that works for both index formats, preserving file order
def iter_index_terms(idx) -> Generator[Tuple[str, str, str], None, None]:
    if isinstance(idx, dict):           # legacy
        for main, subs in idx.items():
            for sub, refs in subs.items():
                for ref in refs:
                    yield main, sub, ref
    elif isinstance(idx, list):         # new
        for entry in idx:
            term = entry.get("term")
            for sub in entry.get("subentries", []):
                text = sub.get("text")
                for ref in sub.get("refs", []):
                    yield term, text, ref
    else:
        raise TypeError("Unknown index structure")

# ── matching utilities (same as before) ────────────────────────────────────
def exact_match(t, s):    return t.lower() in s.lower()
def fuzzy_match(t, s, c=0.85): return bool(difflib.get_close_matches(t.lower(), s.split(), 1, c))
def get_synonyms(t):
    try:
        # time.sleep(1.5)
        rsp = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role":"user",
                       "content":f"Give three synonyms for the legal phrase '{t}' separated by semicolons."}]
        )
        return [w.strip() for w in rsp.choices[0].message.content.split(";") if w.strip()]
    except Exception:
        return []

SEC_RX = re.compile(r"(\d+\.\d+)(\[\d+\])?")
def sec_match(path, sec):
    m = SEC_RX.match(sec)
    if not m:
        return False
    base, sub = m.group(1), m.group(2)
    if not any(base in h for h in path):
        return False
    return True if not sub else any(h.strip().startswith(sub) for h in path)

def llm_match(term, heading, body):
    try:
        # time.sleep(1.5)
        prompt = (
            "Decide whether the following section is about "
            f"the legal term '{term}'. Answer Yes or No.\n\n"
            f"{' > '.join(heading)}\n{body}"
        )
        rsp = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role":"user", "content":prompt}]
        )
        return rsp.choices[0].message.content.strip().lower().startswith("y")
    except Exception:
        return False

# ── main search routine (logic identical, returns dict) ────────────────────
def search(index_data, paras):
    result = {}
    for main, sub, ref in iter_index_terms(index_data):
        key = f"{sub}::{ref}"
        result[key] = "❌ Section not found"   # default

        # candidate paragraphs for §…
        cands = [p for p in paras if sec_match(p["heading_path"], ref)]
        if not cands:
            continue

        # 1 exact
        for p in cands:
            blob = " ".join(p["heading_path"]) + p["text"]
            if exact_match(sub, blob):
                result[key] = "✅ Found [Exact match]"
                break
        if result[key].startswith("✅"): continue

        # 2 synonyms
        # syns = get_synonyms(sub)
        # for p in cands:
        #     blob = " ".join(p["heading_path"]) + p["text"]
        #     if any(exact_match(s, blob) for s in syns):
        #         result[key] = "✅ Found [Synonym match]"
        #         break
        # if result[key].startswith("✅"): continue

        # 3 fuzzy
        for p in cands:
            blob = " ".join(p["heading_path"]) + p["text"].lower()
            if fuzzy_match(sub, blob):
                result[key] = "✅ Found [Fuzzy match]"
                break
        if result[key].startswith("✅"): continue

        # 4 LLM
        for p in cands:
            if llm_match(sub, p["heading_path"], p["text"]):
                result[key] = "✅ Found [LLM match]"
                break
    return result

# ── build structured report in the SAME order/shape as 1744r2024.json ─────
def build_structured_report(index_data, result_map):
    def status_and_flag(st):
        return st, st.startswith("✅")

    if isinstance(index_data, dict):     # legacy dict
        out = []
        for term, subs in index_data.items():
            term_block = {"term": term, "subentries": []}
            for sub, refs in subs.items():
                for ref in refs:
                    key = f"{sub}::{ref}"
                    st, hl = status_and_flag(result_map.get(key, "❌ Not found"))
                    term_block["subentries"].append({
                        "text": sub,
                        "refs": [ref],
                        "status": st,
                        "highlight": hl
                    })
            out.append(term_block)
        return out

    # new format list
    out = []
    for entry in index_data:            # preserves input order
        new_entry = {"term": entry["term"], "subentries": []}
        for sub in entry.get("subentries", []):
            text = sub["text"]
            for ref in sub.get("refs", []):
                key = f"{text}::{ref}"
                st, hl = status_and_flag(result_map.get(key, "❌ Not found"))
                new_entry["subentries"].append({
                    "text": text,
                    "refs": [ref],
                    "status": st,
                    "highlight": hl
                })
        out.append(new_entry)
    return out


def generate_search_report(paragraphs_path: str,index_path: str, output_dir: str):
    output_path = Path(output_dir) / "index_audit_result.json"
    idx = load_json(Path(index_path))
    paras = load_json(Path(paragraphs_path))
    raw = search(idx, paras)
    report = build_structured_report(idx, raw)

    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"✅ index_audit_result.json written to {output_path.resolve()}")
    return output_path




# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    idx  = load_json(IDX_PATH)
    paras = load_json(PARA_PATH)
    raw   = search(idx, paras)
    report = build_structured_report(idx, raw)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"✅ search_result.json written in structured format")