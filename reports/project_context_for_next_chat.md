# Project Context For Next Chat

如果开启新的聊天，请先让 Codex 阅读这个文件。

## 当前项目

项目目录：

```text
D:\coding\qwen lorar sft\qwen-local-lora-sft-dpo
```

项目目标：

```text
在本地 RTX 4060 Laptop GPU 上，用 Qwen2.5-0.5B-Instruct 跑通一条可复现、可解释、适合面试讲述的 LoRA SFT / 数据清洗 / DPO 学习链路。
```

当前路线不是“下载一个数据集然后微调完事”，而是：

```text
Stage 2A/3A/4A: 公开 instruction 数据集建立 public-SFT 基线
Stage 2B/3B/4B: 自采集/自整理技术数据，清洗、去重、转 instruction-answer，再训练 custom-SFT 并做三方对比
Stage 5: SFT 行为稳定后，再做 tiny DPO smoke test
```

术语：

```text
SFT = 有监督微调目标和数据形式
LoRA = 参数高效微调方法
LoRA SFT = 用 LoRA adapter 来执行 SFT
DPO = 用 chosen/rejected 偏好对做直接偏好优化
```

## 环境

```text
conda env: qwen-lora-local
Python: D:\conda-envs\qwen-lora-local\python.exe
GPU: NVIDIA GeForce RTX 4060 Laptop GPU
VRAM: 8 GB
```

稳定依赖：

```text
torch==2.5.1+cu124
transformers==4.46.3
accelerate==1.1.1
peft==0.13.2
datasets==3.1.0
trl==0.12.2
huggingface-hub==0.26.5
fsspec==2024.9.0
```

每次运行前：

```powershell
conda activate qwen-lora-local
cd "D:\coding\qwen lorar sft\qwen-local-lora-sft-dpo"
$env:HF_HOME=(Resolve-Path -LiteralPath ".hf_cache").Path
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"
```

注意：

- 不要随意升级到高版本 `transformers / peft / trl`，之前 Windows 原生训练遇到过 `python.exe` 进程级崩溃。
- 模型已经缓存后，优先加 `--local_files_only`，避免无效代理或网络问题。
- 训练环境暂时不装 `gradio`，以后 demo 单独建环境。

## 已完成阶段

### Stage 1: Base 推理

已完成。Base Qwen 可以本地加载并推理。

重要观察：

```text
base model 会把机器学习里的 LoRA/SFT/DPO 解释成通信、网络安全、数据预处理等错误概念。
```

这些 before badcase 后来用于驱动数据建设。

### Stage 2A: 公开 SFT 数据准备

已完成。

```text
Dataset: llm-wizard/alpaca-gpt4-data-zh
Raw snapshot: data/raw/alpaca_gpt4_data_zh_1200.jsonl
Train: data/processed/sft_train.jsonl, 1003 rows
Eval: data/processed/sft_eval.jsonl, 111 rows
Report: reports/stage2_sft_data_report.md
```

### Stage 3A: Public LoRA SFT

已完成。

```text
Output adapter: outputs/sft_lora_qwen05b_public
Trainable params: 4,399,104
Trainable ratio: 0.8826%
Runtime: about 24.4 minutes
Final train loss: 1.7558
Eval loss at step 100: 1.8263
Report: reports/stage3a_public_lora_sft_report.md
```

用户观察显存：

```text
public LoRA SFT 训练约 5.5GB / 8GB
adapter 推理约 1.2GB / 8GB
```

### Stage 4A: Base vs Public-SFT 对比

已完成。

```text
Raw output: reports/compare_outputs_public_sft.jsonl
Summary: reports/compare_base_sft.md
Report: reports/stage4a_public_sft_comparison_report.md
```

结论：

```text
public-SFT 训练成功，但没有修正 LoRA/SFT/DPO 技术概念误解。
```

这不是失败，而是 Stage 2B 自采集技术数据的依据。

### Stage 2B: 自采集/自整理技术数据

已完成、修订，并在 Stage 2B.2 / Stage 2B.3 做了 badcase patch 和 DPO 前稳定性 gate。

脚本：

```text
scripts/prepare_custom_technical_data.py
```

