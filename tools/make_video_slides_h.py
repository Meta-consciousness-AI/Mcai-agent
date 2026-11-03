import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"C:\Users\HP\Documents\deepseek-harness\default-workspace\mca-agent\video\horizontal")
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1920, 1080
BG = (250, 248, 244)
INK = (28, 27, 25)
MUTED = (110, 104, 94)
ACCENT = (176, 62, 44)
LINE = (214, 207, 195)

FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT = r"C:\Windows\Fonts\msyh.ttc"

slides = [
    ("MCAI · 工程笔记", "让 AI 答对原创术语", "一套学说知识库的工程记录\n方法、复现与四个坑"),
    ("问题", "模型遇到原创术语，\n通常有三种反应", "没听说过，按字面猜；\n用同名概念替换；\n给出似是而非的混合表述。"),
    ("做法", "不是让模型记住，\n而是做成可回查的资料", "概念、问答、关系、引证\n四个对象，\n每条定义都必须带出处。"),
    ("坑 1 · 出处", "只写到章节，\n引文就对不上", "Word 手动换行让位置号重复，\n核验率只有 83.6%。\n补上字符区间后，55 条全部逐字命中。"),
    ("坑 2 · 术语", "规则会误杀\n正常术语", "「五事」「九地」被当成编号，\n「性」「情」「名」被「至少两字」拒绝。\n两次都是规则问题。"),
    ("坑 3 · 定义", "没有定义句，\n就把定义分层", "《道德经》没有「X 者，Y 也」。\n原文归原文，\n编者理解单独标注。"),
    ("坑 4 · 版本", "版本差异\n不是冲突", "「见素抱扑」与「见素抱朴」\n是版本事实，\n并存可查，不强行统一。"),
    ("关系分层", "270 条关系里，\n246 条是共现噪声", "默认只返回人工确认的\ncore 与 derived；\nmention 需要显式打开。"),
    ("结果", "64 个概念，\n213 条原文出处", "122 组问答、270 条关系；\n每条定义都能回查到\n文档、段落与字符区间。"),
    ("复现", "三份公共文本，\n引文核验 100%", "孙子兵法 13/13\n荀子·正名 12/12\n道德经 10/10"),
    ("最新进展", "0.3.2 已发布，\nmcprush 给了 Grade A", "远程 MCP 公开只读实例上线；\n五个平台已发布；\n代码与数据都开放。"),
    ("现状", "仍然几乎没人用", "GitHub 0 Star，\n下载与调用都很少。\n问题可能不在需求，而在入口。"),
    ("怎么用", "装一个包，\n或直接连一个地址", "pip install mcai-knowledge\nmcai-mcp\n\n或连接公开只读 MCP 地址"),
    ("结尾", "需要它的人，\n还没看到它", "如果你在做类似的冷门领域知识库，\n欢迎交流。\n仓库与数据集见简介。"),
]


def load(path, size):
    return ImageFont.truetype(path, size)


def fit(lines, max_width, start=68, floor=44):
    size = start
    while size > floor:
        f = load(FONT_BOLD, size)
        if max(ImageDraw.Draw(Image.new("RGB", (10, 10))).textlength(l, font=f) for l in lines) <= max_width:
            return size
        size -= 2
    return floor


def draw_slide(idx, kicker, title, body):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.rectangle([120, 96, 148, 124], fill=ACCENT)
    d.text((164, 88), "MCAI · 工程笔记", font=load(FONT, 28), fill=MUTED)
    d.text((120, 200), kicker, font=load(FONT, 32), fill=ACCENT)

    size = fit(title.split("\n"), 1500)
    tf = load(FONT_BOLD, size)
    y = 270
    for line in title.split("\n"):
        d.text((120, y), line, font=tf, fill=INK)
        y += int(size * 1.25)

    y += 30
    d.line([120, y, 1800, y], fill=LINE, width=3)
    y += 60

    bf = load(FONT, 38)
    for line in body.split("\n"):
        if line:
            d.text((120, y), line, font=bf, fill=MUTED)
        y += 60

    d.text((120, 990), "mcai-knowledge · 0.3.2", font=load(FONT, 24), fill=(150, 143, 132))
    page = f"{idx:02d} / {len(slides):02d}"
    tw = d.textlength(page, font=load(FONT, 24))
    d.text((1800 - tw, 990), page, font=load(FONT, 24), fill=(150, 143, 132))

    path = OUT / f"slide-{idx:02d}.png"
    img.save(path, "PNG")
    return path


def estimate_seconds(text: str) -> int:
    chars = len(re.sub(r"\s", "", text))
    return max(4, round(chars / 3.8) + 1)


if __name__ == "__main__":
    total = 0
    rows = []
    for i, (k, t, b) in enumerate(slides, 1):
        draw_slide(i, k, t, b)
        # 以标题+正文估算口播长度（标题也会被念）
        sec = estimate_seconds(t.replace("\n", "") + b.replace("\n", ""))
        total += sec
        rows.append((i, t.replace("\n", " "), sec))
    for r in rows:
        print(f"slide-{r[0]:02d} | {r[2]}s | {r[1]}")
    print("total:", total, "s")
