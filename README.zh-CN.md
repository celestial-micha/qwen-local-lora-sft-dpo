# Qwen 本地 LoRA / SFT / DPO 学习项目

中文 | [English](README.md)

这是一个用本地 RTX 4060 Laptop GPU 学习大模型后训练链路的最小可复现项目。当前模型是：

```text
Qwen/Qwen2.5-0.5B-Instruct
```

项目目标不是一开始就做很大的垂直模型，而是把一条能复现、能解释、能写进简历和面试讲述的链路跑通：

```text
环境检查
  -> base Qwen 推理
  -> 公开 SFT 数据准备
  -> public-data LoRA SFT
  -> base vs public-SFT 对比
  -> 自采集/自整理技术数据清洗与转换
  -> custom-data LoRA SFT
  -> base vs public-SFT vs custom-SFT 三方对比
  -> tiny DPO smoke test
```

术语先说清楚：

- `SFT` 是 supervised fine-tuning，也就是有监督微调目标和数据形式。
- `LoRA` 是参数高效微调方法，用 adapter 的方式减少训练参数和显存压力。
- 本项目当前训练叫 `LoRA SFT`：用 LoRA adapter 来执行 SFT。
- `DPO` 是 direct preference optimization，后续用 chosen/rejected 偏好对继续优化模型偏好。

## 当前状态

已经完成：

- 本地 CUDA / RTX 4060 环境验证。
- Windows 稳定训练依赖栈固定。
- Qwen2.5-0.5B base 推理跑通。
- demo SFT 数据、LoRA SFT smoke test、adapter 保存和加载跑通。
- Stage 2A：公开中文 instruction 数据集准备完成。
- Stage 3A：公开数据 LoRA SFT 完成，adapter 保存到 `outputs/sft_lora_qwen05b_public`。
- Stage 4A：base vs public-SFT 对比完成，结论是 public-SFT 没有修正 LoRA/SFT/DPO 概念误解。
- Stage 2B：自采集/自整理技术数据完成并根据训练反馈修订；Stage 2B.3 后当前是 142 train / 15 eval，另有 28 条 focused patch。
- Stage 3B：custom-data LoRA SFT 完成，adapter 保存到 `outputs/sft_lora_qwen05b_custom`。
- Stage 4B：base vs public-SFT vs custom-SFT 三方对比完成，custom-SFT 明显改善 6/8 个固定技术 prompt。
- Stage 2B.2：针对 remaining badcase 做了小数据补丁。v2 从头训练发生回归；从 v1 低学习率续训得到 `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`，保留或改善 7/8 个固定 prompt。
- Stage 2B.3：DPO 前 SFT 稳定性 gate 已完成。当前数据是 142 train / 15 eval，并额外生成 28 条 focused patch；但 v4/v5/v6 都不够稳定，不能替代 v3。
- Stage 5A：tiny DPO preference 数据集已完成，`data/processed/dpo_tiny_train.jsonl` 共 33 pair；起点 adapter 仍是 `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`。
- Stage 5B：tiny DPO smoke test 已完成，输出 `outputs/dpo_lora_qwen05b_tiny`；4 个 optimizer step，约 32.8 秒，无 OOM/原生崩溃，adapter 可重新加载。
- Stage 5C：tiny DPO 固定 prompt 行为对比已完成，但行为 gate 未通过；8 个 prompt 中 5 个明确保住、1 个观察、2 个失败。
- Stage 5A.2/B.2/C.2 和 Stage 5A.3/B.3/C.3 修订循环已完成。硬件继续通过，但行为仍不过 gate；v3 DPO 甚至回归多个旧 prompt。
- Stage 5 结构化行为评分已完成：custom-SFT v3 通过 7/8，DPO v1/v2 通过 6/8，DPO v3 通过 1/8，支持“不要扩大 DPO”的结论。
- 学习型 notebook 已更新：`notebooks/04_full_pipeline_learning.ipynb`。

