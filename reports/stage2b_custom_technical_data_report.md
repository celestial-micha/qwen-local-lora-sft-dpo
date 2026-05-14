# Stage 2B Custom Technical Data Report

Date: 2026-05-14

## Goal

Build the first targeted custom technical SFT dataset for the project.

Stage 4A showed an important negative result: the public-data LoRA SFT adapter
trained successfully, but it still confused LoRA/SFT/DPO with unrelated
concepts. Stage 2B responds to that failure by preparing data focused on:

- LoRA as parameter-efficient fine-tuning
- SFT as supervised fine-tuning
- DPO as direct preference optimization
- public-SFT vs custom-SFT comparison
- data cleaning and instruction-answer conversion
- 8GB VRAM and DPO memory risk
- experiment reporting and interview explanation

## Method

Script:

```text
scripts/prepare_custom_technical_data.py
```

The first Stage 2B pass uses project-owned technical notes and curated concept
seeds. This is deliberate:

- It is reproducible without relying on unstable network access.
- It avoids copying long copyrighted web articles into training data.
- It still exercises the full data pipeline: collect, clean, filter, dedupe,
  rewrite, split, and convert to Qwen chat JSONL.
- The script includes an optional URL input path for future crawling iterations.

## Command

```powershell
D:\conda-envs\qwen-lora-local\python.exe scripts\prepare_custom_technical_data.py `
  --raw_sources_file data\raw\custom_sources.jsonl `
  --cleaned_chunks_file data\raw\custom_cleaned_chunks.jsonl `
  --instruction_seed_file data\raw\custom_instruction_seed.jsonl `
  --train_file data\processed\custom_sft_train.jsonl `
  --eval_file data\processed\custom_sft_eval.jsonl `
  --eval_ratio 0.1 `
  --max_doc_samples 60 `
  --seed 42
```

## Sources

Local project sources used:

- `README.zh-CN.md`
- `PROJECT_RUNBOOK.md`
- `reports/beginner_learning_report_zh.md`
- `reports/data_pipeline_plan.md`
- `reports/stage2_sft_data_report.md`
- `reports/stage3a_public_lora_sft_report.md`
- `reports/stage4a_public_sft_comparison_report.md`
- `reports/vram_and_dpo_plan.md`
- `reports/windows_debug_report.md`
- `reports/project_context_for_next_chat.md`

These sources are self-collected project notes. They record the actual training
process, bad cases, environment debugging, VRAM observations, and next-stage
data strategy.

## Pipeline Result

- Source records: 10
- Accepted cleaned chunks: 81
- Rejected chunks: 9
- Instruction-answer seed samples: 160
- Train samples: 144
- Eval samples: 16
- Duplicate instruction samples: 0

Sample types:

| Type | Count |
|---|---:|
| concept explanation | 25 |
| misconception fix | 25 |
| interview answer | 25 |
| beginner friendly | 25 |
| project record summary | 60 |

## Output Files

Raw and intermediate files:

- `data/raw/custom_sources.jsonl`
- `data/raw/custom_cleaned_chunks.jsonl`
- `data/raw/custom_instruction_seed.jsonl`

Processed training files:

- `data/processed/custom_sft_train.jsonl`
- `data/processed/custom_sft_eval.jsonl`

Fixed future comparison prompts:

- `data/samples/custom_technical_prompts.jsonl`

Note: `data/raw/*` and `data/processed/*` are intentionally ignored by git.
The script and this report make the data reproducible.

## Validation

JSONL validation:

- Train rows: 144
- Eval rows: 16
- Role order: all rows use `system -> user -> assistant`
- Unique prompts: 144 train, 16 eval

Qwen tokenizer length check before truncation:

| Split | Min | Avg | P95 | Max | Over 512 |
|---|---:|---:|---:|---:|---:|
| Train | 117 | 208.4 | 454 | 510 | 0 |
| Eval | 123 | 209.6 | 370 | 391 | 0 |

The processed files were loaded through `ChatSFTDataset` with `max_length=512`
and encoded successfully.

## Why This Dataset Is Different From Public-SFT

The public dataset was broad and general. It proved the engineering pipeline.

The Stage 2B custom dataset is narrow and targeted. It directly trains on the
failure cases observed in Stage 4A:

- explain LoRA correctly
- explain SFT correctly
- explain DPO correctly
- explain why generic public data was not enough
- explain the data-cleaning pipeline
- explain DPO memory constraints on 8GB VRAM

This is the project turning a badcase into a data-improvement loop.

## Next Step

Proceed to Stage 3B:

```text
train custom or mixed LoRA SFT adapter
  -> likely output: outputs/sft_lora_qwen05b_custom
  -> compare with base and public-SFT using data/samples/custom_technical_prompts.jsonl
```

Recommended first Stage 3B training command:

```powershell
D:\conda-envs\qwen-lora-local\python.exe scripts\train_sft_lora.py `
  --train_file data\processed\custom_sft_train.jsonl `
  --eval_file data\processed\custom_sft_eval.jsonl `
  --output_dir outputs\sft_lora_qwen05b_custom `
  --max_length 512 `
  --batch_size 1 `
  --grad_accum 4 `
  --epochs 3 `
  --logging_steps 5 `
  --eval_steps 20 `
  --save_steps 20 `
  --report_to none `
  --local_files_only
```

This custom dataset is small, so `epochs=3` is reasonable for a first experiment.
Watch for overfitting and compare behavior with fixed prompts instead of relying
only on loss.
