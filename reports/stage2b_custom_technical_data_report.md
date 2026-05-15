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
  --max_doc_samples 20 `
  --seed 42
```

Note: the first generated dataset used `--max_doc_samples 60` and produced 160
instruction samples. Stage 3B showed that this version was too noisy: the custom
adapter trained successfully, but still hallucinated and sometimes copied
project-record wording. The dataset was revised to 132 samples, Stage 2B.2
added 8 focused badcase samples, and Stage 2B.3 added loss-vs-behavior plus
replay samples. The current generated dataset has 157 samples.

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
- Accepted cleaned chunks: 96
- Rejected chunks: 12
- Instruction-answer seed samples: 157
- Train samples: 142
- Eval samples: 15
- Focused Stage 2B.3 patch train samples: 28
- Duplicate instruction samples: 0

Sample types:

| Type | Count |
|---|---:|
| concept explanation | 25 |
| misconception fix | 25 |
| interview answer | 25 |
| beginner friendly | 25 |
| targeted technical QA | 12 |
| Stage 2B.2 badcase patch | 8 |
| Stage 2B.3 loss/replay patch | 17 |
| project record summary | 20 |

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

- Train rows: 142
- Eval rows: 15
- Role order: all rows use `system -> user -> assistant`
- Unique prompts: 134 train, 15 eval
- Duplicate train prompts: 8 intentional replay/exact-badcase repeats

Qwen tokenizer length check before truncation:

| Split | Min | Avg | P95 | Max | Over 512 |
|---|---:|---:|---:|---:|---:|
| Train | 111 | 160.6 | 267 | 323 | 0 |
| Eval | 120 | 166.7 | 276 | 291 | 0 |

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

## Stage 3B Feedback

Stage 3B has now been run. The 132-sample revised data improved the custom
adapter on 6 of 8 fixed technical prompts. It also exposed two remaining weak
spots:

- The model still needs cleaner examples for explaining why public-SFT failure
  motivates Stage 2B.
- The model still needs cleaner examples for explaining why loss alone is not
  enough to judge SFT success.

This is the intended data loop: use fixed-prompt badcases to decide exactly what
to collect or write next.

## Stage 2B.2 Feedback

Stage 2B.2 added 8 focused badcase samples and regenerated the current 140-sample
dataset. The follow-up training results were instructive:

- Training v2 from scratch for 5 epochs regressed on previously solved prompts.
- Training v2 from scratch for 10 epochs and comparing the best-eval checkpoint
  still regressed.
- Continuing from `outputs/sft_lora_qwen05b_custom` with low learning rate
  produced `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`, which preserved
  or improved 7 of 8 fixed prompts.

This shows that the data pipeline needs regression testing, not just more rows.
The remaining weak prompt is now mainly the loss-vs-behavior explanation.

## Stage 2B.3 Feedback

Stage 2B.3 added 10 loss-vs-behavior samples and 7 replay samples, then tested
several ways to patch the final prompt before DPO:

- v4 full-data continuation mostly preserved old behavior but did not fix the
  final loss-vs-behavior prompt.
- v5 focused patch fixed that prompt but regressed several older prompts.
- v6 reduced update strength but remained unstable.
- adapter interpolation between v3 and v5 did not fix the prompt in spot checks.

Current recommendation:

```text
Keep outputs/sft_lora_qwen05b_custom_v3_from_v1_patch as the current best adapter.
Pause before DPO and review the tradeoff with the user.
```

## Next Step

Review Stage 2B.3 before DPO:

```text
read reports/stage2b3_sft_stability_gate_report.md
  -> decide whether v3 is acceptable as the SFT checkpoint
  -> only then move to tiny DPO smoke testing
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
  --epochs 10 `
  --logging_steps 10 `
  --eval_steps 50 `
  --save_steps 50 `
  --report_to none `
  --local_files_only
```

The first `epochs=3` run was useful as a smoke test, but the revised 10-epoch
run made the target behavior clearer. Eval loss was best around epoch 5, so the
next version should consider best-checkpoint selection instead of relying only
on the final saved adapter.