当前输出：

```text
data/raw/custom_sources.jsonl
data/raw/custom_cleaned_chunks.jsonl
data/raw/custom_instruction_seed.jsonl
data/processed/custom_sft_train.jsonl
data/processed/custom_sft_eval.jsonl
data/samples/custom_technical_prompts.jsonl
```

当前统计：

```text
Sources: 10
Accepted cleaned chunks: 96
Rejected chunks: 12
Instruction-answer seed samples: 157
Train samples: 142
Eval samples: 15
Stage 2B.3 focused patch train samples: 28
Duplicate instruction samples: 0
Train max tokens before truncation: 323
Eval max tokens before truncation: 291
```

重要迭代：

```text
第一版 Stage 2B 生成 160 条 instruction 样本，Stage 3B 初跑能训练但输出仍有幻觉。
原因是 project_record_summary 样本过多、太泛，容易让模型复制项目记录模板。
后来把 max_doc_samples 从 60 降到 20，并加入 12 条直接命中固定 prompt 的 targeted QA。
Stage 2B.2 又加入 8 条 badcase patch 样本，专门补 public-SFT motivation 和 loss-vs-behavior。
Stage 2B.3 又加入 10 条 loss-vs-behavior 样本和 7 条 replay 样本，并把 targeted/patch/replay 样本固定留在 train。
```

报告：

```text
reports/stage2b_custom_technical_data_report.md
reports/stage2b2_badcase_patch_report.md
reports/stage2b3_sft_stability_gate_report.md
```

### Stage 3B: Custom LoRA SFT

已完成。

```text
Output adapter: outputs/sft_lora_qwen05b_custom
Train rows: 119
Eval rows: 13
Trainable params: 4,399,104
Trainable ratio: 0.8826%
Runtime: about 12.3 minutes
Final train loss: 0.4656
Best observed eval loss: 0.8311 around epoch 5.04
Report: reports/stage3b_custom_lora_sft_report.md
```

训练命令：

```powershell
D:\conda-envs\qwen-lora-local\python.exe scripts\train_sft_lora.py `
  --train_file data\processed\custom_sft_train.jsonl `
  --eval_file data\processed\custom_sft_eval.jsonl `
  --output_dir outputs\sft_lora_qwen05b_custom `
  --max_length 512 `
  --batch_size 1 `
  --grad_accum 4 `
  --epochs 10 `
  --logging_steps 10 `
  --eval_steps 50 `
  --save_steps 50 `
  --report_to none `
  --local_files_only
```

观察：

```text
eval loss 在 epoch 5 左右最好，后面略升，说明小数据 10 epoch 有轻微过拟合风险。
```

### Stage 4B: 三方对比

已完成。

```text
Script: scripts/compare_three_outputs.py
Prompt file: data/samples/custom_technical_prompts.jsonl
Raw output: reports/compare_outputs_three_way_custom.jsonl
Report: reports/stage4b_three_way_comparison_report.md
```

结论：

```text
custom-SFT 明显改善 6 / 8 个固定技术 prompt。
```

修好的典型 prompt：

- 机器学习里的 LoRA，不再解释成无线通信 LoRa。
- SFT 是什么，以及它和 LoRA 的关系。
- DPO 和 SFT 的区别，以及为什么通常先 SFT 后 DPO。
- 自采集数据的采集、清洗、去重、筛选、instruction-answer 转换。
- 8GB 显存下 DPO 风险和降显存手段。
- 面试中如何讲项目数据管线。

仍然弱的 prompt：

- 为什么 public-SFT 没修正概念，反而说明 Stage 2B 有必要。
- 为什么不能只看 loss 判断 SFT 是否成功。

下一轮数据应该围绕这两个 badcase 做小补丁。

### Stage 2B.2 / Stage 3B.2 / Stage 4B.2: Badcase Patch Loop

已完成。

Stage 2B.2 加入 8 条 focused badcase 样本后，做了三次验证：

