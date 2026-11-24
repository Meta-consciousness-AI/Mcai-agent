# 变更记录（`docs/变更记录/`）

> 知识库 `data/kb.json` 是唯一权威源。任何增 / 改 / 删都应通过 `mcai change` 完成，
> 由工具写库并追加一行到 `kb.jsonl`；不要直接编辑 json，否则不留痕。

## 一行一条（JSONL）

| 字段 | 含义 |
|---|---|
| `ts` | 变更时间（本地时区，ISO 8601） |
| `kind` | `term` / `faq` / `relation` |
| `action` | `add` / `update` / `delete` |
| `key` | 术语名、问答问题，或「源术语->目标术语」 |
| `field` | 改的是哪一列（仅 update） |
| `before` / `after` | 改前 / 改后（删除时 after 为 null，新增时 before 为 null） |
| `reason` | 变更理由（数量减少时必填） |
| `basis` | 依据：文稿名/章节，或「作者口述」（必填） |
| `counts_before` / `counts_after` | 变更前后的术语/问答/关系计数 |
| `applied` | 是否已落盘（`--dry-run` 时为 false） |

## 用法

```powershell
# 改定义（需要理由与依据）
mcai change --kind term --action update --key 元识 --field definition --value "……" --reason "……" --basis "《元意识学说极简版》……"

# 删关系（数量减少，必须给理由）
mcai change --kind relation --action delete --key "元识->元知" --reason "……" --basis "……"

# 只校验不落盘
mcai change --kind term --action update --key 元识 --value "……" --basis "作者口述" --dry-run
```

工具会拒绝：缺 `--basis`；数量减少但缺 `--reason`；对象不存在或已存在。拒绝时不写 kb、也不写日志。
