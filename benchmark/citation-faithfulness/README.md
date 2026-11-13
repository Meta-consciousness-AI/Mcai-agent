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
| semantic | 10 | 真正换说法，不含定义原词 | 能按意思定位并带出处 |
| semantic-heldout | 5 | 同类但未参与调词 | 检验是否只是背题 |
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
| paraphrase | 10 | 100.0% | 100.0% | 100.0% | 0.0% | — |
| homonym | 4 | — | — | 100.0% | 0.0% | — |
| semantic | 10 | 100.0% | 100.0% | 100.0% | 0.0% | — |
| semantic-heldout | 5 | 50.0% | 0.0% | 20.0% | 0.0% | — |
| refusal | 10 | — | — | — | — | 100.0% |

## 四、结果说明

- **exact 满分**：题目直接问术语，检索引擎能命中标准问答；
- **paraphrase 100%**：题目从句中抽原句提问，引擎按定义片段定位后给出带出处的答案（2026-11-13 修复）；
- **homonym 通过**：能给出区分性回答，没有编造；
- **semantic 100%（调词后）**：加入「语义线索短语」词表后，这 10 题全部命中；
- **semantic-heldout 20%**：同类但未参与调词的 5 题只命中 1 题，说明线索词表不能泛化，属于「针对题目调参」；
- **refusal 通过**：库外问题都明确说「没有直接命中」。

## 五、已知局限

0. paraphrase 题来自定义原文抽取，属于「抽取式改写」；semantic 层靠人工线索词表，只能覆盖调过的说法，留出题 20%；

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
