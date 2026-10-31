# 变更记录

## 0.3.0 — 2026-10-31

- 概念新增 `definition_type`（`quote` / `editor`）与 `editor_note`，支持无定义句文本的定义分层；
- `Source` / `Document` 新增 `edition`，语料可记录版本、来源与校勘；
- 回答引证、MCP 词条、`provenance.jsonl` 与站点均输出 `edition`；
- 打包脚本在构建 wheel 前同步 `data/kb.json`，避免包内数据过期；
- 人工裁定来源的 `edition` 记为「人工裁定」。

## 0.2.9 — 2026-10-31

- 新增 `config/terminology.json`：同名概念、废弃术语映射；
- 概念新增 `homonyms`，回答与词条接口返回；
- 概念关系分层：`core` / `derived` / `mention`，`related` 默认只返回前两类；
- 新增 `data/concept_versions.jsonl`，记录定义变化的哈希版本；
- MCP `mcai_related` 增加 `include_mentions` 参数。

## 0.2.8 — 2026-10-30

- 出处记录增加字符区间 `char_start` / `char_end`，引文可逐字核验；
- 检索归一化：全角/半角、繁简、标点与空白，支持拼写容错；
- `mcai_answer` 与 HTTP API 支持 `citations` 模式，只返回问题与出处；
- 修复 Word 手动换行导致的重复位置号。

## 0.2.7 — 2026-10-30

- MCP 的 5 个工具与 3 个 prompt 描述全部改为英文；
- 补齐 `mcai_related`、`mcai_list` 的参数说明。

## 0.2.6 及更早

- 站点、数据集、MCP 基础能力与首次发布，详见 git 历史。
