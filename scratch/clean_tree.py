import os

old_password = os.environ.get("OLD_PASSWORD")
new_password = os.environ.get("NEW_PASSWORD")

if not old_password or not new_password:
    raise RuntimeError("Set OLD_PASSWORD and NEW_PASSWORD before running this script.")

for root, dirs, files in os.walk("."):
    if ".git" in root or ".venv" in root or "node_modules" in root:
        continue
    for file in files:
        filepath = os.path.join(root, file)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if old_password in content:
                content = content.replace(old_password, new_password)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
        except Exception:
            pass
