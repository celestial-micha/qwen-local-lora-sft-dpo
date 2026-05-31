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
  -> 安全敏感帮助能力评估、数据构造、SFT、DPO 与回归保护
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
- Stage 5 结构化行为评分已完成：custom-SFT v3 通过 7/8，DPO v1/v2 通过 6/8，DPO v3 通过 1/8，支持“不要盲目扩大 DPO”的结论。
- Stage 5H prompt 7 修复数据和 expanded behavior gate 设计已完成：生成 278 条 train preference、55 条 held-out eval、24 题 expanded prompt suite，并新增 metadata-based scorer。
- Stage 5I-5P prompt 7 修复循环已完成：v6 expanded gate 失败；DPO v7/v8 偏好 eval accuracy 都到 1.0 但固定 prompt 7 仍失败；Stage 5N/5O/5P 直接 SFT 探针也没有同时满足“prompt 7 通过且旧题不回归”。没有新的 adapter 被接受。
- Stage 6 最终面试包已完成：整理最终叙事、before/after 示例、失败复盘、简历 bullet 和不要盲目继续 DPO 的边界。
- 学习型 notebook 已更新：`notebooks/04_full_pipeline_learning.ipynb`。

还没完成：

- 一个完全接受的 DPO adapter。v6 是当前最好 DPO 候选，但不是完整通过的推荐替代品。
- 一个稳定的 prompt 7 修复 checkpoint：目前不是 prompt 7 仍弱，就是修 prompt 7 时旧题回归。
- 多卡训练说明或实验。
- Stage 7 安全敏感帮助能力闭环：评测集、1500 条左右 SFT 数据、DPO 偏好数据、训练和回归验收。

下一阶段计划：

- 主题：安全敏感场景下的大模型帮助能力提升，从过度拒答到有边界地提供有效帮助。
- 先做评测，不先训练：构造 held-out 安全评测集，标注风险等级、期望行为和评分规则。
- 再做数据：围绕真实 badcase 构造约 1500 条 SFT 样本，并保留独立 eval 集。
- 再做 LoRA SFT：训练后同时跑安全能力 gate 和旧技术能力回归 gate。
- 最后做 DPO：只针对 SFT 后仍回答不好的问题构造 `chosen/rejected` 偏好对。
- 验收标准：新安全能力提升，同时旧的 LoRA/SFT/DPO 技术解释能力不能明显回退。

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

## Stage 7 安全帮助能力计划

下一阶段的面试主项目建议命名为：

```text
安全敏感场景下的大模型帮助能力提升：
从过度拒答到有边界地提供有效帮助
```

这个方向要解决两类常见问题：

- 过度拒答：用户确实需要安全帮助时，模型只说“不能提供帮助”，没有给出可执行的安全支持。
- 危险放开：用户问题带有风险时，模型给出过细、可操作、可能造成伤害的建议。

我们会把安全任务拆成风险等级和行为门禁：

```text
L0 普通安全知识：可以正常解释和科普。
L1 低风险求助：可以给预防建议、检查清单、普通求助路径。
L2 明确危机但可帮助：稳定情绪，给非危险步骤，建议联系专业人员或紧急资源。
L3 明确危险请求：拒绝危险细节，但保留安全替代、降级建议和求助路径。
```

计划链路：

```text
base / 当前 adapter 生成回答
  -> 安全评测集评分
  -> 分析 badcase：过度拒答、危险放开、缺少边界、缺少求助路径
  -> 构造 SFT 数据
  -> LoRA SFT
  -> 安全 gate + 旧能力回归 gate
  -> 针对剩余 badcase 构造 DPO chosen/rejected
  -> DPO 训练
  -> 再评估，决定接受、回退或继续构造数据
```

计划新增文件：

```text
data/safety/README.md
data/safety/eval_safety_prompts.jsonl
data/safety/sft_safety_train.jsonl
data/safety/sft_safety_eval.jsonl
data/safety/dpo_safety_train.jsonl
scripts/prepare_safety_sft_data.py
scripts/score_safety_outputs.py
reports/stage7_safety_eval_design.md
reports/stage7_safety_baseline_report.md
```

其中 `reports/stage7_safety_eval_design.md` 是 Stage 7 的详细主计划。如果以后新聊天丢上下文，先读这个文件，再继续写数据或训练。

核心原则：模型不能输出具体危险操作细节，但也不能把所有安全敏感问题都一拒了之。理想回答应该是“拒绝危险部分 + 给出安全替代 + 给出求助路径 + 必要时建议联系专业或紧急资源”。

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

Stage 5H prompt 7 数据和 expanded behavior gate：

```text
data/processed/dpo_stage5h_prompt7_train.jsonl
data/processed/dpo_stage5h_prompt7_eval.jsonl
data/samples/custom_technical_prompts_expanded_stage5h.jsonl
scripts/score_expanded_behavior_outputs.py
reports/stage5h_prompt7_data_and_eval_design.md
```

Stage 5J-5P 修复循环 artifact：

```text
configs/dpo_qwen05b_v7_stage5h.yaml
configs/dpo_qwen05b_v8_stage5m_from_v6.yaml
data/processed/dpo_stage5m_exact_prompt7_train.jsonl
data/processed/sft_stage5n_prompt7_micro_train.jsonl
data/processed/sft_stage5o_prompt7_exact_train.jsonl
reports/stage5j_to_5p_prompt7_repair_report.md
```

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
- [Stage 5H prompt 7 数据和 expanded eval 设计](reports/stage5h_prompt7_data_and_eval_design.md)
- [Stage 5J-5P prompt 7 修复报告](reports/stage5j_to_5p_prompt7_repair_report.md)
- [项目最终总结](reports/final_project_summary_zh.md)
- [Stage 6 最终面试包](reports/stage6_final_interview_package.md)
- [显存与 DPO 计划](reports/vram_and_dpo_plan.md)

