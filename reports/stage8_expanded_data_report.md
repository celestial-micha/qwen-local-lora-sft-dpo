# Stage 8 Expanded Technical Data Report

Date: 2026-07-02

## Scope

Stage 8 upgrades the project data scale so the resume story no longer depends
only on the earlier 142 / 15 custom SFT split and 8-prompt pilot gate.

This stage generates training-ready data and a larger held-out behavior suite.
It does **not** claim that the existing accepted checkpoint was retrained on
the new data. The old 7 / 8 result remains a pilot fixed-gate result until a
new training and evaluation run is executed.

## Outputs

```text
data/processed/custom_sft_expanded_train.jsonl
data/processed/custom_sft_expanded_eval.jsonl
data/processed/dpo_expanded_train.jsonl
data/processed/dpo_expanded_eval.jsonl
data/samples/custom_technical_prompts_stage8_expanded.jsonl
data/references/stage8_expanded_source_registry.jsonl
```

## Scale Upgrade

| Asset | Previous Main Size | Stage 8 Size | Notes |
|---|---:|---:|---|
| Custom SFT train | 142 | 1500 | more than 10x |
| Custom SFT eval | 15 | 160 | independent held-out chat rows |
| Fixed behavior prompts | 8 | 96 | 12x expanded behavior suite |
| DPO preference train | 278 Stage 5H rows | 1500 | expanded chosen/rejected pairs |
| DPO preference eval | 55 Stage 5H rows | 160 | held-out preference pairs |

## Source Policy

Stage 8 uses local project reports and public reference metadata. It does not
copy long web text into the training set. The generated Chinese QA rows are
synthetic/curated around project badcases, definitions, near-miss rejected
answers, and evaluation rubrics.

| Source ID | Type | Use |
|---|---|---|
| `local_final_summary` | local_project_report | project timeline, accepted checkpoint decision, fixed-gate results |
| `local_stage6_interview` | local_project_report | interview narrative, before/after examples, failure review |
| `local_stage2b_data` | local_project_report | custom data pipeline, source metadata, cleaning and split policy |
| `local_stage5_scores` | local_project_report | rubric areas, old prompt failures, DPO gate decisions |
| `web_lora_paper` | public_reference_metadata | LoRA concept grounding: low-rank adaptation and parameter efficiency |
| `web_dpo_paper` | public_reference_metadata | DPO concept grounding: chosen/rejected preference optimization |
| `web_peft_lora_docs` | public_reference_metadata | PEFT/LoRA implementation framing |
| `web_trl_dpo_docs` | public_reference_metadata | TRL DPO training schema and preference-data framing |
| `web_qwen_model_card` | public_reference_metadata | base model identity and model-card reference |

## SFT Data Stats

- Train prompt chars min/avg/max: 77 / 117.8 / 174
- Train answer chars min/avg/max: 207 / 265.1 / 323
- Eval prompt chars min/avg/max: 84 / 117.2 / 156
- Schema: Qwen chat JSONL with `system`, `user`, `assistant`

Train area distribution:

| Area | Rows |
|---|---:|
| DPO 与 SFT 区别 | 143 |
| DPO 显存风险 | 151 |
| LoRA 定义与边界 | 153 |
| SFT 与 LoRA 关系 | 160 |
| checkpoint 选择与拒绝理由 | 162 |
| loss 与行为验收 | 145 |
| public-SFT 诊断价值 | 128 |
| 固定 Prompt 与扩展评测 | 151 |
| 自采集技术数据管线 | 139 |
| 面试叙事与边界 | 168 |

Eval area distribution:

| Area | Rows |
|---|---:|
| DPO 与 SFT 区别 | 22 |
| DPO 显存风险 | 16 |
| LoRA 定义与边界 | 14 |
| SFT 与 LoRA 关系 | 15 |
| checkpoint 选择与拒绝理由 | 15 |
| loss 与行为验收 | 14 |
| public-SFT 诊断价值 | 18 |
| 固定 Prompt 与扩展评测 | 16 |
| 自采集技术数据管线 | 16 |
| 面试叙事与边界 | 14 |

