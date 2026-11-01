"""打印今天的发现工作（按星期轮换），并提示对应命令。"""
from __future__ import annotations

import datetime as dt

TASKS = {
    0: ("指标与趋势", "python tools/metrics_scan.py，并更新 docs/指标记录.md"),
    1: ("检查一个 MCP 目录", "打开 registry.modelcontextprotocol.io 或 glama.ai，确认版本与描述"),
    2: ("IndexNow + Bing", "python tools/indexnow.py；再用 site: 查收录"),
    3: ("包描述检查", "看 PyPI 与注册表的关键词、摘要是否仍准确"),
    4: ("第三方提及", "搜索 DOI、项目名、包名，看是否有引用"),
    5: ("数据集同步", "对比 Zenodo / ModelScope 文件与 dist/dataset 是否一致"),
    6: ("留白", "今天不做发现工作"),
}


def main() -> int:
    today = dt.date.today()
    title, action = TASKS[today.weekday()]
    print(f"日期：{today}（星期{'一二三四五六日'[today.weekday()]}）")
    print(f"今日发现工作：{title}")
    print(f"做法：{action}")
    print("上限：20–30 分钟；没有硬信号就不追加投入。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
