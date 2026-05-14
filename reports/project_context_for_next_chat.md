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

已完成并修订。

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
Accepted cleaned chunks: 85
Rejected chunks: 9
Instruction-answer seed samples: 132
Train samples: 119
Eval samples: 13
Duplicate instruction samples: 0
Train max tokens before truncation: 486
Eval max tokens before truncation: 238
```

重要迭代：

```text
第一版 Stage 2B 生成 160 条 instruction 样本，Stage 3B 初跑能训练但输出仍有幻觉。
原因是 project_record_summary 样本过多、太泛，容易让模型复制项目记录模板。
后来把 max_doc_samples 从 60 降到 20，并加入 12 条直接命中固定 prompt 的 targeted QA。
```

报告：

```text
reports/stage2b_custom_technical_data_report.md
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

## Notebook

主 notebook：

```text
notebooks/04_full_pipeline_learning.ipynb
```

作用：

```text
把环境检查、base 推理、公开数据、public LoRA SFT、Stage 4A、Stage 2B、Stage 3B、Stage 4B 和 DPO 显存计划串成可逐格运行的学习路线。
```

耗时训练 cell 默认用布尔开关关闭，避免误运行。

## DPO 显存判断

报告：

```text
reports/vram_and_dpo_plan.md
```

判断：

```text
8GB 可以尝试 tiny DPO smoke test，但朴素 DPO 风险较高。
```

原因：

- DPO 要处理 chosen/rejected。
- 通常还要 reference policy 评分。
- 如果加载两份完整模型，8GB 很容易爆显存或落到共享内存导致非常慢。

建议第一版 DPO：

- 20-50 pair。
- `batch_size=1`。
- 短 `max_length` 和短 `max_prompt_length`。
- 少 eval。
- 使用 LoRA/PEFT，并尽量共享 reference。

## 下一步建议

用户现在会以检查和理解为主。下一次如果继续推进，推荐顺序：

```text
1. 阅读 Stage 3B 和 Stage 4B 报告，确认 custom-SFT 改善点和 remaining badcase。
2. 做 Stage 2B.2 小数据补丁，只补 prompt 4 和 prompt 7。
3. 可选：短训 custom adapter 或选择 epoch 5 左右最佳 checkpoint。
4. 再进入 tiny DPO smoke test。
```