```text
1. outputs/sft_lora_qwen05b_custom_v2
   从头训练 5 epoch，final train loss 1.0496，行为回归，不推荐。

2. outputs/sft_lora_qwen05b_custom_v2_10ep/checkpoint-100
   从头训练 10 epoch，并选 best-eval checkpoint，仍然回归，不推荐。

3. outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
   从 outputs/sft_lora_qwen05b_custom 低学习率续训 2 epoch，当前最好。
```

v3 结果：

```text
Runtime: about 157.5 seconds
Final train loss: 0.2873
Eval loss at epoch 1.90: 0.0348
Fixed-prompt behavior: preserved or improved 7 / 8 prompts
```

重要结论：

```text
小 badcase patch 如果从头训练，可能破坏旧 adapter 已经学会的好行为。
更稳的做法是从当前最好 adapter 低学习率续训，并把固定 prompt 当作回归测试集。
```

当前仍然弱的 prompt：

```text
为什么不能只看 loss 判断一次 SFT 是否成功？
```

这个结论后来进入 Stage 2B.3：围绕 loss-vs-behavior 做更小的数据补丁，同时 replay 已经修好的 7 个 prompt。

### Stage 2B.3 / Stage 3B.3 / Stage 4B.3: DPO 前 SFT 稳定性 gate

已完成，并且停在 DPO 之前。

目标：

```text
修第 7 个 loss-vs-behavior badcase
保住 v3 已经答好的 7 个 prompt
如果不稳定，就不进入 DPO
```

尝试结果：

```text
v4: outputs/sft_lora_qwen05b_custom_v4_stage2b3_loss_patch
    从 v3 用完整 Stage 2B.3 数据低学习率续训。
    结果：大多旧能力还在，但第 7 个 prompt 仍弱，prompt 4 有轻微回归。不推荐。

v5: outputs/sft_lora_qwen05b_custom_v5_stage2b3_focused_patch
    用 28 条 focused patch 训练，exact loss prompt 重复 12 次。
    结果：第 7 个 prompt 修好了，但多个旧 prompt 明显回归。不推荐。

v6: outputs/sft_lora_qwen05b_custom_v6_stage2b3_balanced_patch
    降低学习率和 epoch。
    结果：仍然不稳，不推荐。

v7 interpolation probe:
    用 scripts/interpolate_lora_adapters.py 混合 v3 和 v5。
    alpha 0.15/0.25/0.40 spot-check 没修好第 7 个 prompt，不继续 full compare。
```

当前推荐：

```text
继续把 outputs/sft_lora_qwen05b_custom_v3_from_v1_patch 作为 Stage 5 起点。
Stage 5 已拆分：先 DPO 数据，再 tiny DPO，再固定 prompt 对比，最后才考虑扩大 DPO。
见 reports/stage5_dpo_plan.md。
```

### Stage 5A: Tiny DPO preference 数据

已完成，但还没有开始 DPO 训练。

输出：