还没完成：

- Stage 5D：扩大 DPO。当前被 Stage 5C 阻塞，需要先修 preference 数据。
- 多卡训练说明或实验。

## 为什么要先 public-SFT，再 custom-SFT

公开通用数据集先跑通，是为了证明训练、保存、加载、对比这一整条工程链路没问题。Stage 4A 的结果很关键：public-SFT 虽然训练成功，但没有修正 LoRA/SFT/DPO 技术概念误解。

这不是项目失败，反而是数据工程闭环的起点：

```text
公开数据证明工程链路可跑
  -> 固定 prompt 暴露目标 badcase
  -> 自采集/自整理技术数据
  -> 清洗、去重、筛选、转 instruction-answer
  -> custom-SFT
  -> 再做三方对比
```

这样面试时可以讲清楚：我们不是“下载一个数据集然后微调完事”，而是通过 badcase 驱动下一轮数据建设。

## 本地环境

```text
Python 3.10
torch==2.5.1+cu124
transformers==4.46.3
accelerate==1.1.1
peft==0.13.2
datasets==3.1.0
trl==0.12.2
huggingface-hub==0.26.5
fsspec==2024.9.0
```

训练环境里暂时不安装 `gradio`。以后如果要做 demo，建议单独建环境。

每次运行前：

```powershell
conda activate qwen-lora-local
cd "D:\coding\qwen lorar sft\qwen-local-lora-sft-dpo"
$env:HF_HOME=(Resolve-Path -LiteralPath ".hf_cache").Path
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"
```

## 常用命令

检查环境：

```powershell
python scripts/check_env.py
```

运行 base 推理：

```powershell
python scripts/infer.py --prompt "请用三点解释什么是 LoRA 微调。" --max_new_tokens 128 --local_files_only
```

准备 Stage 2B 自采集技术数据：

```powershell
python scripts\prepare_custom_technical_data.py `
  --raw_sources_file data\raw\custom_sources.jsonl `
  --cleaned_chunks_file data\raw\custom_cleaned_chunks.jsonl `
  --instruction_seed_file data\raw\custom_instruction_seed.jsonl `
  --train_file data\processed\custom_sft_train.jsonl `
  --eval_file data\processed\custom_sft_eval.jsonl `
  --eval_ratio 0.1 `
  --max_doc_samples 20 `
  --seed 42
```

训练 Stage 3B custom LoRA SFT：

```powershell
python scripts\train_sft_lora.py `
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

运行 Stage 4B 三方对比：

```powershell
python scripts\compare_three_outputs.py `
  --prompt_file data\samples\custom_technical_prompts.jsonl `
  --public_adapter_path outputs\sft_lora_qwen05b_public `
  --custom_adapter_path outputs\sft_lora_qwen05b_custom `
  --output_file reports\compare_outputs_three_way_custom.jsonl `
  --max_new_tokens 128 `
  --temperature 0 `
  --local_files_only
```

Stage 2B.2 后从已有 custom adapter 低学习率续训：

```powershell
python scripts\train_sft_lora.py `
  --init_adapter_path outputs\sft_lora_qwen05b_custom `
  --train_file data\processed\custom_sft_train.jsonl `
  --eval_file data\processed\custom_sft_eval.jsonl `
  --output_dir outputs\sft_lora_qwen05b_custom_v3_from_v1_patch `
  --max_length 512 `
  --batch_size 1 `
  --grad_accum 4 `
  --epochs 2 `
  --lr 5e-5 `
  --logging_steps 10 `
  --eval_steps 30 `
  --save_steps 30 `
  --report_to none `
  --local_files_only
