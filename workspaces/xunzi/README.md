# 荀子《正名》· 第三语料复现

定义密集型的先秦哲学文本，用于检验单字术语与抽象概念的抽取。

## 结构

```
workspaces/xunzi/
├─ config/
│  ├─ corpus.json      # 术语表 + 原文（引证）
│  └─ curated.json     # 英文名、分类、9 条人工关系
├─ corpus/
│  ├─ glossary.txt     # 12 个术语：原文中的「谓之」定义句
│  └─ xunzi.txt        # 《正名》原文（剔除译文）
└─ data/kb.json        # 构建产物（不入库）
```

## 构建

```bash
python -m mcai build --home workspaces/xunzi
python tools/verify_citations.py --kb workspaces/xunzi/data/kb.json --config workspaces/xunzi/config/corpus.json
```

## 结果

- 12 个概念、5 组问答、9 条关系、12 条引证；
- 引文核验 12/12，逐字命中；
- 「什么是性」「名和辞有什么关系」「什么是约定俗成」均正常。

详细结论见 [docs/复现案例-荀子正名.md](../../docs/复现案例-荀子正名.md)。
