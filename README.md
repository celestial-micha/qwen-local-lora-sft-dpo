# Qwen Local LoRA SFT DPO

[中文](README.zh-CN.md) | English

A minimal local post-training project for learning and demonstrating LoRA SFT
and later DPO with `Qwen/Qwen2.5-0.5B-Instruct` on an RTX 4060 laptop GPU.

This project intentionally starts small. The goal is not to build a large
domain model first, but to finish a clean, reproducible, explainable training
pipeline that can be discussed in interviews.

## Current Status

Completed:

- Local CUDA environment verified on an NVIDIA GeForce RTX 4060 Laptop GPU.
- Stable Windows training stack pinned.
- Qwen2.5-0.5B base inference runs locally.
- Demo SFT data generation works.
- Minimal LoRA SFT smoke test runs successfully.
- LoRA adapter saving and loading works.
- Base vs SFT comparison output is generated.

Not completed yet:

- Real 500-2000 sample SFT dataset.
- Meaningful SFT training run.
- DPO dataset and DPO training.
- Multi-GPU notes or experiments.

## Why This Project Exists

The previous plan was too broad: domain-specific military assistant, Colab-first
training, DPO, safety evaluation, Gradio, and possible multi-GPU work all at
once. That was useful as a long-term idea, but too large for a first solid
interview project.

This version focuses on the smallest useful local workflow:

```text
environment check
  -> base Qwen inference
  -> SFT data preparation
  -> LoRA SFT
  -> adapter loading
  -> base vs SFT comparison
  -> DPO later
```

## Model

First model:

```text
Qwen/Qwen2.5-0.5B-Instruct
```

This model is small enough for fast local iteration and large enough to show the
real Hugging Face + PEFT training workflow.

## Stable Local Stack

The training environment is:

```text
Python 3.10
torch==2.5.1+cu124
transformers==4.46.3
accelerate==1.1.1
peft==0.13.2
datasets==3.1.0
trl==0.12.2
huggingface-hub==0.26.5
fsspec==2024.9.0
```

`gradio` is intentionally not installed in this training environment. If a demo
is needed later, use a separate environment.

## Quick Start

```powershell
conda activate qwen-lora-local
cd "D:\coding\qwen lorar sft\qwen-local-lora-sft-dpo"
$env:HF_HOME=(Resolve-Path -LiteralPath ".hf_cache").Path
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"
```

Check environment:

```powershell
python scripts/check_env.py
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda')"
```

Run base inference:

```powershell
python scripts/infer.py --prompt "请用三点解释什么是LoRA微调。" --max_new_tokens 128 --local_files_only
```

Prepare demo data:

```powershell
python scripts/prepare_data.py --demo --train_file data\processed\sft_train.jsonl --eval_file data\processed\sft_eval.jsonl
```

Run LoRA SFT smoke test:

```powershell
python scripts/train_sft_lora.py `
  --train_file data\processed\sft_train.jsonl `
  --eval_file data\processed\sft_eval.jsonl `
  --output_dir outputs\sft_lora_qwen05b_demo `
  --max_length 256 `
  --batch_size 1 `
  --grad_accum 1 `
  --epochs 1 `
  --logging_steps 1 `
  --eval_steps 2 `
  --save_steps 2 `
  --report_to none `
  --local_files_only
```

Compare outputs:

```powershell
python scripts/compare_outputs.py `
  --adapter_path outputs\sft_lora_qwen05b_demo `
  --output_file reports\compare_outputs_demo.jsonl `
  --max_new_tokens 48
```

## Important Reports

- [Project context for next chat](reports/project_context_for_next_chat.md)
- [Windows debug report](reports/windows_debug_report.md)
- [Beginner learning report in Chinese](reports/beginner_learning_report_zh.md)
- [Base vs SFT demo outputs](reports/compare_outputs_demo.jsonl)

## Next Step

The next meaningful stage is real SFT data preparation:

1. Choose a common Chinese instruction dataset.
2. Convert 500-2000 samples into Qwen chat JSONL.
3. Run LoRA SFT with a small but real dataset.
4. Compare base vs SFT behavior on fixed prompts.
5. Only then move to DPO.
