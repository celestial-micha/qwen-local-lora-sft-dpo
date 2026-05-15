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
- Observed training VRAM: about `5.5 GB / 8 GB`.
- Observed adapter-inference VRAM: about `1.2 GB / 8 GB`.
- Next action: Stage 4A fixed-prompt comparison report, then Stage 2B custom technical data collection and cleaning.

## Stage 4A: Base vs Public-SFT Comparison

- Date: 2026-05-14
- Prompt file: `data/samples/smoke_prompts.jsonl`
- Adapter: `outputs/sft_lora_qwen05b_public`
- Raw output: `reports/compare_outputs_public_sft.jsonl`
- Summary table: `reports/compare_base_sft.md`
- Report: `reports/stage4a_public_sft_comparison_report.md`
- Result: public-SFT did not fix the target LoRA/SFT/DPO concept mistakes.
- Interpretation: this is useful negative evidence for Stage 2B targeted technical data.
- Next action: build a self-collected technical-data pipeline before custom/mixed SFT.

## DPO VRAM Planning

- Date: 2026-05-14
- Report: `reports/vram_and_dpo_plan.md`
- Judgment: 8 GB VRAM may support a tiny DPO smoke test, but naive DPO is risky.
- First DPO target: 20-50 pairs, short sequence lengths, `batch_size=1`, gradient accumulation, minimal eval, and PEFT/reference sharing where possible.

## Stage 2B: Custom Technical Data Preparation

- Date: 2026-05-14
- Script: `scripts/prepare_custom_technical_data.py`
- Sources: 10 project-owned technical notes
- Raw sources file: `data/raw/custom_sources.jsonl`
- Cleaned chunks file: `data/raw/custom_cleaned_chunks.jsonl`
- Instruction seed file: `data/raw/custom_instruction_seed.jsonl`
- Processed train file: `data/processed/custom_sft_train.jsonl`
- Processed eval file: `data/processed/custom_sft_eval.jsonl`
- Accepted chunks: 85
- Rejected chunks: 9
- Instruction-answer seed samples: 132
- Train rows: 119
- Eval rows: 13
- Duplicate instruction samples: 0
- Token validation: train max 486, eval max 238, no rows over 512 before truncation.
- Dataset focus: LoRA/SFT/DPO concept correction, data cleaning, fixed-prompt comparison, 8GB VRAM and DPO risk, interview explanation.
- Report: `reports/stage2b_custom_technical_data_report.md`
- Revision note: the first 160-sample version trained but still hallucinated; the current version reduces generic project-record summaries and adds targeted QA badcase samples.
- Follow-up: Stage 3B custom-data LoRA SFT, recorded below.

## Stage 3B: Custom Technical LoRA SFT

- Date: 2026-05-14
- Method: LoRA SFT on the revised Stage 2B custom technical dataset.
- Train file: `data/processed/custom_sft_train.jsonl`
- Eval file: `data/processed/custom_sft_eval.jsonl`
- Output adapter: `outputs/sft_lora_qwen05b_custom`
- Train rows: 119
- Eval rows: 13
- Trainable params: 4,399,104
- Trainable ratio: 0.8826%
- Runtime: about 12.3 minutes
- Final train loss: 0.4656
- Best observed eval loss: 0.8311 around epoch 5.04
- Later eval loss: 0.8669 at epoch 8.40, suggesting mild overfitting risk.
- Report: `reports/stage3b_custom_lora_sft_report.md`
- Main finding: custom technical data fixed many target LoRA/SFT/DPO prompts, but not all.

## Stage 4B: Base vs Public-SFT vs Custom-SFT Comparison

- Date: 2026-05-14
- Prompt file: `data/samples/custom_technical_prompts.jsonl`
- Public adapter: `outputs/sft_lora_qwen05b_public`
- Custom adapter: `outputs/sft_lora_qwen05b_custom`
- Script: `scripts/compare_three_outputs.py`
- Raw output: `reports/compare_outputs_three_way_custom.jsonl`
- Report: `reports/stage4b_three_way_comparison_report.md`
- Result: custom-SFT strongly improved 6 of 8 fixed technical prompts.
- Remaining weak prompts: explaining why public-SFT failure motivates Stage 2B; explaining why loss alone is insufficient.
- Next action: review and understand results, then optionally run a small Stage 2B.2 data patch before DPO.

## Stage 2B.2: Badcase Patch Data Preparation

- Date: 2026-05-15
- Script: `scripts/prepare_custom_technical_data.py`
- Main code change: added `badcase_patch_samples()` with 8 focused samples.
- Patch focus: public-SFT as engineering baseline, Stage 4A as behavior evaluation, Stage 2B as data improvement, and loss-vs-behavior evaluation.
- Sources: 10 project-owned technical notes
- Accepted chunks: 90
- Rejected chunks: 12
- Instruction-answer seed samples: 140
- Train rows: 126
- Eval rows: 14
- Duplicate instruction samples: 0
- Token validation: train max 323, eval max 277, no rows over 512 before truncation.
- Report: `reports/stage2b2_badcase_patch_report.md`

## Stage 3B.2 Attempt 1: v2 From Scratch, 5 Epochs

- Date: 2026-05-15
- Output adapter: `outputs/sft_lora_qwen05b_custom_v2`
- Train file: `data/processed/custom_sft_train.jsonl`
- Eval file: `data/processed/custom_sft_eval.jsonl`
- Runtime: about 415.5 seconds
- Final train loss: 1.0496
- Best observed eval loss: 0.8561 at epoch 3.81
- Raw comparison: `reports/compare_outputs_three_way_custom_v2.jsonl`
- Result: not recommended. It regressed on previously solved LoRA/SFT prompts.

