import json, urllib.request
url = "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.Meta-consciousness-AI/mcai-knowledge"
data = json.load(urllib.request.urlopen(url, timeout=20))
servers = data.get("servers", data if isinstance(data, list) else [])
print("count:", len(servers))
for s in servers[:3]:
    srv = s.get("server", s)
    print("name:", srv.get("name"))
    print("version:", srv.get("version"))
    print("description:", (srv.get("description") or "")[:60])
    for p in srv.get("packages", []):
        print("  package:", p.get("registryType"), p.get("identifier"), p.get("version"))
    meta = s.get("_meta", {})
    print("  status:", meta.get("io.modelcontextprotocol.registry/official", {}).get("status"))