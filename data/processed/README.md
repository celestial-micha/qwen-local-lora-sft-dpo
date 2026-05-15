# Processed Data

Processed files will be generated here.

Planned files:

- `sft_train.jsonl`
- `sft_eval.jsonl`
- `dpo_train.jsonl`

Current Stage 2 SFT files:

- `sft_train.jsonl`: 1,003 rows
- `sft_eval.jsonl`: 111 rows
- Format: Qwen chat JSONL with `system`, `user`, and `assistant` messages

Planned Stage 2B custom-data files:

- `custom_sft_train.jsonl`
- `custom_sft_eval.jsonl`
- optional `mixed_sft_train.jsonl`
- optional `mixed_sft_eval.jsonl`

Current Stage 2B custom-data files:

- `custom_sft_train.jsonl`: 142 rows
- `custom_sft_eval.jsonl`: 15 rows
- `custom_sft_stage2b3_patch_train.jsonl`: 28 rows
- Token check before truncation: max train length 323, max eval length 291
- This is the Stage 2B.3 dataset used for the DPO-before SFT stability gate.
  The current best local adapter remains
  `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`; v4/v5/v6 patch attempts
  are documented but not recommended.
