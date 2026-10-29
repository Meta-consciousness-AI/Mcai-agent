import hashlib, json, urllib.request
from pathlib import Path
data = json.load(urllib.request.urlopen("https://pypi.org/pypi/mcai-knowledge/json", timeout=20))
info = data["info"]
print("version:", info["version"])
desc = info.get("description") or ""
print("description has mcp-name:", "mcp-name: io.github.Meta-consciousness-AI/mcai-knowledge" in desc)
for f in data["urls"]:
    print(f["filename"], f["size"], f["digests"]["sha256"][:16])
local = Path("dist_pkg/mcai_knowledge-0.2.1-py3-none-any.whl")
print("match:", hashlib.sha256(local.read_bytes()).hexdigest() == data["urls"][0]["digests"]["sha256"])