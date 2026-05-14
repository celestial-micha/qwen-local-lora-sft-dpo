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

- `custom_sft_train.jsonl`: 144 rows
- `custom_sft_eval.jsonl`: 16 rows
- Token check before truncation: max train length 510, max eval length 391
