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

- `custom_sft_train.jsonl`: 119 rows
- `custom_sft_eval.jsonl`: 13 rows
- Token check before truncation: max train length 486, max eval length 238
- This is the revised Stage 2B dataset used for Stage 3B custom LoRA SFT.
