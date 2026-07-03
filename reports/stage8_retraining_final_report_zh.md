# Stage 8 扩容后重训与最终 checkpoint 决策

Date: 2026-07-04

## 结论

本轮 Stage 8 不只是补数据，而是完整重跑了“扩容数据 -> SFT -> 96 题行为评测 -> badcase patch -> DPO -> 再评测 -> checkpoint 决策”的闭环。

最终保留：

```text
outputs/sft_lora_qwen05b_stage8_expanded_v2
```

拒绝：

```text
outputs/sft_lora_qwen05b_stage8_expanded
outputs/sft_lora_qwen05b_stage8_expanded_v3
outputs/sft_lora_qwen05b_stage8_expanded_v4_targeted
outputs/dpo_lora_qwen05b_stage8_from_sft_v2
```

保留 SFT-v2 的原因不是它完美，而是它在本轮 expanded 96 题行为套件上最高，并且 DPO / v3 / v4 都没有同时做到“分数更高、旧问题不回归、项目事实不漂移”。

## 数据规模

Stage 8 将原先小规模技术微调数据扩展为：

| Asset | Rows | Purpose |
|---|---:|---|
| SFT train v1 | 1,500 | 初始扩容 SFT |
| SFT eval v1 | 160 | held-out SFT eval |
| SFT train v2 | 1,500 | Stage 8C badcase 后的 balanced replay / correction patch |
| SFT eval v2 | 160 | v2 held-out eval |
| SFT train v3 | 1,500 | fact-guard patch，尝试压制项目事实编造 |
| SFT eval v3 | 160 | v3 held-out eval |
| SFT train v4 targeted | 1,500 | 针对 DPO-vs-SFT / public-SFT 两个弱区的低学习率 patch |
| SFT eval v4 targeted | 160 | v4 held-out eval |
| DPO train | 1,500 | expanded preference pairs |
| DPO eval | 160 | held-out preference eval pairs |
| Behavior prompts | 96 | 8 个核心技术区域，每区 12 题 |

## 96 题行为评测结果

评分脚本：`scripts/score_stage8_behavior_outputs.py`。它是透明关键词 gate，不是最终 LLM judge；报告中所有 checkpoint 决策都结合了人工 badcase 抽查。

| Variant | Passed | Total Score | Decision |
|---|---:|---:|---|
| base | 0 / 96 | 128 | baseline only |
| public-SFT | 0 / 96 | 78 | baseline only |
| old custom-SFT v3 | 25 / 96 | 227 | old stable reference |
| old DPO v6 | 22 / 96 | 237 | old DPO artifact, not accepted as final |
| Stage 8 SFT v1 | 20 / 96 | 229 | rejected: loss 好看但行为未提升 |
| Stage 8 SFT v2 | 48 / 96 | 295 | accepted for Stage 8 expanded run |
| Stage 8 SFT v3 | 18 / 96 | 227 | rejected: fact-guard 过强导致整体退化 |
| Stage 8 DPO from v2 | 44 / 96 | 294 | rejected: DPO 指标好，但行为低于 SFT-v2 且抽查有事实漂移 |
| Stage 8 SFT v4 targeted | 39 / 96 | 277 | rejected: public-SFT 有改善，但引入更多混乱表达 |

SFT-v2 的区域结果：

| Area | Passed |
|---|---:|
| LoRA 定义与边界 | 9 / 12 |
| SFT 与 LoRA 关系 | 5 / 12 |
| DPO 与 SFT 区别 | 0 / 12 |
| public-SFT 诊断价值 | 0 / 12 |
| 自采集技术数据管线 | 4 / 12 |
| DPO 显存风险 | 7 / 12 |
| loss 与行为验收 | 12 / 12 |
| 固定 Prompt 与扩展评测 | 11 / 12 |

## 训练指标

| Run | Init Adapter | Train Rows | LR | Final / Key Metrics |
|---|---|---:|---:|---|
| SFT v1 | old custom-SFT v3 | 1,500 | 3e-5 | train_loss 0.7535, eval_loss 0.1991 |
| SFT v2 | old custom-SFT v3 | 1,500 | 2e-5 | train_loss 0.6524, eval_loss 0.0899 |
| SFT v3 | SFT v2 | 1,500 | 1e-5 | train_loss 0.7034, eval_loss 0.1790 |
| DPO from v2 | SFT v2 | 1,500 pairs | 5e-6 | eval preference accuracy 1.0, train_loss 0.0035 |
| SFT v4 targeted | SFT v2 | 1,500 | 5e-6 | train_loss 0.5552, eval_loss 0.2400 |

