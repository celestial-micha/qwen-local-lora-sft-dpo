# 项目最终总结：Qwen 本地 LoRA SFT / DPO 学习链路

Date: 2026-05-16

## 一句话结论

这个项目已经从环境验证、base 推理、public-SFT、自采集技术数据、
custom-SFT、tiny/naive DPO、expanded behavior gate，一直推进到 Stage 6
面试包。最终没有接受任何 DPO/SFT repair adapter 作为默认模型，因为 prompt
7 仍无法在不回归旧题的情况下稳定通过行为验收。

最终推荐：

```text
保守推荐 checkpoint: outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
最好 DPO artifact:   outputs/dpo_lora_qwen05b_naive_v6
最终展示报告:        reports/stage6_final_interview_package.md
```

## 项目目标

项目目标不是训练一个大而全的垂直模型，而是在本地 RTX 4060 Laptop GPU 上
跑通一条可解释、可复现、适合面试讲述的后训练链路：

```text
环境检查 -> base Qwen 推理 -> public instruction SFT
-> base vs public-SFT 行为对比 -> 自采集技术数据清洗和转换
-> custom LoRA SFT -> 固定 prompt 回归测试
-> tiny / naive DPO -> expanded behavior gate -> Stage 6 面试包装
```

## 最终状态

| 项目维度 | 最终状态 |
|---|---|
| 本地环境 | Windows + RTX 4060 Laptop GPU 可跑 Qwen2.5-0.5B LoRA SFT/DPO |
| 稳定模型栈 | `torch 2.5.1+cu124`, `transformers 4.46.3`, `peft 0.13.2`, `trl 0.12.2` |
| public-SFT | 训练成功，但未修正目标技术概念 |
| custom-SFT | v3 通过 7 / 8 固定 prompt，是保守推荐 checkpoint |
| DPO | v1-v8 多轮均可跑，v6/v7/v8 固定 gate 最高 7 / 8 |
| expanded gate | v6 在 24 题 expanded suite 只过 7 / 24，loss-vs-behavior 0 / 13 |
| 最终瓶颈 | prompt 7：为什么不能只看 loss 判断 SFT 是否成功 |
| Stage 6 | 已完成最终面试包和中英简历 bullet |

## 阶段时间线

| 阶段 | 做了什么 | 结果 |
|---|---|---|
| Stage 1 | base Qwen 本地推理 | base 会把 LoRA/SFT/DPO 解释成错误概念 |
| Stage 2A | 公开中文 instruction 数据准备 | 1003 train / 111 eval |
| Stage 3A | public LoRA SFT | 训练成功，final train loss 1.7558 |
| Stage 4A | base vs public-SFT 对比 | public-SFT 没修正目标概念 |
| Stage 2B | 自采集技术数据 | 10 source, 96 cleaned chunks, 157 seed samples |
| Stage 3B | custom LoRA SFT | v1 改善 6 / 8 prompt |
| Stage 2B.2/3B.2 | badcase patch | v3 低学习率续训保留/改善 7 / 8 |
| Stage 2B.3/3B.3 | prompt 7 SFT patch | 单点修复会导致旧题回归，保留 v3 |
| Stage 5A-C | tiny DPO | 可跑无 OOM，但行为不通过 |
| Stage 5D-G | DPO v2-v6 | v6 separate ref 最稳，7 / 8 |
| Stage 5H | prompt 7 数据和 expanded gate 设计 | 278 train / 55 eval / 24 prompt suite |
| Stage 5I | v6 expanded eval | 7 / 24，loss-vs-behavior 0 / 13 |
| Stage 5J/M | DPO v7/v8 | preference accuracy 1.0，但仍 7 / 8 |
| Stage 5K/N/O/P | SFT repair probes | 不能同时修 prompt 7 且保住旧题 |
| Stage 6 | 最终面试包 | 完成最终叙事、示例、失败复盘和简历 bullet |

## 数据资产

Public SFT:

```text
data/raw/alpaca_gpt4_data_zh_1200.jsonl
data/processed/sft_train.jsonl
data/processed/sft_eval.jsonl
```

Custom technical SFT:

