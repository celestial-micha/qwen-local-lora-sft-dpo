# Stage 8 Expanded Behavior Score Report

Date: 2026-07-03

## Scope

This report scores Stage 8 expanded behavior outputs with transparent
keyword-based gates. It is a reproducible helper, not a final LLM judge.
Failures should be reviewed manually before data patching.

Outputs:

```text
reports/stage8i_sft_v4_targeted_expanded_scores.jsonl
reports/stage8i_sft_v4_targeted_expanded_scores.csv
```

## Summary

| Variant | Passed | Total Score | Weakest Areas |
|---|---:|---:|---|
| `stage8_sft_v4_targeted_answer` | 39 / 96 | 277 | DPO 与 SFT 区别 0/12, DPO 显存风险 2/12, LoRA 定义与边界 7/12, SFT 与 LoRA 关系 8/12, loss 与行为验收 8/12, public-SFT 诊断价值 4/12, 固定 Prompt 与扩展评测 10/12, 自采集技术数据管线 0/12 |

## Failed Checks

| Variant | Prompt ID | Area | Score | Missing | Forbidden |
|---|---|---|---:|---|---|
| `stage8_sft_v4_targeted_answer` | stage8_lora_definition_001 | LoRA 定义与边界 | 3 | frozen base, not wireless | - |
| `stage8_sft_v4_targeted_answer` | stage8_lora_definition_002 | LoRA 定义与边界 | 1 | parameter efficient, adapter, frozen base, not wireless | - |
| `stage8_sft_v4_targeted_answer` | stage8_lora_definition_005 | LoRA 定义与边界 | 1 | parameter efficient, adapter, frozen base, not wireless | - |
| `stage8_sft_v4_targeted_answer` | stage8_lora_definition_007 | LoRA 定义与边界 | 2 | parameter efficient, frozen base, not wireless | - |
| `stage8_sft_v4_targeted_answer` | stage8_lora_definition_009 | LoRA 定义与边界 | 1 | parameter efficient, adapter, frozen base, not wireless | - |
| `stage8_sft_v4_targeted_answer` | stage8_sft_lora_relation_002 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_v4_targeted_answer` | stage8_sft_lora_relation_004 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_v4_targeted_answer` | stage8_sft_lora_relation_005 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_v4_targeted_answer` | stage8_sft_lora_relation_007 | SFT 与 LoRA 关系 | 3 | objective/data | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vs_sft_001 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vs_sft_002 | DPO 与 SFT 区别 | 2 | chosen rejected, sft first | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vs_sft_003 | DPO 与 SFT 区别 | 2 | chosen rejected, sft first | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vs_sft_004 | DPO 与 SFT 区别 | 2 | chosen rejected, sft first | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vs_sft_005 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vs_sft_006 | DPO 与 SFT 区别 | 2 | chosen rejected, sft first | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vs_sft_007 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vs_sft_008 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vs_sft_009 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vs_sft_010 | DPO 与 SFT 区别 | 2 | chosen rejected, sft first | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vs_sft_011 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vs_sft_012 | DPO 与 SFT 区别 | 3 | sft first | - |
| `stage8_sft_v4_targeted_answer` | stage8_public_sft_motivation_001 | public-SFT 诊断价值 | 1 | public baseline, not fixed, stage2b | - |
| `stage8_sft_v4_targeted_answer` | stage8_public_sft_motivation_002 | public-SFT 诊断价值 | 1 | engineering proof, not fixed, stage2b | - |
| `stage8_sft_v4_targeted_answer` | stage8_public_sft_motivation_003 | public-SFT 诊断价值 | 3 | not fixed | - |
| `stage8_sft_v4_targeted_answer` | stage8_public_sft_motivation_004 | public-SFT 诊断价值 | 3 | not fixed | - |
| `stage8_sft_v4_targeted_answer` | stage8_public_sft_motivation_006 | public-SFT 诊断价值 | 3 | stage2b | - |
| `stage8_sft_v4_targeted_answer` | stage8_public_sft_motivation_007 | public-SFT 诊断价值 | 1 | engineering proof, not fixed, stage2b | - |
| `stage8_sft_v4_targeted_answer` | stage8_public_sft_motivation_010 | public-SFT 诊断价值 | 3 | not fixed | - |
| `stage8_sft_v4_targeted_answer` | stage8_public_sft_motivation_012 | public-SFT 诊断价值 | 2 | not fixed, stage2b | - |
| `stage8_sft_v4_targeted_answer` | stage8_data_pipeline_001 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_sft_v4_targeted_answer` | stage8_data_pipeline_002 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_sft_v4_targeted_answer` | stage8_data_pipeline_003 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_sft_v4_targeted_answer` | stage8_data_pipeline_004 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_sft_v4_targeted_answer` | stage8_data_pipeline_005 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_sft_v4_targeted_answer` | stage8_data_pipeline_006 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_sft_v4_targeted_answer` | stage8_data_pipeline_007 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_sft_v4_targeted_answer` | stage8_data_pipeline_008 | 自采集技术数据管线 | 2 | source metadata, clean, dedup filter | - |
| `stage8_sft_v4_targeted_answer` | stage8_data_pipeline_009 | 自采集技术数据管线 | 2 | source metadata, clean, dedup filter | - |
| `stage8_sft_v4_targeted_answer` | stage8_data_pipeline_010 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_sft_v4_targeted_answer` | stage8_data_pipeline_011 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_sft_v4_targeted_answer` | stage8_data_pipeline_012 | 自采集技术数据管线 | 1 | source metadata, clean, dedup filter, instruction conversion | - |
| `stage8_sft_v4_targeted_answer` | stage8_loss_behavior_005 | loss 与行为验收 | 3 | not sufficient, badcase regression | - |
| `stage8_sft_v4_targeted_answer` | stage8_loss_behavior_006 | loss 与行为验收 | 3 | loss signal, not sufficient | - |
| `stage8_sft_v4_targeted_answer` | stage8_loss_behavior_011 | loss 与行为验收 | 1 | loss signal, not sufficient, badcase regression, project example | - |
| `stage8_sft_v4_targeted_answer` | stage8_loss_behavior_012 | loss 与行为验收 | 3 | not sufficient, badcase regression | - |
| `stage8_sft_v4_targeted_answer` | stage8_behavior_eval_004 | 固定 Prompt 与扩展评测 | 2 | scoring, regression | - |
| `stage8_sft_v4_targeted_answer` | stage8_behavior_eval_012 | 固定 Prompt 与扩展评测 | 1 | fixed comparable, expanded heldout, regression | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vram_001 | DPO 显存风险 | 1 | chosen rejected, reference, memory risk, smoke boundary | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vram_002 | DPO 显存风险 | 1 | chosen rejected, reference, memory risk, smoke boundary | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vram_003 | DPO 显存风险 | 3 | memory risk, smoke boundary | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vram_005 | DPO 显存风险 | 2 | memory risk, mitigation, smoke boundary | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vram_006 | DPO 显存风险 | 3 | mitigation, smoke boundary | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vram_007 | DPO 显存风险 | 3 | memory risk, smoke boundary | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vram_008 | DPO 显存风险 | 3 | mitigation, smoke boundary | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vram_009 | DPO 显存风险 | 3 | memory risk, smoke boundary | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vram_010 | DPO 显存风险 | 2 | chosen rejected, reference, memory risk | - |
| `stage8_sft_v4_targeted_answer` | stage8_dpo_vram_011 | DPO 显存风险 | 3 | memory risk, smoke boundary | - |
