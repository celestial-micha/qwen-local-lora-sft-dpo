# Stage 5H/5I Expanded Behavior Score Report

Date: 2026-05-16

## Scope

This report scores expanded Stage 5H/5I comparison outputs. The scorer uses
`prompt_area` metadata when available and falls back to the original fixed
8-prompt row order only for legacy comparison files.

It is still a transparent keyword gate helper, not an LLM judge.

Outputs:

```text
reports/stage5h_expanded_behavior_scores_v6.jsonl
reports/stage5h_expanded_behavior_scores_v6.csv
```

## Summary Table

| Run | Variant | Passed Prompts | Loss-vs-Behavior Passed | Total Score | Failed Areas |
|---|---|---:|---:|---:|---|
| dpo_naive_v6 | `base_answer` | 0 / 24 | 0 / 13 | 7 | fixed_01: LoRA definition, fixed_02: SFT and LoRA relation, fixed_03: DPO vs SFT, fixed_04: Public-SFT motivation, fixed_05: Data pipeline, fixed_06: DPO VRAM risk, fixed_07: Loss vs behavior, fixed_08: Interview data pipeline, stage5h_p7_holdout_01: Loss vs behavior, stage5h_p7_holdout_02: Loss vs behavior, stage5h_p7_holdout_03: Loss vs behavior, stage5h_p7_holdout_04: Loss vs behavior, stage5h_p7_holdout_05: Loss vs behavior, stage5h_p7_holdout_06: Loss vs behavior, stage5h_p7_holdout_07: Loss vs behavior, stage5h_p7_holdout_08: Loss vs behavior, stage5h_p7_holdout_09: Loss vs behavior, stage5h_p7_holdout_10: Loss vs behavior, stage5h_p7_holdout_11: Loss vs behavior, stage5h_p7_holdout_12: Loss vs behavior, replay_public_sft_motivation_01: Public-SFT motivation, replay_dpo_vram_01: DPO VRAM risk, replay_data_pipeline_01: Data pipeline, replay_interview_narrative_01: Interview data pipeline |
| dpo_naive_v6 | `public_sft_answer` | 0 / 24 | 0 / 13 | 7 | fixed_01: LoRA definition, fixed_02: SFT and LoRA relation, fixed_03: DPO vs SFT, fixed_04: Public-SFT motivation, fixed_05: Data pipeline, fixed_06: DPO VRAM risk, fixed_07: Loss vs behavior, fixed_08: Interview data pipeline, stage5h_p7_holdout_01: Loss vs behavior, stage5h_p7_holdout_02: Loss vs behavior, stage5h_p7_holdout_03: Loss vs behavior, stage5h_p7_holdout_04: Loss vs behavior, stage5h_p7_holdout_05: Loss vs behavior, stage5h_p7_holdout_06: Loss vs behavior, stage5h_p7_holdout_07: Loss vs behavior, stage5h_p7_holdout_08: Loss vs behavior, stage5h_p7_holdout_09: Loss vs behavior, stage5h_p7_holdout_10: Loss vs behavior, stage5h_p7_holdout_11: Loss vs behavior, stage5h_p7_holdout_12: Loss vs behavior, replay_public_sft_motivation_01: Public-SFT motivation, replay_dpo_vram_01: DPO VRAM risk, replay_data_pipeline_01: Data pipeline, replay_interview_narrative_01: Interview data pipeline |
| dpo_naive_v6 | `custom_sft_v3_answer` | 7 / 24 | 0 / 13 | 62 | fixed_07: Loss vs behavior, stage5h_p7_holdout_01: Loss vs behavior, stage5h_p7_holdout_02: Loss vs behavior, stage5h_p7_holdout_03: Loss vs behavior, stage5h_p7_holdout_04: Loss vs behavior, stage5h_p7_holdout_05: Loss vs behavior, stage5h_p7_holdout_06: Loss vs behavior, stage5h_p7_holdout_07: Loss vs behavior, stage5h_p7_holdout_08: Loss vs behavior, stage5h_p7_holdout_09: Loss vs behavior, stage5h_p7_holdout_10: Loss vs behavior, stage5h_p7_holdout_11: Loss vs behavior, stage5h_p7_holdout_12: Loss vs behavior, replay_public_sft_motivation_01: Public-SFT motivation, replay_dpo_vram_01: DPO VRAM risk, replay_data_pipeline_01: Data pipeline, replay_interview_narrative_01: Interview data pipeline |
| dpo_naive_v6 | `dpo_tiny_answer` | 7 / 24 | 0 / 13 | 69 | fixed_07: Loss vs behavior, stage5h_p7_holdout_01: Loss vs behavior, stage5h_p7_holdout_02: Loss vs behavior, stage5h_p7_holdout_03: Loss vs behavior, stage5h_p7_holdout_04: Loss vs behavior, stage5h_p7_holdout_05: Loss vs behavior, stage5h_p7_holdout_06: Loss vs behavior, stage5h_p7_holdout_07: Loss vs behavior, stage5h_p7_holdout_08: Loss vs behavior, stage5h_p7_holdout_09: Loss vs behavior, stage5h_p7_holdout_10: Loss vs behavior, stage5h_p7_holdout_11: Loss vs behavior, stage5h_p7_holdout_12: Loss vs behavior, replay_public_sft_motivation_01: Public-SFT motivation, replay_dpo_vram_01: DPO VRAM risk, replay_data_pipeline_01: Data pipeline, replay_interview_narrative_01: Interview data pipeline |

