import json, urllib.request
try:
    data = json.load(urllib.request.urlopen("https://api.github.com/repos/Meta-consciousness-AI/mcai-agent", timeout=20))
    print("repo:", data["full_name"], "| private:", data["private"])
    commits = json.load(urllib.request.urlopen("https://api.github.com/repos/Meta-consciousness-AI/mcai-agent/commits?per_page=1", timeout=20))
    print("latest commit:", commits[0]["sha"][:8], "|", commits[0]["commit"]["message"].splitlines()[0])
except Exception as e:
    print("查询失败:", type(e).__name__, str(e)[:80])