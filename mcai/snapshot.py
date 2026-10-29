"""本地快照：把代码、配置、知识库与语料打包成带清单的 zip，并自动轮转。

不依赖 git。每次执行生成 backups/snapshot-YYYYmmdd-HHMMSS.zip，
保留最近 N 份；可列出、校验、恢复到指定目录（默认恢复到一个新目录，不覆盖现有文件）。
"""
from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path

INCLUDE_DIRS = ["mcai", "tests", "deploy", "config", "docs", "tools"]
INCLUDE_FILES = [
    "README.md", "HANDOFF.md", "pyproject.toml", "requirements.txt",
    "run.py", "start.bat", "启动.cmd", "停止.cmd", "install.ps1", ".gitignore",
]
# 排除：可再生成、体积大或含运行痕迹
EXCLUDE_PARTS = {
    "__pycache__", ".build", "dist", "content", "node_modules",
    "usage.jsonl", "access.log", "autopilot.jsonl", "status.json",
    "quality.json", "selftest.json", "server.log", "server.err.log",
}
INCLUDE_DATA = ["kb.json", "changelog.jsonl"]


def _iter_files(root: Path, rel_dir: str) -> list[Path]:
    base = root / rel_dir
    if not base.exists():
        return []
    out = []
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDE_PARTS for part in path.relative_to(root).parts):
            continue
        out.append(path)
    return out


def _corpus_files(root: Path) -> list[Path]:
    cfg_path = root / "config" / "corpus.json"
    if not cfg_path.exists():
        return []
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return []
    files = []
    for spec in cfg.get("corpus", []):
        raw = Path(spec.get("path", ""))
        path = raw if raw.is_absolute() else root / raw
        if path.exists() and path.is_file():
            files.append(path)
    return files


def create(root: str | Path, note: str = "", keep: int = 8, with_corpus: bool = True) -> dict:
    root = Path(root).resolve()
    backups = root / "backups"
    backups.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3]
    archive = backups / f"snapshot-{stamp}.zip"

    files: list[Path] = []
    for d in INCLUDE_DIRS:
        files.extend(_iter_files(root, d))
    for name in INCLUDE_FILES:
        p = root / name
        if p.exists() and p.is_file():
            files.append(p)
    for name in INCLUDE_DATA:
        p = root / "data" / name
        if p.exists() and p.is_file():
            files.append(p)

    corpus = _corpus_files(root) if with_corpus else []

    kb_stats = {}
    kb_path = root / "data" / "kb.json"
    if kb_path.exists():
        try:
            stats = json.loads(kb_path.read_text(encoding="utf-8")).get("meta", {}).get("stats", {})
            kb_stats = {k: stats.get(k) for k in ("concepts", "faqs", "relations", "evidence")}
        except json.JSONDecodeError:
            pass

    manifest = {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "note": note,
        "workspace": str(root),
        "kb": kb_stats,
        "corpus": [str(p) for p in corpus],
        "files": len(files) + len(corpus),
    }

    total = 0
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("snapshot-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for path in files:
            zf.write(path, path.relative_to(root).as_posix())
            total += path.stat().st_size
        for path in corpus:
            zf.write(path, f"corpus/{path.name}")
            total += path.stat().st_size

    manifest["bytes"] = total
    manifest["archive"] = archive.name
    manifest["archive_bytes"] = archive.stat().st_size

    removed = _rotate(backups, keep)
    return {"archive": str(archive), "manifest": manifest, "removed": removed}


def _rotate(backups: Path, keep: int) -> list[str]:
    archives = sorted(backups.glob("snapshot-*.zip"))
    if keep <= 0 or len(archives) <= keep:
        return []
    removed = []
    for old in archives[: len(archives) - keep]:
        try:
            old.unlink()
            removed.append(old.name)
        except OSError:
            pass
    return removed


def list_snapshots(root: str | Path, limit: int = 20) -> list[dict]:
    backups = Path(root) / "backups"
    if not backups.exists():
        return []
    out = []
    for archive in sorted(backups.glob("snapshot-*.zip"), reverse=True)[:limit]:
        entry = {
            "archive": archive.name,
            "bytes": archive.stat().st_size,
            "created_at": datetime.fromtimestamp(archive.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
            "note": "",
            "kb": {},
        }
        try:
            with zipfile.ZipFile(archive) as zf:
                manifest = json.loads(zf.read("snapshot-manifest.json").decode("utf-8"))
                entry["note"] = manifest.get("note", "")
                entry["kb"] = manifest.get("kb", {})
                entry["created_at"] = manifest.get("created_at", entry["created_at"])
        except (KeyError, json.JSONDecodeError, zipfile.BadZipFile):
            pass
        out.append(entry)
    return out


def verify(archive: str | Path) -> dict:
    archive = Path(archive)
    if not archive.exists():
        return {"ok": False, "error": f"文件不存在：{archive}"}
    try:
        with zipfile.ZipFile(archive) as zf:
            bad = zf.testzip()
            names = zf.namelist()
        return {"ok": bad is None, "files": len(names), "broken": bad or ""}
    except zipfile.BadZipFile as exc:
        return {"ok": False, "error": str(exc)}


def restore(archive: str | Path, target: str | Path, force: bool = False) -> dict:
    archive = Path(archive)
    target = Path(target).resolve()
    if target.exists() and any(target.iterdir()) and not force:
        return {"ok": False, "error": f"目标目录非空：{target}（加 --force 覆盖）"}
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(target)
    return {"ok": True, "target": str(target), "files": len(list(target.rglob("*")))}