## DPO Candidate Prompt Scores

| Prompt ID | Area | Score | Pass | Missing | Forbidden |
|---|---|---:|---|---|---|
| fixed_01 | LoRA definition | 5 | True | - | - |
| fixed_02 | SFT and LoRA relation | 4 | True | - | - |
| fixed_03 | DPO vs SFT | 4 | True | - | - |
| fixed_04 | Public-SFT motivation | 4 | True | - | - |
| fixed_05 | Data pipeline | 5 | True | - | - |
| fixed_06 | DPO VRAM risk | 5 | True | - | - |
| fixed_07 | Loss vs behavior | 2 | False | loss average signal, fixed prompt behavior, badcase/regression, metric split | - |
| fixed_08 | Interview data pipeline | 5 | True | - | - |
| stage5h_p7_holdout_01 | Loss vs behavior | 4 | False | not sufficient, project example | - |
| stage5h_p7_holdout_02 | Loss vs behavior | 2 | False | not sufficient, fixed prompt behavior, badcase/regression, metric split | - |
| stage5h_p7_holdout_03 | Loss vs behavior | 2 | False | loss average signal, not sufficient, badcase/regression, metric split | - |
| stage5h_p7_holdout_04 | Loss vs behavior | 2 | False | loss average signal, not sufficient, badcase/regression, metric split | - |
| stage5h_p7_holdout_05 | Loss vs behavior | 4 | False | loss average signal, badcase/regression | - |
| stage5h_p7_holdout_06 | Loss vs behavior | 4 | False | not sufficient, badcase/regression | - |
| stage5h_p7_holdout_07 | Loss vs behavior | 3 | False | loss average signal, not sufficient, metric split | - |
| stage5h_p7_holdout_08 | Loss vs behavior | 0 | False | loss average signal, not sufficient, fixed prompt behavior, badcase/regression, project example, metric split | - |
| stage5h_p7_holdout_09 | Loss vs behavior | 2 | False | loss average signal, not sufficient, badcase/regression, metric split | - |
| stage5h_p7_holdout_10 | Loss vs behavior | 2 | False | not sufficient, fixed prompt behavior, project example, metric split | - |
| stage5h_p7_holdout_11 | Loss vs behavior | 2 | False | loss average signal, not sufficient, badcase/regression, metric split | - |
| stage5h_p7_holdout_12 | Loss vs behavior | 3 | False | not sufficient, badcase/regression, project example | - |
| replay_public_sft_motivation_01 | Public-SFT motivation | 3 | False | Stage 2B data repair | - |
| replay_dpo_vram_01 | DPO VRAM risk | 1 | False | reference policy, 8GB risk, small batch/short length, LoRA/small pairs | - |
| replay_data_pipeline_01 | Data pipeline | 0 | False | source metadata, cleaning, dedup/filter, instruction-answer conversion, Qwen chat JSONL | - |
| replay_interview_narrative_01 | Interview data pipeline | 1 | False | public baseline, Stage 4A badcase, Stage 2B pipeline, instruction-answer | - |

## Gate Interpretation

- A future DPO adapter should pass the original fixed prompts and the expanded
  loss-vs-behavior holdouts.
- Prompt 7 answers must not merely say "cannot only look at loss"; they should
  include the average-objective nature of loss, why that is not sufficient,
  fixed-prompt behavior, badcase/regression review, and a project example such
  as public-SFT or DPO v6.
- Preference accuracy, train loss, and eval loss remain supporting metrics, not
  final acceptance criteria.