## Stage 3B.2 Attempt 2: v2 From Scratch, 10 Epochs

- Date: 2026-05-15
- Output adapter: `outputs/sft_lora_qwen05b_custom_v2_10ep`
- Best-eval checkpoint compared: `outputs/sft_lora_qwen05b_custom_v2_10ep/checkpoint-100`
- Runtime: about 776.0 seconds
- Final train loss: 0.4931
- Best observed eval loss: 0.8614 at epoch 3.17
- Later eval loss: 1.1130 at epoch 9.52
- Raw comparison: `reports/compare_outputs_three_way_custom_v2_checkpoint100.jsonl`
- Result: not recommended. Lower loss did not prevent behavior regression.

## Stage 3B.2 Attempt 3: v3 Continue From v1 With Low LR

- Date: 2026-05-15
- Training script update: `scripts/train_sft_lora.py` now supports `--init_adapter_path`.
- Init adapter: `outputs/sft_lora_qwen05b_custom`
- Output adapter: `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`
- Learning rate: `5e-5`
- Epochs: 2
- Runtime: about 157.5 seconds
- Final train loss: 0.2873
- Eval loss at epoch 0.95: 0.0371
- Eval loss at epoch 1.90: 0.0348
- Raw comparison: `reports/compare_outputs_three_way_custom_v3_from_v1_patch.jsonl`
- Result: current best local adapter. It preserved or improved 7/8 fixed prompts.
- Remaining weak prompt: explaining why loss alone is insufficient to judge SFT success.
- Next action: Stage 2B.3 small replay-style patch for loss-vs-behavior before DPO.

## Stage 2B.3: SFT Stability Gate Data Preparation

- Date: 2026-05-15
- Script: `scripts/prepare_custom_technical_data.py`
- Main code changes: added `stage2b3_loss_behavior_samples()`, force-train split logic for targeted/patch/replay rows, and optional focused patch export.
- Added helper script: `scripts/interpolate_lora_adapters.py`
- Sources: 10 project-owned technical notes
- Accepted chunks: 96
- Rejected chunks: 12
- Instruction-answer seed samples: 157
- Train rows: 142
- Eval rows: 15
- Focused patch train rows: 28
- Exact loss prompt repeats in focused patch: 12
- Token validation: train max 323, eval max 291, no rows over 512 before truncation.
- Report: `reports/stage2b3_sft_stability_gate_report.md`

## Stage 3B.3 Attempt 1: v4 Full Stage 2B.3 Data

- Date: 2026-05-15
- Init adapter: `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`
- Train file: `data/processed/custom_sft_train.jsonl`
- Output adapter: `outputs/sft_lora_qwen05b_custom_v4_stage2b3_loss_patch`
- Learning rate: `3e-5`
- Epochs: 2
- Runtime: about 244.2 seconds
- Final train loss: 0.5474
- Eval loss: 0.0160 then 0.0173
- Raw comparison: `reports/compare_outputs_three_way_custom_v4_stage2b3_loss_patch.jsonl`
- Result: not recommended. Prompt 7 remained weak and prompt 4 mildly regressed.

## Stage 3B.3 Attempt 2: v5 Focused Patch

- Date: 2026-05-15
- Init adapter: `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`
- Train file: `data/processed/custom_sft_stage2b3_patch_train.jsonl`
- Output adapter: `outputs/sft_lora_qwen05b_custom_v5_stage2b3_focused_patch`
- Learning rate: `8e-5`
- Epochs: 4
- Runtime: about 120.2 seconds
- Final train loss: 1.2324
- Best observed eval loss: 0.0997
- Raw comparison: `reports/compare_outputs_three_way_custom_v5_stage2b3_focused_patch.jsonl`
- Result: not recommended. Prompt 7 was fixed, but several previously stable prompts regressed.

## Stage 3B.3 Attempt 3: v6 Balanced Focused Patch

- Date: 2026-05-15
- Init adapter: `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`
- Train file: `data/processed/custom_sft_stage2b3_patch_train.jsonl`
- Output adapter: `outputs/sft_lora_qwen05b_custom_v6_stage2b3_balanced_patch`
- Learning rate: `3e-5`
- Epochs: 1
- Runtime: about 23.3 seconds
- Final train loss: 3.1996
- Raw comparison: `reports/compare_outputs_three_way_custom_v6_stage2b3_balanced_patch.jsonl`
- Result: not recommended. The update was weaker than v5 but still destabilized old prompts.

## Stage 3B.3 Attempt 4: Adapter Interpolation Probe

- Date: 2026-05-15
- Script: `scripts/interpolate_lora_adapters.py`
- Base adapter: `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`
- Patch adapter: `outputs/sft_lora_qwen05b_custom_v5_stage2b3_focused_patch`
- Tested alphas: 0.15, 0.25, 0.40
- Result: not recommended. Spot-checks did not fix the loss-vs-behavior prompt.

## Stage 5 Gate: Pause Before DPO

- Date: 2026-05-15
- Decision: do not start DPO yet.
- Current best local adapter remains `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`.
- Reason: v3 preserves 7/8 prompts; later attempts either failed to fix prompt 7 or fixed it with unacceptable regressions.
- Next action: review Stage 2B.3 with the user before choosing DPO or another SFT replay pass.
