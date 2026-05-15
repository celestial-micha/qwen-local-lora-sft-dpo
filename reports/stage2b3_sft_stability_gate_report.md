# Stage 2B.3 SFT Stability Gate Report

Date: 2026-05-15

## Goal

Stage 2B.2 left one main weak prompt:

```text
为什么不能只看 loss 判断一次 SFT 是否成功？
```

Stage 2B.3 tried to patch this prompt before DPO. The rule for this stage was:

```text
fix the loss-vs-behavior badcase
  -> preserve the seven prompts already working
  -> stop before DPO and review with the user
```

## Data Changes

Script updated:

```text
scripts/prepare_custom_technical_data.py
```

Main changes:

- Added `stage2b3_loss_behavior_samples()`.
- Added 10 loss-vs-behavior samples.
- Added 7 replay samples for the prompts that v3 already answered well.
- Forced `targeted_technical_qa`, `badcase_patch_stage2b2`,
  `loss_behavior_patch_stage2b3`, and `replay_stage2b3` samples into train
  rather than random eval.
- Added optional focused patch export:
  `--stage2b3_patch_train_file`.
- Added `--stage2b3_loss_repeats` so the exact remaining badcase can be repeated
  in a tiny patch file.

Regeneration command:

```powershell
D:\conda-envs\qwen-lora-local\python.exe scripts\prepare_custom_technical_data.py `
  --raw_sources_file data\raw\custom_sources.jsonl `
  --cleaned_chunks_file data\raw\custom_cleaned_chunks.jsonl `
  --instruction_seed_file data\raw\custom_instruction_seed.jsonl `
  --train_file data\processed\custom_sft_train.jsonl `
  --eval_file data\processed\custom_sft_eval.jsonl `
  --stage2b3_patch_train_file data\processed\custom_sft_stage2b3_patch_train.jsonl `
  --stage2b3_loss_repeats 12 `
  --eval_ratio 0.1 `
  --max_doc_samples 20 `
  --seed 42
```

Current Stage 2B.3 data:

```text
Sources: 10
Accepted cleaned chunks: 96
Rejected chunks: 12
Instruction samples: 157
Train samples: 142
Eval samples: 15
Stage 2B.3 focused patch train samples: 28
Duplicate instruction samples: 0
```

Token validation before truncation:

| Split | Rows | Unique Prompts | Duplicate Prompts | Min | Avg | P95 | Max | Over 512 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Train | 142 | 134 | 8 | 111 | 160.6 | 267 | 323 | 0 |
| Eval | 15 | 15 | 0 | 120 | 166.7 | 276 | 291 | 0 |

The duplicate train prompts are intentional replay and exact-badcase repeats.

## Training Attempts

### Attempt 1: v4 Full Dataset Continuation

Output:

```text
outputs/sft_lora_qwen05b_custom_v4_stage2b3_loss_patch
```

Command summary:

```text
init adapter: outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
train file: data/processed/custom_sft_train.jsonl
lr: 3e-5
epochs: 2
grad_accum: 4
```

Result:

```text
Runtime: 244.2 seconds
Final train loss: 0.5474
Eval loss at epoch 0.85: 0.0160
Eval loss at epoch 1.69: 0.0173
Comparison: reports/compare_outputs_three_way_custom_v4_stage2b3_loss_patch.jsonl
```

Behavior finding:

- Preserved most old behavior.
- The loss-vs-behavior prompt was still weak.
- The public-SFT motivation prompt became wordier and slightly regressed.
- Not recommended as the DPO-start adapter.

### Attempt 2: v5 Focused Patch

Output:

```text
outputs/sft_lora_qwen05b_custom_v5_stage2b3_focused_patch
```

Command summary:

```text
init adapter: outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
train file: data/processed/custom_sft_stage2b3_patch_train.jsonl
patch rows: 28
exact loss prompt repeats: 12
lr: 8e-5
epochs: 4
grad_accum: 1
```

Result:

