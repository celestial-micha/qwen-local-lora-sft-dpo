# Project Runbook

Read this file first if the project context is lost.

## Project Direction

The project has been reset to a minimal local training project.

Old direction:

- Large military/strategy assistant.
- Colab-first workflow.
- Full pipeline from domain data to Gradio.

New direction:

- Local RTX 4060 first.
- `Qwen/Qwen2.5-0.5B-Instruct` first.
- Learn and demonstrate LoRA SFT and DPO with the smallest useful workflow.
- Use common instruction data first as a controlled baseline.
- Then build a small self-collected data pipeline with crawling, cleaning,
  filtering, instruction rewriting, and custom-data SFT.

Terminology:

- SFT is the supervised fine-tuning objective and data format.
- LoRA is the parameter-efficient tuning method.
- This project trains LoRA adapters with an SFT objective, so the correct name
  for the current training stage is LoRA SFT.

## Runtime

Main runtime:

```text
Windows local machine
conda environment: qwen-lora-local
GPU: NVIDIA GeForce RTX 4060 Laptop GPU
```

Confirmed by user:

```text
torch 2.5.1+cu124
cuda available: True
GPU: NVIDIA GeForce RTX 4060 Laptop GPU
```

Set these environment variables before downloading Hugging Face models:

```powershell
$env:HF_HOME=(Resolve-Path -LiteralPath ".hf_cache").Path
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"
```

Stable local package stack after debugging:

```text
torch: 2.5.1+cu124
transformers: 4.46.3
accelerate: 1.1.1
peft: 0.13.2
datasets: 3.1.0
trl: 0.12.2
huggingface-hub: 0.26.5
fsspec: 2024.9.0
gradio: not installed in the training environment
```

## Stage Plan

### Stage 0: Clean Local Scaffold

Status: completed in this new project.

Goal:

- Create a small local repo structure.
- Remove the previous military/Colab-first assumptions.
- Keep the plan focused on Qwen 0.5B local LoRA/SFT/DPO.

### Stage 1: Environment and Base Inference

Goal:

- Run `scripts/check_env.py`.
- Run `scripts/infer.py`.
- Confirm that Qwen loads locally and answers a Chinese prompt.

Success criteria:

- CUDA is available.
- The 4060 is visible to PyTorch.
- Qwen model downloads automatically from Hugging Face.
- Base inference produces a readable answer.

Status: completed. Base inference runs locally from `.hf_cache`.

### Stage 2A: Public SFT Dataset Baseline

Goal:

- Use a common instruction dataset such as an Alpaca-style Chinese dataset.
- Convert samples into Qwen chat format.
- Keep the first dataset small: 500 to 2000 samples.

Planned output:

- `data/processed/sft_train.jsonl`
- `data/processed/sft_eval.jsonl`

Status: completed for the first real SFT dataset.

Current dataset:

- Source: `llm-wizard/alpaca-gpt4-data-zh`
- Raw snapshot: `data/raw/alpaca_gpt4_data_zh_1200.jsonl`
- Train rows: 1,003
- Eval rows: 111
- Report: `reports/stage2_sft_data_report.md`

Why this comes first:

- It keeps the first real SFT run reproducible.
- It separates training-pipeline bugs from messy custom-data bugs.
- It creates a baseline adapter for later comparison against custom-data SFT.

### Stage 3A: LoRA SFT on Public Data

Goal:

- Run LoRA SFT on Qwen2.5-0.5B-Instruct.
- Avoid QLoRA/bitsandbytes in the first Windows version unless needed.

Initial training target:

- LoRA only.
- Small batch size.
- Gradient accumulation.
- Short max length.
- Save adapter to `outputs/sft_lora_qwen05b_public`.

Smoke status: completed with demo data.

Output:

```text
outputs/sft_lora_qwen05b_demo
```

The smoke test proves the training/save/load path works. It does not prove model
quality because it used only 4 train samples and 1 eval sample.

Public-data status: completed.

Result:

- Output adapter: `outputs/sft_lora_qwen05b_public`
- Trainable params: 4,399,104
- Trainable ratio: 0.8826%
- Final train loss: 1.7558
- Eval loss at step 100: 1.8263
- Runtime: about 24.4 minutes
- Report: `reports/stage3a_public_lora_sft_report.md`

Important finding:

- Public-data LoRA SFT trained successfully, but it did not fix LoRA/SFT/DPO
  concept confusion. This supports the Stage 2B custom technical-data plan.

### Stage 4A: Base vs Public-SFT Comparison

Goal:

- Compare fixed prompts before and after SFT.
- Record results in `reports/compare_base_sft.md`.

### Stage 2B: Self-Collected Data Pipeline

Goal:

- Collect a small set of preferred-topic Chinese text using crawling or manual
  source collection.
- Clean boilerplate, navigation text, duplicates, noisy text, and off-topic
  content.
- Convert useful content into instruction-answer pairs.
- Keep the first custom pass small: 100 to 300 accepted samples.
- Preserve source metadata so the data process is explainable in interviews.

Planned raw outputs:

- `data/raw/custom_sources.jsonl`
- `data/raw/custom_cleaned_chunks.jsonl`
- `data/raw/custom_instruction_seed.jsonl`

Planned processed outputs:

- `data/processed/custom_sft_train.jsonl`
- `data/processed/custom_sft_eval.jsonl`
- optional mixed data: `data/processed/mixed_sft_train.jsonl`

Suggested first custom topic:

- Chinese technical learning content around LoRA, SFT, DPO, Hugging Face,
  CUDA/Windows debugging, experiment logging, and interview explanations.

Important rule:

- Do this after the public-data SFT loop is trainable end to end. Otherwise,
  dirty-data issues and training issues become hard to separate.

### Stage 3B: LoRA SFT on Custom or Mixed Data

Goal:

- Train either a custom-only adapter or a mixed public+custom adapter.
- Save adapter to `outputs/sft_lora_qwen05b_custom` or
  `outputs/sft_lora_qwen05b_mixed`.
- Compare behavior against both the base model and the public-data adapter.

### Stage 4B: Three-Way Comparison

Goal:

- Compare base, public-SFT, and custom/mixed-SFT on the same fixed prompt set.
- Record wins, regressions, overfitting signs, and bad cases.
- Turn the result into an interview-ready data pipeline narrative.

### Stage 5: DPO

Goal:

- Build 50 to 200 preference pairs.
- Run minimal DPO after SFT behavior is stable.
- Save adapter to `outputs/dpo_lora_qwen05b`.

### Stage 6: Final Interview Package

Goal:

- README with commands.
- Experiment log.
- Loss observations.
- Before/after examples.
- Data pipeline report covering public download, custom crawling, cleaning, and
  conversion.
- DPO notes.
- Resume-ready summary.

## Rules

- Do not start with a large model.
- Do not start with a niche domain.
- Do not add Colab complexity unless local training fails.
- Do not add bitsandbytes until regular LoRA is tested.
- Keep every step reproducible and explainable.
- Do not jump into crawling before one real public-data SFT run succeeds.
- Keep custom crawling legally and ethically scoped: prefer permissive sources,
  public docs, own notes, summaries, and small excerpts rather than copying full
  copyrighted articles.
