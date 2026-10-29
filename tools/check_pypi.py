import json, sys, urllib.request, urllib.error
from pathlib import Path

# 1) PyPI 包名是否可用
for name in ["mcai-knowledge", "mcai-agent", "meta-consciousness"]:
    try:
        r = urllib.request.urlopen(f"https://pypi.org/pypi/{name}/json", timeout=15)
        data = json.load(r)
        print(f"{name}: 已存在（最新 {data['info']['version']}）")
    except urllib.error.HTTPError as e:
        print(f"{name}: {'可用' if e.code == 404 else 'HTTP ' + str(e.code)}")
    except Exception as e:
        print(f"{name}: 查询失败 {type(e).__name__}")

# 2) 直接从 wheel 导入（zipimport），验证打包内容
whl = Path("dist_pkg/mcai_knowledge-0.1.0-py3-none-any.whl")
sys.path.insert(0, str(whl))
import mcai
from mcai import knowledge
kb = knowledge.load(Path("."))
print("zipimport:", mcai.__file__)
print("kb:", len(kb.concepts), "concepts /", len(kb.faqs), "faqs")