```text
data/raw/custom_sources.jsonl
data/raw/custom_cleaned_chunks.jsonl
data/raw/custom_instruction_seed.jsonl
data/processed/custom_sft_train.jsonl
data/processed/custom_sft_eval.jsonl
```

DPO / repair data:

```text
data/processed/dpo_tiny_train.jsonl
data/processed/dpo_larger_v6_train.jsonl
data/processed/dpo_stage5h_prompt7_train.jsonl
data/processed/dpo_stage5m_exact_prompt7_train.jsonl
data/processed/sft_stage5n_prompt7_micro_train.jsonl
data/processed/sft_stage5o_prompt7_exact_train.jsonl
```

## 模型与 checkpoint 决策

接受：

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

理由：

- 固定 prompt 通过 7 / 8；
- 比从头重训更稳；
- 没有明显破坏 LoRA/SFT/DPO、数据管线、显存风险等已修好的行为；
- 适合作为简历/面试里的“保守可复盘 checkpoint”。

最好但不接受为默认：

```text
outputs/dpo_lora_qwen05b_naive_v6
```

理由：

- DPO 中表现最好，固定 prompt 7 / 8；
- separate frozen reference model 跑通；
- preference eval accuracy 1.0；
- 但 prompt 7 仍失败，expanded loss-vs-behavior 0 / 13。

拒绝的典型案例：

- SFT v5 / Stage 5O：能强行修 prompt 7，但旧题回归；
- DPO v3：偏好更新过强，旧能力大面积回归；
- DPO v7/v8：preference 指标很好，但 fixed behavior gate 不过。

## 核心评测结论

固定 8 prompt gate：

```text
custom-SFT v3: 7 / 8
DPO v6:        7 / 8
DPO v7:        7 / 8
DPO v8:        7 / 8
Stage 5N:      7 / 8
Stage 5O:      4 / 8
Stage 5P:      6 / 8
```

expanded Stage 5H gate：

```text
DPO v6: 7 / 24
loss-vs-behavior subset: 0 / 13
```

最终判断：

```text
loss 下降、eval loss 好看、preference accuracy 1.0 都不是最终验收。
最终验收必须看固定 prompt 行为、expanded holdout、badcase 和旧能力回归。
```

## 项目最重要的技术经验

1. public-SFT 是工程 baseline，不是目标行为保证。
2. badcase 比单纯 loss 更能指导数据建设。
3. custom 数据不能只堆数量；要减少噪声、增加 targeted QA 和 replay。
4. 从头重训可能破坏旧能力；低学习率续训更稳。
5. DPO 在 8GB 上可行，但要小 batch、短序列、谨慎 reference 设计。
6. preference accuracy 可以到 1.0，但行为 gate 仍可能失败。
7. exact prompt 修复可能造成过拟合，必须用旧题回归测试拦住。
8. 最终停止训练也是工程决策的一部分。

## 面试讲法

```text
我在本地 RTX 4060 上做了一个 Qwen2.5-0.5B 的 LoRA SFT/DPO 后训练项目。
public-SFT 用来证明工程链路，custom-SFT 用自采集技术数据修正目标概念，
DPO 用来验证偏好优化和显存可行性。最终最有价值的结论是：loss 和
preference accuracy 不能替代 behavior gate，所以我保留稳定 SFT v3，
把 DPO v6 当实验 artifact，而不是盲目继续加训练。
```

详细面试包：

```text
reports/stage6_final_interview_package.md
```

## 最终文件入口

建议以后先读这些：

```text
reports/final_project_summary_zh.md
reports/stage6_final_interview_package.md
reports/stage5j_to_5p_prompt7_repair_report.md
reports/stage5_structured_behavior_score_report.md
reports/project_context_for_next_chat.md
notebooks/04_full_pipeline_learning.ipynb
README.zh-CN.md
PROJECT_RUNBOOK.md
```

## 后续边界

当前不要继续盲目 DPO/SFT。

如果将来恢复训练，必须先重新设计 prompt 7 curriculum：

- 不只重复 exact prompt；
- 增加更多 loss/eval/preference/fixed gate 的改写；
- 增加 prompts 1-6/8 的 replay；
- 先跑固定 8 prompt，再跑 expanded Stage 5H gate；
- 只有 prompt 7 通过且旧题不回归，才接受新 checkpoint。
