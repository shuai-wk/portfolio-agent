# LLM-as-Judge 忠实度检查

## 方法

- 从 `eval/golden_set.jsonl` 中随机抽取 10 条（种子 42）。
- 检索：`fixed` 切块索引，pgvector 召回 top-3。
- 生成：当前后端的 `MockLLM`（经 `LangfuseLLM` 包装）。
- Judge：本地确定性判官，计算回答的字符 bigram 与检索上下文的重合度，作为忠实度分数。
- 判定：分数 >= 0.7 为 `faithful`，>= 0.4 为 `partial`，否则为 `not_faithful`。

## 结果

| 问题 | 忠实度 | 判定 |
| --- | --- | --- |
| 你熟悉哪些编程语言？ | 0.2105 | not_faithful |
| 你在第一家公司负责什么系统？ | 0.3333 | not_faithful |
| 你的职业定位是什么？ | 0.1053 | not_faithful |
| 你熟悉 Kubernetes 吗？ | 0.3556 | not_faithful |
| 你用 Docker 和 Kubernetes 吗？ | 0.5192 | partial |
| 你部署过生产环境吗？ | 0.2895 | not_faithful |
| 你是什么专业毕业的？ | 0.2105 | not_faithful |
| 你做过后端数据库优化吗？ | 0.3250 | not_faithful |
| 你有开源项目吗？ | 0.3143 | not_faithful |
| 电商项目你负责订单还是库存？ | 0.2195 | not_faithful |

平均忠实度：**0.2883**

## 结论

当前 `MockLLM` 生成的是模板化回答，没有真正引用检索到的上下文，因此忠实度整体偏低，10 条中 9 条判定为 `not_faithful`、1 条为 `partial`。

这符合预期：本阶段 LLM 仍是 mock，后续接入真实生成模型后，需要用同样的 judge 重新评估，确保回答被检索来源支撑、不产生幻觉。

以上数字均来自 `python eval/faithfulness.py` 的真实输出，原始结果保存在 `eval/faithfulness_results.json`。
