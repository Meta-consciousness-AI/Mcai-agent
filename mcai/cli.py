"""命令行入口。

所有命令都支持 --home 指定工作区；未指定时按 MCAI_HOME → 当前目录 → 源码目录 的顺序解析。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__, pipeline, workspace
from .corpus import load_config

ROOT = workspace.DEV_ROOT


def _home(args: argparse.Namespace) -> Path:
    return workspace.resolve_home(getattr(args, "home", None))


def cmd_init(args: argparse.Namespace) -> int:
    result = workspace.init_workspace(args.path or ".", force=args.force)
    print(f"✅ 工作区已初始化：{result['root']}")
    for path in result["created"]:
        print(f"  + {path}")
    for path in result["skipped"]:
        print(f"  = 已存在，跳过 {path}")
    print("\n下一步：")
    print("  1. 把文档放进 corpus/，在 config/corpus.json 的 corpus 数组里登记")
    print("  2. mcai build")
    print("  3. mcai serve  或  mcai mcp")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    home = _home(args)
    result = pipeline.rebuild(home)
    print(f"✅ 构建完成：{result['concepts']} 个概念 / {result['faqs']} 组问答 / "
          f"{result['relations']} 条关系 / {result['pages']} 个页面")
    if result["conflicts"]:
        print("⚠️  定义冲突待裁定：" + "、".join(result["conflicts"]))
    if result["coverage_missing"]:
        print("⚠️  词表覆盖缺失：" + "、".join(result["coverage_missing"]))
    print(f"📄 站点：{home / 'dist' / 'index.html'}")
    if args.serve:
        from .server import serve
        serve(home, args.port)
    return 0


def _serve(args: argparse.Namespace) -> int:
    from .server import serve
    token = (getattr(args, "token", "") or os.environ.get("MCAI_TOKEN", "")).strip()
    serve(_home(args), args.port, host=args.host, token=token, rate_limit=args.rate_limit,
          autopilot_interval=getattr(args, "autopilot", 0))
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    return _serve(args)


def cmd_api(args: argparse.Namespace) -> int:
    return _serve(args)


def cmd_mcp(args: argparse.Namespace) -> int:
    from .mcp_server import main as mcp_main
    mcp_main(_home(args))
    return 0


def cmd_autopilot(args: argparse.Namespace) -> int:
    from .autopilot import Autopilot
    pilot = Autopilot(_home(args), port=args.port, ensure_server=not args.no_server)
    if args.once:
        outcome = pilot.run_once()
        s = outcome["status"]
        print(f"{'✅' if s['ok'] else '❌'} 检查完成 · 重建={outcome['rebuilt']} · "
              f"{s['concepts']} 概念 / {s['faqs']} 问答 · 服务={'在线' if s['server_ok'] else '离线'}")
        if s["error"]:
            print(f"   错误：{s['error']}")
        diff = outcome["diff"]
        if diff["added"] or diff["removed"] or diff["changed"]:
            print(f"   变更：+{len(diff['added'])} −{len(diff['removed'])} ~{len(diff['changed'])}")
        print(f"   状态文件：{_home(args) / 'data' / 'status.json'}")
        return 0 if s["ok"] else 1
    try:
        pilot.loop(args.interval)
    except KeyboardInterrupt:
        print("\n已停止。")
    return 0


def cmd_quality(args: argparse.Namespace) -> int:
    from . import quality
    result = quality.inspect(_home(args))
    counts = result["counts"]
    print(f"质量巡检：{'✅ 通过' if result['ok'] else '❌ 有问题'} "
          f"（错误 {counts['error']} · 警告 {counts['warn']} · 提示 {counts['info']}）")
    for issue in (result["errors"] + result["warnings"])[:20]:
        mark = "❌" if issue["level"] == "error" else "⚠️"
        print(f"  {mark} [{issue['code']}] {issue['detail']}")
    return 0 if result["ok"] else 1


def cmd_selftest(args: argparse.Namespace) -> int:
    from . import selftest
    result = selftest.run(_home(args))
    mark = "✅" if result["ok"] else "❌"
    print(f"接口自测：{mark} {result['passed']}/{result['total']} 通过")
    for c in result["checks"]:
        if not c["ok"]:
            print(f"  ❌ {c['name']} {c['detail']}")
    return 0 if result["ok"] else 1


def cmd_snapshot(args: argparse.Namespace) -> int:
    from . import snapshot
    result = snapshot.create(_home(args), note=args.note, keep=args.keep,
                             with_corpus=not args.no_corpus)
    m = result["manifest"]
    print(f"✅ 快照已生成：{result['archive']}")
    print(f"   {m['files']} 个文件 · 原始 {m['bytes'] / 1024:.0f} KB · 压缩 {m['archive_bytes'] / 1024:.0f} KB")
    if m.get("kb"):
        kb = m["kb"]
        print(f"   知识库：{kb.get('concepts')} 概念 / {kb.get('faqs')} 问答 / {kb.get('relations')} 关系")
    if m.get("corpus"):
        print(f"   语料：{len(m['corpus'])} 份（含在包内）")
    if result["removed"]:
        print("   轮转删除：" + "、".join(result["removed"]))
    return 0


def cmd_snapshots(args: argparse.Namespace) -> int:
    from . import snapshot
    rows = snapshot.list_snapshots(_home(args), limit=args.limit)
    if not rows:
        print("还没有快照。运行 mcai snapshot 生成第一份。")
        return 0
    print(f"{'时间':<26} {'大小':>8}  {'概念':>4} {'问答':>4}  备注")
    for r in rows:
        kb = r.get("kb") or {}
        print(f"{r['created_at']:<26} {r['bytes'] / 1024:>7.0f}K  {kb.get('concepts', '-'):>4} "
              f"{kb.get('faqs', '-'):>4}  {r.get('note', '')}")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    from . import snapshot
    check = snapshot.verify(args.archive)
    if not check.get("ok"):
        print(f"❌ 快照损坏或不存在：{check.get('error') or check.get('broken')}")
        return 1
    result = snapshot.restore(args.archive, args.to, force=args.force)
    if not result.get("ok"):
        print(f"❌ {result.get('error')}")
        return 1
    print(f"✅ 已恢复到：{result['target']}（{result['files']} 个条目）")
    print("   检查后可用：mcai build --home <该目录>，再 mcai serve --home <该目录>")
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    from . import dashboard
    path = dashboard.render(_home(args))
    print(f"✅ 观测台已生成：{path}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    path = _home(args) / "data" / "status.json"
    if not path.exists():
        print("还没有状态文件：先运行 mcai autopilot --once")
        return 1
    status = json.loads(path.read_text(encoding="utf-8"))
    print(f"检查时间：{status.get('checked_at')}")
    print(f"健康：{'✅' if status.get('ok') else '❌'}")
    print(f"概念 {status.get('concepts')} · 问答 {status.get('faqs')} · 关系 {status.get('relations')}")
    print(f"服务：{'在线' if status.get('server_ok') else '离线'}"
          f"（本轮启动：{'是' if status.get('started_server') else '否'}）")
    print(f"本轮重建：{'是' if status.get('rebuilt') else '否'}")
    q = status.get("quality") or {}
    t = status.get("selftest") or {}
    if q:
        print(f"质量巡检：{'✅' if q.get('ok') else '❌'} 错误 {q.get('errors', 0)} · 警告 {q.get('warnings', 0)}")
    if t:
        print(f"接口自测：{'✅' if t.get('ok') else '❌'} {t.get('passed', 0)}/{t.get('total', 0)}")
    if status.get("error"):
        print(f"错误：{status['error']}")
    return 0 if status.get("ok") else 1


def cmd_token(args: argparse.Namespace) -> int:
    from .deploy import new_token
    token = new_token()
    print(token)
    print("\n用法：")
    print(f"  mcai serve --host 0.0.0.0 --token {token}")
    print(f"  mcai doctor --url <你的地址> --token {token}")
    return 0


def cmd_set_url(args: argparse.Namespace) -> int:
    from .deploy import set_site_url
    home = _home(args)
    try:
        info = set_site_url(home, args.url)
    except ValueError as exc:
        print(f"❌ {exc}")
        return 1
    print(f"站点地址：{info['old'] or '（未设置）'} → {info['new']}")
    if args.no_build:
        print("已跳过重建（--no-build）")
        return 0
    result = pipeline.rebuild(home)
    print(f"✅ 已重建：{result['concepts']} 概念 / {result['faqs']} 问答 / {result['pages']} 页面")
    manifest = home / "dist" / ".well-known" / "mcp.json"
    if manifest.exists():
        base = json.loads(manifest.read_text(encoding="utf-8")).get("http", {}).get("base", "")
        print(f"   清单地址已更新：{base}")
    print("\n下一步：mcai doctor --url " + info["new"] + " [--token <令牌>]")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    from .deploy import doctor
    token = (getattr(args, "token", "") or os.environ.get("MCAI_TOKEN", "")).strip()
    checks = doctor(args.url, token=token)
    print(f"体检目标：{args.url}\n")
    failed = 0
    for c in checks:
        mark = "✅" if c["ok"] else "❌"
        print(f"{mark} {c['name']:<10} {c['detail']}")
        if not c["ok"]:
            failed += 1
            if c.get("hint"):
                print(f"   ↳ {c['hint']}")
    print()
    if failed:
        print(f"共 {failed} 项未通过。")
        return 1
    print("全部通过。")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    kb = pipeline.load_kb(_home(args))
    stats = kb["meta"]["stats"]
    print(f"构建时间：{kb['meta']['built_at']}")
    print(f"概念 {stats['concepts']} · 问答 {stats['faqs']} · 关系 {stats['relations']} "
          f"· 引证 {stats.get('evidence', 0)} · 文档 {stats['documents']} · 段落 {stats['blocks']} "
          f"· 字数 {stats['characters']:,}")
    print("\n文档类型：")
    for name, count in stats.get("by_kind", {}).items():
        print(f"  {name:<12} {count:>3}")
    print("\n分类：")
    for name, count in stats["categories"].items():
        print(f"  {name:<12} {count:>3}")
    print("\n状态：")
    for name, count in stats["status"].items():
        print(f"  {name:<12} {count:>3}")
    conflicts = [c for c in kb["concepts"] if c["status"] == "conflict"]
    if conflicts:
        print("\n冲突条目：")
        for c in conflicts:
            print(f"  - {c['term']}（{len(c['variants'])} 个版本）")
    cov = stats["coverage"]
    print(f"\n词表覆盖：{cov['covered']}/{cov['expected']}")
    if cov["missing"]:
        print("  缺失：" + "、".join(cov["missing"]))
    return 0


def cmd_disambig(args: argparse.Namespace) -> int:
    from . import knowledge
    kb = knowledge.load(_home(args))
    camp = kb.meta.get("stats", {}).get("disambiguation") or {}
    print(f"阶段性消歧：{'开启' if camp.get('enabled') else '关闭'}")
    print(f"  阶段名：{camp.get('campaign', '')}")
    print(f"  复核期：{camp.get('review_after', '')}")
    print(f"  覆盖术语：{camp.get('items', 0)} 条")
    print(f"  相关问答：{kb.meta.get('stats', {}).get('campaign_faqs', 0)} 组")
    print("\n说明：" + camp.get("note", ""))
    print("\n开关：编辑 config/disambiguation.json 的 campaign.enabled，然后 mcai build")
    return 0


def cmd_gaps(args: argparse.Namespace) -> int:
    from .telemetry import for_root
    rows = for_root(_home(args)).gaps(limit=args.limit)
    if not rows:
        print("暂无未命中的问题。")
        return 0
    print(f"未命中问题（{len(rows)} 条），可作为人工补词输入：")
    for r in rows:
        print(f"  [{r['count']}次] {r['query']}  （最近 {r['last_seen']}）")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    from .telemetry import for_root
    s = for_root(_home(args)).stats()
    origin = s.get("by_origin") or {}
    print(f"累计 {s['total']} 次：业务问答 {s.get('business', 0)} · 健康探测 {s.get('probes', 0)}")
    print(f"批量问答：{s.get('batch_calls', 0)} 次调用 / {s.get('batch_answers', 0)} 个问题 · "
          f"命中率 {round((s.get('hit_rate') or 0) * 100)}%")
    print(f"来源：本机 {origin.get('local', 0)} · 外部 {origin.get('external', 0)} · 未标记 {origin.get('unknown', 0)}")
    kinds = s.get("by_client_kind") or {}
    print(f"客户端：自检 {kinds.get('self', 0)} · 命令行 {kinds.get('shell', 0)} · 浏览器 {kinds.get('browser', 0)} · MCP {kinds.get('mcp', 0)}")
    print(f"渠道：{s['by_channel']}")
    print(f"类型：{s['by_type']}")
    print("最近 14 天：")
    for day, n in s["by_day"].items():
        bar = "█" * min(n, 40)
        print(f"  {day}  {n:>3} {bar}")
    if s["top_questions"]:
        print("高频问题：")
        for item in s["top_questions"][:8]:
            print(f"  [{item['count']}] {item['question']}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    from . import dataset
    from .corpus import load_corpus
    from .disambig import load as load_disambig
    from .extract import build as build_kb

    home = _home(args)
    corpus = load_corpus(home / "config" / "corpus.json")
    curated = load_config(home / "config" / "curated.json")
    overrides_path = home / "config" / "overrides.json"
    overrides = load_config(overrides_path) if overrides_path.exists() else {}
    disambig = load_disambig(home / "config" / "disambiguation.json")
    kb = build_kb(corpus, curated, overrides, disambig)
    result = dataset.export(kb, args.out or home / "export")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_probe(args: argparse.Namespace) -> int:
    from . import knowledge, probe
    from .llm import LLM

    home = _home(args)
    kb = knowledge.load(home)
    llm = LLM(home / "config" / "llm.json")
    if not llm.available:
        print("❌ 未找到 API 密钥：请检查 config/llm.json 的 key_path，或设置 DEEPSEEK_API_KEY")
        return 1
    questions = probe.build_questions(kb, limit=args.limit)
    if not questions:
        print("❌ 没有生成出题目，请检查知识库")
        return 1
    print(f"抽检 {len(questions)} 道题 × 2 种条件（baseline / grounded）…")

    def progress(i: int, total: int, label: str) -> None:
        print(f"  [{i}/{total}] {label}")

    result = probe.run(llm, kb, questions, progress=progress)
    report = probe.write_report(result, home / "reports")
    s = report["summary"]
    print("\n结果：")
    print(f"  答案对齐率   baseline {s['baseline']['alignment_rate']:.0%} → "
          f"grounded {s['grounded']['alignment_rate']:.0%}（{s['uplift']['alignment_rate']:+.0%}）")
    print(f"  答案覆盖度   baseline {s['baseline']['coverage_mean']:.2f} → "
          f"grounded {s['grounded']['coverage_mean']:.2f}（{s['uplift']['coverage']:+.2f}）")
    print(f"  学说术语数   baseline {s['baseline']['kb_terms_mean']:.1f} → "
          f"grounded {s['grounded']['kb_terms_mean']:.1f}（{s['uplift']['kb_terms']:+.1f}）")
    print(f"  报告：{report['markdown']}")
    return 0


def cmd_factory(args: argparse.Namespace) -> int:
    from . import factory, knowledge
    from .llm import LLM

    home = _home(args)
    kb = knowledge.load(home)
    names = [n.strip() for n in (args.concepts or "").split(",") if n.strip()]
    if names:
        concepts = []
        for name in names:
            c = kb.resolve(name)
            if not c:
                print(f"⚠️  未找到术语：{name}")
                continue
            concepts.append(c)
    else:
        order = ["元意识", "观测创造实在", "序生智能体"]
        concepts = [kb.by_term[t] for t in order if t in kb.by_term][: args.top]
    if not concepts:
        print("❌ 没有可用的概念")
        return 1

    formats = list(factory.FORMATS) if args.formats == "all" else [
        f.strip() for f in args.formats.split(",") if f.strip() in factory.FORMATS
    ]
    if not formats:
        print("❌ 未知的格式，可选：" + "、".join(factory.FORMATS))
        return 1

    llm = LLM(home / "config" / "llm.json")
    offline = args.offline or not llm.available
    if offline and not args.offline:
        print("⚠️  未找到 API 密钥，自动切换到离线模板模式")

    print(f"生成 {len(concepts)} 个概念 × {len(formats)} 种格式 → {home / 'content'}")

    def progress(i: int, total: int, label: str) -> None:
        print(f"  [{i}/{total}] {label}")

    result = factory.generate_batch(
        llm if not offline else None, kb, concepts, formats,
        home / "content", force=args.force, offline=offline, progress=progress,
    )
    print(f"\n完成：新建 {len(result['created'])}，跳过 {len(result['skipped'])}，失败 {len(result['failed'])}")
    for item in result["created"]:
        flag = "" if item["status"] == "draft" else "（需复核：" + "、".join(item["issues"]) + "）"
        print(f"  · {item['concept']} / {item['format']} {flag}")
    for item in result["failed"]:
        print(f"  ✗ {item['concept']} / {item['format']}：{item['error']}")
    return 0 if not result["failed"] else 2


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--home", default=None, help="工作区目录（默认：MCAI_HOME 或当前目录）")

    parser = argparse.ArgumentParser(prog="mcai", description="元意识知识资产引擎")
    parser.add_argument("--version", action="version", version=f"mcai-knowledge {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", parents=[common], help="初始化一个工作区（复制配置模板）")
    p_init.add_argument("path", nargs="?", default=".", help="目标目录，默认当前目录")
    p_init.add_argument("--force", action="store_true", help="覆盖已有配置")
    p_init.set_defaults(func=cmd_init)

    p_build = sub.add_parser("build", parents=[common], help="从语料重建知识库与站点")
    p_build.add_argument("--serve", action="store_true", help="构建后启动本地服务")
    p_build.add_argument("--port", type=int, default=8787)
    p_build.set_defaults(func=cmd_build)

    p_serve = sub.add_parser("serve", parents=[common], help="启动本地 Web 应用与 HTTP API")
    p_serve.add_argument("--port", type=int, default=8787)
    p_serve.add_argument("--host", default="127.0.0.1", help="监听地址；对外暴露用 0.0.0.0")
    p_serve.add_argument("--token", default="", help="Bearer 令牌；也可用环境变量 MCAI_TOKEN")
    p_serve.add_argument("--rate-limit", type=int, default=60, help="每 IP 每分钟请求上限")
    p_serve.add_argument("--autopilot", type=int, default=0, metavar="秒",
                         help="在服务内启用自动驾驶：每 N 秒检查语料并自检（0=关闭）")
    p_serve.set_defaults(func=cmd_serve)

    p_api = sub.add_parser("api", parents=[common], help="只启动 HTTP API（同一套服务）")
    p_api.add_argument("--port", type=int, default=8788)
    p_api.add_argument("--host", default="127.0.0.1")
    p_api.add_argument("--token", default="")
    p_api.add_argument("--rate-limit", type=int, default=60)
    p_api.add_argument("--autopilot", type=int, default=0, metavar="秒")
    p_api.set_defaults(func=cmd_api)

    p_mcp = sub.add_parser("mcp", parents=[common], help="启动 MCP 服务器（stdio）")
    p_mcp.set_defaults(func=cmd_mcp)

    p_auto = sub.add_parser("autopilot", parents=[common],
                            help="自动驾驶：检查语料、自动重建、健康自检")
    p_auto.add_argument("--once", action="store_true", help="只跑一轮（适合计划任务）")
    p_auto.add_argument("--interval", type=int, default=60, help="常驻模式的检查间隔秒数")
    p_auto.add_argument("--port", type=int, default=8787)
    p_auto.add_argument("--no-server", action="store_true", help="不自动拉起服务")
    p_auto.set_defaults(func=cmd_autopilot)

    p_quality = sub.add_parser("quality", parents=[common], help="质量巡检：定义、关系、死链、JSON-LD")
    p_quality.set_defaults(func=cmd_quality)

    p_selftest = sub.add_parser("selftest", parents=[common], help="接口自测：MCP 工具与关键问答")
    p_selftest.set_defaults(func=cmd_selftest)

    p_snap = sub.add_parser("snapshot", parents=[common], help="生成一份本地快照（zip，自动轮转）")
    p_snap.add_argument("-m", "--note", default="", help="备注，例如「接入新语料前」")
    p_snap.add_argument("--keep", type=int, default=8, help="保留最近几份，默认 8")
    p_snap.add_argument("--no-corpus", action="store_true", help="不打包语料文件（包更小）")
    p_snap.set_defaults(func=cmd_snapshot)

    p_snaps = sub.add_parser("snapshots", parents=[common], help="列出已有快照")
    p_snaps.add_argument("--limit", type=int, default=20)
    p_snaps.set_defaults(func=cmd_snapshots)

    p_restore = sub.add_parser("restore", help="把快照恢复到指定目录")
    p_restore.add_argument("archive", help="快照 zip 的路径")
    p_restore.add_argument("--to", required=True, help="恢复目标目录（建议新目录）")
    p_restore.add_argument("--force", action="store_true", help="目标非空时覆盖")
    p_restore.set_defaults(func=cmd_restore)

    p_dash = sub.add_parser("dashboard", parents=[common], help="生成本地观测台页面")
    p_dash.set_defaults(func=cmd_dashboard)

    p_status = sub.add_parser("status", parents=[common], help="查看自动驾驶写入的状态")
    p_status.set_defaults(func=cmd_status)

    p_token = sub.add_parser("token", help="生成一个 Bearer 令牌")
    p_token.set_defaults(func=cmd_token)

    p_seturl = sub.add_parser("set-url", parents=[common], help="设置对外地址并重建（更新清单里的链接）")
    p_seturl.add_argument("url", help="如 https://xxx.trycloudflare.com")
    p_seturl.add_argument("--no-build", action="store_true", help="只改配置，不立即重建")
    p_seturl.set_defaults(func=cmd_set_url)

    p_doctor = sub.add_parser("doctor", help="对已部署实例做远程体检")
    p_doctor.add_argument("--url", required=True, help="如 https://xxx.trycloudflare.com")
    p_doctor.add_argument("--token", default="", help="Bearer 令牌；也可用 MCAI_TOKEN")
    p_doctor.set_defaults(func=cmd_doctor)

    p_report = sub.add_parser("report", parents=[common], help="知识库体检报告")
    p_report.set_defaults(func=cmd_report)

    p_dis = sub.add_parser("disambig", parents=[common], help="阶段性消歧状态")
    p_dis.set_defaults(func=cmd_disambig)

    p_stats = sub.add_parser("stats", parents=[common], help="调用统计")
    p_stats.set_defaults(func=cmd_stats)

    p_gaps = sub.add_parser("gaps", parents=[common], help="未命中的问题（人工补词输入）")
    p_gaps.add_argument("--limit", type=int, default=20)
    p_gaps.set_defaults(func=cmd_gaps)

    p_probe = sub.add_parser("probe", parents=[common], help="抽检模型的自发知识与注入增益")
    p_probe.add_argument("--limit", type=int, default=12)
    p_probe.set_defaults(func=cmd_probe)

    p_factory = sub.add_parser("factory", parents=[common], help="内容工厂（可选配件）")
    p_factory.add_argument("--concepts", type=str, default="")
    p_factory.add_argument("--top", type=int, default=3)
    p_factory.add_argument("--formats", type=str, default="all")
    p_factory.add_argument("--offline", action="store_true")
    p_factory.add_argument("--force", action="store_true")
    p_factory.set_defaults(func=cmd_factory)

    p_export = sub.add_parser("export", parents=[common], help="仅导出数据集")
    p_export.add_argument("--out", type=str, default="")
    p_export.set_defaults(func=cmd_export)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