```text
Generator: scripts/prepare_tiny_dpo_data.py
Data: data/processed/dpo_tiny_train.jsonl
Report: reports/stage5a_dpo_tiny_data_report.md
Pairs: 33
Unique prompts: 33
Start adapter for Stage 5B: outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

设计：

- 包含 exact loss-vs-behavior prompt。
- 包含 public-SFT motivation pair。
- 包含 LoRA/SFT/DPO replay、data-pipeline、DPO-VRAM 和 interview narrative。
- rejected 答案尽量模拟 base/public/v4/v5/v6 的真实 badcase 或 near-miss。

Tokenizer spot check：

```text
max prompt tokens: 29
max prompt+chosen tokens: 100
max prompt+rejected tokens: 69
```

### Stage 5B: Tiny DPO smoke test

已完成。这只是显存/运行可行性 smoke test，不是最终行为验收。

输出：

```text
Script: scripts/train_dpo.py
Config: configs/dpo_qwen05b.yaml
Input data: data/processed/dpo_tiny_train.jsonl
Start adapter: outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
Output adapter: outputs/dpo_lora_qwen05b_tiny
Report: reports/stage5b_tiny_dpo_smoke_report.md
```

结果：

```text
Rows: 33
Optimizer steps: 4
Train runtime: 32.8 seconds
Train loss: 0.9319
torch max allocated: 2.179 GB
torch max reserved: 4.059 GB
nvidia-smi before/after idle: 25 MiB / 8188 MiB
OOM/native crash: no
Adapter reload check: passed
```

注意：

- 成功命令只设置 `HF_HOME=.hf_cache`，并移除 `TRANSFORMERS_CACHE`。
- 如果把 `TRANSFORMERS_CACHE` 指到 `.hf_cache`，会找不到 `.hf_cache/hub`
  下面的模型缓存。
- PEFT 保存时尝试远程查 base config，被代理拒绝后忽略；adapter 已成功保存
  并可重新加载。

### Stage 5C: Tiny DPO behavior check

已完成，但行为 gate 没过，不建议扩大 DPO。

输出：

```text
Script: scripts/compare_four_outputs.py
Raw output: reports/compare_outputs_four_way_dpo_tiny.jsonl
Report: reports/stage5c_tiny_dpo_behavior_report.md
Compared: base / public-SFT / custom-SFT v3 / DPO-tiny
```

结果：

```text
Clear pass: 5 / 8
Watch: 1 / 8
Fail: 2 / 8
Core success criterion: not met
```

具体判断：

- Prompt 1 LoRA definition：DPO-tiny 和 v3 一样好。
- Prompt 2 SFT/LoRA relation：DPO-tiny 和 v3 一样好。
- Prompt 3 DPO/SFT：DPO-tiny 和 v3 一样好。
- Prompt 4 public-SFT motivation：DPO-tiny 回归，出现“从零开始建模型”“三到六个月”等无依据说法。
- Prompt 5 data pipeline：DPO-tiny 和 v3 一样好。
- Prompt 6 DPO VRAM：DPO-tiny 略微更具体，保住。
- Prompt 7 loss-vs-behavior：仍然弱，没有稳定说清楚 loss 只是必要不充分、要看固定 prompt 行为和回归。
- Prompt 8 interview data pipeline：大体保住，但比 v3 略绕，列为 watch。

结论：

```text
Stage 5B 证明显存/运行可行。
Stage 5C 说明当前 tiny DPO 数据/训练还没有通过行为 gate。
不要直接进入 Stage 5D 扩大 DPO。
下一步应修 Stage 5A preference 数据，尤其 prompt 4 和 prompt 7，再重新 tiny DPO。
```

### Stage 5A.2 / 5B.2 / 5C.2 and Stage 5A.3 / 5B.3 / 5C.3

已完成，详见：

```text
reports/stage5_dpo_revision_loop_report.md
```

v2 修订：

```text
Data: data/processed/dpo_tiny_v2_train.jsonl
Config: configs/dpo_qwen05b_v2.yaml
Output adapter: outputs/dpo_lora_qwen05b_tiny_v2
Rows: 47
Optimizer steps: 5
Runtime: 43.9 seconds
Train loss: 0.8345
torch max allocated: 2.180 GB
Adapter reload: passed
Raw compare: reports/compare_outputs_four_way_dpo_tiny_v2.jsonl
```

v2 结论：

```text
没有 OOM/崩溃，但 prompt 7 仍弱，并再次出现“三到六个月”等无依据说法。
不通过行为 gate。
```

v3 修订：

```text
Data: data/processed/dpo_tiny_v3_train.jsonl
Config: configs/dpo_qwen05b_v3.yaml
Output adapter: outputs/dpo_lora_qwen05b_tiny_v3
Rows: 57
Epochs: 2
Optimizer steps: 14
Runtime: 64.7 seconds
Train loss: 1.1842
torch max allocated: 2.191 GB
Adapter reload: passed
Raw compare: reports/compare_outputs_four_way_dpo_tiny_v3.jsonl
```

v3 结论：

```text
没有 OOM/崩溃，但 DPO 更新过强，多个原本稳定的 prompt 回归。
prompt 7 话题更接近，但仍没有清楚表达 loss 是必要不充分、固定 prompt 行为是 gate。
不通过行为 gate。
```

最终建议：

```text
Stage 5D larger DPO 继续阻塞。
当前推荐 checkpoint 仍是 outputs/sft_lora_qwen05b_custom_v3_from_v1_patch。
DPO 系列 adapter 只作为实验产物保留，不推荐替代 v3 SFT。
硬件不是当前瓶颈；行为稳定性和 preference 数据设计才是瓶颈。
```

### Stage 5 Structured Behavior Scoring

已完成。为了避免只靠人工报告判断，新增结构化评分脚本：

```text
Script: scripts/score_fixed_prompt_outputs.py
Report: reports/stage5_structured_behavior_score_report.md
Scores JSONL: reports/stage5_structured_behavior_scores.jsonl
Scores CSV: reports/stage5_structured_behavior_scores.csv
```

评分方式：

```text
每个固定 prompt 配 required concepts 和 forbidden phrases。
不是 LLM judge，而是透明、可复现的 gate helper。
```

评分结果：

```text
custom-SFT v3: 7 / 8 prompts passed
DPO-tiny v1: 6 / 8 prompts passed
DPO-tiny v2: 6 / 8 prompts passed
DPO-tiny v3: 1 / 8 prompts passed
```

结论：

```text
结构化评分支持人工判断：不扩大 DPO，推荐 checkpoint 仍是 SFT v3。
```

## Notebook

主 notebook：

```text
notebooks/04_full_pipeline_learning.ipynb
```

作用：

```text
把环境检查、base 推理、公开数据、public LoRA SFT、Stage 4A、Stage 2B、Stage 3B、Stage 4B、Stage 2B.2/2B.3 badcase patch 和 DPO 显存计划串成可逐格运行的学习路线。
```

耗时训练 cell 默认用布尔开关关闭，避免误运行。

## DPO 显存判断

报告：

```text
reports/vram_and_dpo_plan.md
```

判断：

```text
8GB 已跑通多轮 tiny DPO smoke test，57 pair / 2 epoch 也没有 OOM。
但 Stage 5C / 5C.2 / 5C.3 行为 gate 都没有通过，因此不能扩大 DPO。
```

原因：

- DPO 要处理 chosen/rejected。
- 通常还要 reference policy 评分。
- 如果加载两份完整模型，8GB 很容易爆显存或落到共享内存导致非常慢。

建议第一版 DPO：

- 33 pair：`data/processed/dpo_tiny_train.jsonl`。
- 起点 adapter: `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`。
- `batch_size=1`。
- 短 `max_length` 和短 `max_prompt_length`。
- 少 eval。
- 使用 LoRA/PEFT，并尽量共享 reference。
- 用户需要记录专用显存、共享显存、系统内存、step 速度和是否 OOM/崩溃。

## 下一步建议

用户现在会以检查和理解为主。下一次如果继续推进，推荐顺序：

```text
1. 阅读 reports/stage5_dpo_plan.md 和 reports/stage2b3_sft_stability_gate_report.md。
2. Stage 5A 已完成：data/processed/dpo_tiny_train.jsonl，33 个 preference pair。
3. Stage 5B 已完成：outputs/dpo_lora_qwen05b_tiny，未 OOM/崩溃，adapter 可加载。
4. Stage 5C 已完成：行为 gate 未通过。
5. v2/v3 修订循环也已完成：硬件通过，行为仍不过 gate。
6. 结构化评分已完成：确认 SFT v3 仍是推荐 checkpoint，DPO v1/v2/v3 不替代。
7. 下一步不是扩大 DPO，而是重新设计更干净的 preference 数据和自动评分/验证集。
```

## 2026-05-16 最新 Stage 5 状态

继续完成了 candidate-derived DPO v4/v5：

```text
v4 train/eval: 20 / 5
v4 output: outputs/dpo_lora_qwen05b_candidate_v4
v4 behavior: 6 / 8 prompts passed
v4 failed: prompt 4 public-SFT motivation, prompt 7 loss-vs-behavior

