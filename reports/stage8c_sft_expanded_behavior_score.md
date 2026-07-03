# Stage 8 Expanded Behavior Score Report

Date: 2026-07-03

## Scope

This report scores Stage 8 expanded behavior outputs with transparent
keyword-based gates. It is a reproducible helper, not a final LLM judge.
Failures should be reviewed manually before data patching.

Outputs:

```text
reports/stage8c_sft_expanded_scores.jsonl
reports/stage8c_sft_expanded_scores.csv
```

## Summary

| Variant | Passed | Total Score | Weakest Areas |
|---|---:|---:|---|
| `old_sft_v3_answer` | 25 / 96 | 227 | DPO 与 SFT 区别 3/12, DPO 显存风险 3/12, LoRA 定义与边界 5/12, SFT 与 LoRA 关系 8/12, loss 与行为验收 2/12, public-SFT 诊断价值 4/12, 固定 Prompt 与扩展评测 0/12, 自采集技术数据管线 0/12 |
| `stage8_sft_answer` | 20 / 96 | 229 | DPO 与 SFT 区别 2/12, DPO 显存风险 1/12, LoRA 定义与边界 1/12, SFT 与 LoRA 关系 1/12, loss 与行为验收 6/12, public-SFT 诊断价值 2/12, 固定 Prompt 与扩展评测 7/12, 自采集技术数据管线 0/12 |

## Failed Checks

