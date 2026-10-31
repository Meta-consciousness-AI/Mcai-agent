# 道德经 · 定义分层验证

用于验证 V1.1 的「原文句 + 编者释义」规则：`definition` 必须是原文，`editor_note` 单独存放编者理解。

## 结构

```
workspaces/daodejing/
├─ config/
│  ├─ corpus.json      # 术语表 + 原文（引证）
│  └─ curated.json     # 英文名、分类、7 条关系、concept_meta（editor 标记与释义）
├─ corpus/
│  ├─ glossary.txt     # 10 个术语：原文句
│  └─ daodejing.txt    # 八十一章原文（剔除直译）
└─ data/kb.json        # 构建产物（不入库）
```

## 构建

```bash
python -m mcai build --home workspaces/daodejing
python tools/verify_citations.py --kb workspaces/daodejing/data/kb.json --config workspaces/daodejing/config/corpus.json
```

## 结果

- 10 个概念、8 组问答、7 条关系、10 条引证；
- 引文核验 10/10，逐字命中；
- 全部概念 `definition_type = "editor"`，页面与接口均显示「编者释义（非原文）」。

详细结论见 [docs/复现案例-道德经.md](../../docs/复现案例-道德经.md)。
