import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"C:\Users\HP\Documents\deepseek-harness\default-workspace\mca-agent\video\vertical")
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920
BG = (250, 248, 244)
INK = (28, 27, 25)
MUTED = (110, 104, 94)
ACCENT = (176, 62, 44)
LINE = (214, 207, 195)

FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT = r"C:\Windows\Fonts\msyh.ttc"

slides = [
    ("AI × 学说", "AI 总把「元意识」\n理解错", "不是模型笨，\n是它没有一套\n可回查的资料。"),
    ("我们做了什么", "把它做成\n可调用的库", "64 个术语\n122 组问答\n270 条关系\n213 条原文出处"),
    ("坑 1 · 出处", "只写章节，\n引文对不上", "Word 手动换行\n让位置号重复，\n核验率只有 83.6%。\n\n补上字符区间后，\n55 条出处全部逐字命中。"),
    ("坑 2 · 术语", "规则会误杀\n正常术语", "「五事」「九地」\n被当成列表编号；\n「性」「情」「名」\n被「至少两字」拒绝。\n\n两次都是规则问题。"),
    ("坑 3 · 定义", "没有定义句，\n就把定义分层", "《道德经》没有\n「X 者，Y 也」。\n\n原文归原文，\n编者理解单独标注，\n不能混。"),
    ("坑 4 · 版本", "版本差异\n不是冲突", "「见素抱扑」\n与「见素抱朴」\n是版本事实。\n\n并存可查，\n不强行统一。"),
    ("关系分层", "270 条关系，\n246 条是噪声", "默认只返回人工确认的\ncore 与 derived；\nmention 需要显式打开。"),
    ("结果", "三份复现，\n引文核验 100%", "孙子兵法 13/13\n荀子·正名 12/12\n道德经 10/10"),
    ("最新进展", "0.3.2 发布，\nmcprush Grade A", "远程 MCP 公开只读实例上线；\n五个平台已发布。\n\npip install mcai-knowledge"),
    ("现状", "仍然几乎\n没人用", "GitHub 0 Star，\n下载与调用都很少。\n\n问题可能不在需求，\n而在还没被\n需要它的人看到。"),
]


def load(path, size):
    return ImageFont.truetype(path, size)


def draw_slide(idx, kicker, title, body):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # 顶部标识
    d.rectangle([90, 104, 118, 132], fill=ACCENT)
    d.text((136, 94), "MCAI · 工程笔记", font=load(FONT, 34), fill=MUTED)

    # 小标签
    d.text((90, 330), kicker, font=load(FONT, 40), fill=ACCENT)

    # 标题
    title_font = load(FONT_BOLD, 92)
    y = 420
    for line in title.split("\n"):
        d.text((90, y), line, font=title_font, fill=INK)
        y += 124

    # 分隔线
    y += 30
    d.line([90, y, 990, y], fill=LINE, width=3)
    y += 70

    # 正文
    body_font = load(FONT, 48)
    for line in body.split("\n"):
        if line:
            d.text((90, y), line, font=body_font, fill=MUTED)
        y += 80

    # 页脚
    d.text((90, 1800), "mcai-knowledge · 0.3.2", font=load(FONT, 28), fill=(150, 143, 132))
    page = f"{idx:02d} / {len(slides):02d}"
    tw = d.textlength(page, font=load(FONT, 28))
    d.text((990 - tw, 1800), page, font=load(FONT, 28), fill=(150, 143, 132))

    path = OUT / f"slide-{idx:02d}.png"
    img.save(path, "PNG")
    return path


if __name__ == "__main__":
    for i, (k, t, b) in enumerate(slides, 1):
        print(draw_slide(i, k, t, b))
