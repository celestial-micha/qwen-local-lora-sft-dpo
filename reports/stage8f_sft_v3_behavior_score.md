# Stage 8 Expanded Behavior Score Report

Date: 2026-07-03

## Scope

This report scores Stage 8 expanded behavior outputs with transparent
keyword-based gates. It is a reproducible helper, not a final LLM judge.
Failures should be reviewed manually before data patching.

Outputs:

```text
reports/stage8f_sft_v3_expanded_scores.jsonl
reports/stage8f_sft_v3_expanded_scores.csv
```

## Summary

| Variant | Passed | Total Score | Weakest Areas |
|---|---:|---:|---|
| `stage8_sft_v3_answer` | 18 / 96 | 227 | DPO 与 SFT 区别 0/12, DPO 显存风险 3/12, LoRA 定义与边界 2/12, SFT 与 LoRA 关系 2/12, loss 与行为验收 6/12, public-SFT 诊断价值 1/12, 固定 Prompt 与扩展评测 4/12, 自采集技术数据管线 0/12 |

## Failed Checks

| Variant | Prompt ID | Area | Score | Missing | Forbidden |
|---|---|---|---:|---|---|
| `stage8_sft_v3_answer` | stage8_lora_definition_001 | LoRA 定义与边界 | 2 | parameter efficient, frozen base, not wireless | - |
| `stage8_sft_v3_answer` | stage8_lora_definition_002 | LoRA 定义与边界 | 1 | parameter efficient, adapter, frozen base, not wireless | - |
| `stage8_sft_v3_answer` | stage8_lora_definition_003 | LoRA 定义与边界 | 1 | parameter efficient, adapter, frozen base, not wireless | - |
| `stage8_sft_v3_answer` | stage8_lora_definition_005 | LoRA 定义与边界 | 2 | parameter efficient, frozen base, not wireless | - |
| `stage8_sft_v3_answer` | stage8_lora_definition_006 | LoRA 定义与边界 | 2 | parameter efficient, frozen base, not wireless | - |
| `stage8_sft_v3_answer` | stage8_lora_definition_007 | LoRA 定义与边界 | 1 | parameter efficient, adapter, frozen base, not wireless | - |
| `stage8_sft_v3_answer` | stage8_lora_definition_008 | LoRA 定义与边界 | 2 | adapter, frozen base, not wireless | - |
| `stage8_sft_v3_answer` | stage8_lora_definition_009 | LoRA 定义与边界 | 1 | parameter efficient, adapter, frozen base, not wireless | - |
| `stage8_sft_v3_answer` | stage8_lora_definition_011 | LoRA 定义与边界 | 2 | adapter, frozen base, not wireless | - |
| `stage8_sft_v3_answer` | stage8_lora_definition_012 | LoRA 定义与边界 | 2 | adapter, frozen base, not wireless | - |
| `stage8_sft_v3_answer` | stage8_sft_lora_relation_001 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_v3_answer` | stage8_sft_lora_relation_002 | SFT 与 LoRA 关系 | 2 | objective/data, relationship | - |
| `stage8_sft_v3_answer` | stage8_sft_lora_relation_003 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_v3_answer` | stage8_sft_lora_relation_004 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_v3_answer` | stage8_sft_lora_relation_005 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_v3_answer` | stage8_sft_lora_relation_007 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_v3_answer` | stage8_sft_lora_relation_009 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_v3_answer` | stage8_sft_lora_relation_010 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_v3_answer` | stage8_sft_lora_relation_011 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_v3_answer` | stage8_sft_lora_relation_012 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_v3_answer` | stage8_dpo_vs_sft_001 | DPO 与 SFT 区别 | 2 | chosen rejected, sft first | - |
| `stage8_sft_v3_answer` | stage8_dpo_vs_sft_002 | DPO 与 SFT 区别 | 2 | chosen rejected, sft first | - |
| `stage8_sft_v3_answer` | stage8_dpo_vs_sft_003 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_v3_answer` | stage8_dpo_vs_sft_004 | DPO 与 SFT 区别 | 0 | chosen rejected, sft first | data protection |
| `stage8_sft_v3_answer` | stage8_dpo_vs_sft_005 | DPO 与 SFT 区别 | 2 | chosen rejected, sft first | - |
| `stage8_sft_v3_answer` | stage8_dpo_vs_sft_006 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_v3_answer` | stage8_dpo_vs_sft_007 | DPO 与 SFT 区别 | 2 | chosen rejected, sft first | - |
| `stage8_sft_v3_answer` | stage8_dpo_vs_sft_008 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_v3_answer` | stage8_dpo_vs_sft_009 | DPO 与 SFT 区别 | 2 | chosen rejected, sft first | - |
| `stage8_sft_v3_answer` | stage8_dpo_vs_sft_010 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_v3_answer` | stage8_dpo_vs_sft_011 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_v3_answer` | stage8_dpo_vs_sft_012 | DPO 与 SFT 区别 | 2 | chosen rejected, sft first | - |
| `stage8_sft_v3_answer` | stage8_public_sft_motivation_001 | public-SFT 诊断价值 | 3 | not fixed | - |
| `stage8_sft_v3_answer` | stage8_public_sft_motivation_002 | public-SFT 诊断价值 | 2 | not fixed, stage2b | - |
| `stage8_sft_v3_answer` | stage8_public_sft_motivation_003 | public-SFT 诊断价值 | 3 | stage2b | - |
| `stage8_sft_v3_answer` | stage8_public_sft_motivation_004 | public-SFT 诊断价值 | 2 | not fixed, stage2b | - |
| `stage8_sft_v3_answer` | stage8_public_sft_motivation_005 | public-SFT 诊断价值 | 3 | stage2b | - |
| `stage8_sft_v3_answer` | stage8_public_sft_motivation_006 | public-SFT 诊断价值 | 3 | not fixed | - |
| `stage8_sft_v3_answer` | stage8_public_sft_motivation_007 | public-SFT 诊断价值 | 2 | not fixed, stage2b | - |
| `stage8_sft_v3_answer` | stage8_public_sft_motivation_008 | public-SFT 诊断价值 | 2 | not fixed, stage2b | - |
| `stage8_sft_v3_answer` | stage8_public_sft_motivation_009 | public-SFT 诊断价值 | 3 | stage2b | - |
| `stage8_sft_v3_answer` | stage8_public_sft_motivation_011 | public-SFT 诊断价值 | 2 | not fixed, stage2b | - |
| `stage8_sft_v3_answer` | stage8_public_sft_motivation_012 | public-SFT 诊断价值 | 2 | not fixed, stage2b | - |
| `stage8_sft_v3_answer` | stage8_data_pipeline_001 | 自采集技术数据管线 | 0 | source metadata, clean, dedup filter, instruction conversion, split | - |
| `stage8_sft_v3_answer` | stage8_data_pipeline_002 | 自采集技术数据管线 | 3 | clean, dedup filter | - |
| `stage8_sft_v3_answer` | stage8_data_pipeline_003 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_sft_v3_answer` | stage8_data_pipeline_004 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_sft_v3_answer` | stage8_data_pipeline_005 | 自采集技术数据管线 | 0 | source metadata, clean, dedup filter, instruction conversion, split | - |
| `stage8_sft_v3_answer` | stage8_data_pipeline_006 | 自采集技术数据管线 | 0 | source metadata, clean, dedup filter, instruction conversion, split | - |
| `stage8_sft_v3_answer` | stage8_data_pipeline_007 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_sft_v3_answer` | stage8_data_pipeline_008 | 自采集技术数据管线 | 2 | source metadata, clean, dedup filter | - |
| `stage8_sft_v3_answer` | stage8_data_pipeline_009 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_sft_v3_answer` | stage8_data_pipeline_010 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_sft_v3_answer` | stage8_data_pipeline_011 | 自采集技术数据管线 | 0 | source metadata, clean, dedup filter, instruction conversion, split | - |
| `stage8_sft_v3_answer` | stage8_data_pipeline_012 | 自采集技术数据管线 | 0 | source metadata, clean, dedup filter, instruction conversion, split | - |
| `stage8_sft_v3_answer` | stage8_loss_behavior_002 | loss 与行为验收 | 2 | not sufficient, fixed behavior, badcase regression | - |
| `stage8_sft_v3_answer` | stage8_loss_behavior_003 | loss 与行为验收 | 2 | not sufficient, fixed behavior, badcase regression | - |
| `stage8_sft_v3_answer` | stage8_loss_behavior_004 | loss 与行为验收 | 3 | fixed behavior, badcase regression | - |
| `stage8_sft_v3_answer` | stage8_loss_behavior_007 | loss 与行为验收 | 1 | loss signal, not sufficient, badcase regression, project example | - |
| `stage8_sft_v3_answer` | stage8_loss_behavior_009 | loss 与行为验收 | 2 | not sufficient, fixed behavior, badcase regression | - |
| `stage8_sft_v3_answer` | stage8_loss_behavior_012 | loss 与行为验收 | 3 | not sufficient, fixed behavior | - |
| `stage8_sft_v3_answer` | stage8_behavior_eval_001 | 固定 Prompt 与扩展评测 | 0 | fixed comparable, expanded heldout, scoring, regression | - |
| `stage8_sft_v3_answer` | stage8_behavior_eval_002 | 固定 Prompt 与扩展评测 | 2 | expanded heldout, scoring | - |
| `stage8_sft_v3_answer` | stage8_behavior_eval_004 | 固定 Prompt 与扩展评测 | 2 | scoring, regression | - |
| `stage8_sft_v3_answer` | stage8_behavior_eval_005 | 固定 Prompt 与扩展评测 | 2 | scoring, regression | - |
| `stage8_sft_v3_answer` | stage8_behavior_eval_006 | 固定 Prompt 与扩展评测 | 2 | scoring, regression | - |
| `stage8_sft_v3_answer` | stage8_behavior_eval_007 | 固定 Prompt 与扩展评测 | 1 | fixed comparable, scoring, regression | - |
| `stage8_sft_v3_answer` | stage8_behavior_eval_009 | 固定 Prompt 与扩展评测 | 2 | expanded heldout, scoring | - |
| `stage8_sft_v3_answer` | stage8_behavior_eval_012 | 固定 Prompt 与扩展评测 | 1 | fixed comparable, scoring, regression | - |
| `stage8_sft_v3_answer` | stage8_dpo_vram_001 | DPO 显存风险 | 2 | chosen rejected, reference, smoke boundary | - |
| `stage8_sft_v3_answer` | stage8_dpo_vram_002 | DPO 显存风险 | 3 | chosen rejected, smoke boundary | - |
| `stage8_sft_v3_answer` | stage8_dpo_vram_003 | DPO 显存风险 | 2 | chosen rejected, reference, smoke boundary | - |
| `stage8_sft_v3_answer` | stage8_dpo_vram_005 | DPO 显存风险 | 3 | reference, smoke boundary | - |
| `stage8_sft_v3_answer` | stage8_dpo_vram_007 | DPO 显存风险 | 2 | chosen rejected, reference, smoke boundary | - |
| `stage8_sft_v3_answer` | stage8_dpo_vram_008 | DPO 显存风险 | 2 | reference, mitigation, smoke boundary | - |
| `stage8_sft_v3_answer` | stage8_dpo_vram_009 | DPO 显存风险 | 3 | mitigation, smoke boundary | - |
| `stage8_sft_v3_answer` | stage8_dpo_vram_010 | DPO 显存风险 | 2 | chosen rejected, reference, smoke boundary | - |
| `stage8_sft_v3_answer` | stage8_dpo_vram_012 | DPO 显存风险 | 1 | chosen rejected, reference, mitigation, smoke boundary | - |