## DPO Data Stats

- Train prompt chars min/avg/max: 78 / 117.0 / 186
- Train chosen chars min/avg/max: 205 / 264.6 / 329
- Train rejected chars min/avg/max: 49 / 69.0 / 99
- Schema: `prompt`, `chosen`, `rejected`, plus metadata

Train area distribution:

| Area | Rows |
|---|---:|
| DPO 与 SFT 区别 | 162 |
| DPO 显存风险 | 160 |
| LoRA 定义与边界 | 130 |
| SFT 与 LoRA 关系 | 141 |
| checkpoint 选择与拒绝理由 | 162 |
| loss 与行为验收 | 141 |
| public-SFT 诊断价值 | 154 |
| 固定 Prompt 与扩展评测 | 166 |
| 自采集技术数据管线 | 153 |
| 面试叙事与边界 | 131 |

Eval area distribution:

| Area | Rows |
|---|---:|
| DPO 与 SFT 区别 | 14 |
| DPO 显存风险 | 13 |
| LoRA 定义与边界 | 11 |
| SFT 与 LoRA 关系 | 21 |
| checkpoint 选择与拒绝理由 | 16 |
| loss 与行为验收 | 14 |
| public-SFT 诊断价值 | 19 |
| 固定 Prompt 与扩展评测 | 16 |
| 自采集技术数据管线 | 15 |
| 面试叙事与边界 | 21 |

## Behavior Suite

The expanded behavior suite contains 96 held-out prompts
across the original core areas:

| Area | Rows |
|---|---:|
| DPO 与 SFT 区别 | 12 |
| DPO 显存风险 | 12 |
| LoRA 定义与边界 | 12 |
| SFT 与 LoRA 关系 | 12 |
| loss 与行为验收 | 12 |
| public-SFT 诊断价值 | 12 |
| 固定 Prompt 与扩展评测 | 12 |
| 自采集技术数据管线 | 12 |

Each prompt includes `must_cover` and `forbidden_behavior` metadata so future
scoring can be extended beyond the original 8-prompt pilot gate.

## Resume-Safe Interpretation

Recommended phrasing:

```text
在原 8 题 pilot gate 基础上，将项目数据扩展为 1500 条 SFT 训练样本、
160 条 SFT held-out 样本、1500 条 DPO preference pair、160 条 DPO eval
pair，并构建 96 条扩展行为评测 prompt；扩容数据由项目 badcase、公开
LoRA/DPO/PEFT/TRL/Qwen 参考元数据和自构造中文技术问答组成。
```

Boundary:

```text
旧 checkpoint 的 7 / 8 结果仍然对应 pilot gate。若要汇报扩展评测通过率，
必须先用 Stage 8 数据重新训练或至少重新跑 96 条行为评测。
```

## Next Training Command Sketch

SFT:

```powershell
python scripts\train_sft_lora.py `
  --init_adapter_path outputs\sft_lora_qwen05b_custom_v3_from_v1_patch `
  --train_file data\processed\custom_sft_expanded_train.jsonl `
  --eval_file data\processed\custom_sft_expanded_eval.jsonl `
  --output_dir outputs\sft_lora_qwen05b_stage8_expanded `
  --max_length 512 `
  --batch_size 1 `
  --grad_accum 4 `
  --epochs 1 `
  --lr 3e-5 `
  --logging_steps 20 `
  --eval_steps 100 `
  --save_steps 200 `
  --report_to none `
  --local_files_only
```

DPO:

```powershell
python scripts\train_dpo.py `
  --config configs\dpo_qwen05b_v6_naive.yaml `
  --dpo_file data\processed\dpo_expanded_train.jsonl `
  --eval_file data\processed\dpo_expanded_eval.jsonl `
  --output_dir outputs\dpo_lora_qwen05b_stage8_expanded `
  --local_files_only
```
