import fitz  # PyMuPDF
import json, re, os
from difflib import SequenceMatcher

# -------------------------------------------------------------------
# NOTE: function signature unchanged
# -------------------------------------------------------------------
def getMarkdownToJson2(markdown_path, pdf_path, bounding_box_path, output_directory):
    os.makedirs(output_directory, exist_ok=True)
    json_path = os.path.join(output_directory, "markdown_to_json.json")

    # ---------------- helpers --------------------------------------
    def normalize(t): return re.sub(r"[^\w\s]", "", t.lower()).strip()

    def get_top_corners(poly):
        if poly and len(poly) >= 2:
            return poly[0], poly[1]
        return None, None

    # ---------------- step-1  read markdown ------------------------
    with open(markdown_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # ---------------- step-2  PDF TOC → heading-to-page ------------
    doc = fitz.open(pdf_path)
    heading_to_page = {normalize(title): page for _, title, page in doc.get_toc()}

    # ---------------- step-3  bounding-box json → quick map --------
    with open(bounding_box_path, "r", encoding="utf-8") as f:
        bounding_data = json.load(f)

    # “content → {page, polygon}”
    line_bbox_map = {}
    for page in bounding_data.get("pages", []):
        pno = page.get("page_number")
        for ln in page.get("lines", []):
            txt = ln.get("content", "").strip()
            poly = ln.get("polygon")
            if txt and poly:
                line_bbox_map[normalize(txt)] = {"page_number": pno, "polygon": poly}

    # ---------------- step-4  walk markdown → hierarchical dict ----
    data, stack, buffer = {}, [], []

    def flush():
        if not stack or not buffer:
            buffer.clear()
            return

        content = "\n".join(buffer).strip()
        buffer.clear()
        if not content:
            return

        # descend into nested dicts per heading level
        ref = data
        for h in stack[:-1]:
            ref = ref.setdefault(h, {})

        key = stack[-1]
        norm_key = normalize(key)
        page_num = heading_to_page.get(norm_key)

        # find best polygon on that page (fuzzy match)
        best_ratio, best_poly = 0, None
        if page_num:
            for ln in bounding_data.get("pages", []):
                if ln.get("page_number") != page_num:
                    continue
                for line in ln.get("lines", []):
                    ratio = SequenceMatcher(None, key.lower(), line.get("content", "").lower()).ratio()
                    if ratio > 0.6 and ratio > best_ratio:
                        best_ratio = ratio
                        best_poly = line.get("polygon")

        ref[key] = {
            "section_text": content,
            "page_number": page_num,
            "bounding_box": best_poly,
            # four identical entries for now; will adjust later
            "bounding_box_page_numbers": [page_num] * 4
        }

    # walk the markdown lines
    for raw in lines:
        txt = raw.strip()
        if not txt:
            continue
        m = re.match(r"^(#+)\s+(.*)", txt)
        if m:
            flush()
            level = len(m.group(1))
            title = m.group(2).replace(" (Page", "").strip()
            stack = stack[: level - 1] + [title]
        else:
            buffer.append(txt)
    flush()

    # ---------------- step-5  extend box down to next heading ------
    def propagate_boxes(node):
        if not isinstance(node, dict):
            return
        keys = list(node.keys())
        for i, key in enumerate(keys):
            cur = node[key]
            if isinstance(cur, dict) and "section_text" in cur:
                # current box + pages
                cur_poly = cur.get("bounding_box")
                cur_pages = cur.get("bounding_box_page_numbers")
                cur_page  = cur.get("page_number")

                # next heading info (if any)
                nxt_page = nxt_poly = None
                if i + 1 < len(keys):
                    nxt = node[keys[i + 1]]
                    if isinstance(nxt, dict):
                        nxt_page = nxt.get("page_number")
                        nxt_poly = nxt.get("bounding_box")

                # reuse current corners; swap bottoms with next heading's tops
                if cur_poly:
                    tl, tr = get_top_corners(cur_poly)
                    bl, br = tl, tr
                    if nxt_poly:
                        bl, br = get_top_corners(nxt_poly)
                    cur["bounding_box"] = [tl, tr, bl, br]

                    # update page-number list
                    cur["bounding_box_page_numbers"] = [
                        cur_page,                      # TL
                        cur_page,                      # TR
                        nxt_page or cur_page,          # BL
                        nxt_page or cur_page           # BR
                    ]
            else:
                propagate_boxes(cur)

    propagate_boxes(data)

    # ---------------- step-6  write file ---------------------------
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return json_path
