# Stage 5 Structured Behavior Score Report

Date: 2026-05-16

## Scope

This report applies a transparent keyword-based scoring script to the fixed
prompt comparison outputs from Stage 5C, Stage 5C.2, Stage 5C.3, and any
candidate-derived follow-up runs included on the command line.

It is not an LLM judge. It is a reproducible gate helper that checks required
concepts and known-bad phrases for each fixed prompt.

Inputs:

```text
reports/compare_outputs_four_way_dpo_tiny.jsonl
reports/compare_outputs_four_way_dpo_tiny_v2.jsonl
reports/compare_outputs_four_way_dpo_tiny_v3.jsonl
reports/compare_outputs_four_way_dpo_candidate_v4.jsonl
reports/compare_outputs_four_way_dpo_candidate_v5.jsonl
reports/compare_outputs_four_way_dpo_naive_v6.jsonl
reports/compare_outputs_four_way_dpo_v7_stage5h.jsonl
reports/compare_outputs_four_way_stage5k_sft_repair.jsonl
reports/compare_outputs_four_way_dpo_v8_stage5m_from_v6.jsonl
reports/compare_outputs_four_way_stage5n_prompt7_micro_sft.jsonl
reports/compare_outputs_four_way_stage5o_prompt7_exact_sft.jsonl
reports/compare_outputs_four_way_stage5p_prompt7_balanced_sft.jsonl
```

Outputs:

```text
reports/stage5_structured_behavior_scores.jsonl
reports/stage5_structured_behavior_scores.csv
```

## Summary Table

| Run | Variant | Passed Prompts | Total Score | Failed Areas |
|---|---|---:|---:|---|
| dpo_tiny_v1 | `base_answer` | 0 / 8 | -5 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| dpo_tiny_v1 | `public_sft_answer` | 0 / 8 | -11 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| dpo_tiny_v1 | `custom_sft_v3_answer` | 7 / 8 | 33 | 7: Loss vs behavior |
| dpo_tiny_v1 | `dpo_tiny_answer` | 6 / 8 | 27 | 4: Public-SFT motivation, 7: Loss vs behavior |
| dpo_tiny_v2 | `base_answer` | 0 / 8 | -5 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| dpo_tiny_v2 | `public_sft_answer` | 0 / 8 | -11 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| dpo_tiny_v2 | `custom_sft_v3_answer` | 7 / 8 | 33 | 7: Loss vs behavior |
| dpo_tiny_v2 | `dpo_tiny_answer` | 6 / 8 | 29 | 4: Public-SFT motivation, 7: Loss vs behavior |
| dpo_tiny_v3 | `base_answer` | 0 / 8 | -5 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| dpo_tiny_v3 | `public_sft_answer` | 0 / 8 | -11 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| dpo_tiny_v3 | `custom_sft_v3_answer` | 7 / 8 | 33 | 7: Loss vs behavior |
| dpo_tiny_v3 | `dpo_tiny_answer` | 1 / 8 | 4 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| dpo_candidate_v4 | `base_answer` | 0 / 8 | -5 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| dpo_candidate_v4 | `public_sft_answer` | 0 / 8 | -11 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| dpo_candidate_v4 | `custom_sft_v3_answer` | 7 / 8 | 33 | 7: Loss vs behavior |
| dpo_candidate_v4 | `dpo_tiny_answer` | 6 / 8 | 33 | 4: Public-SFT motivation, 7: Loss vs behavior |
| dpo_candidate_v5 | `base_answer` | 0 / 8 | -5 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| dpo_candidate_v5 | `public_sft_answer` | 0 / 8 | -11 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| dpo_candidate_v5 | `custom_sft_v3_answer` | 7 / 8 | 33 | 7: Loss vs behavior |
| dpo_candidate_v5 | `dpo_tiny_answer` | 6 / 8 | 31 | 4: Public-SFT motivation, 7: Loss vs behavior |
| dpo_naive_v6 | `base_answer` | 0 / 8 | -5 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| dpo_naive_v6 | `public_sft_answer` | 0 / 8 | -11 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| dpo_naive_v6 | `custom_sft_v3_answer` | 7 / 8 | 33 | 7: Loss vs behavior |
| dpo_naive_v6 | `dpo_tiny_answer` | 7 / 8 | 34 | 7: Loss vs behavior |
| dpo_v7_stage5h | `base_answer` | 0 / 8 | -5 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| dpo_v7_stage5h | `public_sft_answer` | 0 / 8 | -11 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| dpo_v7_stage5h | `custom_sft_v3_answer` | 7 / 8 | 33 | 7: Loss vs behavior |
| dpo_v7_stage5h | `dpo_tiny_answer` | 7 / 8 | 33 | 7: Loss vs behavior |
| stage5k_sft_repair | `base_answer` | 0 / 8 | -5 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| stage5k_sft_repair | `public_sft_answer` | 0 / 8 | -11 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| stage5k_sft_repair | `custom_sft_v3_answer` | 1 / 8 | 21 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| stage5k_sft_repair | `dpo_tiny_answer` | 7 / 8 | 33 | 7: Loss vs behavior |
| dpo_v8_stage5m | `base_answer` | 0 / 8 | -5 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| dpo_v8_stage5m | `public_sft_answer` | 0 / 8 | -11 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| dpo_v8_stage5m | `custom_sft_v3_answer` | 7 / 8 | 33 | 7: Loss vs behavior |
| dpo_v8_stage5m | `dpo_tiny_answer` | 7 / 8 | 34 | 7: Loss vs behavior |
| stage5n_prompt7_micro_sft | `base_answer` | 0 / 8 | -5 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| stage5n_prompt7_micro_sft | `public_sft_answer` | 0 / 8 | -11 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| stage5n_prompt7_micro_sft | `custom_sft_v3_answer` | 7 / 8 | 35 | 7: Loss vs behavior |
| stage5n_prompt7_micro_sft | `dpo_tiny_answer` | 7 / 8 | 34 | 7: Loss vs behavior |
| stage5o_prompt7_exact_sft | `base_answer` | 0 / 8 | -5 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| stage5o_prompt7_exact_sft | `public_sft_answer` | 0 / 8 | -11 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| stage5o_prompt7_exact_sft | `custom_sft_v3_answer` | 4 / 8 | 26 | 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 6: DPO VRAM risk |
| stage5o_prompt7_exact_sft | `dpo_tiny_answer` | 7 / 8 | 34 | 7: Loss vs behavior |
| stage5p_prompt7_balanced_sft | `base_answer` | 0 / 8 | -5 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| stage5p_prompt7_balanced_sft | `public_sft_answer` | 0 / 8 | -11 | 1: LoRA definition, 2: SFT and LoRA relation, 3: DPO vs SFT, 4: Public-SFT motivation, 5: Data pipeline, 6: DPO VRAM risk, 7: Loss vs behavior, 8: Interview data pipeline |
| stage5p_prompt7_balanced_sft | `custom_sft_v3_answer` | 6 / 8 | 30 | 2: SFT and LoRA relation, 7: Loss vs behavior |
| stage5p_prompt7_balanced_sft | `dpo_tiny_answer` | 7 / 8 | 34 | 7: Loss vs behavior |

