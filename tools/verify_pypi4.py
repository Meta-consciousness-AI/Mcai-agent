import json, urllib.request
for url in ["https://pypi.org/pypi/mcai-knowledge/0.2.1/json",
            "https://pypi.org/pypi/mcai-knowledge/json"]:
    try:
        data = json.load(urllib.request.urlopen(url, timeout=20))
        info = data["info"]
        desc = info.get("description") or ""
        print(url.split("/pypi/")[1])
        print("  version:", info["version"])
        print("  mcp-name:", "mcp-name: io.github.Meta-consciousness-AI/mcai-knowledge" in desc)
        print("  files:", [f["filename"] for f in data["urls"]])
    except Exception as e:
        print(url, "ERR", e)