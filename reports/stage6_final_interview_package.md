# Stage 6 Final Interview Package

Date: 2026-05-16

## Final Position

This project is now ready to present as a local post-training engineering
project. The accepted checkpoint and the best DPO artifact are deliberately
different:

```text
Recommended checkpoint: outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
Best DPO artifact:      outputs/dpo_lora_qwen05b_naive_v6
```

The DPO adapters are useful experiment artifacts, but none is accepted as the
default model because prompt 7 still failed the behavior gate. Stage 6 does not
add training steps.

## 30-Second Interview Story

Chinese:

我在 RTX 4060 Laptop GPU 上跑通了一条 Qwen2.5-0.5B 的本地 LoRA
SFT/DPO 后训练链路。项目不是只追 loss，而是先用 public-SFT 证明训练、
保存、加载和对比链路可跑，再用固定 badcase 驱动自采集技术数据和
custom-SFT。后面 DPO 证明 8GB 显存可以跑 preference optimization，但
v6/v7/v8 即使 preference 指标很好，也没稳定通过 prompt 7 的行为 gate。
所以这个项目最后讲的是一条可复盘的工程闭环：训练指标、偏好指标和真实
行为验收必须分开看。

English:

I built a local Qwen2.5-0.5B LoRA SFT/DPO pipeline on an RTX 4060 Laptop GPU.
The project starts with public instruction SFT to prove the Windows/CUDA/PEFT
training path works, then uses fixed badcases to drive a self-collected
technical-data loop. Custom LoRA SFT fixed most LoRA/SFT/DPO concept mistakes,
and DPO proved memory-feasible on 8GB VRAM. The most important result was not a
single better loss number: multiple DPO runs reached strong preference metrics,
but behavior gates still caught prompt-level failures. That gave me a clean
experiment story about why loss, preference accuracy, and actual model behavior
must be evaluated separately.

## Two-Minute Narrative

Chinese:

这个项目从一个很具体的 badcase 开始：base Qwen2.5-0.5B 会把机器学习
里的 LoRA、SFT、DPO 解释成通信、网络、数据预处理等错误概念。第一步我
没有直接上复杂数据，而是先做 public instruction SFT，目的是证明本地
Windows/CUDA/PEFT 链路能训练、保存 adapter、重新加载并做对比。

Stage 4A 发现 public-SFT 虽然训练成功，但没有修正目标技术概念。这不是
失败，而是进入 Stage 2B 的依据：我做了自采集技术数据管线，保留 source
metadata，做清洗、去重、筛选，再转成 instruction-answer 样本。custom
SFT 后，固定 prompt 从大量概念误解提升到 7/8。

之后我没有直接大规模 DPO，而是把 Stage 5 拆成 preference 数据准备、
tiny smoke test、行为检查和后续扩展。硬件不是主要瓶颈：v6 separate
reference DPO、v7/v8 都能跑，preference accuracy 也能到 1.0。但 prompt
7 仍然暴露问题：模型会说“不能只看 loss”，却没有稳定覆盖 loss 是平均
优化信号、必要但不充分、要看固定 prompt、badcase 和旧能力回归。Stage
5O 甚至证明 exact SFT 可以强行修 prompt 7，但会把旧题打坏。所以我最终
停止训练，把结论整理成 Stage 6：loss 和 preference accuracy 都只是支持
证据，真正验收要看 behavior gate。

English:

The project began with base Qwen2.5-0.5B confusing technical terms. For example,
it explained machine-learning LoRA as "Local Recurrent Attention" or wireless
LoRa, and it confused SFT/DPO with networking or data-preprocessing terms.

I first trained a public-data LoRA SFT adapter using a Chinese instruction
dataset. That run was important because it proved the local environment,
adapter save/load, and comparison scripts worked. But Stage 4A showed the public
adapter did not repair the target technical concepts. That failure became the
reason to build Stage 2B: a self-collected technical-data pipeline with source
metadata, cleaning, deduplication, filtering, and instruction-answer conversion.

The custom SFT loop then improved 7 of 8 fixed prompts. I kept a conservative
checkpoint, `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`, because later
SFT patches could fix one prompt while breaking older prompts.

Stage 5 tested DPO carefully. I split it into preference data preparation,
tiny smoke tests, behavior checks, and larger follow-up runs. The hardware was
not the blocker: even separate-reference DPO v6 and later v7/v8 ran without OOM.
But prompt 7, "为什么不能只看 loss 判断一次 SFT 是否成功？", stayed hard. DPO
v7/v8 reached preference accuracy 1.0, yet fixed behavior scoring still failed
prompt 7. Direct SFT could force prompt 7 to pass, but then old prompts
regressed. That is the core engineering lesson: good loss and preference
metrics are supporting evidence, not final acceptance criteria.

## Before / After Examples

### Example 1: LoRA Definition

Prompt:

```text
请用三点解释机器学习里的 LoRA 微调，不要解释成无线通信 LoRa。
```

Base failure:

```text
LoRA（Local Recurrent Attention）是一种特殊的循环神经网络架构...
```

Accepted custom-SFT v3 / DPO v6 behavior:

```text
机器学习里的 LoRA 是参数高效微调方法，全称常解释为低秩适配，
不是无线通信 LoRa。它冻结基础模型大部分参数，只在部分线性层旁边
训练低秩 adapter 矩阵。
```

What this shows:

- The model moved from a wrong expansion to the correct low-rank adapter
  concept.
- It also learned to state the "not wireless LoRa" boundary explicitly.

### Example 2: SFT vs LoRA

Prompt:

```text
SFT 是什么？它和 LoRA 是什么关系？
```

Base failure:

```text
SFT（Shortest Flawed Link）是一种用于优化网络连接的算法...
```

