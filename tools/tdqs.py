import re, urllib.request
url = "https://glama.ai/mcp/servers/Meta-consciousness-AI/Mcai-agent"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
print("page chars:", len(html))
for kw in ["TDQS", "Tool Definition Quality", "score"]:
    idxs = [m.start() for m in re.finditer(kw, html, re.I)][:3]
    print(f"--- {kw}: {len(idxs)} hits")
    for i in idxs:
        snippet = re.sub(r"<[^>]+>", " ", html[max(0,i-200):i+300])
        snippet = " ".join(snippet.split())
        print("   ", snippet[:260])