# Qwen Local LoRA SFT DPO

[中文](README.zh-CN.md) | English

A minimal local post-training project for learning and demonstrating LoRA SFT
and later DPO with `Qwen/Qwen2.5-0.5B-Instruct` on an RTX 4060 laptop GPU.

Terminology note: SFT is the supervised fine-tuning objective and data format.
LoRA is the parameter-efficient tuning method. The current training path is
LoRA SFT: supervised fine-tuning implemented by training LoRA adapters.

This project intentionally starts small. The goal is not to build a large
domain model first, but to finish a clean, reproducible, explainable training
pipeline that can be discussed in interviews. The data plan has two loops:
first a public Chinese instruction dataset baseline, then a self-collected data
pipeline with crawling, cleaning, filtering, instruction conversion, and another
SFT comparison.

## Current Status

Completed:

- Local CUDA environment verified on an NVIDIA GeForce RTX 4060 Laptop GPU.
- Stable Windows training stack pinned.
- Qwen2.5-0.5B base inference runs locally.
- Demo SFT data generation works.
- Minimal LoRA SFT smoke test runs successfully.
- LoRA adapter saving and loading works.
- Base vs SFT comparison output is generated.
- Real Stage 2 SFT data is prepared from `llm-wizard/alpaca-gpt4-data-zh`.
- Stage 3A public-data LoRA SFT completed and saved `outputs/sft_lora_qwen05b_public`.
- Stage 4A base vs public-SFT comparison completed.
- Learning notebook added: `notebooks/04_full_pipeline_learning.ipynb`.
- Stage 2B custom technical data prepared and revised with 119 train and 13 eval samples.
- Stage 3B custom-data LoRA SFT completed and saved `outputs/sft_lora_qwen05b_custom`.
- Stage 4B base vs public-SFT vs custom-SFT comparison completed.

Not completed yet:

- Stage 2B.2 targeted data patch for the remaining custom-SFT badcases.
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
  -> public SFT data preparation
  -> public-data LoRA SFT
  -> base vs public-SFT comparison
  -> self-collected data crawling and cleaning
  -> custom or mixed-data LoRA SFT
  -> base vs public-SFT vs custom-SFT comparison
  -> DPO later
```

The public dataset comes first on purpose. It proves that the training pipeline
works with controlled data. The custom-data loop comes after that, so crawling
and cleaning issues can be analyzed separately instead of being mixed with
training bugs.

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

Prepare real Stage 2 SFT data:

```powershell
python scripts\download_hf_sft_data.py `
  --dataset_name llm-wizard/alpaca-gpt4-data-zh `
  --split train `
  --output_file data\raw\alpaca_gpt4_data_zh_1200.jsonl `
  --max_samples 1200 `
  --seed 42

python scripts\prepare_data.py `
  --input_file data\raw\alpaca_gpt4_data_zh_1200.jsonl `
  --train_file data\processed\sft_train.jsonl `
  --eval_file data\processed\sft_eval.jsonl `
  --eval_ratio 0.1 `
  --max_samples 1200 `
  --min_answer_chars 20 `
  --seed 42
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

Run Stage 4A public-SFT comparison:

```powershell
python scripts\compare_outputs.py `
  --prompt_file data\samples\smoke_prompts.jsonl `
  --adapter_path outputs\sft_lora_qwen05b_public `
  --output_file reports\compare_outputs_public_sft.jsonl `
  --max_new_tokens 96 `
  --local_files_only
```

Prepare Stage 2B custom technical data:

```powershell
python scripts\prepare_custom_technical_data.py `
  --raw_sources_file data\raw\custom_sources.jsonl `
  --cleaned_chunks_file data\raw\custom_cleaned_chunks.jsonl `
  --instruction_seed_file data\raw\custom_instruction_seed.jsonl `
  --train_file data\processed\custom_sft_train.jsonl `
  --eval_file data\processed\custom_sft_eval.jsonl `
  --eval_ratio 0.1 `
  --max_doc_samples 20 `
  --seed 42
```

Run Stage 3B custom-data LoRA SFT:

```powershell
python scripts\train_sft_lora.py `
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

Run Stage 4B three-way comparison:

```powershell
python scripts\compare_three_outputs.py `
  --prompt_file data\samples\custom_technical_prompts.jsonl `
  --public_adapter_path outputs\sft_lora_qwen05b_public `
  --custom_adapter_path outputs\sft_lora_qwen05b_custom `
  --output_file reports\compare_outputs_three_way_custom.jsonl `
  --max_new_tokens 128 `
  --temperature 0 `
  --local_files_only
```

## Learning Notebook

The main step-by-step notebook is:

```text
notebooks/04_full_pipeline_learning.ipynb
```

It is designed as a guided learning map for this whole project. It currently
covers environment checks, base inference, public SFT data preparation, public
LoRA SFT, Stage 4A comparison, Stage 2B custom technical data preparation,
Stage 3B custom LoRA SFT, Stage 4B three-way comparison, and DPO VRAM notes.
Heavy cells are guarded by Boolean switches so the notebook can be read and run
gradually.

## Important Reports

- [Project context for next chat](reports/project_context_for_next_chat.md)
- [Windows debug report](reports/windows_debug_report.md)
- [Beginner learning report in Chinese](reports/beginner_learning_report_zh.md)
- [Base vs SFT demo outputs](reports/compare_outputs_demo.jsonl)
- [Data pipeline plan](reports/data_pipeline_plan.md)
- [Stage 2 SFT data report](reports/stage2_sft_data_report.md)
- [Stage 3A public LoRA SFT report](reports/stage3a_public_lora_sft_report.md)
- [Stage 4A public-SFT comparison report](reports/stage4a_public_sft_comparison_report.md)
- [Stage 2B custom technical data report](reports/stage2b_custom_technical_data_report.md)
- [Stage 3B custom LoRA SFT report](reports/stage3b_custom_lora_sft_report.md)
- [Stage 4B three-way comparison report](reports/stage4b_three_way_comparison_report.md)
- [VRAM and DPO plan](reports/vram_and_dpo_plan.md)

## Next Step

The next meaningful step is review plus a small Stage 2B.2 data patch:

1. Review `reports/stage3b_custom_lora_sft_report.md` and `reports/stage4b_three_way_comparison_report.md`.
2. Add targeted samples for the two remaining weak prompts.
3. Optionally retrain or select the best custom checkpoint around epoch 5.
4. Only after the SFT loops are stable, move to tiny DPO smoke testing.
