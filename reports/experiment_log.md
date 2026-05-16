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

## Stage 5 Planning: Split DPO

- Date: 2026-05-15
- Decision: start Stage 5 from `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`.
- Plan report: `reports/stage5_dpo_plan.md`
- Config updated: `configs/dpo_qwen05b.yaml`
- Stage 5A: prepare `data/processed/dpo_tiny_train.jsonl` with 20-50 preference pairs.
- Stage 5B: tiny DPO smoke test on 8GB VRAM.
- Stage 5C: compare fixed prompts after tiny DPO.
- Stage 5D: larger or more naive DPO only if tiny DPO memory and behavior are acceptable.
- User observation requested: dedicated VRAM peak, shared GPU memory growth, system RAM, step speed, crash/OOM status.

## Stage 5 Candidate DPO v4/v5 Follow-Up

- Date: 2026-05-16
- Starting adapter for both runs: `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`
- v4 data: `data/processed/dpo_candidate_train.jsonl`, 20 train pairs; `data/processed/dpo_candidate_eval.jsonl`, 5 eval pairs.
- v4 output: `outputs/dpo_lora_qwen05b_candidate_v4`
- v4 result: no OOM, adapter reload passed, final eval accuracy 0.8000, structured behavior score 6/8.
- v5 data: `data/processed/dpo_candidate_v5_train.jsonl`, 28 train pairs; `data/processed/dpo_candidate_v5_eval.jsonl`, 7 eval pairs.
- v5 output: `outputs/dpo_lora_qwen05b_candidate_v5`
- v5 result: no OOM, adapter reload passed, final eval accuracy 0.8571, structured behavior score 6/8.
- Decision: Stage 5D larger DPO remains blocked. Candidate v4/v5 still failed prompt 4 public-SFT motivation and prompt 7 loss-vs-behavior.
- Report: `reports/stage5_candidate_dpo_v4_v5_report.md`

## Stage 5G: Larger Naive DPO v6

- Date: 2026-05-16
- Starting adapter: `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`
- Train file: `data/processed/dpo_larger_v6_train.jsonl`, 192 preference pairs.
- Eval file: `data/processed/dpo_larger_v6_eval.jsonl`, 24 preference pairs.
- Config: `configs/dpo_qwen05b_v6_naive.yaml`
- Training mode: separate frozen reference model (`separate_ref_model: true`)
- Output adapter: `outputs/dpo_lora_qwen05b_naive_v6`
- Optimizer steps: 48
- Runtime: 271.4 seconds including save.
- Final train loss: 0.2418
- Final eval loss: 0.0474
- Final eval preference accuracy: 1.0000
- Max allocated VRAM: 3.415 GB
- Max reserved VRAM: 8.686 GB
- Adapter reload: passed.
- Fixed-prompt score: 7 / 8, best DPO candidate so far.
- Remaining failure: prompt 7 loss-vs-behavior.
- Report: `reports/stage5g_naive_dpo_v6_report.md`

## Stage 5H: Prompt-7 Data And Expanded Gate Design

- Date: 2026-05-16
- Training run: none.
- Goal: prepare stronger loss-vs-behavior preference/eval data and an expanded
  behavior gate before any DPO v7 training.
- Generator: `scripts/prepare_stage5h_prompt7_data.py`
- Train file: `data/processed/dpo_stage5h_prompt7_train.jsonl`, 278 preference
  pairs.
- Eval file: `data/processed/dpo_stage5h_prompt7_eval.jsonl`, 55 preference
  pairs.
- New prompt-7 train pairs: 72.
- New prompt-7 eval pairs: 24.
- Expanded behavior suite:
  `data/samples/custom_technical_prompts_expanded_stage5h.jsonl`, 24 prompts.
- Expanded scorer: `scripts/score_expanded_behavior_outputs.py`
- Report: `reports/stage5h_prompt7_data_and_eval_design.md`
- Decision: review data and expanded gate first; do not continue training from
  DPO v6, and do not run DPO v7 until this design is accepted.

## Stage 5I-5P: Prompt-7 Repair Loop

- Date: 2026-05-16
- Stage 5I expanded gate check:
  - Input: `reports/compare_outputs_four_way_dpo_naive_v6_expanded_stage5h.jsonl`
  - Report: `reports/stage5i_expanded_behavior_score_v6_report.md`
  - Result: DPO v6 passed 7 / 24 expanded prompts and 0 / 13 loss-vs-behavior prompts.
- Stage 5J DPO v7:
  - Config: `configs/dpo_qwen05b_v7_stage5h.yaml`
  - Train/eval: 278 / 55 preference pairs.
  - Output: `outputs/dpo_lora_qwen05b_v7_stage5h`
  - Preference eval accuracy: 1.0000.
  - Fixed behavior: 7 / 8; prompt 7 still failed.
- Stage 5K direct SFT repair:
  - Data: `data/processed/sft_stage5k_prompt7_repair_train.jsonl`, 193 train rows.
  - Output: `outputs/sft_lora_qwen05b_stage5k_prompt7_repair`
  - Fixed behavior: 1 / 8 on the custom variant.
  - Decision: rejected due to severe regression.
- Stage 5M exact-failure DPO v8:
  - Config: `configs/dpo_qwen05b_v8_stage5m_from_v6.yaml`
  - Train/eval: 162 / 41 preference pairs.
  - Output: `outputs/dpo_lora_qwen05b_v8_stage5m_from_v6`
  - Preference eval accuracy: 1.0000.
  - Fixed behavior: 7 / 8; prompt 7 improved but still failed.
- Stage 5N micro-SFT from v6:
  - Data: `data/processed/sft_stage5n_prompt7_micro_train.jsonl`, 116 train rows.
  - Output: `outputs/sft_lora_qwen05b_stage5n_prompt7_micro_from_v6`
  - Fixed behavior: 7 / 8; old prompts preserved but prompt 7 still failed.
- Stage 5O exact SFT from Stage 5N:
  - Data: `data/processed/sft_stage5o_prompt7_exact_train.jsonl`, 196 train rows.
  - Output: `outputs/sft_lora_qwen05b_stage5o_prompt7_exact_from_5n`
  - Fixed behavior: 4 / 8; prompt 7 passed but older prompts regressed.
- Stage 5P balanced half-epoch SFT:
  - Data: same as Stage 5O.
  - Output: `outputs/sft_lora_qwen05b_stage5p_prompt7_balanced_from_5n`
  - Fixed behavior: 6 / 8; prompt 7 failed again.
- Decision: stop the training loop. No Stage 5J-5P adapter is accepted.
- Report: `reports/stage5j_to_5p_prompt7_repair_report.md`

## Stage 6: Final Interview Package

- Date: 2026-05-16
- Training run: none.
- Goal: package the project for interview/resume use instead of adding more
  DPO/SFT steps.
- Report: `reports/stage6_final_interview_package.md`
- Final project summary: `reports/final_project_summary_zh.md`
- Contents:
  - 30-second and two-minute interview narratives.
  - Before/after examples for LoRA definition, SFT vs LoRA, and the data
    pipeline.
  - Failure review for prompt 7 and why loss/preference accuracy were not
    accepted as behavior gates.
  - Chinese and English resume bullets.
  - Recommended demo flow and next-work boundary.
- Decision: Stage 6 is complete. Keep
  `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch` as the conservative
  checkpoint and `outputs/dpo_lora_qwen05b_naive_v6` as the best DPO artifact.