Accepted custom-SFT v3 / DPO v6 behavior:

```text
SFT 是 supervised fine-tuning，也就是有监督微调，描述训练目标、
数据形式和损失函数。LoRA 是参数高效微调方法，描述怎样少量更新
模型参数。所以 LoRA SFT 的意思是：用 LoRA adapter 来执行 SFT。
```

What this shows:

- The answer separates objective/data format from parameter-efficient training
  method.
- It gives the interview-friendly phrasing for "LoRA SFT".

### Example 3: Data Pipeline

Prompt:

```text
如果面试官问你这个项目的数据管线，你会怎么讲？
```

Base failure:

```text
数据预处理包括清理缺失值、填充空值、标准化...
```

Accepted custom-SFT v3 behavior:

```text
先说公开数据集用来建立可复现基线，证明 LoRA SFT 链路能训练、
保存和加载。然后说 Stage 4A 发现 public-SFT 没修正 LoRA/SFT/DPO
概念误解，所以进入 Stage 2B。Stage 2B 做自采集技术数据：采集、
清洗、去重、筛选、转 instruction-answer，再训练 custom-SFT 并做三方对比。
```

What this shows:

- The model learned the project-specific pipeline rather than generic tabular
  preprocessing.
- This is the strongest resume/interview example because it ties engineering
  process to model behavior.

## Failure Review

### Prompt 7: Loss vs Behavior

Prompt:

```text
为什么不能只看 loss 判断一次 SFT 是否成功？
```

What a good answer must include:

- loss is an average training/eval optimization signal;
- loss is necessary but not sufficient;
- fixed prompt behavior must be checked;
- badcases and old-capability regression must be reviewed;
- the public-SFT / LoRA/SFT/DPO example from this project.

What happened:

- SFT v3 was stable at 7 / 8, but prompt 7 stayed weak.
- DPO v6 reached eval preference accuracy 1.0 and fixed 7 / 8 prompts, but
  expanded scoring showed 0 / 13 loss-vs-behavior prompts passed.
- DPO v7 and v8 also reached preference accuracy 1.0 but still failed prompt 7.
- Stage 5N micro-SFT preserved old prompts but still failed prompt 7.
- Stage 5O forced prompt 7 to pass, but old prompts regressed to 4 / 8.
- Stage 5P tried a middle point but ended at 6 / 8.

Decision:

```text
Stop training. Do not add DPO/SFT steps just because metrics look good.
```

## What I Would Emphasize In An Interview

1. I treated public-SFT as an engineering baseline, not a final target model.
2. I used fixed prompts as a reproducible behavior gate before and after every
   training change.
3. I kept source metadata and reports so the data pipeline is auditable.
4. I separated three signals: train/eval loss, preference accuracy, and visible
   behavior.
5. I rejected models that improved one metric while regressing old prompts.
6. I stopped the training loop when more DPO/SFT steps were no longer producing
   reliable behavior gains.

## Resume Bullets

Chinese:

- 在 RTX 4060 Laptop GPU 上搭建 Qwen2.5-0.5B 本地 LoRA SFT/DPO 后训练链路，完成数据准备、训练、adapter 保存加载、固定 prompt 回归测试和结构化评分报告。
- 构建自采集技术数据管线，覆盖 source metadata、清洗、去重、筛选和 instruction-answer 转换，用 badcase 驱动 custom-SFT 数据迭代。
- 通过 public-SFT、custom-SFT、tiny DPO、separate-reference DPO 多阶段实验验证：loss 和 preference accuracy 不能替代行为验收，最终保留稳定 SFT checkpoint，拒绝会造成 prompt 回归的候选模型。

English:

- Built a local Qwen2.5-0.5B LoRA SFT/DPO post-training pipeline on an RTX 4060
  laptop GPU, including data preparation, adapter training, save/load checks,
  fixed-prompt regression tests, and structured behavior scoring.
- Designed a self-collected technical-data pipeline with source metadata,
  cleaning, deduplication, filtering, and instruction-answer conversion, using
  model badcases to drive custom-SFT data iteration.
- Evaluated public-SFT, custom-SFT, tiny DPO, and separate-reference DPO runs;
  showed that loss and preference accuracy were insufficient without behavior
  gates, and rejected candidates that improved one prompt while regressing
  older capabilities.

## Portfolio / README Summary

```text
This project is a local, reproducible Qwen2.5-0.5B LoRA SFT/DPO learning
pipeline. It demonstrates not only how to train adapters, but how to evaluate
post-training behavior responsibly: public-SFT proves the engineering loop,
custom technical data repairs target concepts, and DPO is tested only behind
fixed-prompt behavior gates. The final lesson is that lower loss and high
preference accuracy are not enough unless visible behavior and regression tests
also pass.
```

## Recommended Demo Flow

1. Show the base LoRA/SFT/DPO confusion in `reports/compare_outputs_public_sft.jsonl`.
2. Show public-SFT as pipeline proof, not concept repair.
3. Show custom-SFT v3 fixing LoRA/SFT/DPO and data-pipeline prompts.
4. Show DPO v6 as the best DPO artifact but not accepted.
5. Show Stage 5I-5P as the strongest evidence that behavior gates matter.

Core files:

```text
reports/stage6_final_interview_package.md
reports/stage5j_to_5p_prompt7_repair_report.md
reports/stage5_structured_behavior_score_report.md
reports/stage5i_expanded_behavior_score_v6_report.md
notebooks/04_full_pipeline_learning.ipynb
```

## Next Work Boundary

Do not continue blind DPO. If training resumes, start with a broader prompt-7
curriculum and stronger replay protection, then require both:

- original fixed 8 prompt gate;
- expanded Stage 5H behavior gate.

Until then, Stage 6 should be treated as the completed presentation package.
