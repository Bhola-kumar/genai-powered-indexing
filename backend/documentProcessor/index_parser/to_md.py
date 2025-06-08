import json
from pathlib import Path
import re

# === Input/Output Paths ===
input_json_path = Path(r"C:\Users\e430272.SPI-GLOBAL\Desktop\Straive-Work\GenAI Powered Indexing\GenAI-Powered-Indexing\backend\temp\index_terms_with_styles.json")  # Your styled JSON file
output_md_path = Path("index_terms_output.md")

# === Function to convert style to markdown hash ===
def style_to_hash(style: str) -> str:
    if style.lower() == "main":
        return "#"
    match = re.match(r"sub (\d+)", style.lower())
    if match:
        level = int(match.group(1))
        return "#" * (level + 1)  # Sub 1 = ##, Sub 2 = ###, etc.
    return ""  # Default: no heading for unknown or ahead

# === Load JSON and Write Markdown ===
with open(input_json_path, "r", encoding="utf-8") as f:
    entries = json.load(f)

with open(output_md_path, "w", encoding="utf-8") as md_file:
    for entry in entries:
        text = entry.get("text", "").strip()
        style = entry.get("style", "").strip()
        if not text:
            continue  # skip empty text

        prefix = style_to_hash(style)
        md_line = f"{prefix} {text}".strip()
        md_file.write(md_line + "\n")

print(f"✅ Markdown file saved at: {output_md_path}")