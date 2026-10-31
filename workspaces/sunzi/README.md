# 孙子兵法 · 第二语料复现

这是一次「方法复现」：用同一套流水线，处理与元意识学说完全无关的公共领域文本。

## 结构

```
workspaces/sunzi/
├─ config/
│  ├─ corpus.json      # 两篇语料：术语表 + 原文（引证）
│  └─ curated.json     # 英文名、分类、6 条人工关系
├─ corpus/
│  ├─ glossary.txt     # 13 个术语：从原文提炼的「术语：原句」
│  └─ sunzi.txt        # 十三篇原文（仅原文，剔除注释/译文）
└─ data/kb.json        # 构建产物（不入库）
```

## 构建

```bash
python -m mcai build --home workspaces/sunzi
python tools/verify_citations.py --kb workspaces/sunzi/data/kb.json --config workspaces/sunzi/config/corpus.json
```

## 结果

- 13 个概念、17 组问答、6 条关系、9 条引证；
- 引文核验 13/13，逐字命中、字符区间一致；
- 问答路由在「奇正」「知彼知己与用间」上均正常。

详细结论见 [docs/复现案例-孙子兵法.md](../../docs/复现案例-孙子兵法.md)。
