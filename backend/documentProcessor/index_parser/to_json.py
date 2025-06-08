#creates a json file with style tags
from docx import Document
import json
from pathlib import Path

# === INPUT ===
docx_path = r"C:\Users\e430272.SPI-GLOBAL\Desktop\Straive-Work\GenAI Powered Indexing\GenAI-Powered-Indexing\input\manuscriptsDocx\01744-ch0002_Release_2024_Jun-28-24-0931 - checked.docx"  # Replace with your actual file path
doc = Document(docx_path)

# === OUTPUT JSON FILE PATH ===
output_path = Path("index_terms_with_styles.json")

# === COLLECT TEXT + STYLE ===
data = []
for para in doc.paragraphs:
    text = para.text.strip()
    style = para.style.name if para.style else "Unknown"
    if text:  # skip empty lines
        data.append({
            "text": text,
            "style": style
        })

# === SAVE TO JSON ===
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Saved {len(data)} styled lines to {output_path}")