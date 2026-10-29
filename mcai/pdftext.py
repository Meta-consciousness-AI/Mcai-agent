"""轻量 PDF 文本抽取：支持 Type0 + ToUnicode 的常见导出（WPS/Word）。

只依赖标准库；按文本基线重建行，保持流式阅读顺序。
"""
from __future__ import annotations

import re
import zlib

_OBJ = re.compile(rb"(\d+)\s+(\d+)\s+obj\b")


def _objects(data: bytes) -> dict[int, bytes]:
    spans = list(_OBJ.finditer(data))
    out: dict[int, bytes] = {}
    for i, m in enumerate(spans):
        start = m.end()
        end = data.find(b"endobj", start)
        if end == -1:
            end = spans[i + 1].start() if i + 1 < len(spans) else len(data)
        out[int(m.group(1))] = data[start:end]
    return out


def _stream(body: bytes) -> bytes | None:
    m = re.search(rb"stream\r?\n", body)
    if not m:
        return None
    head, raw = body[: m.start()], body[m.end():]
    end = raw.rfind(b"endstream")
    if end != -1:
        raw = raw[:end]
    raw = raw.rstrip(b"\r\n")
    if b"FlateDecode" in head:
        for candidate in (raw, raw.rstrip(b"\n").rstrip(b"\r")):
            try:
                return zlib.decompress(candidate)
            except zlib.error:
                continue
        return None
    return raw


