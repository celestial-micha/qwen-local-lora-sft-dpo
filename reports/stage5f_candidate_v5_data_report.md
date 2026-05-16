# Stage 5F Candidate DPO v5 Data Report

Date: 2026-05-16

## Scope

Stage 5F keeps the v4 candidate-derived data and adds a narrow repair set for
the two v4 behavior failures:

- prompt 4: public-SFT motivation
- prompt 7: loss-vs-behavior

## Outputs

```text
data/processed/dpo_candidate_v5_train.jsonl
data/processed/dpo_candidate_v5_eval.jsonl
```

## Dataset Summary

- Base candidate train rows: 20
- Added focused rows: 8
- Total v5 train rows: 28
- Eval rows: 7
- Train prompt length min/avg/max chars: 18 / 33.2 / 63
- Train chosen length min/avg/max chars: 68 / 138.9 / 191
- Train rejected length min/avg/max chars: 43 / 112.2 / 253

## Train Sources

| Source Type | Rows |
|---|---:|
| `curated_guardrail` | 8 |
| `custom_sft_known_gap_vs_curated` | 1 |
| `failed_candidate_vs_curated` | 3 |
| `failed_candidate_vs_custom_sft` | 8 |
| `v4_exact_failure_focus` | 2 |
| `v4_near_miss_focus` | 6 |

## Decision Rule

Stage 5B.5 should still remain a tiny DPO retry. If prompt 4 or prompt 7 still
fails, or if old prompt stability regresses, Stage 5D larger DPO remains
blocked.
