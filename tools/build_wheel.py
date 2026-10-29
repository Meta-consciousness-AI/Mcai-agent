import base64, hashlib, zipfile
from pathlib import Path

import tomllib

root = Path(".").resolve()
meta = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
version = meta["version"]
out = root / "dist_pkg" / f"mcai_knowledge-{version}-py3-none-any.whl"
out.parent.mkdir(parents=True, exist_ok=True)

files = []
for p in sorted((root / "mcai").rglob("*")):
    if p.is_file() and (p.suffix == ".py" or p.suffix == ".json"):
        files.append((p.relative_to(root).as_posix(), p.read_bytes()))

readme = (root / "README.md").read_text(encoding="utf-8")
license_text = (meta.get("license") or {}).get("text", "MIT")
classifiers = "\n".join(f"Classifier: {c}" for c in meta.get("classifiers", []))
dist = f"mcai_knowledge-{version}.dist-info"
license_files = []
for name in ("LICENSE", "LICENSE-CONTENT"):
    path = root / name
    if path.exists():
        license_files.append((f"{dist}/licenses/{name}", path.read_bytes()))
metadata = f"""Metadata-Version: 2.1
Name: mcai-knowledge
Version: {version}
Summary: 元意识知识资产引擎：把学说变成可被 AI / Agent 调用的结构化知识
Author: 元意识（重庆）人工智能科技有限公司
License: {license_text}
License-File: LICENSE
License-File: LICENSE-CONTENT
{classifiers}
Requires-Python: >=3.10
Requires-Dist: python-docx>=1.1.0
Requires-Dist: lxml>=5.0.0
Description-Content-Type: text/markdown

{readme}
"""
wheel = """Wheel-Version: 1.0
Generator: manual-stdlib
Root-Is-Purelib: true
Tag: py3-none-any
"""
entry = """[console_scripts]
mcai = mcai.cli:main
mcai-mcp = mcai.mcp_server:main_entry
"""
dist = f"mcai_knowledge-{version}.dist-info"
entries = files + license_files + [
    (f"{dist}/METADATA", metadata.encode("utf-8")),
    (f"{dist}/WHEEL", wheel.encode("utf-8")),
    (f"{dist}/entry_points.txt", entry.encode("utf-8")),
]

records = []
for name, data in entries:
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
    records.append(f"{name},sha256={digest},{len(data)}")
records.append(f"{dist}/RECORD,,")

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for name, data in entries:
        z.writestr(name, data)
    z.writestr(f"{dist}/RECORD", "\n".join(records) + "\n")
print("built:", out, round(out.stat().st_size / 1024, 1), "KB")