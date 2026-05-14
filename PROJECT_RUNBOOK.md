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
- Use common instruction data before any niche domain data.

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

### Stage 2: Data Preparation

Goal:

- Use a common instruction dataset such as an Alpaca-style Chinese dataset.
- Convert samples into Qwen chat format.
- Keep the first dataset small: 500 to 2000 samples.

Planned output:

- `data/processed/sft_train.jsonl`
- `data/processed/sft_eval.jsonl`

### Stage 3: LoRA SFT

Goal:

- Run LoRA SFT on Qwen2.5-0.5B-Instruct.
- Avoid QLoRA/bitsandbytes in the first Windows version unless needed.

Initial training target:

- LoRA only.
- Small batch size.
- Gradient accumulation.
- Short max length.
- Save adapter to `outputs/sft_lora_qwen05b`.

Smoke status: completed with demo data.

Output:

```text
outputs/sft_lora_qwen05b_demo
```

The smoke test proves the training/save/load path works. It does not prove model
quality because it used only 4 train samples and 1 eval sample.

### Stage 4: Base vs SFT Comparison

Goal:

- Compare fixed prompts before and after SFT.
- Record results in `reports/compare_base_sft.md`.

### Stage 5: DPO

Goal:

- Build 50 to 200 preference pairs.
- Run minimal DPO on the SFT adapter.
- Save adapter to `outputs/dpo_lora_qwen05b`.

### Stage 6: Final Interview Package

Goal:

- README with commands.
- Experiment log.
- Loss observations.
- Before/after examples.
- DPO notes.
- Resume-ready summary.

## Rules

- Do not start with a large model.
- Do not start with a niche domain.
- Do not add Colab complexity unless local training fails.
- Do not add bitsandbytes until regular LoRA is tested.
- Keep every step reproducible and explainable.
