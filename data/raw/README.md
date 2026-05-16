# Raw Data

Raw downloaded or manually prepared data goes here.

For the first SFT experiment, use a small Alpaca-style instruction dataset and
convert it into chat format.

Current Stage 2 raw snapshot:

- `alpaca_gpt4_data_zh_1200.jsonl`
- Source: `llm-wizard/alpaca-gpt4-data-zh`
- Rows: 1,200
- Seed: 42

Planned Stage 2B custom-data raw files:

- `custom_sources.jsonl`: crawled or manually collected source records
- `custom_cleaned_chunks.jsonl`: cleaned, deduplicated text chunks
- `custom_instruction_seed.jsonl`: candidate instruction-answer samples before final conversion

Current Stage 2B local custom-data snapshot:

- `custom_sources.jsonl`: 10 self-collected project-note sources
- `custom_cleaned_chunks.jsonl`: 96 accepted cleaned chunks
- `custom_instruction_seed.jsonl`: 157 targeted instruction-answer seed samples
- Note: the first Stage 2B pass produced 160 seed samples, but Stage 3B showed
  it was too noisy. The current snapshot is the revised version with fewer
  generic project-record samples, more direct targeted QA samples, and the
  Stage 2B.2/2B.3 badcase patches.

Final project update:

- The raw/custom data loop supported the final accepted SFT checkpoint:
  `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`.
- Later DPO and repair datasets live under `data/processed/`.
- The best DPO artifact is `outputs/dpo_lora_qwen05b_naive_v6`, but it is not
  the default recommended checkpoint.
- Final summary entry points:
  `reports/final_project_summary_zh.md` and
  `reports/stage6_final_interview_package.md`.
