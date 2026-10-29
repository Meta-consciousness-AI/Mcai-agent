import json, urllib.request, urllib.error
for name in ["mcai-knowledge", "mca-knowledge"]:
    try:
        data = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/{name}/json", timeout=15))
        print(f"{name}: 已存在，最新 {data['info']['version']}")
    except urllib.error.HTTPError as e:
        print(f"{name}: {'可用' if e.code == 404 else 'HTTP '+str(e.code)}")
    except Exception as e:
        print(f"{name}: 查询失败 {type(e).__name__}")