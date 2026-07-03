# Stage 8 Expanded Behavior Score Report

Date: 2026-07-03

## Scope

This report scores Stage 8 expanded behavior outputs with transparent
keyword-based gates. It is a reproducible helper, not a final LLM judge.
Failures should be reviewed manually before data patching.

Outputs:

```text
reports/stage8h_dpo_from_sft_v2_expanded_scores.jsonl
reports/stage8h_dpo_from_sft_v2_expanded_scores.csv
```

## Summary

| Variant | Passed | Total Score | Weakest Areas |
|---|---:|---:|---|
| `stage8_dpo_from_v2_answer` | 44 / 96 | 294 | DPO 与 SFT 区别 0/12, DPO 显存风险 9/12, LoRA 定义与边界 8/12, SFT 与 LoRA 关系 2/12, loss 与行为验收 11/12, public-SFT 诊断价值 0/12, 固定 Prompt 与扩展评测 9/12, 自采集技术数据管线 5/12 |

## Failed Checks

| Variant | Prompt ID | Area | Score | Missing | Forbidden |
|---|---|---|---:|---|---|
| `stage8_dpo_from_v2_answer` | stage8_lora_definition_001 | LoRA 定义与边界 | 1 | parameter efficient, adapter, frozen base, not wireless | - |
| `stage8_dpo_from_v2_answer` | stage8_lora_definition_002 | LoRA 定义与边界 | 1 | lora, parameter efficient, frozen base, not wireless | - |
| `stage8_dpo_from_v2_answer` | stage8_lora_definition_004 | LoRA 定义与边界 | 1 | parameter efficient, adapter, frozen base, not wireless | - |
| `stage8_dpo_from_v2_answer` | stage8_lora_definition_007 | LoRA 定义与边界 | 0 | lora, parameter efficient, adapter, frozen base, not wireless | - |
| `stage8_dpo_from_v2_answer` | stage8_sft_lora_relation_001 | SFT 与 LoRA 关系 | 2 | objective/data, relationship | - |
| `stage8_dpo_from_v2_answer` | stage8_sft_lora_relation_002 | SFT 与 LoRA 关系 | 2 | objective/data, relationship | - |
| `stage8_dpo_from_v2_answer` | stage8_sft_lora_relation_003 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_dpo_from_v2_answer` | stage8_sft_lora_relation_004 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_dpo_from_v2_answer` | stage8_sft_lora_relation_006 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_dpo_from_v2_answer` | stage8_sft_lora_relation_007 | SFT 与 LoRA 关系 | 1 | objective/data, lora method, relationship | - |
| `stage8_dpo_from_v2_answer` | stage8_sft_lora_relation_008 | SFT 与 LoRA 关系 | 2 | - | mutual exclusion |
| `stage8_dpo_from_v2_answer` | stage8_sft_lora_relation_009 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_dpo_from_v2_answer` | stage8_sft_lora_relation_010 | SFT 与 LoRA 关系 | 2 | objective/data, relationship | - |
| `stage8_dpo_from_v2_answer` | stage8_sft_lora_relation_012 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_dpo_from_v2_answer` | stage8_dpo_vs_sft_001 | DPO 与 SFT 区别 | 2 | chosen rejected, sft first | - |
| `stage8_dpo_from_v2_answer` | stage8_dpo_vs_sft_002 | DPO 与 SFT 区别 | 1 | sft answer imitation, chosen rejected, sft first | - |
| `stage8_dpo_from_v2_answer` | stage8_dpo_vs_sft_003 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_dpo_from_v2_answer` | stage8_dpo_vs_sft_004 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_dpo_from_v2_answer` | stage8_dpo_vs_sft_005 | DPO 与 SFT 区别 | 1 | sft first | data protection |
| `stage8_dpo_from_v2_answer` | stage8_dpo_vs_sft_006 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_dpo_from_v2_answer` | stage8_dpo_vs_sft_007 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_dpo_from_v2_answer` | stage8_dpo_vs_sft_008 | DPO 与 SFT 区别 | 1 | sft first | data protection |
| `stage8_dpo_from_v2_answer` | stage8_dpo_vs_sft_009 | DPO 与 SFT 区别 | 1 | sft first | data protection |
| `stage8_dpo_from_v2_answer` | stage8_dpo_vs_sft_010 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_dpo_from_v2_answer` | stage8_dpo_vs_sft_011 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_dpo_from_v2_answer` | stage8_dpo_vs_sft_012 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_dpo_from_v2_answer` | stage8_public_sft_motivation_001 | public-SFT 诊断价值 | 0 | public baseline, engineering proof, not fixed, stage2b | - |
| `stage8_dpo_from_v2_answer` | stage8_public_sft_motivation_002 | public-SFT 诊断价值 | 3 | stage2b | - |
| `stage8_dpo_from_v2_answer` | stage8_public_sft_motivation_003 | public-SFT 诊断价值 | 2 | not fixed, stage2b | - |
| `stage8_dpo_from_v2_answer` | stage8_public_sft_motivation_004 | public-SFT 诊断价值 | 3 | stage2b | - |
| `stage8_dpo_from_v2_answer` | stage8_public_sft_motivation_005 | public-SFT 诊断价值 | 3 | stage2b | - |
| `stage8_dpo_from_v2_answer` | stage8_public_sft_motivation_006 | public-SFT 诊断价值 | 3 | stage2b | - |
| `stage8_dpo_from_v2_answer` | stage8_public_sft_motivation_007 | public-SFT 诊断价值 | 2 | engineering proof, stage2b | - |
| `stage8_dpo_from_v2_answer` | stage8_public_sft_motivation_008 | public-SFT 诊断价值 | 3 | stage2b | - |
| `stage8_dpo_from_v2_answer` | stage8_public_sft_motivation_009 | public-SFT 诊断价值 | 3 | stage2b | - |
| `stage8_dpo_from_v2_answer` | stage8_public_sft_motivation_010 | public-SFT 诊断价值 | 3 | stage2b | - |
| `stage8_dpo_from_v2_answer` | stage8_public_sft_motivation_011 | public-SFT 诊断价值 | 3 | stage2b | - |
| `stage8_dpo_from_v2_answer` | stage8_public_sft_motivation_012 | public-SFT 诊断价值 | 3 | stage2b | - |
| `stage8_dpo_from_v2_answer` | stage8_data_pipeline_001 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_dpo_from_v2_answer` | stage8_data_pipeline_002 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_dpo_from_v2_answer` | stage8_data_pipeline_003 | 自采集技术数据管线 | 2 | clean, dedup filter, instruction conversion | - |
| `stage8_dpo_from_v2_answer` | stage8_data_pipeline_004 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_dpo_from_v2_answer` | stage8_data_pipeline_005 | 自采集技术数据管线 | 3 | dedup filter, instruction conversion | - |
| `stage8_dpo_from_v2_answer` | stage8_data_pipeline_007 | 自采集技术数据管线 | 2 | source metadata, clean, dedup filter | - |
| `stage8_dpo_from_v2_answer` | stage8_data_pipeline_010 | 自采集技术数据管线 | 0 | source metadata, clean, dedup filter, instruction conversion, split | - |
| `stage8_dpo_from_v2_answer` | stage8_loss_behavior_002 | loss 与行为验收 | 3 | not sufficient, badcase regression | - |
| `stage8_dpo_from_v2_answer` | stage8_behavior_eval_005 | 固定 Prompt 与扩展评测 | 2 | scoring, regression | - |
| `stage8_dpo_from_v2_answer` | stage8_behavior_eval_008 | 固定 Prompt 与扩展评测 | 2 | scoring, regression | - |
| `stage8_dpo_from_v2_answer` | stage8_behavior_eval_011 | 固定 Prompt 与扩展评测 | 2 | scoring, regression | - |
| `stage8_dpo_from_v2_answer` | stage8_dpo_vram_001 | DPO 显存风险 | 3 | memory risk, smoke boundary | - |
| `stage8_dpo_from_v2_answer` | stage8_dpo_vram_002 | DPO 显存风险 | 2 | memory risk, mitigation, smoke boundary | - |
| `stage8_dpo_from_v2_answer` | stage8_dpo_vram_007 | DPO 显存风险 | 1 | chosen rejected, reference, memory risk, smoke boundary | - |
