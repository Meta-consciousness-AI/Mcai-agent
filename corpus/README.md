# corpus/

把自己的 Word / PDF 语料放在这个目录，然后在 `config/corpus.json` 里登记：

```json
{
  "id": "glossary",
  "path": "corpus/标准词表.docx",
  "title": "标准词表",
  "kind": "glossary",
  "priority": 100
}
```

`kind` 取值：

- `glossary`：词表，定义优先；
- `evidence`：正文，供引文；
- `playbook`：方法论文档。

初始化配置：

```bash
cp config/corpus.example.json config/corpus.json
cp config/llm.example.json config/llm.json
```

编辑 `config/corpus.json` 里的 `corpus` 列表，再执行 `mcai build`。