def _utf16(hexstr: bytes | str) -> str:
    h = hexstr.decode("ascii") if isinstance(hexstr, bytes) else hexstr
    if len(h) % 4:
        h = h.zfill((len(h) // 4 + 1) * 4)
    try:
        return bytes.fromhex(h).decode("utf-16-be")
    except (ValueError, UnicodeDecodeError):
        return ""


def _cmap(text: bytes) -> dict[int, str]:
    table: dict[int, str] = {}
    for block in re.findall(rb"beginbfchar(.*?)endbfchar", text, re.S):
        for src, dst in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            table[int(src, 16)] = _utf16(dst)
    for block in re.findall(rb"beginbfrange(.*?)endbfrange", text, re.S):
        pattern = rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(<[0-9A-Fa-f]+>|\[[^\]]*\])"
        for m in re.finditer(pattern, block, re.S):
            lo, hi, dst = int(m.group(1), 16), int(m.group(2), 16), m.group(3)
            if dst.startswith(b"["):
                for k, item in enumerate(re.findall(rb"<([0-9A-Fa-f]+)>", dst)):
                    if lo + k > hi:
                        break
                    table[lo + k] = _utf16(item)
            else:
                base = _utf16(dst[1:-1])
                for code in range(lo, hi + 1):
                    if not base:
                        table[code] = ""
                    elif code == lo:
                        table[code] = base
                    else:
                        table[code] = base[:-1] + chr(ord(base[-1]) + code - lo)
    return table


_TOKEN = re.compile(
    rb"""
      /(?P<font>[A-Za-z0-9_.+-]+)\s+(?P<fsize>[\d.]+)\s+Tf
    | (?P<e>-?[\d.]+)\s+(?P<f>-?[\d.]+)\s+Tm
    | (?P<ty>-?[\d.]+)\s+(?P<tdop>Td|TD)
    | (?P<tj>\[(?P<arr>[^\]]*)\]\s*TJ)
    | (?P<tj1>\((?:\\.|[^\\)])*\)\s*Tj)
    | (?P<tj2><[0-9A-Fa-f\s]*>\s*Tj)
    """,
    re.S | re.X,
)


def _decode_hex(value: bytes, table: dict[int, str]) -> str:
    h = re.sub(rb"\s", b"", value).decode("ascii")
    if len(h) % 2:
        h += "0"
    raw = bytes.fromhex(h)
    return "".join(table.get((raw[i] << 8) | raw[i + 1], "") for i in range(0, len(raw) - 1, 2))


def _decode_lit(value: bytes, table: dict[int, str]) -> str:
    s = value.replace(rb"\(", b"(").replace(rb"\)", b")").replace(rb"\\", b"\\")
    if len(s) % 2:
        return s.decode("latin1", "replace")
    return "".join(table.get((s[i] << 8) | s[i + 1], "") for i in range(0, len(s) - 1, 2))


def _fonts(res: bytes) -> dict[str, int]:
    out: dict[str, int] = {}
    m = re.search(rb"/Font\s*<<(.*?)>>", res, re.S)
    if m:
        for name, num in re.findall(rb"/([A-Za-z0-9_.+-]+)\s+(\d+)\s+0\s+R", m.group(1)):
            out[name.decode()] = int(num)
    return out


def _pages(objects: dict[int, bytes]) -> list[int]:
    catalog = next((n for n, b in objects.items() if re.search(rb"/Type\s*/Catalog", b)), None)
    found: list[int] = []

    def walk(num: int) -> None:
        body = objects.get(num, b"")
        if re.search(rb"/Type\s*/Pages", body):
            kids = re.search(rb"/Kids\s*\[(.*?)\]", body, re.S)
            if kids:
                for k in re.findall(rb"(\d+)\s+0\s+R", kids.group(1)):
                    walk(int(k))
        elif re.search(rb"/Type\s*/Page\b", body):
            found.append(num)

    if catalog is not None:
        root = re.search(rb"/Pages\s+(\d+)\s+0\s+R", objects[catalog])
        if root:
            walk(int(root.group(1)))
    return found


def extract_pdf_text(path: str) -> list[str]:
    """返回每一页的文本（按行）。"""
    data = open(path, "rb").read()
    objects = _objects(data)

    cmaps: dict[int, dict[int, str]] = {}
    for num, body in objects.items():
        ref = re.search(rb"/ToUnicode\s+(\d+)\s+0\s+R", body)
        if ref:
            raw = _stream(objects.get(int(ref.group(1)), b""))
            if raw:
                cmaps[num] = _cmap(raw)

    pages_out: list[str] = []
    for page in _pages(objects):
        body = objects[page]
        res = b""
        ref = re.search(rb"/Resources\s+(\d+)\s+0\s+R", body)
        if ref:
            res = objects.get(int(ref.group(1)), b"")
        else:
            inline = re.search(rb"/Resources\s*<<(.*)", body, re.S)
            if inline:
                res = inline.group(1)
        font_map = _fonts(res)

        refs: list[int] = []
        one = re.search(rb"/Contents\s+(\d+)\s+0\s+R", body)
        if one:
            refs = [int(one.group(1))]
        else:
            many = re.search(rb"/Contents\s*\[(.*?)\]", body, re.S)
            if many:
                refs = [int(x) for x in re.findall(rb"(\d+)\s+0\s+R", many.group(1))]
        stream = b"".join((_stream(objects.get(r, b"")) or b"") + b"\n" for r in refs)

        y = 0.0
        last_y: float | None = None
        table: dict[int, str] = {}
        buf: list[str] = []
        for m in _TOKEN.finditer(stream):
            if m.group("font"):
                table = cmaps.get(font_map.get(m.group("font").decode(), -1), {})
            elif m.group("f") is not None:
                y = float(m.group("f"))
            elif m.group("tdop"):
                y += float(m.group("ty"))
            elif m.group("tj") or m.group("tj1") or m.group("tj2"):
                if m.group("tj"):
                    text = ""
                    parts = re.findall(rb"<([0-9A-Fa-f\s]*)>|\(((?:\\.|[^\\)])*)\)|(-?[\d.]+)", m.group("arr"), re.S)
                    for hx, lit, num in parts:
                        if hx:
                            text += _decode_hex(hx, table)
                        elif lit:
                            text += _decode_lit(lit, table)
                        elif num and float(num) < -120:
                            text += " "
                else:
                    raw = (m.group("tj1") or m.group("tj2"))
                    raw = raw[: raw.rfind(b"Tj")]
                    hm = re.search(rb"<([0-9A-Fa-f\s]*)>", raw)
                    if hm:
                        text = _decode_hex(hm.group(1), table)
                    else:
                        lm = re.search(rb"\(((?:\\.|[^\\)])*)\)", raw, re.S)
                        text = _decode_lit(lm.group(1), table) if lm else ""
                if not text:
                    continue
                if last_y is not None and abs(y - last_y) > 3.0:
                    buf.append("\n")
                last_y = y
                buf.append(text)
        raw_text = "".join(buf)
        lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in raw_text.split("\n")]
        pages_out.append("\n".join(ln for ln in lines if ln))
    return pages_out