```

准备 Stage 2B.3 数据和 focused patch 文件：

```powershell
python scripts\prepare_custom_technical_data.py `
  --raw_sources_file data\raw\custom_sources.jsonl `
  --cleaned_chunks_file data\raw\custom_cleaned_chunks.jsonl `
  --instruction_seed_file data\raw\custom_instruction_seed.jsonl `
  --train_file data\processed\custom_sft_train.jsonl `
  --eval_file data\processed\custom_sft_eval.jsonl `
  --stage2b3_patch_train_file data\processed\custom_sft_stage2b3_patch_train.jsonl `
  --stage2b3_loss_repeats 12 `
  --eval_ratio 0.1 `
  --max_doc_samples 20 `
  --seed 42
```

## 显存和 DPO 计划

已观察到：

- public LoRA SFT 训练约 `5.5GB / 8GB`。
- adapter 推理约 `1.2GB / 8GB`。

DPO 会比 SFT 更吃显存，因为它通常要同时处理 chosen/rejected，并和 reference policy 对比。8GB 可以尝试 tiny smoke test，但不要一开始做朴素大 DPO。

第一版 DPO 建议：

- Stage 5A 已准备 33 pair：`data/processed/dpo_tiny_train.jsonl`。
- `batch_size=1`。
- 短 `max_length` 和短 `max_prompt_length`。
- 少 eval。
- 尽量使用 LoRA / PEFT / reference 共享。

## 重要文件

- [项目上下文，下一次聊天先读](reports/project_context_for_next_chat.md)
- [项目运行手册](PROJECT_RUNBOOK.md)
- [学习型 notebook](notebooks/04_full_pipeline_learning.ipynb)
- [数据管线计划](reports/data_pipeline_plan.md)
- [Stage 2B 自采集技术数据报告](reports/stage2b_custom_technical_data_report.md)
- [Stage 3B custom LoRA SFT 报告](reports/stage3b_custom_lora_sft_report.md)
- [Stage 4B 三方对比报告](reports/stage4b_three_way_comparison_report.md)
- [Stage 2B.2 badcase patch 报告](reports/stage2b2_badcase_patch_report.md)
- [Stage 2B.3 SFT 稳定性 gate 报告](reports/stage2b3_sft_stability_gate_report.md)
- [Stage 5 DPO 拆分计划](reports/stage5_dpo_plan.md)
- [Stage 5A tiny DPO 数据报告](reports/stage5a_dpo_tiny_data_report.md)
- [Stage 5B tiny DPO smoke test 报告](reports/stage5b_tiny_dpo_smoke_report.md)
- [Stage 5C tiny DPO 行为报告](reports/stage5c_tiny_dpo_behavior_report.md)
- [Stage 5 DPO 修订循环报告](reports/stage5_dpo_revision_loop_report.md)
- [Stage 5 结构化行为评分报告](reports/stage5_structured_behavior_score_report.md)
- [显存与 DPO 计划](reports/vram_and_dpo_plan.md)

## 下一步

Stage 5A/5B/5C 和后续 v2/v3 修订循环已完成，但行为 gate 仍没过。

当前 tiny DPO 系列证明 8GB 本地环境可以跑 DPO，小数据甚至 57 pair / 2 epoch 都没有 OOM。但行为质量没有过关：结构化评分显示 DPO v1/v2 都卡在 6/8，DPO v3 只有 1/8。因此当前不建议扩大 DPO；推荐 checkpoint 仍是 `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`。

## 2026-05-16 Stage 5 补充结论

已经继续完成 candidate-derived DPO v4/v5：

- v4：20 条 train / 5 条 eval，显存无 OOM，adapter 可加载，但固定 prompt 仍是 6/8，通过不了 public-SFT motivation 和 loss-vs-behavior。
- v5：28 条 train / 7 条 eval，显存无 OOM，adapter 可加载，但仍是 6/8，而且 loss-vs-behavior 更弱。
- 结构化评分已更新到 v1/v2/v3/v4/v5。

结论不变：Stage 5D larger DPO 继续阻塞；当前推荐 checkpoint 仍然是 `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`。详见：

- `reports/stage5_candidate_dpo_v4_v5_report.md`
- `reports/stage5_structured_behavior_score_report.md`
