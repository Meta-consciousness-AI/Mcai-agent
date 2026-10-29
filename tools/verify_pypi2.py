import hashlib, json, urllib.request
from pathlib import Path
data = json.load(urllib.request.urlopen("https://pypi.org/pypi/mcai-knowledge/json", timeout=20))
info = data["info"]
print("name:", info["name"], "| version:", info["version"], "| license:", info.get("license"))
print("requires:", info.get("requires_dist"))
for f in data["urls"]:
    print("file:", f["filename"], f["size"], "bytes")
    print("  sha256:", f["digests"]["sha256"])
local = Path("dist_pkg/mcai_knowledge-0.2.0-py3-none-any.whl")
print("local sha256:", hashlib.sha256(local.read_bytes()).hexdigest())
print("match:", hashlib.sha256(local.read_bytes()).hexdigest() == data["urls"][0]["digests"]["sha256"])