## DPO Candidate Prompt Scores

| Run | Prompt | Area | Score | Pass | Missing | Forbidden |
|---|---:|---|---:|---|---|---|
| dpo_tiny_v1 | 1 | LoRA definition | 5 | True | - | - |
| dpo_tiny_v1 | 2 | SFT and LoRA relation | 4 | True | - | - |
| dpo_tiny_v1 | 3 | DPO vs SFT | 4 | True | - | - |
| dpo_tiny_v1 | 4 | Public-SFT motivation | 0 | False | - | from-zero claim, invented duration |
| dpo_tiny_v1 | 5 | Data pipeline | 5 | True | - | - |
| dpo_tiny_v1 | 6 | DPO VRAM risk | 5 | True | - | - |
| dpo_tiny_v1 | 7 | Loss vs behavior | -1 | False | loss average signal, not sufficient, fixed prompt behavior, badcase/regression | invented duration |
| dpo_tiny_v1 | 8 | Interview data pipeline | 5 | True | - | - |
| dpo_tiny_v2 | 1 | LoRA definition | 5 | True | - | - |
| dpo_tiny_v2 | 2 | SFT and LoRA relation | 4 | True | - | - |
| dpo_tiny_v2 | 3 | DPO vs SFT | 4 | True | - | - |
| dpo_tiny_v2 | 4 | Public-SFT motivation | 2 | False | - | public adapter fixes concepts |
| dpo_tiny_v2 | 5 | Data pipeline | 5 | True | - | - |
| dpo_tiny_v2 | 6 | DPO VRAM risk | 5 | True | - | - |
| dpo_tiny_v2 | 7 | Loss vs behavior | -1 | False | loss average signal, not sufficient, fixed prompt behavior, badcase/regression | invented duration |
| dpo_tiny_v2 | 8 | Interview data pipeline | 5 | True | - | - |
| dpo_tiny_v3 | 1 | LoRA definition | 2 | False | frozen base model | adapter-state confusion |
| dpo_tiny_v3 | 2 | SFT and LoRA relation | 1 | False | LoRA SFT relation | architecture confusion |
| dpo_tiny_v3 | 3 | DPO vs SFT | -3 | False | SFT imitation, DPO preference pairs, prefer chosen | DPO object confusion, SFT safety metric confusion |
| dpo_tiny_v3 | 4 | Public-SFT motivation | -2 | False | engineering loop works, target concepts not solved | robustness-only claim, long-stack confusion |
| dpo_tiny_v3 | 5 | Data pipeline | 4 | True | Qwen chat JSONL | - |
| dpo_tiny_v3 | 6 | DPO VRAM risk | 2 | False | LoRA/small pairs | fabricated memory numbers |
| dpo_tiny_v3 | 7 | Loss vs behavior | 0 | False | badcase/regression | DPO metric confusion, adapter-loss confusion |
| dpo_tiny_v3 | 8 | Interview data pipeline | 0 | False | instruction-answer | tokenizer/storage confusion, base adapter/public adapter confusion |
| dpo_candidate_v4 | 1 | LoRA definition | 5 | True | - | - |
| dpo_candidate_v4 | 2 | SFT and LoRA relation | 4 | True | - | - |
| dpo_candidate_v4 | 3 | DPO vs SFT | 4 | True | - | - |
| dpo_candidate_v4 | 4 | Public-SFT motivation | 2 | False | engineering loop works, target concepts not solved | - |
| dpo_candidate_v4 | 5 | Data pipeline | 5 | True | - | - |
| dpo_candidate_v4 | 6 | DPO VRAM risk | 5 | True | - | - |
| dpo_candidate_v4 | 7 | Loss vs behavior | 3 | False | loss average signal, badcase/regression | - |
| dpo_candidate_v4 | 8 | Interview data pipeline | 5 | True | - | - |
| dpo_candidate_v5 | 1 | LoRA definition | 5 | True | - | - |
| dpo_candidate_v5 | 2 | SFT and LoRA relation | 4 | True | - | - |
| dpo_candidate_v5 | 3 | DPO vs SFT | 4 | True | - | - |
| dpo_candidate_v5 | 4 | Public-SFT motivation | 2 | False | engineering loop works, target concepts not solved | - |
| dpo_candidate_v5 | 5 | Data pipeline | 5 | True | - | - |
| dpo_candidate_v5 | 6 | DPO VRAM risk | 5 | True | - | - |
| dpo_candidate_v5 | 7 | Loss vs behavior | 1 | False | loss average signal, fixed prompt behavior, badcase/regression, public-SFT example | - |
| dpo_candidate_v5 | 8 | Interview data pipeline | 5 | True | - | - |
| dpo_naive_v6 | 1 | LoRA definition | 5 | True | - | - |
| dpo_naive_v6 | 2 | SFT and LoRA relation | 4 | True | - | - |
| dpo_naive_v6 | 3 | DPO vs SFT | 4 | True | - | - |
| dpo_naive_v6 | 4 | Public-SFT motivation | 4 | True | - | - |
| dpo_naive_v6 | 5 | Data pipeline | 5 | True | - | - |
| dpo_naive_v6 | 6 | DPO VRAM risk | 5 | True | - | - |
| dpo_naive_v6 | 7 | Loss vs behavior | 2 | False | loss average signal, fixed prompt behavior, badcase/regression | - |
| dpo_naive_v6 | 8 | Interview data pipeline | 5 | True | - | - |
| dpo_v7_stage5h | 1 | LoRA definition | 5 | True | - | - |
| dpo_v7_stage5h | 2 | SFT and LoRA relation | 4 | True | - | - |
| dpo_v7_stage5h | 3 | DPO vs SFT | 4 | True | - | - |
| dpo_v7_stage5h | 4 | Public-SFT motivation | 4 | True | - | - |
| dpo_v7_stage5h | 5 | Data pipeline | 5 | True | - | - |
| dpo_v7_stage5h | 6 | DPO VRAM risk | 4 | True | small batch/short length | - |
| dpo_v7_stage5h | 7 | Loss vs behavior | 2 | False | loss average signal, not sufficient, badcase/regression | - |
| dpo_v7_stage5h | 8 | Interview data pipeline | 5 | True | - | - |
| stage5k_sft_repair | 1 | LoRA definition | 5 | True | - | - |
| stage5k_sft_repair | 2 | SFT and LoRA relation | 4 | True | - | - |
| stage5k_sft_repair | 3 | DPO vs SFT | 4 | True | - | - |
| stage5k_sft_repair | 4 | Public-SFT motivation | 4 | True | - | - |
| stage5k_sft_repair | 5 | Data pipeline | 5 | True | - | - |
| stage5k_sft_repair | 6 | DPO VRAM risk | 4 | True | small batch/short length | - |
| stage5k_sft_repair | 7 | Loss vs behavior | 2 | False | loss average signal, not sufficient, badcase/regression | - |
| stage5k_sft_repair | 8 | Interview data pipeline | 5 | True | - | - |
| dpo_v8_stage5m | 1 | LoRA definition | 5 | True | - | - |
| dpo_v8_stage5m | 2 | SFT and LoRA relation | 4 | True | - | - |
| dpo_v8_stage5m | 3 | DPO vs SFT | 4 | True | - | - |
| dpo_v8_stage5m | 4 | Public-SFT motivation | 4 | True | - | - |
| dpo_v8_stage5m | 5 | Data pipeline | 5 | True | - | - |
| dpo_v8_stage5m | 6 | DPO VRAM risk | 4 | True | small batch/short length | - |
| dpo_v8_stage5m | 7 | Loss vs behavior | 3 | False | not sufficient, badcase/regression | - |
| dpo_v8_stage5m | 8 | Interview data pipeline | 5 | True | - | - |
| stage5n_prompt7_micro_sft | 1 | LoRA definition | 5 | True | - | - |
| stage5n_prompt7_micro_sft | 2 | SFT and LoRA relation | 4 | True | - | - |
| stage5n_prompt7_micro_sft | 3 | DPO vs SFT | 4 | True | - | - |
| stage5n_prompt7_micro_sft | 4 | Public-SFT motivation | 4 | True | - | - |
| stage5n_prompt7_micro_sft | 5 | Data pipeline | 5 | True | - | - |
| stage5n_prompt7_micro_sft | 6 | DPO VRAM risk | 4 | True | small batch/short length | - |
| stage5n_prompt7_micro_sft | 7 | Loss vs behavior | 3 | False | not sufficient, badcase/regression | - |
| stage5n_prompt7_micro_sft | 8 | Interview data pipeline | 5 | True | - | - |
| stage5o_prompt7_exact_sft | 1 | LoRA definition | 5 | True | - | - |
| stage5o_prompt7_exact_sft | 2 | SFT and LoRA relation | 4 | True | - | - |
| stage5o_prompt7_exact_sft | 3 | DPO vs SFT | 4 | True | - | - |
| stage5o_prompt7_exact_sft | 4 | Public-SFT motivation | 4 | True | - | - |
| stage5o_prompt7_exact_sft | 5 | Data pipeline | 5 | True | - | - |
| stage5o_prompt7_exact_sft | 6 | DPO VRAM risk | 4 | True | small batch/short length | - |
| stage5o_prompt7_exact_sft | 7 | Loss vs behavior | 3 | False | not sufficient, badcase/regression | - |
| stage5o_prompt7_exact_sft | 8 | Interview data pipeline | 5 | True | - | - |
| stage5p_prompt7_balanced_sft | 1 | LoRA definition | 5 | True | - | - |
| stage5p_prompt7_balanced_sft | 2 | SFT and LoRA relation | 4 | True | - | - |
| stage5p_prompt7_balanced_sft | 3 | DPO vs SFT | 4 | True | - | - |
| stage5p_prompt7_balanced_sft | 4 | Public-SFT motivation | 4 | True | - | - |
| stage5p_prompt7_balanced_sft | 5 | Data pipeline | 5 | True | - | - |
| stage5p_prompt7_balanced_sft | 6 | DPO VRAM risk | 4 | True | small batch/short length | - |
| stage5p_prompt7_balanced_sft | 7 | Loss vs behavior | 3 | False | not sufficient, badcase/regression | - |
| stage5p_prompt7_balanced_sft | 8 | Interview data pipeline | 5 | True | - | - |

## Decision

The structured scores support the manual Stage 5 decision:

- DPO-tiny v1 and v2 preserved several prompts, but both failed the
  public-SFT motivation and loss-vs-behavior gates.
- DPO-tiny v3 pushed harder but introduced broad regressions.
- Candidate-derived v4 recovered stability relative to v3 but still failed
  public-SFT motivation and loss-vs-behavior.
- Focused candidate v5 did not fix those two gates and weakened the
  loss-vs-behavior answer again.
- Larger naive v6 is the best DPO candidate so far at 7 / 8 prompts. It fixed
  public-SFT motivation, but still failed the core loss-vs-behavior gate.
- Stage 5H/5J/5M showed that larger prompt-7 preference data and exact-failure
  DPO-on-DPO repair can improve wording but still did not pass prompt 7.
- Stage 5K direct SFT repair is rejected because it regressed older prompts.
- Stage 5N stayed stable at 7 / 8 but still missed prompt 7; Stage 5O passed
  prompt 7 only by regressing older prompts; Stage 5P did not find a stable
  middle point.
- No DPO or SFT repair adapter has fully passed the fixed-prompt gate yet.
- Further training expansion remains blocked until prompt 7 can pass without
  old-prompt regression.

Recommended checkpoint remains:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```