训练指标不能单独决定 checkpoint。SFT v1 和 v3 的 eval loss 都不差，但 96 题行为结果分别只有 20/96 和 18/96。DPO from v2 的 preference eval accuracy 达到 1.0，但行为分数低于 SFT-v2。

## Badcase 复盘

Stage 8C 发现 SFT v1 的主要问题：

- loss 下降但行为没有超过旧 custom-SFT v3；
- 回答中混入不存在的 stage / savepoint / eval_node 等项目事实；
- LoRA 定义、DPO vs SFT、数据管线等区域仍会偏题。

Stage 8E 的 SFT-v2 显著提升到 48/96，但仍有两个明显弱区：

- `DPO 与 SFT 区别`: 0/12，常缺少“先做 SFT”和 chosen/rejected preference pair 的完整表述。
- `public-SFT 诊断价值`: 0/12，常不能稳定说清 public-SFT 只是工程 baseline，且没有修正目标概念。

Stage 8H 的 DPO from v2 没有被接受：

- preference eval accuracy = 1.0，但 96 题行为只有 44/96；
- 抽查出现未记录事实，例如虚构显存、虚构通过率、虚构 adapter 关系；
- 证明 DPO 指标不能替代行为 gate。

Stage 8I 的 v4 targeted patch 也没有被接受：

- public-SFT 区域从 0/12 提升到 4/12；
- 但总分降到 39/96，并且 DPO-vs-SFT 仍为 0/12；
- 抽查显示 targeted patch 让模型把 LoRA/SFT/DPO 概念混在一起，旧能力回归。

## 简历可用表述

可以写：

```text
在原 142/15 custom SFT 与 8 题 pilot gate 基础上，将技术概念数据扩展为
1,500 条 SFT train、160 条 SFT held-out eval、1,500 条 DPO preference pair、
160 条 DPO eval pair，并构建 96 条 expanded 行为评测 prompt。重新跑通
SFT / DPO 训练与评测闭环后，old custom-SFT v3 在 96 题透明规则 gate 上为
25/96，Stage 8 SFT-v2 提升到 48/96；DPO from v2 虽然 preference eval
accuracy 达到 1.0，但 96 题行为为 44/96 且存在事实漂移，因此最终保留
行为更稳定的 SFT-v2 checkpoint。
```

边界必须说明：

```text
48/96 是透明关键词 gate 的行为评测结果，不是人工终审准确率；这个结果说明
扩容和 badcase 迭代有效，但模型仍在 DPO-vs-SFT、public-SFT 诊断价值等区域
有明显弱点。因此简历中应强调“数据扩容、重训、评测、拒绝坏 checkpoint 的
工程闭环”，不要包装成大规模高准确率模型。
```

## 重要文件

```text
data/processed/custom_sft_expanded_train.jsonl
data/processed/custom_sft_expanded_eval.jsonl
data/processed/custom_sft_expanded_v2_train.jsonl
data/processed/custom_sft_expanded_v2_eval.jsonl
data/processed/custom_sft_expanded_v3_train.jsonl
data/processed/custom_sft_expanded_v3_eval.jsonl
data/processed/custom_sft_expanded_v4_targeted_train.jsonl
data/processed/custom_sft_expanded_v4_targeted_eval.jsonl
data/processed/dpo_expanded_train.jsonl
data/processed/dpo_expanded_eval.jsonl
data/samples/custom_technical_prompts_stage8_expanded.jsonl
configs/dpo_qwen05b_stage8_expanded_from_sft_v2.yaml
scripts/stage8_compare_adapters.py
scripts/score_stage8_behavior_outputs.py
scripts/prepare_stage8_v2_balanced_sft_data.py
scripts/prepare_stage8_v3_fact_guard_sft_data.py
scripts/prepare_stage8_v4_targeted_sft_data.py
reports/stage8a_baseline_expanded_eval.md
reports/stage8c_sft_expanded_behavior_score.md
reports/stage8e_sft_v2_train_and_eval_report.md
reports/stage8f_sft_v3_behavior_score.md
reports/stage8h_dpo_from_sft_v2_behavior_score.md
reports/stage8i_sft_v4_targeted_behavior_score.md
```
