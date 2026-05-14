# Stage 2 SFT Data Report

Date: 2026-05-14

## Goal

Prepare a small real Chinese instruction-tuning dataset for the first meaningful
Qwen2.5-0.5B-Instruct LoRA SFT run.

This is Stage 2A, the public dataset baseline. It is not the end of the data
work. The next data milestone after the public-data SFT run is Stage 2B:
self-collected data crawling, cleaning, filtering, instruction conversion, and
custom or mixed-data SFT.

## Dataset

- Source: `llm-wizard/alpaca-gpt4-data-zh`
- Format: Alpaca-style `instruction`, optional `input`, and `output`
- Full source split size: 48,818 rows
- Local raw snapshot: `data/raw/alpaca_gpt4_data_zh_1200.jsonl`
- Sampling: 1,200 rows, shuffled with seed `42`

## Commands

```powershell
$env:HF_HOME=(Resolve-Path -LiteralPath ".hf_cache").Path
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"

D:\conda-envs\qwen-lora-local\python.exe scripts\download_hf_sft_data.py `
  --dataset_name llm-wizard/alpaca-gpt4-data-zh `
  --split train `
  --output_file data\raw\alpaca_gpt4_data_zh_1200.jsonl `
  --max_samples 1200 `
  --seed 42

D:\conda-envs\qwen-lora-local\python.exe scripts\prepare_data.py `
  --input_file data\raw\alpaca_gpt4_data_zh_1200.jsonl `
  --train_file data\processed\sft_train.jsonl `
  --eval_file data\processed\sft_eval.jsonl `
  --eval_ratio 0.1 `
  --max_samples 1200 `
  --min_answer_chars 20 `
  --seed 42
```

## Conversion Result

- Raw samples loaded: 1,200
- Valid converted samples: 1,114
- Train samples: 1,003
- Eval samples: 111
- Dropped samples: 86
- Duplicate prompts: 0
- Output format: Qwen chat JSONL with `system`, `user`, `assistant`

## Validation

Basic JSONL validation:

- `data/processed/sft_train.jsonl`: 1,003 rows, 1,003 unique prompts
- `data/processed/sft_eval.jsonl`: 111 rows, 111 unique prompts
- Role order check: all rows use `system -> user -> assistant`

Assistant answer character lengths:

| Split | Min | Avg | Max |
|---|---:|---:|---:|
| Train | 20 | 231.0 | 982 |
| Eval | 20 | 244.1 | 1760 |

Qwen tokenizer length check before training truncation:

| Split | Min | Avg | P95 | Max | Over 512 |
|---|---:|---:|---:|---:|---:|
| Train | 47 | 177.5 | 314 | 531 | 2 |
| Eval | 50 | 179.2 | 319 | 555 | 1 |

The processed files were also loaded through `ChatSFTDataset` with
`max_length=512` and encoded successfully.

## Next Step

Run Stage 3A, the first real LoRA SFT training on public data:

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

After Stage 3A and the base-vs-public-SFT comparison are complete, continue
with `reports/data_pipeline_plan.md` and build the self-collected data pipeline.
