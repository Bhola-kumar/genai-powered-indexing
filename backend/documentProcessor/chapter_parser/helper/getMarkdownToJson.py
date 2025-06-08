import os
import re
import json

def getMarkdownToJson(md_path, output_directory):
    
    os.makedirs(output_directory, exist_ok=True)
    json_path = os.path.join(output_directory, "markdown_to_json.json")

    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    data = {}
    stack = []
    buffer = []

    def flush():
        if not stack or not buffer:
            return
        content = "\n".join(buffer).strip()
        if content:
            ref = data
            for level in stack[:-1]:
                if level not in ref or not isinstance(ref[level], dict):
                    ref[level] = {}
                ref = ref[level]
            key = stack[-1]
            if key in ref and isinstance(ref[key], dict):
                ref[key]["_content"] = content
            else:
                ref[key] = content
        buffer.clear()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = re.match(r"^(#+)\s+(.*)", line)
        if match:
            flush()
            level = len(match.group(1))
            title = match.group(2)

            # Normalize the stack to match current level
            stack = stack[:level - 1]
            stack.append(title)
        else:
            buffer.append(line)

    flush()

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return json_path

