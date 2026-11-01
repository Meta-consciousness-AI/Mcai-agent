"""定期指标扫描：PyPI、GitHub、Zenodo、ModelScope。

用法：python tools/metrics_scan.py
结果追加到 data/metrics.jsonl，并打印摘要。
注意：ModelScope 的 Downloads 是下载事件计数器（本人与抓取都会 +1），不能直接当作外部使用。
Bing 收录需要浏览器或 web_fetch，另行补查。
"""

import datetime as dt
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "metrics.jsonl"
PKG = "mcai-knowledge"
REPO = "Meta-consciousness-AI/Mcai-agent"
ZENODO_RECORDS = {
    "dataset": 23789330,
    "preprint": 23830600,
    "spec_v11": 23831131,
    "spec_v13": 23850554,
}
MODELSCOPE_DATASET = "Metaconsciousness/mcai-knowledge"


def get_json(url: str, timeout: int = 25):
    req = urllib.request.Request(url, headers={"User-Agent": "mcai-metrics/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def pypi_stats():
    recent = get_json(f"https://pypistats.org/api/packages/{PKG}/recent")
    data = recent.get("data", {})
    overall = get_json(f"https://pypistats.org/api/packages/{PKG}/overall?mirrors=false")
    rows = overall.get("data", [])
    last7 = sum(r.get("downloads", 0) for r in rows[-7:])
    last30 = sum(r.get("downloads", 0) for r in rows[-30:])
    return {
        "pypi_last_day": data.get("last_day"),
        "pypi_last_week": data.get("last_week"),
        "pypi_last_month": data.get("last_month"),
        "pypi_7d_sum": last7,
        "pypi_30d_sum": last30,
    }


def github_stats():
    r = get_json(f"https://api.github.com/repos/{REPO}")
    return {
        "github_stars": r.get("stargazers_count"),
        "github_forks": r.get("forks_count"),
        "github_watchers": r.get("subscribers_count"),
        "github_open_issues": r.get("open_issues_count"),
    }


def zenodo_stats():
    out = {}
    for name, rid in ZENODO_RECORDS.items():
        d = get_json(f"https://zenodo.org/api/records/{rid}")
        s = d.get("stats") or {}
        out[f"zenodo_{name}_views"] = s.get("views")
        out[f"zenodo_{name}_downloads"] = s.get("downloads")
    out["zenodo_views_total"] = sum(v for k, v in out.items() if k.endswith("_views") and isinstance(v, int))
    out["zenodo_downloads_total"] = sum(v for k, v in out.items() if k.endswith("_downloads") and isinstance(v, int))
    return out


def modelscope_stats():
    d = get_json(f"https://modelscope.cn/api/v1/datasets/{MODELSCOPE_DATASET}")
    data = d.get("Data") or {}
    return {
        "modelscope_downloads": data.get("Downloads"),
        "modelscope_likes": data.get("Likes"),
    }


def main():
    ts = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    row = {"ts": ts}
    for fn in (pypi_stats, github_stats, zenodo_stats, modelscope_stats):
        try:
            row.update(fn())
        except Exception as e:  # 单点失败不影响整行
            row[fn.__name__ + "_error"] = f"{type(e).__name__}: {e}"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
