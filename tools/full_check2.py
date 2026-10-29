import json, re, urllib.request

def get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")

print("== PyPI ==")
try:
    d = json.loads(get("https://pypi.org/pypi/mcai-knowledge/json"))
    desc = d["info"].get("description") or ""
    print("version:", d["info"]["version"], "| mcp-name:", "mcp-name: io.github.Meta-consciousness-AI/mcai-knowledge" in desc)
except Exception as e:
    print("ERR", type(e).__name__, str(e)[:80])

print("== MCP Registry ==")
try:
    name = "io.github.Meta-consciousness-AI%2Fmcai-knowledge"
    d = json.loads(get(f"https://registry.modelcontextprotocol.io/v0.1/servers/{name}/versions"))
    for s in d.get("servers", [])[:2]:
        srv = s.get("server", s); meta = s.get("_meta", {}).get("io.modelcontextprotocol.registry/official", {})
        print("version:", srv.get("version"), "| status:", meta.get("status"), "| latest:", meta.get("isLatest"))
except Exception as e:
    print("ERR", type(e).__name__, str(e)[:80])

print("== GitHub ==")
try:
    c = json.loads(get("https://api.github.com/repos/Meta-consciousness-AI/Mcai-agent/commits?per_page=1"))[0]
    print(c["sha"][:8], c["commit"]["message"].splitlines()[0])
except Exception as e:
    print("ERR", type(e).__name__, str(e)[:80])

print("== Glama ==")
try:
    html = get("https://glama.ai/mcp/servers/Meta-consciousness-AI/Mcai-agent")
    m = re.search(r"Average TDQS[^<]*", re.sub(r"<[^>]+>", " ", html))
    print("HTTP ok | TDQS:", (m.group(0)[:60] if m else "未解析"), "| 4.5/5:", "4.5/5" in html, "| tools:", "mcai_answer" in html)
except Exception as e:
    print("ERR", type(e).__name__, str(e)[:80])

print("== Local 8787 ==")
try:
    h = json.loads(get("http://127.0.0.1:8787/api/v1/health", timeout=5))
    print("ok:", h.get("ok"), "| concepts:", h.get("concepts"), "| faqs:", h.get("faqs"))
except Exception as e:
    print("未运行或不可达", type(e).__name__)