```text
Runtime: 120.2 seconds
Final train loss: 1.2324
Best observed eval loss: 0.0997
Comparison: reports/compare_outputs_three_way_custom_v5_stage2b3_focused_patch.jsonl
```

Behavior finding:

- The exact loss-vs-behavior prompt was finally answered correctly.
- But several previously stable prompts regressed badly.
- This proves the patch was too strong and overfit the focused data.
- Not recommended as the DPO-start adapter.

### Attempt 3: v6 Balanced Focused Patch

Output:

```text
outputs/sft_lora_qwen05b_custom_v6_stage2b3_balanced_patch
```

Command summary:

```text
init adapter: outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
train file: data/processed/custom_sft_stage2b3_patch_train.jsonl
lr: 3e-5
epochs: 1
grad_accum: 1
```

Result:

```text
Runtime: 23.3 seconds
Final train loss: 3.1996
Comparison: reports/compare_outputs_three_way_custom_v6_stage2b3_balanced_patch.jsonl
```

Behavior finding:

- This was less aggressive than v5 but still destabilized multiple prompts.
- The loss-vs-behavior answer improved in topic but remained confused.
- Not recommended as the DPO-start adapter.

### Attempt 4: Adapter Interpolation Probe

Script added:

```text
scripts/interpolate_lora_adapters.py
```

Idea:

```text
stable v3 adapter + small alpha of overfit v5 adapter
```

Tested local outputs:

```text
outputs/sft_lora_qwen05b_custom_v7_stage2b3_interp_alpha015
outputs/sft_lora_qwen05b_custom_v7_stage2b3_interp_alpha025
outputs/sft_lora_qwen05b_custom_v7_stage2b3_interp_alpha040
```

Spot-check result:

- Alpha 0.15 and 0.25 did not fix the loss-vs-behavior prompt.
- Alpha 0.40 also stayed confused.
- No full comparison was run because the spot-check already failed the primary
  gate.
- Not recommended.

## Current Best Adapter

The best current local adapter remains:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

Reason:

- It preserves or improves 7 of 8 fixed prompts.
- Later attempts either failed to fix the final badcase or fixed it by breaking
  other prompts.
- This is the safest adapter for review and possible future DPO planning, but
  it is not a perfect SFT endpoint.

## DPO Gate Decision

Do not use v4/v5/v6 as the DPO start adapter.

The Stage 5 start adapter is:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

Stage 5 is split in `reports/stage5_dpo_plan.md`:

- Stage 5A: prepare a 20-50 pair tiny DPO dataset.
- Stage 5B: run a tiny DPO smoke test and record VRAM/RAM behavior.
- Stage 5C: compare fixed prompts after tiny DPO.
- Stage 5D: only then consider larger or more naive DPO.

## Likely Causes And Future Fixes

v4 likely failed because the new loss-vs-behavior signal was diluted inside the
full dataset. It was cautious enough to preserve most old behavior, but too weak
to reliably move the final badcase.

v5 likely failed because the focused patch over-weighted one prompt. It taught
the exact loss answer, but the tiny and repeated patch shifted the adapter enough
to damage neighboring concepts.

v6 likely failed because lower LR/epochs reduced the damage but did not change
the narrow direction of the update. The patch was still too small and too
specialized.

Future fixes:

- Use DPO pairs where the rejected answer looks like the actual v3/v4 failure
  and the chosen answer is the desired loss-vs-behavior explanation.
- Keep replay preference pairs for the seven stable prompts.
- Treat tiny DPO as a memory and behavior probe, not a final model-quality run.
- If DPO still regresses, return to a broader SFT replay dataset or consider
  that Qwen2.5-0.5B may be hitting a small-model ceiling for this meta prompt.

## Main Lesson

The strongest lesson from Stage 2B.3 is:

```text
SFT stability is not just "can I fix one badcase?"
SFT stability is "can I fix that badcase without regressing the existing suite?"
```

This is a useful interview point. It shows why fixed-prompt regression tests,
replay samples, and DPO gates matter in a real fine-tuning workflow.
