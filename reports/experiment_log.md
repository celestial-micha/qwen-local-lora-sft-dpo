# Experiment Log

## Stage 1: Base Inference

- Date:
- Conda env:
- GPU:
- Torch version:
- CUDA available:
- Model:
- Prompt:
- Output summary:
- Problems:
- Next action:

## Stage 2: Real SFT Data Preparation

- Date: 2026-05-14
- Conda env: `qwen-lora-local`
- Dataset: `llm-wizard/alpaca-gpt4-data-zh`
- Raw snapshot: `data/raw/alpaca_gpt4_data_zh_1200.jsonl`
- Processed train file: `data/processed/sft_train.jsonl`
- Processed eval file: `data/processed/sft_eval.jsonl`
- Raw sampled rows: 1,200
- Valid converted rows: 1,114
- Train rows: 1,003
- Eval rows: 111
- Dropped rows: 86
- Duplicate prompts: 0
- Validation: JSONL role order passed; Qwen tokenizer encoding passed.
- Report: `reports/stage2_sft_data_report.md`
- Data strategy: this public dataset is the controlled baseline, not the final custom dataset.
- Next action: run Stage 3A real LoRA SFT with `outputs/sft_lora_qwen05b_public`.
- Later action: build Stage 2B self-collected data pipeline after public-data SFT succeeds.

## Stage 3A: Public LoRA SFT

- Date: 2026-05-14
- Method: LoRA SFT. SFT is the objective; LoRA is the adapter training method.
- Train file: `data/processed/sft_train.jsonl`
- Eval file: `data/processed/sft_eval.jsonl`
- Output adapter: `outputs/sft_lora_qwen05b_public`
- Trainable params: 4,399,104
- Trainable ratio: 0.8826%
- Runtime: about 24.4 minutes
- Final train loss: 1.7558
- Eval loss at step 100: 1.8263
- Loading test: passed.
- Comparison output: `reports/compare_outputs_public_sft.jsonl`
- Report: `reports/stage3a_public_lora_sft_report.md`
- Main finding: public-data LoRA SFT trained successfully, but did not fix LoRA/SFT/DPO concept confusion.
- Next action: Stage 2B custom technical data collection and cleaning.
