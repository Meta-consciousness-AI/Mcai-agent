import json, urllib.request

def get(path):
    return json.load(urllib.request.urlopen(f"http://127.0.0.1:8787{path}", timeout=8))

r=get("/api/v1/answer?q=%E4%BB%80%E4%B9%88%E6%98%AF%E5%85%83%E6%84%8F%E8%AF%86&format=markdown")
print("MARKDOWN:", r["markdown"][:100].replace("\n"," | "))

body=json.dumps({"questions":["什么是元意识","元识和元知是什么关系","什么是量子引力"]},ensure_ascii=False).encode()
req=urllib.request.Request("http://127.0.0.1:8787/api/v1/answer/batch",data=body,headers={"Content-Type":"application/json"})
r=json.load(urllib.request.urlopen(req,timeout=10))
print("BATCH:", r["count"], [x["type"] for x in r["results"]])
print("SUGGEST:", r["results"][2].get("did_you_mean"))

g=urllib.request.urlopen("http://127.0.0.1:8787/guide.md",timeout=8).read().decode("utf-8")
print("GUIDE:", len(g), g.splitlines()[0])