| Variant | Prompt ID | Area | Score | Missing | Forbidden |
|---|---|---|---:|---|---|
| `old_sft_v3_answer` | stage8_lora_definition_001 | LoRA 定义与边界 | 1 | parameter efficient, adapter, frozen base, not wireless | - |
| `stage8_sft_answer` | stage8_lora_definition_001 | LoRA 定义与边界 | 1 | parameter efficient, adapter, frozen base, not wireless | - |
| `old_sft_v3_answer` | stage8_lora_definition_002 | LoRA 定义与边界 | 0 | lora, parameter efficient, adapter, frozen base, not wireless | - |
| `stage8_sft_answer` | stage8_lora_definition_002 | LoRA 定义与边界 | 0 | lora, parameter efficient, adapter, frozen base, not wireless | - |
| `old_sft_v3_answer` | stage8_lora_definition_003 | LoRA 定义与边界 | 2 | parameter efficient, frozen base, not wireless | - |
| `stage8_sft_answer` | stage8_lora_definition_003 | LoRA 定义与边界 | 3 | frozen base, not wireless | - |
| `old_sft_v3_answer` | stage8_lora_definition_004 | LoRA 定义与边界 | 1 | parameter efficient, adapter, frozen base, not wireless | - |
| `stage8_sft_answer` | stage8_lora_definition_004 | LoRA 定义与边界 | 0 | lora, parameter efficient, adapter, frozen base, not wireless | - |
| `stage8_sft_answer` | stage8_lora_definition_005 | LoRA 定义与边界 | 2 | parameter efficient, frozen base, not wireless | - |
| `old_sft_v3_answer` | stage8_lora_definition_006 | LoRA 定义与边界 | 2 | adapter, frozen base, not wireless | - |
| `old_sft_v3_answer` | stage8_lora_definition_007 | LoRA 定义与边界 | 1 | parameter efficient, adapter, frozen base, not wireless | - |
| `stage8_sft_answer` | stage8_lora_definition_007 | LoRA 定义与边界 | 2 | parameter efficient, frozen base, not wireless | - |
| `stage8_sft_answer` | stage8_lora_definition_008 | LoRA 定义与边界 | 1 | adapter, frozen base | wireless as main concept |
| `stage8_sft_answer` | stage8_lora_definition_009 | LoRA 定义与边界 | 2 | parameter efficient, frozen base, not wireless | - |
| `stage8_sft_answer` | stage8_lora_definition_010 | LoRA 定义与边界 | 1 | parameter efficient, frozen base | wireless as main concept |
| `old_sft_v3_answer` | stage8_lora_definition_011 | LoRA 定义与边界 | 2 | parameter efficient, frozen base, not wireless | - |
| `stage8_sft_answer` | stage8_lora_definition_011 | LoRA 定义与边界 | 1 | adapter, frozen base | wireless as main concept |
| `stage8_sft_answer` | stage8_lora_definition_012 | LoRA 定义与边界 | 0 | parameter efficient, frozen base, not wireless | wireless as main concept |
| `old_sft_v3_answer` | stage8_sft_lora_relation_001 | SFT 与 LoRA 关系 | 1 | sft supervised, objective/data, relationship | - |
| `stage8_sft_answer` | stage8_sft_lora_relation_001 | SFT 与 LoRA 关系 | 1 | objective/data, lora method, relationship | - |
| `old_sft_v3_answer` | stage8_sft_lora_relation_002 | SFT 与 LoRA 关系 | 3 | relationship | - |
| `stage8_sft_answer` | stage8_sft_lora_relation_002 | SFT 与 LoRA 关系 | 0 | sft supervised, objective/data, lora method, relationship | - |
| `stage8_sft_answer` | stage8_sft_lora_relation_003 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_answer` | stage8_sft_lora_relation_005 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_answer` | stage8_sft_lora_relation_006 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `old_sft_v3_answer` | stage8_sft_lora_relation_007 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_answer` | stage8_sft_lora_relation_007 | SFT 与 LoRA 关系 | 2 | objective/data, lora method | - |
| `old_sft_v3_answer` | stage8_sft_lora_relation_008 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_answer` | stage8_sft_lora_relation_008 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_answer` | stage8_sft_lora_relation_009 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_answer` | stage8_sft_lora_relation_010 | SFT 与 LoRA 关系 | 2 | objective/data, lora method | - |
| `stage8_sft_answer` | stage8_sft_lora_relation_011 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_answer` | stage8_sft_lora_relation_012 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `old_sft_v3_answer` | stage8_dpo_vs_sft_001 | DPO 与 SFT 区别 | 0 | sft answer imitation, dpo preference, chosen rejected, sft first | - |
| `stage8_sft_answer` | stage8_dpo_vs_sft_001 | DPO 与 SFT 区别 | 3 | chosen rejected | - |
| `old_sft_v3_answer` | stage8_dpo_vs_sft_002 | DPO 与 SFT 区别 | 0 | sft answer imitation, dpo preference, chosen rejected, sft first | - |
| `stage8_sft_answer` | stage8_dpo_vs_sft_002 | DPO 与 SFT 区别 | 2 | chosen rejected, sft first | - |
| `stage8_sft_answer` | stage8_dpo_vs_sft_003 | DPO 与 SFT 区别 | 3 | sft first | - |
| `old_sft_v3_answer` | stage8_dpo_vs_sft_004 | DPO 与 SFT 区别 | 2 | - | data protection |
| `stage8_sft_answer` | stage8_dpo_vs_sft_004 | DPO 与 SFT 区别 | 2 | chosen rejected, sft first | - |
| `old_sft_v3_answer` | stage8_dpo_vs_sft_005 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_answer` | stage8_dpo_vs_sft_005 | DPO 与 SFT 区别 | 3 | sft first | - |
| `old_sft_v3_answer` | stage8_dpo_vs_sft_006 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_answer` | stage8_dpo_vs_sft_007 | DPO 与 SFT 区别 | 1 | sft answer imitation, chosen rejected, sft first | - |
| `old_sft_v3_answer` | stage8_dpo_vs_sft_008 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_answer` | stage8_dpo_vs_sft_008 | DPO 与 SFT 区别 | 3 | sft first | - |
| `old_sft_v3_answer` | stage8_dpo_vs_sft_009 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_answer` | stage8_dpo_vs_sft_009 | DPO 与 SFT 区别 | 3 | sft first | - |
| `old_sft_v3_answer` | stage8_dpo_vs_sft_010 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_answer` | stage8_dpo_vs_sft_010 | DPO 与 SFT 区别 | 2 | chosen rejected, sft first | - |
| `old_sft_v3_answer` | stage8_dpo_vs_sft_012 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_answer` | stage8_dpo_vs_sft_012 | DPO 与 SFT 区别 | 2 | chosen rejected, sft first | - |
| `old_sft_v3_answer` | stage8_public_sft_motivation_001 | public-SFT 诊断价值 | 3 | stage2b | - |
| `stage8_sft_answer` | stage8_public_sft_motivation_001 | public-SFT 诊断价值 | 2 | public baseline, not fixed | - |
| `old_sft_v3_answer` | stage8_public_sft_motivation_002 | public-SFT 诊断价值 | 1 | engineering proof, not fixed, stage2b | - |
| `stage8_sft_answer` | stage8_public_sft_motivation_002 | public-SFT 诊断价值 | 2 | public baseline, not fixed | - |
| `old_sft_v3_answer` | stage8_public_sft_motivation_003 | public-SFT 诊断价值 | 3 | stage2b | - |
| `stage8_sft_answer` | stage8_public_sft_motivation_003 | public-SFT 诊断价值 | 3 | stage2b | - |
| `old_sft_v3_answer` | stage8_public_sft_motivation_004 | public-SFT 诊断价值 | 3 | not fixed | - |
| `old_sft_v3_answer` | stage8_public_sft_motivation_005 | public-SFT 诊断价值 | 3 | stage2b | - |
| `stage8_sft_answer` | stage8_public_sft_motivation_005 | public-SFT 诊断价值 | 1 | stage2b | overclaim fixed |
| `stage8_sft_answer` | stage8_public_sft_motivation_006 | public-SFT 诊断价值 | 3 | engineering proof | - |
| `stage8_sft_answer` | stage8_public_sft_motivation_007 | public-SFT 诊断价值 | 2 | engineering proof, stage2b | - |
| `old_sft_v3_answer` | stage8_public_sft_motivation_009 | public-SFT 诊断价值 | 3 | not fixed | - |
| `stage8_sft_answer` | stage8_public_sft_motivation_009 | public-SFT 诊断价值 | 3 | not fixed | - |
| `old_sft_v3_answer` | stage8_public_sft_motivation_010 | public-SFT 诊断价值 | 3 | stage2b | - |
| `stage8_sft_answer` | stage8_public_sft_motivation_010 | public-SFT 诊断价值 | 3 | engineering proof | - |
| `stage8_sft_answer` | stage8_public_sft_motivation_011 | public-SFT 诊断价值 | 3 | stage2b | - |
| `old_sft_v3_answer` | stage8_public_sft_motivation_012 | public-SFT 诊断价值 | 3 | not fixed | - |
| `stage8_sft_answer` | stage8_public_sft_motivation_012 | public-SFT 诊断价值 | 3 | stage2b | - |
| `old_sft_v3_answer` | stage8_data_pipeline_001 | 自采集技术数据管线 | 0 | source metadata, clean, dedup filter, instruction conversion, split | - |
| `stage8_sft_answer` | stage8_data_pipeline_001 | 自采集技术数据管线 | 1 | clean, dedup filter, instruction conversion, split | - |
| `old_sft_v3_answer` | stage8_data_pipeline_002 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_sft_answer` | stage8_data_pipeline_002 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `old_sft_v3_answer` | stage8_data_pipeline_003 | 自采集技术数据管线 | 0 | source metadata, clean, dedup filter, instruction conversion, split | - |
| `stage8_sft_answer` | stage8_data_pipeline_003 | 自采集技术数据管线 | 3 | source metadata, instruction conversion | - |
| `old_sft_v3_answer` | stage8_data_pipeline_004 | 自采集技术数据管线 | 1 | clean, dedup filter, instruction conversion, split | - |
| `stage8_sft_answer` | stage8_data_pipeline_004 | 自采集技术数据管线 | 0 | source metadata, clean, dedup filter, instruction conversion, split | - |
| `old_sft_v3_answer` | stage8_data_pipeline_005 | 自采集技术数据管线 | 0 | source metadata, clean, dedup filter, instruction conversion, split | - |
| `stage8_sft_answer` | stage8_data_pipeline_005 | 自采集技术数据管线 | 2 | source metadata, clean, split | - |
| `old_sft_v3_answer` | stage8_data_pipeline_006 | 自采集技术数据管线 | 1 | source metadata, clean, instruction conversion, split | - |
| `stage8_sft_answer` | stage8_data_pipeline_006 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `old_sft_v3_answer` | stage8_data_pipeline_007 | 自采集技术数据管线 | 0 | source metadata, clean, dedup filter, instruction conversion, split | - |
| `stage8_sft_answer` | stage8_data_pipeline_007 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `old_sft_v3_answer` | stage8_data_pipeline_008 | 自采集技术数据管线 | 0 | source metadata, clean, dedup filter, instruction conversion, split | - |
| `stage8_sft_answer` | stage8_data_pipeline_008 | 自采集技术数据管线 | 2 | source metadata, clean, split | - |
| `old_sft_v3_answer` | stage8_data_pipeline_009 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, split | - |
| `stage8_sft_answer` | stage8_data_pipeline_009 | 自采集技术数据管线 | 3 | clean, instruction conversion | - |
| `old_sft_v3_answer` | stage8_data_pipeline_010 | 自采集技术数据管线 | 2 | dedup filter, instruction conversion, split | - |
| `stage8_sft_answer` | stage8_data_pipeline_010 | 自采集技术数据管线 | 2 | clean, dedup filter, instruction conversion | - |
| `old_sft_v3_answer` | stage8_data_pipeline_011 | 自采集技术数据管线 | 2 | source metadata, instruction conversion, split | - |
| `stage8_sft_answer` | stage8_data_pipeline_011 | 自采集技术数据管线 | 3 | source metadata, split | - |
| `old_sft_v3_answer` | stage8_data_pipeline_012 | 自采集技术数据管线 | 0 | source metadata, clean, dedup filter, instruction conversion, split | - |
| `stage8_sft_answer` | stage8_data_pipeline_012 | 自采集技术数据管线 | 3 | instruction conversion, split | - |
| `old_sft_v3_answer` | stage8_loss_behavior_001 | loss 与行为验收 | 2 | not sufficient, fixed behavior, badcase regression | - |
| `stage8_sft_answer` | stage8_loss_behavior_001 | loss 与行为验收 | 2 | not sufficient, fixed behavior, badcase regression | - |
| `stage8_sft_answer` | stage8_loss_behavior_002 | loss 与行为验收 | 2 | not sufficient, badcase regression, project example | - |
| `old_sft_v3_answer` | stage8_loss_behavior_003 | loss 与行为验收 | 3 | not sufficient, badcase regression | - |
| `old_sft_v3_answer` | stage8_loss_behavior_004 | loss 与行为验收 | 3 | not sufficient, badcase regression | - |
| `old_sft_v3_answer` | stage8_loss_behavior_005 | loss 与行为验收 | 2 | not sufficient, badcase regression, project example | - |
| `stage8_sft_answer` | stage8_loss_behavior_005 | loss 与行为验收 | 3 | not sufficient, badcase regression | - |
| `old_sft_v3_answer` | stage8_loss_behavior_006 | loss 与行为验收 | 3 | not sufficient, badcase regression | - |
| `stage8_sft_answer` | stage8_loss_behavior_007 | loss 与行为验收 | 3 | not sufficient, badcase regression | - |
| `old_sft_v3_answer` | stage8_loss_behavior_008 | loss 与行为验收 | 2 | not sufficient, badcase regression, project example | - |
| `old_sft_v3_answer` | stage8_loss_behavior_009 | loss 与行为验收 | 2 | not sufficient, fixed behavior, badcase regression | - |
| `stage8_sft_answer` | stage8_loss_behavior_009 | loss 与行为验收 | 1 | not sufficient, fixed behavior, badcase regression, project example | - |
| `old_sft_v3_answer` | stage8_loss_behavior_010 | loss 与行为验收 | 3 | not sufficient, badcase regression | - |
| `old_sft_v3_answer` | stage8_loss_behavior_011 | loss 与行为验收 | 3 | not sufficient, badcase regression | - |
| `stage8_sft_answer` | stage8_loss_behavior_011 | loss 与行为验收 | 3 | badcase regression, project example | - |
| `old_sft_v3_answer` | stage8_loss_behavior_012 | loss 与行为验收 | 3 | not sufficient, badcase regression | - |
| `old_sft_v3_answer` | stage8_behavior_eval_001 | 固定 Prompt 与扩展评测 | 0 | fixed comparable, expanded heldout, scoring, regression | - |
| `stage8_sft_answer` | stage8_behavior_eval_001 | 固定 Prompt 与扩展评测 | 0 | fixed comparable, expanded heldout, scoring, regression | - |
| `old_sft_v3_answer` | stage8_behavior_eval_002 | 固定 Prompt 与扩展评测 | 1 | fixed comparable, scoring, regression | - |
| `stage8_sft_answer` | stage8_behavior_eval_002 | 固定 Prompt 与扩展评测 | 1 | fixed comparable, scoring, regression | - |
| `old_sft_v3_answer` | stage8_behavior_eval_003 | 固定 Prompt 与扩展评测 | 2 | scoring, regression | - |
| `old_sft_v3_answer` | stage8_behavior_eval_004 | 固定 Prompt 与扩展评测 | 2 | scoring, regression | - |
| `old_sft_v3_answer` | stage8_behavior_eval_005 | 固定 Prompt 与扩展评测 | 2 | scoring, regression | - |
| `old_sft_v3_answer` | stage8_behavior_eval_006 | 固定 Prompt 与扩展评测 | 2 | scoring, regression | - |
| `stage8_sft_answer` | stage8_behavior_eval_006 | 固定 Prompt 与扩展评测 | 2 | scoring, regression | - |
| `old_sft_v3_answer` | stage8_behavior_eval_007 | 固定 Prompt 与扩展评测 | 0 | fixed comparable, expanded heldout, scoring, regression | - |
| `stage8_sft_answer` | stage8_behavior_eval_007 | 固定 Prompt 与扩展评测 | 0 | fixed comparable, expanded heldout, scoring, regression | - |
| `old_sft_v3_answer` | stage8_behavior_eval_008 | 固定 Prompt 与扩展评测 | 2 | scoring, regression | - |
| `old_sft_v3_answer` | stage8_behavior_eval_009 | 固定 Prompt 与扩展评测 | 1 | expanded heldout, scoring, regression | - |
| `stage8_sft_answer` | stage8_behavior_eval_009 | 固定 Prompt 与扩展评测 | 2 | scoring, regression | - |
| `old_sft_v3_answer` | stage8_behavior_eval_010 | 固定 Prompt 与扩展评测 | 2 | scoring, regression | - |
| `old_sft_v3_answer` | stage8_behavior_eval_011 | 固定 Prompt 与扩展评测 | 2 | scoring, regression | - |
| `old_sft_v3_answer` | stage8_behavior_eval_012 | 固定 Prompt 与扩展评测 | 2 | scoring, regression | - |
| `old_sft_v3_answer` | stage8_dpo_vram_001 | DPO 显存风险 | 2 | chosen rejected, reference, smoke boundary | - |
| `stage8_sft_answer` | stage8_dpo_vram_001 | DPO 显存风险 | 2 | memory risk, mitigation, smoke boundary | - |
| `old_sft_v3_answer` | stage8_dpo_vram_002 | DPO 显存风险 | 1 | chosen rejected, reference, memory risk, smoke boundary | - |
| `stage8_sft_answer` | stage8_dpo_vram_002 | DPO 显存风险 | 0 | chosen rejected, reference, memory risk, mitigation, smoke boundary | - |
| `stage8_sft_answer` | stage8_dpo_vram_003 | DPO 显存风险 | 3 | mitigation, smoke boundary | - |
| `old_sft_v3_answer` | stage8_dpo_vram_004 | DPO 显存风险 | 1 | chosen rejected, reference, mitigation, smoke boundary | - |
| `stage8_sft_answer` | stage8_dpo_vram_004 | DPO 显存风险 | 3 | chosen rejected, reference | - |
| `old_sft_v3_answer` | stage8_dpo_vram_005 | DPO 显存风险 | 1 | chosen rejected, reference, mitigation, smoke boundary | - |
| `stage8_sft_answer` | stage8_dpo_vram_005 | DPO 显存风险 | 3 | reference, smoke boundary | - |
| `old_sft_v3_answer` | stage8_dpo_vram_006 | DPO 显存风险 | 2 | chosen rejected, reference, smoke boundary | - |
| `stage8_sft_answer` | stage8_dpo_vram_006 | DPO 显存风险 | 2 | chosen rejected, reference, smoke boundary | - |
| `old_sft_v3_answer` | stage8_dpo_vram_007 | DPO 显存风险 | 3 | mitigation, smoke boundary | - |
| `stage8_sft_answer` | stage8_dpo_vram_007 | DPO 显存风险 | 0 | chosen rejected, reference, memory risk, mitigation, smoke boundary | - |
| `old_sft_v3_answer` | stage8_dpo_vram_008 | DPO 显存风险 | 1 | chosen rejected, reference, mitigation, smoke boundary | - |
| `stage8_sft_answer` | stage8_dpo_vram_008 | DPO 显存风险 | 2 | chosen rejected, reference, smoke boundary | - |
| `stage8_sft_answer` | stage8_dpo_vram_009 | DPO 显存风险 | 2 | chosen rejected, reference, smoke boundary | - |
| `old_sft_v3_answer` | stage8_dpo_vram_010 | DPO 显存风险 | 0 | chosen rejected, reference, memory risk, mitigation, smoke boundary | - |
| `stage8_sft_answer` | stage8_dpo_vram_010 | DPO 显存风险 | 2 | chosen rejected, reference, smoke boundary | - |
| `stage8_sft_answer` | stage8_dpo_vram_011 | DPO 显存风险 | 2 | chosen rejected, reference, smoke boundary | - |
| `old_sft_v3_answer` | stage8_dpo_vram_012 | DPO 显存风险 | 3 | mitigation, smoke boundary | - |
