# 引用忠实度评测集（Citation Faithfulness Benchmark）

> 目的：测一个知识包/问答系统在回答时，引用是否真实、可回查，以及是否会对库外问题明确说「不知道」。
> 状态：v0.1，2026-11-13。
> 依赖：`mcai.verify` 的语料加载能力。

## 一、四个层级

| 层级 | 数量 | 问法 | 期望 |
|---|---:|---|---|
| exact | 54 | 直接问「什么是 X？」 | 答对并带正确出处 |
| paraphrase | 10 | 用定义改写，不出现术语名 | 仍能定位到正确概念并带出处 |
| homonym | 4 | 近义/同名混淆问题 | 能区分，不编造 |
| refusal | 10 | 库外问题 | 明确说「未找到」，不硬答 |

## 二、运行

```bash
# 1. 生成题目
python benchmark/citation-faithfulness/build_items.py

# 2. 生成基线预测（本地知识引擎）
python benchmark/citation-faithfulness/run_local.py

# 3. 评分
python benchmark/citation-faithfulness/score.py
```

也可以用任意系统的输出替换 `predictions-local.jsonl`，格式：

```json
{"id": "exact-meta-consciousness", "type": "faq", "answer": "...",
 "citations": [{"doc": "...", "section": "...", "quote": "..."}]}
```

## 三、当前基线（2026-11-13）

| 层级 | n | precision | recall | coverage | fabrication | refusal |
|---|---:|---:|---:|---:|---:|---:|
| exact | 54 | 100.0% | 100.0% | 100.0% | 0.0% | — |
| paraphrase | 10 | — | 0.0% | 0.0% | — | — |
| homonym | 4 | — | — | 100.0% | 0.0% | — |
| refusal | 10 | — | — | — | — | 100.0% |

## 四、结果说明

- **exact 满分**：题目直接问术语，检索引擎能命中标准问答；
- **paraphrase 0%**：改写提问时，引擎只返回「相关词条」，不给带出处的答案，这是当前最明显的短板；
- **homonym 通过**：能给出区分性回答，没有编造；
- **refusal 通过**：库外问题都明确说「没有直接命中」。

## 五、已知局限

1. exact 层偏简单，满分不代表真实能力；
2. 评分只测「引用是否真实、是否命中标准出处」，不测答案是否优美；
3. 语料匹配用去空白归一化，不做语义相似；
4. 这是自评基线，不是第三方评测。

## 六、下一步

- [ ] 改进 paraphrase：按定义关键词检索，而不是按术语名；
- [ ] 增加「跨概念比较」题；
- [ ] 增加「版本差异」题（同一术语多版本）；
- [ ] 发布为可引用的 benchmark（Zenodo / HuggingFace）。

## 变更记录

- 2026-11-13：建立，四层 78 题，跑出基线。
