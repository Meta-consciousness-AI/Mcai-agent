import json, ssl, urllib.request, urllib.error
base = "https://chubby-teams-graham-diagnostic.trycloudflare.com"
ctx = ssl.create_default_context()
for name, req in [
    ("health", base + "/api/v1/health"),
    ("answer-noauth", base + "/api/v1/answer?q=%E4%BB%80%E4%B9%88%E6%98%AF%E5%85%83%E6%84%8F%E8%AF%86"),
]:
    try:
        r = urllib.request.urlopen(req, context=ctx, timeout=15)
        print(name, r.status, r.read()[:120])
    except urllib.error.HTTPError as e:
        print(name, e.code, e.read()[:120])
    except Exception as e:
        print(name, "ERR", type(e).__name__, str(e)[:120])