import json, urllib.request, urllib.error
base = "https://drew-vegetable-gives-tri.trycloudflare.com"
token = "idJCCJSWvkfDuWwPK2hxlMC7pH4ocrbZ"

def get(path, auth=False):
    req = urllib.request.Request(base + path)
    if auth:
        req.add_header("Authorization", "Bearer " + token)
    try:
        r = urllib.request.urlopen(req, timeout=20)
        return r.status, r.read()[:200].decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:200].decode("utf-8", "replace")

print("health        :", get("/api/v1/health"))
print("answer 无令牌 :", get("/api/v1/answer?q=%E4%BB%80%E4%B9%88%E6%98%AF%E5%85%83%E6%84%8F%E8%AF%86"))
print("answer 带令牌 :", get("/api/v1/answer?q=%E4%BB%80%E4%B9%88%E6%98%AF%E5%85%83%E6%84%8F%E8%AF%86", True))