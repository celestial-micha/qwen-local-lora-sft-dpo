# Data Pipeline Plan

Date: 2026-05-14

## Project Story

The project should not stop at downloading one public dataset. The stronger
interview story is a two-loop plan:

```text
Loop A: public instruction dataset
  -> convert
  -> train LoRA SFT
  -> compare base vs SFT
  -> prove the training pipeline is stable

Loop B: self-collected data
  -> crawl or collect preferred content
  -> clean and filter
  -> rewrite into instruction-answer samples
  -> train or continue-train LoRA SFT
  -> compare against Loop A
```

This order is intentional. The public dataset loop keeps the first real SFT run
controlled and reproducible. After that, the custom data loop becomes a data
engineering and model-behavior improvement story, rather than a debugging mess
where training bugs and dirty data are mixed together.

## Current Decision

Use the current `llm-wizard/alpaca-gpt4-data-zh` dataset as the first real SFT
baseline. Do not discard it.

The public-data LoRA SFT adapter has now been trained, loaded, and compared.
Stage 4A showed that it did not fix LoRA/SFT/DPO concept confusion. Next, add
the self-collected technical-data pipeline.

Terminology note:

- SFT is the supervised fine-tuning objective.
- LoRA is the parameter-efficient method used to train adapters.
- The current and next adapters are LoRA SFT adapters.

## Target Final Pipeline

```text
Stage 0: project scaffold and environment
Stage 1: base inference and demo smoke test
Stage 2A: public SFT dataset baseline
Stage 3A: real LoRA SFT on public data
Stage 4A: base vs public-SFT comparison
Stage 2B: self-collected data crawling and cleaning
Stage 3B: LoRA SFT using custom or mixed data
Stage 4B: compare base vs public-SFT vs custom-SFT
Stage 5: DPO after SFT behavior is stable
Stage 6: interview package
```

## Stage 2A: Public Dataset Baseline

Status: completed.

Purpose:

- Prove that data conversion, tokenization, training, saving, and loading work
  on a real dataset.
- Keep data quality and format risk low.
- Create a baseline adapter for later comparison.

Current artifacts:

- Raw: `data/raw/alpaca_gpt4_data_zh_1200.jsonl`
- Train: `data/processed/sft_train.jsonl`
- Eval: `data/processed/sft_eval.jsonl`
- Report: `reports/stage2_sft_data_report.md`

## Stage 3A: Public Dataset SFT

Status: completed.

Goal:

- Train `outputs/sft_lora_qwen05b_public`.
- Record train loss, eval loss, training time, and any memory issues.
- Run fixed prompts through both base and SFT adapter.

Result:

- Adapter: `outputs/sft_lora_qwen05b_public`
- Final train loss: 1.7558
- Eval loss at step 100: 1.8263
- Report: `reports/stage3a_public_lora_sft_report.md`

Key finding:

- General public instruction data did not fix LoRA/SFT/DPO technical concept
  confusion. This makes Stage 2B necessary, not optional.

Recommended command:

```powershell
D:\conda-envs\qwen-lora-local\python.exe scripts\train_sft_lora.py `
  --train_file data\processed\sft_train.jsonl `
  --eval_file data\processed\sft_eval.jsonl `
  --output_dir outputs\sft_lora_qwen05b_public `
  --max_length 512 `
  --batch_size 1 `
  --grad_accum 8 `
  --epochs 1 `
  --logging_steps 10 `
  --eval_steps 100 `
  --save_steps 100 `
  --report_to none `
  --local_files_only
```

## Stage 4A: Public-SFT Comparison

Status: completed.

Artifacts:

- `reports/compare_outputs_public_sft.jsonl`
- `reports/compare_base_sft.md`
- `reports/stage4a_public_sft_comparison_report.md`

Finding:

- The public-data adapter did not fix the project-specific LoRA/SFT/DPO concept
  mistakes.
- This is useful negative evidence. It shows why a targeted custom technical
  dataset is necessary.

## Stage 2B: Self-Collected Data Pipeline

Next immediate task.

Purpose:

- Demonstrate real data work: collection, cleaning, filtering, formatting, and
  dataset versioning.
- Build a small dataset that reflects the user's preferred topics and answer
  style.
- Avoid pretending that model tuning is only `load_dataset(...)`.

Suggested first scope:

- 100 to 300 cleaned samples for the first custom-data pass.
- Chinese technical learning content is a good first topic because it matches
  this project: LoRA, SFT, DPO, model training, CUDA, Hugging Face, debugging,
  and experiment reporting.
- Avoid copyrighted full-text book/article replication. Prefer short excerpts,
  public documentation, own notes, permissive sources, or manually written
  summaries.

Planned raw files:

- `data/raw/custom_sources.jsonl`: one source document or crawled page per row
- `data/raw/custom_cleaned_chunks.jsonl`: cleaned and deduplicated text chunks
- `data/raw/custom_instruction_seed.jsonl`: candidate instruction-answer rows

Planned processed files:

- `data/processed/custom_sft_train.jsonl`
- `data/processed/custom_sft_eval.jsonl`
- optional mixed dataset: `data/processed/mixed_sft_train.jsonl`

## Cleaning Rules

Minimum cleaning checklist:

- Remove navigation bars, ads, cookie banners, repeated footers, and boilerplate.
- Normalize whitespace and punctuation.
- Drop very short chunks and very long chunks.
- Deduplicate exact and near-duplicate text.
- Keep source URL or source note for traceability.
- Filter unsafe, low-quality, spam-like, or off-topic content.
- Convert only useful content into instruction-answer pairs.
- Keep a small manual review file of accepted and rejected examples.

## Custom Instruction Formats

The custom dataset should not be only raw scraped text. Convert it into tasks
that teach the target behavior:

```json
{
  "instruction": "用三点解释 LoRA 微调为什么适合个人 GPU 学习。",
  "input": "",
  "output": "第一，LoRA 只训练少量 adapter 参数..."
}
```

Good task types:

- Concept explanation
- Step-by-step debugging
- Command explanation
- Experiment-log summarization
- Before/after output analysis
- Beginner-friendly analogy
- Interview-style project explanation

## Comparison Plan

Use the same fixed prompt set across three models:

- Base Qwen
- Public-data SFT adapter
- Custom or mixed-data SFT adapter

The final report should answer:

- Did the public-data SFT improve general instruction following?
- Did custom data improve the target style or topic accuracy?
- Did custom data introduce overfitting, verbosity, or hallucination?
- Which examples became better, worse, or unchanged?

## Interview Talking Points

Short version:

> I first used a public Chinese Alpaca-style dataset to establish a reproducible
> LoRA SFT baseline. After the baseline trained and loaded correctly, I built a
> second data loop for self-collected content: crawling, boilerplate removal,
> deduplication, filtering, converting into instruction-answer pairs, and then
> comparing a custom-data adapter against the public-data adapter.

This tells a better story than simply saying "I downloaded a dataset and
fine-tuned a model."
