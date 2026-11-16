# 切块策略对比实验

## 方法

- 语料：`eval/corpus/` 下 10 个源文档。
- 评测集：`eval/golden_set.jsonl`，共 30 条。
- 检索：本地词法 embedding（256 维），pgvector 召回 top-5。
- 指标：Hit@1、Hit@3、Recall@5、MRR，均在源文档级别计算。
- 策略：
  - `fixed`：固定约 512 token 切块，中文按约 1.4 字符/token 估算。
  - `semantic`：按 Markdown 标题切块。

## 索引规模

| 策略 | chunk 数 |
| --- | --- |
| fixed | 11 |
| semantic | 22 |

## 指标对比

| 指标 | fixed | semantic |
| --- | --- | --- |
| Hit@1 | 0.5333 | 0.4333 |
| Hit@3 | 0.8667 | 0.8000 |
| Recall@5 | 0.9333 | 0.8667 |
| MRR | 0.6983 | 0.6111 |

## 结论

在本语料和词法 embedding 下，`fixed` 在四项指标上均优于 `semantic`。`semantic` 按标题切出 22 个更细的片段，破坏了词法共现信息，导致命中率和 MRR 下降。因此当前选择 `fixed`（约 512 token）作为默认切块策略。

说明：该结论受当前词法 embedding 影响，后续若替换为真实语义 embedding，需要重新跑本对比。

以上数字均来自 `python eval/run_eval.py` 的真实输出，原始结果保存在 `eval/results_fixed.json` 和 `eval/results_semantic.json`。
