import os

for root, dirs, files in os.walk("."):
    if ".git" in root:
        continue
    for file in files:
        if file == "clean_history.py":
            continue
        filepath = os.path.join(root, file)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "VisionInspect@Admin2026" in content:
                content = content.replace("VisionInspect@Admin2026", "VisionInspect@Admin2026")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
        except Exception:
            pass
