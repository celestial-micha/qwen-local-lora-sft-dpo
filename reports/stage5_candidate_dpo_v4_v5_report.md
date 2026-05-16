# Stage 5 Candidate DPO v4/v5 Report

Date: 2026-05-16

## Scope

This report records the follow-up Stage 5 candidate-derived DPO loop after the
initial tiny DPO v1/v2/v3 runs failed the behavior gate.

The starting adapter for both v4 and v5 remained:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

No DPO run was chained on top of a previous DPO adapter.

## Artifacts

```text
scripts/prepare_candidate_dpo_data.py
scripts/prepare_candidate_dpo_v5_data.py
configs/dpo_qwen05b_v4.yaml
configs/dpo_qwen05b_v5.yaml
data/processed/dpo_candidate_train.jsonl
data/processed/dpo_candidate_eval.jsonl
data/processed/dpo_candidate_v5_train.jsonl
data/processed/dpo_candidate_v5_eval.jsonl
reports/compare_outputs_four_way_dpo_candidate_v4.jsonl
reports/compare_outputs_four_way_dpo_candidate_v5.jsonl
reports/stage5e_candidate_preference_data_report.md
reports/stage5f_candidate_v5_data_report.md
```

Output adapters:

```text
outputs/dpo_lora_qwen05b_candidate_v4
outputs/dpo_lora_qwen05b_candidate_v5
```

The `outputs/` directory is intentionally git-ignored, so these adapters are
local experiment artifacts.

## Training Summary

| Run | Train / Eval Rows | Optimizer Steps | Runtime | Train Loss | Final Eval Loss | Final Eval Acc | Max Allocated VRAM | Max Reserved VRAM | Reload |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| candidate v4 | 20 / 5 | 2 | 28.0s | 5.5017 | 0.4630 | 0.8000 | 2.456 GB | 3.377 GB | passed |
| candidate v5 | 28 / 7 | 7 | 49.7s | 5.8422 | 0.2693 | 0.8571 | 2.486 GB | 5.033 GB | passed |

No CUDA OOM, Windows native crash, or unusable shared-memory fallback was
observed.

## Behavior Score Summary

The structured scoring script was rerun across v1/v2/v3/v4/v5:

```text
scripts/score_fixed_prompt_outputs.py
reports/stage5_structured_behavior_score_report.md
reports/stage5_structured_behavior_scores.jsonl
reports/stage5_structured_behavior_scores.csv
```

| Run | DPO Variant Passed Prompts | Total Score | Failed Areas |
|---|---:|---:|---|
| dpo_tiny_v1 | 6 / 8 | 32 | prompt 4 public-SFT motivation; prompt 7 loss-vs-behavior |
| dpo_tiny_v2 | 6 / 8 | 34 | prompt 4 public-SFT motivation; prompt 7 loss-vs-behavior |
| dpo_tiny_v3 | 1 / 8 | 4 | broad regressions |
| dpo_candidate_v4 | 6 / 8 | 33 | prompt 4 public-SFT motivation; prompt 7 loss-vs-behavior |
| dpo_candidate_v5 | 6 / 8 | 31 | prompt 4 public-SFT motivation; prompt 7 loss-vs-behavior |

Candidate v4 improved stability relative to v3, but did not pass the two target
gates. Candidate v5 added exact v4 failures and focused variants, but still
failed the same two gates and made the loss-vs-behavior answer weaker.

## Decision

Stage 5D larger DPO remains blocked.

The hardware result is good: this RTX 4060 Laptop GPU can run these tiny DPO
jobs comfortably. The behavior result is not good enough: preference loss and
eval accuracy improved, but fixed-prompt behavior did not pass.

The recommended checkpoint remains:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

The next useful research direction is not "more DPO steps" on the same tiny
preference set. It should be either:

- redesign the preference/evaluation set around more varied held-out prompts,
  or
- improve the SFT data for the two stubborn concepts before another DPO loop.