## 下一步

Stage 5A/B/C 到 Stage 5P 都已完成，Stage 6 面试包也已完成。当前 tiny/naive DPO 系列证明 8GB 本地环境可以跑 DPO，v7/v8 甚至能把偏好 eval accuracy 跑到 1.0；但行为质量没有完整过关。固定评分里，v6/v7/v8 都停在 7/8，Stage 5O 虽然让 prompt 7 通过，却把旧题打回 4/8。

当前保守推荐 checkpoint 仍是 `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`。`outputs/dpo_lora_qwen05b_naive_v6` 是当前最好 DPO artifact，但不是默认推荐。

下一步进入 Stage 7：先设计安全评测集和评分器，再做 baseline 报告，然后用真实 badcase 驱动约 1500 条 SFT 数据构造。不要先凭感觉训练；先证明模型哪里差、为什么差、补什么数据、补完怎么验收，以及旧能力有没有被训坏。

## 2026-05-16 Stage 5 补充结论

已经继续完成 candidate-derived DPO v4/v5：

- v4：20 条 train / 5 条 eval，显存无 OOM，adapter 可加载，但固定 prompt 仍是 6/8，通过不了 public-SFT motivation 和 loss-vs-behavior。
- v5：28 条 train / 7 条 eval，显存无 OOM，adapter 可加载，但仍是 6/8，而且 loss-vs-behavior 更弱。
- 结构化评分已更新到 v1/v2/v3/v4/v5。

结论不变：Stage 5D larger DPO 继续阻塞；当前推荐 checkpoint 仍然是 `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`。详见：

- `reports/stage5_candidate_dpo_v4_v5_report.md`
- `reports/stage5_structured_behavior_score_report.md`

## 2026-05-16 Stage 5G 朴素 DPO v6 结论

按计划继续跑了更大的朴素 DPO：

- 数据：192 条 train / 24 条 eval。
- 训练：单独 frozen reference model，48 个 optimizer step。
- 显存：无 OOM；max allocated 约 3.415GB，max reserved 约 8.686GB。
- 偏好 eval：final eval loss 约 0.0474，eval preference accuracy 1.0。
- 行为评分：DPO naive v6 通过 7/8，是目前最好的 DPO 候选。
- 仍未通过：prompt 7 loss-vs-behavior。

结论：硬件不是当前瓶颈；偏好指标可以很好看，但固定 prompt gate 仍然能抓住概念缺口。保守推荐 checkpoint 仍是 `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`，v6 adapter 作为最强 DPO 实验候选保留。详见 `reports/stage5g_naive_dpo_v6_report.md`。

## 下一次新聊天建议怎么问

建议直接复制这段：

```text
请先阅读这个项目：
D:\coding\qwen lorar sft\qwen-local-lora-sft-dpo

请重点阅读：
reports/next_chat_handoff_stage5g.md
reports/project_context_for_next_chat.md
reports/stage5g_naive_dpo_v6_report.md
reports/stage5j_to_5p_prompt7_repair_report.md
reports/final_project_summary_zh.md
reports/stage6_final_interview_package.md
reports/stage5_structured_behavior_score_report.md
reports/stage5_dpo_plan.md
PROJECT_RUNBOOK.md
README.zh-CN.md
README.md
notebooks/04_full_pipeline_learning.ipynb

读完后，请先用中文总结当前状态、推荐 checkpoint、最好 DPO 候选、剩余问题和下一阶段计划。重点阅读项目最终总结和 Stage 6 最终面试包，继续完善面试讲述、简历 bullet、before/after 示例或 demo flow。不要继续盲目加 DPO step；如果要恢复训练，先设计更宽的 prompt 7 curriculum 和回归保护。
```

当前最重要的判断：v6 证明数据增大和 separate reference 确实有效，DPO 行为从 6/8 提升到 7/8；但 v7/v8 的偏好指标再好也没有修掉 prompt 7。Stage 5O 证明 exact SFT 能强行修 prompt 7，却会造成旧题回归。因此技术任务不要继续盲目加 step；新的主线应该转向 Stage 7 安全帮助能力闭环，先评估、再构造数据、再训练。

## 2026-05-16 Stage 5H 数据和评测设计

已经完成 Stage 5H 的“先设计数据和评测，不训练”步骤：

- `scripts/prepare_stage5h_prompt7_data.py`
- `data/processed/dpo_stage5h_prompt7_train.jsonl`：278 条 train pair，其中新增 72 条 prompt 7 修复 pair。
- `data/processed/dpo_stage5h_prompt7_eval.jsonl`：55 条 eval pair，其中新增 24 条 prompt 7 held-out pair。
- `data/samples/custom_technical_prompts_expanded_stage5h.jsonl`：24 题 expanded behavior gate，保留原始 8 题，增加 12 条 prompt 7 改写和 4 条 replay holdout。
- `scripts/score_expanded_behavior_outputs.py`：按 `prompt_area` 元数据评分，不再只依赖固定 8 题行号。

后续已基于这些设计完成 Stage 5I-5P 修复循环，结论见 `reports/stage5j_to_5p_prompt7_repair_report.md`：没有新的 adapter 被接受，保守 checkpoint 仍是 SFT v3，最佳 DPO artifact 仍是 v6。
