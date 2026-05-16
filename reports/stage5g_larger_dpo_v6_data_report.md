# Stage 5G Larger DPO v6 Data Report

Date: 2026-05-16

## Scope

Stage 5G prepares a larger preference dataset for a more naive DPO probe with a
separate reference model. It keeps replay coverage for all fixed-prompt topics
instead of only repeating the two stubborn prompts.

## Outputs

```text
data/processed/dpo_larger_v6_train.jsonl
data/processed/dpo_larger_v6_eval.jsonl
```

## Dataset Summary

- Train rows: 192
- Eval rows: 24
- Train prompt length min/avg/max chars: 17 / 30.6 / 63
- Train chosen length min/avg/max chars: 68 / 118.2 / 191
- Train rejected length min/avg/max chars: 23 / 54.2 / 253

## Train Sources

| Source Type | Rows |
|---|---:|
| `base:dpo_tiny_train.jsonl` | 16 |
| `base:dpo_tiny_v2_train.jsonl` | 14 |
| `base:dpo_tiny_v3_train.jsonl` | 10 |
| `curated_guardrail` | 8 |
| `custom_sft_known_gap_vs_curated` | 1 |
| `failed_candidate_vs_curated` | 3 |
| `failed_candidate_vs_custom_sft` | 8 |
| `generated_data_pipeline` | 16 |
| `generated_dpo_vram` | 16 |
| `generated_dpo_vs_sft` | 16 |
| `generated_interview_narrative` | 16 |
| `generated_lora_definition` | 15 |
| `generated_loss_vs_behavior` | 15 |
| `generated_public_sft_motivation` | 15 |
| `generated_sft_lora_relation` | 15 |
| `v4_exact_failure_focus` | 2 |
| `v4_near_miss_focus` | 6 |

## Design

- Reuses previous tiny DPO and candidate-derived preference rows.
- Adds balanced generated replay rows for eight topics:
  LoRA definition, SFT/LoRA relation, DPO/SFT distinction, public-SFT
  motivation, data pipeline, DPO VRAM risk, loss-vs-behavior, and interview
  narrative.
- Holds out a separate eval split so preference metrics are not only training
  set metrics.
