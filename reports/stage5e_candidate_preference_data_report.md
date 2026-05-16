# Stage 5E Candidate Preference Data Report

Date: 2026-05-16

## Scope

This data step prepares a smaller Stage 5 DPO retry based on actual failed
candidate outputs from:

```text
reports/compare_outputs_four_way_dpo_tiny.jsonl
reports/compare_outputs_four_way_dpo_tiny_v2.jsonl
reports/compare_outputs_four_way_dpo_tiny_v3.jsonl
```

The goal is to teach against concrete failures, while preserving the current
recommended SFT adapter as the DPO starting point:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

## Outputs

```text
data/processed/dpo_candidate_train.jsonl
data/processed/dpo_candidate_eval.jsonl
```

## Dataset Summary

- Train rows: 20
- Eval rows: 5
- Train unique prompts: 15
- Train prompt length min/avg/max chars: 18 / 32.3 / 63
- Train chosen length min/avg/max chars: 68 / 133.8 / 191
- Train rejected length min/avg/max chars: 43 / 122.9 / 253

## Train Sources

| Source Type | Rows |
|---|---:|
| `curated_guardrail` | 8 |
| `custom_sft_known_gap_vs_curated` | 1 |
| `failed_candidate_vs_curated` | 3 |
| `failed_candidate_vs_custom_sft` | 8 |

## Design Notes

- Failed DPO v1/v2/v3 outputs become rejected answers directly.
- Passing custom-SFT v3 answers are used as chosen answers where they already
  pass the structured gate.
- The known custom-SFT v3 loss-vs-behavior gap uses a curated chosen answer.
- Held-out eval pairs cover public-SFT motivation, loss-vs-behavior, DPO smoke
  interpretation, LoRA definition, and data-source metadata.

Next step: run Stage 5B.4 with an eval split and keep it blocked unless the
behavior comparison improves without broad regressions.
