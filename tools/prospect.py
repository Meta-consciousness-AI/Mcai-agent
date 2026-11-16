# -*- coding: utf-8 -*-
"""线上获客：名单管理、邮件草稿、漏斗统计。

数据存在 data/prospects.jsonl（本地，不入库）。
用法：
    python tools/prospect.py add --name "某出版社" --type 出版社 --city 北京 \
        --url https://example.com --email edit@example.com --book "《某某》"
    python tools/prospect.py list
    python tools/prospect.py draft --id p-0001
    python tools/prospect.py status --id p-0001 --to sent
    python tools/prospect.py stats
"""
import argparse
import json
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "data" / "prospects.jsonl"

STATUSES = ["new", "queued", "sent", "replied", "pilot", "rejected", "bounced"]


def load():
    if not STORE.exists():
        return []
    rows = []
    for line in STORE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def save(rows):
    STORE.parent.mkdir(parents=True, exist_ok=True)
    with STORE.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def find(rows, pid):
    for row in rows:
        if row["id"] == pid:
            return row
    return None


def cmd_add(args):
    rows = load()
    pid = "p-" + uuid.uuid4().hex[:6]
    row = {
        "id": pid,
        "name": args.name,
        "type": args.type,
        "city": args.city,
        "url": args.url,
        "email": args.email,
        "book": args.book,
        "status": "new",
        "notes": args.notes,
        "created": time.strftime("%Y-%m-%d"),
        "contacted": "",
    }
    rows.append(row)
    save(rows)
    print(f"已添加 {pid} {args.name}")


def cmd_list(args):
    rows = load()
    if args.status:
        rows = [r for r in rows if r["status"] == args.status]
    if not rows:
        print("（空）")
        return
    print(f"{'ID':10} {'状态':10} {'类型':6} 名称 / 邮箱")
    for r in rows:
        print(f"{r['id']:10} {r['status']:10} {r['type']:6} {r['name']} / {r['email']}")


def cmd_status(args):
    rows = load()
    row = find(rows, args.id)
    if not row:
        print("未找到", args.id)
        return
    row["status"] = args.to
    if args.to == "sent" and not row.get("contacted"):
        row["contacted"] = time.strftime("%Y-%m-%d")
    if args.note:
        row["notes"] = (row.get("notes") or "") + ("\n" if row.get("notes") else "") + args.note
    save(rows)
    print(f"{args.id} -> {args.to}")


def cmd_draft(args):
    rows = load()
    row = find(rows, args.id)
    if not row:
        print("未找到", args.id)
        return
    book = row.get("book") or "贵社/贵刊的出版物"
    print("主题：关于书稿引文核对的一个免费试点\n")
    print(f"""您好，

我是元意识知识资产项目的负责人。我们做了一套引文核验工具：给定书稿和原文，逐条比对引文是否与原文一致，指出差异位置，不改写原文。

看到贵方出版过{book}，引文密度较高，想请教：是否愿意拿一部书稿或一期稿件做一次免费试点？我们出一份差异报告，供编辑部评估。

我们不收取费用，也不要求独家；报告只给贵方，不外传。

如果方便，回复本邮件即可。

此致
Meta-consciousness-AI
3818490932@qq.com""")


def cmd_stats(args):
    rows = load()
    total = len(rows)
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"名单 {total} 家")
    for st in STATUSES:
        if counts.get(st):
            print(f"  {st}: {counts[st]}")
    replied = counts.get("replied", 0) + counts.get("pilot", 0)
    sent = counts.get("sent", 0) + replied + counts.get("rejected", 0)
    if sent:
        print(f"  回复率: {replied / sent:.1%}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add")
    p.add_argument("--name", required=True)
    p.add_argument("--type", default="出版社")
    p.add_argument("--city", default="")
    p.add_argument("--url", default="")
    p.add_argument("--email", default="")
    p.add_argument("--book", default="")
    p.add_argument("--notes", default="")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("list")
    p.add_argument("--status", default="")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("status")
    p.add_argument("--id", required=True)
    p.add_argument("--to", required=True, choices=STATUSES)
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("draft")
    p.add_argument("--id", required=True)
    p.set_defaults(func=cmd_draft)

    p = sub.add_parser("stats")
    p.set_defaults(func=cmd_stats)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
