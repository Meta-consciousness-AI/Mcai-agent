import re
from pathlib import Path

ROOT = Path(r"C:\Users\HP\Documents\deepseek-harness\default-workspace\mca-agent\video")
final_text = (ROOT / "口播稿（定稿）.txt").read_text(encoding="utf-8")
paras = [p.strip() for p in re.split(r"\n\s*\n", final_text) if p.strip()]
# 用法与搜索合并为一页，保持 14 页
if len(paras) == 15:
    paras[12] = paras[12] + " " + paras[13]
    del paras[13]

topics = [
    "开场：如何让 AI 答对原创术语",
    "问题：三种反应",
    "做法：做成可回查的资料",
    "坑 1：出处只写到章节",
    "坑 2：规则误杀",
    "坑 3：道德经没有定义句",
    "坑 4：版本差异不是冲突",
    "关系分层",
    "结果：64 / 122 / 270 / 213",
    "复现：三份经典 100%",
    "最新：0.3.2 / mcprush Grade A",
    "现状：用的人还不多",
    "用法与搜索指引",
    "结尾",
]

def secs(text: str) -> int:
    chars = len(re.sub(r"\s", "", text))
    return max(4, round(chars / 3.8) + 1)

rows = []
total = 0
for i, para in enumerate(paras):
    s = secs(para)
    total += s
    rows.append((i + 1, topics[i] if i < len(topics) else "", s, para))

lines = [
    "# 横屏视频分镜（按定稿）",
    "",
    "- 尺寸：1920×1080；素材：`slide-01.png` … `slide-14.png`",
    "- 语速按 3.8 字/秒估算；剪映「文本朗读」偏快时调到 0.9–1.0",
    "- 每页时长以音频实际长度为准",
    "",
    "| 页 | 主题 | 时长 | 口播 |",
    "|---|---|---|---|",
]
for n, topic, s, para in rows:
    lines.append(f"| {n:02d} | {topic} | {s}s | {para} |")
lines += ["", f"合计约 **{total} 秒**（{total/60:.1f} 分钟）。", ""]
(ROOT / "horizontal" / "分镜.md").write_text("\n".join(lines), encoding="utf-8")
print("paras:", len(paras), "| total:", total, "s")
