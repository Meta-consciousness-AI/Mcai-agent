import json, re
from docx import Document

kb=json.load(open("data/kb.json",encoding="utf-8"))
known=set()
for c in kb["concepts"]:
    known.add(c["term"]); known.update(c.get("aliases") or [])

d=Document(r"E:\th\元意识\元意识运营\3、元意识学说极简版.docx")
texts=[p.text.strip() for p in d.paragraphs if p.text.strip()]
quoted=[]
for t in texts:
    for m in re.findall(r"[“「]([\u4e00-\u9fff]{2,14})[”」]", t):
        quoted.append(m)
from collections import Counter
cnt=Counter(quoted)
missing=[(w,n) for w,n in cnt.items() if w not in known]
print("极简版引号内术语:", len(cnt), " 未收录:", len(missing))
for w,n in missing[:25]:
    print(f"  {w}  ×{n}")
print("\n极简版段落数:", len(texts))

