# Stage 2B.2 Badcase Patch Report

Date: 2026-05-15

## Goal

Stage 4B left two weak prompts:

- Why public-SFT failure motivates Stage 2B.
- Why loss alone is insufficient to judge SFT success.

Stage 2B.2 adds a small badcase patch and tests whether it can improve those
prompts without breaking the six prompts that custom-SFT v1 already answered
well.

## Data Patch

Script updated:

```text
scripts/prepare_custom_technical_data.py
```

Main change:

- Added `badcase_patch_samples()`.
- Added 8 `badcase_patch_stage2b2` samples.
- The samples focus on public-SFT as an engineering baseline, Stage 4A as
  behavior evaluation, Stage 2B as data improvement, and loss-vs-behavior
  evaluation.

Regeneration command:

```powershell
D:\conda-envs\qwen-lora-local\python.exe scripts\prepare_custom_technical_data.py `
  --raw_sources_file data\raw\custom_sources.jsonl `
  --cleaned_chunks_file data\raw\custom_cleaned_chunks.jsonl `
  --instruction_seed_file data\raw\custom_instruction_seed.jsonl `
  --train_file data\processed\custom_sft_train.jsonl `
  --eval_file data\processed\custom_sft_eval.jsonl `
  --eval_ratio 0.1 `
  --max_doc_samples 20 `
  --seed 42
```

Current Stage 2B.2 data:

```text
Sources: 10
Accepted cleaned chunks: 90
Rejected chunks: 12
Instruction samples: 140
Train samples: 126
Eval samples: 14
Duplicate instruction samples: 0
```

Token validation before truncation:

| Split | Rows | Unique Prompts | Min | Avg | P95 | Max | Over 512 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Train | 126 | 126 | 111 | 161.5 | 273 | 323 | 0 |
| Eval | 14 | 14 | 117 | 170.0 | 247 | 277 | 0 |

## Training Attempts

### Attempt 1: Train v2 From Scratch, 5 Epochs

Output:

```text
outputs/sft_lora_qwen05b_custom_v2
```

Result:

```text
Runtime: 415.5 seconds
Final train loss: 1.0496
Best observed eval loss: 0.8561 at epoch 3.81
Final observed eval loss: 0.8937 at epoch 4.76
```

Comparison:

```text
reports/compare_outputs_three_way_custom_v2.jsonl
```

Finding:

- This adapter regressed on previously solved prompts.
- LoRA and SFT explanations became unstable.
- Not recommended.

### Attempt 2: Train v2 From Scratch, 10 Epochs

Output:

```text
outputs/sft_lora_qwen05b_custom_v2_10ep
```

Result:

```text
Runtime: 776.0 seconds
Final train loss: 0.4931
Best observed eval loss: 0.8614 at epoch 3.17
Later eval loss rose to 1.1130 at epoch 9.52
```

Comparison used the best-eval checkpoint:

```text
outputs/sft_lora_qwen05b_custom_v2_10ep/checkpoint-100
reports/compare_outputs_three_way_custom_v2_checkpoint100.jsonl
```

Finding:

- Lower loss did not fix behavior.
- The checkpoint still regressed on important concept prompts.
- This is strong evidence that small badcase patches should not be retrained
  from scratch without replaying or preserving previous good behavior.

### Attempt 3: Continue From v1 With Low Learning Rate

Training script update:

```text
scripts/train_sft_lora.py --init_adapter_path
```

Output:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

Command:

```powershell
D:\conda-envs\qwen-lora-local\python.exe scripts\train_sft_lora.py `
  --init_adapter_path outputs\sft_lora_qwen05b_custom `
  --train_file data\processed\custom_sft_train.jsonl `
  --eval_file data\processed\custom_sft_eval.jsonl `
  --output_dir outputs\sft_lora_qwen05b_custom_v3_from_v1_patch `
  --max_length 512 `
  --batch_size 1 `
  --grad_accum 4 `
  --epochs 2 `
  --lr 5e-5 `
  --logging_steps 10 `
  --eval_steps 30 `
  --save_steps 30 `
  --report_to none `
  --local_files_only
```

Result:

```text
Runtime: 157.5 seconds
Final train loss: 0.2873
Eval loss at epoch 0.95: 0.0371
Eval loss at epoch 1.90: 0.0348
```

The eval set is tiny, so fixed-prompt behavior remains the real judge.

Comparison:

```text
reports/compare_outputs_three_way_custom_v3_from_v1_patch.jsonl
```

Behavior summary:

| Prompt | Result |
|---|---|
| LoRA concept | Correct |
| SFT and LoRA relation | Correct |
| DPO vs SFT | Correct |
| Why public-SFT failure motivates Stage 2B | Improved; concise but correct direction |
| Custom data pipeline | Correct |
| 8GB DPO memory risk | Correct |
| Why loss alone is insufficient | Still weak |
| Interview data pipeline | Correct |

Overall:

```text
v3 improves or preserves 7 / 8 prompts.
Prompt 7 remains the next badcase.
```

## Main Lesson

The most important lesson is not just "add more data." It is:

```text
small data patches can cause regressions if retrained from scratch
```

The safer strategy was:

```text
start from the best existing adapter
  -> use a lower learning rate
  -> train briefly
  -> run the same fixed-prompt regression suite
```

This is a stronger interview story than claiming every patch immediately works.

## Current Recommendation

Use v3 as the current local custom adapter for learning and comparison:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

Do not start DPO yet. The next useful step is a focused Stage 2B.3 patch for
loss-vs-behavior explanation, ideally with replay samples for the seven prompts
that are already good.