v5 train/eval: 28 / 7
v5 output: outputs/dpo_lora_qwen05b_candidate_v5
v5 behavior: 6 / 8 prompts passed
v5 failed: prompt 4 public-SFT motivation, prompt 7 loss-vs-behavior
```

硬件结论：8GB RTX 4060 Laptop GPU 可以继续跑这些 tiny DPO；v4/v5 都无 OOM，adapter reload 均通过。

行为结论：Stage 5D larger DPO 仍然阻塞，不建议继续扩大同一套 tiny DPO。推荐 checkpoint 仍然是：

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

关键报告：

```text
reports/stage5_candidate_dpo_v4_v5_report.md
reports/stage5_structured_behavior_score_report.md
reports/stage5_dpo_plan.md
```

## 2026-05-16 Stage 5G naive DPO v6

用户允许放开一点做更大的朴素 DPO 后，已完成：

```text
train/eval: 192 / 24
config: configs/dpo_qwen05b_v6_naive.yaml
output: outputs/dpo_lora_qwen05b_naive_v6
mode: separate frozen reference model
optimizer steps: 48
runtime: 271.4 seconds
final eval loss: 0.0474
final eval preference accuracy: 1.0
max allocated VRAM: 3.415 GB
max reserved VRAM: 8.686 GB
behavior score: 7 / 8
remaining fail: prompt 7 loss-vs-behavior
```

这个结果说明：硬件确实能扛更大的 naive DPO；v6 是目前最好的 DPO 候选，但核心 prompt 7 仍未过 gate。下一轮如果继续，应优先重新设计 loss-vs-behavior 的 held-out prompt 和 preference 数据，而不是只继续加 step。

关键报告：

```text
reports/stage5g_naive_dpo_v6_report.md
reports/stage5_structured_behavior_score_report.md
reports/compare_outputs_four_way_dpo_naive_v6.jsonl
```

## 2026-05-16 Stage 5H prompt 7 数据和 expanded gate 设计

已完成数据和评测设计，但没有运行 DPO v7 训练：

```text
scripts/prepare_stage5h_prompt7_data.py
scripts/score_expanded_behavior_outputs.py
data/processed/dpo_stage5h_prompt7_train.jsonl
data/processed/dpo_stage5h_prompt7_eval.jsonl
data/samples/custom_technical_prompts_expanded_stage5h.jsonl
reports/stage5h_prompt7_data_and_eval_design.md
```

数据规模：

```text
Train rows: 278
Eval rows: 55
New prompt-7 train pairs: 72
New prompt-7 eval pairs: 24
Expanded behavior prompts: 24
```

设计意图：

- 保留 Stage 5G v6 的广覆盖 replay 分布。
- 围绕 train loss、eval loss、preference accuracy、fixed prompt、badcase、
  regression、public-SFT 和 DPO v6 设计 prompt 7 变体。
- rejected answer 采用 near-miss 形式：看起来合理，但会漏掉必要概念或过度相信某个指标。
- expanded gate 保留原始 8 个固定 prompt，并加入 12 个 prompt 7 held-out
  改写和 4 个 replay holdout。

下一步：先人工审核 Stage 5H 数据和 expanded gate，再考虑从
`outputs/sft_lora_qwen05b_custom_v3_from_v1_patch` 出发训练 DPO v7。不要从
DPO v6 继续叠 adapter。

## 下一次空聊天入口提示

推荐用户下一次这样问：

```text
请先阅读这个项目：
D:\coding\qwen lorar sft\qwen-local-lora-sft-dpo

请重点阅读：
reports/next_chat_handoff_stage5g.md
reports/project_context_for_next_chat.md
reports/stage5g_naive_dpo_v6_report.md
reports/stage5_structured_behavior_score_report.md
reports/stage5_dpo_plan.md
PROJECT_RUNBOOK.md
README.zh-CN.md
README.md
notebooks/04_full_pipeline_learning.ipynb

读完后，请先用中文总结当前状态、推荐 checkpoint、最好 DPO 候选、剩余问题和下一阶段计划。然后审核 Stage 5H 已生成的 prompt 7 preference/eval 数据和 expanded behavior gate：确认数据分布、near-miss rejected answers 和 scorer 规则是否合理。不要直接继续加 DPO step；只有数据和评测设计通过后，才从 SFT v3 出发准备 DPO v7。
```

下一阶段不要从 DPO v6 继续叠 adapter，优先从 SFT v3 重新开始设计 v7。v6 是最佳 DPO 候选，但不是完全通过的推荐替代品。
