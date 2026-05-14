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
