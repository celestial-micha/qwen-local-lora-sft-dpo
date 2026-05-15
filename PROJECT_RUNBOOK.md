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

Observed memory:

- Public LoRA SFT training: about 5.5 GB / 8 GB VRAM
- Adapter inference: about 1.2 GB / 8 GB VRAM
- DPO is expected to be more memory-sensitive than SFT and should start as a
  tiny smoke test only.

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

Status: completed.

Outputs:

- Raw JSONL: `reports/compare_outputs_public_sft.jsonl`
- Summary table: `reports/compare_base_sft.md`
- Report: `reports/stage4a_public_sft_comparison_report.md`

Finding:

- Public-data LoRA SFT trained successfully, but fixed-prompt testing showed it
  did not fix LoRA/SFT/DPO concept confusion.
- This validates the Stage 2B plan: targeted technical data is needed.

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

Status: completed, revised after Stage 3B feedback, patched in Stage 2B.2, and
expanded in Stage 2B.3 for the DPO-before gate.

Current Stage 2B.3 result:

- Script: `scripts/prepare_custom_technical_data.py`
- Raw sources: `data/raw/custom_sources.jsonl`
- Cleaned chunks: `data/raw/custom_cleaned_chunks.jsonl`
- Instruction seeds: `data/raw/custom_instruction_seed.jsonl`
- Train file: `data/processed/custom_sft_train.jsonl`
- Eval file: `data/processed/custom_sft_eval.jsonl`
- Train rows: 142
- Eval rows: 15
- Focused Stage 2B.3 patch train rows: 28
- Report: `reports/stage2b_custom_technical_data_report.md`
- Patch report: `reports/stage2b2_badcase_patch_report.md`
- Stability gate report: `reports/stage2b3_sft_stability_gate_report.md`

Stage 2B uses project-owned technical notes plus curated LoRA/SFT/DPO concept
seeds. The script also supports optional URL collection for later crawling
iterations, but the first pass avoids copying external copyrighted articles.

Important feedback:

- The initial 160-sample dataset trained but still produced hallucinated
  answers. That version had too many generic project-record summary samples.
- The revised dataset reduces `project_record_summary` samples and adds direct
  targeted QA for the fixed technical prompts.
- Stage 2B.2 adds 8 focused badcase samples for public-SFT motivation and
  loss-vs-behavior evaluation.
- Stage 2B.3 adds loss-vs-behavior samples, replay samples, force-train split
  logic for targeted rows, and a focused patch export for tiny continuation
  runs.
- This is a useful project story: badcases from comparison drive the next data
  revision.

### Stage 3B: LoRA SFT on Custom or Mixed Data

Goal:

- Train either a custom-only adapter or a mixed public+custom adapter.
- Save adapter to `outputs/sft_lora_qwen05b_custom` or
  `outputs/sft_lora_qwen05b_mixed`.
- Compare behavior against both the base model and the public-data adapter.

Status: completed for custom-only data, then followed by a Stage 2B.2
continuation run.

Output:

```text
outputs/sft_lora_qwen05b_custom
```

Result:

- Train rows: 119
- Eval rows: 13
- Trainable params: 4,399,104
- Trainable ratio: 0.8826%
- Runtime: about 12.3 minutes
- Final train loss: 0.4656
- Best observed eval loss: 0.8311 around epoch 5
- Report: `reports/stage3b_custom_lora_sft_report.md`

Important finding:

- The custom adapter improved most target technical prompts.
- Mild overfitting risk appeared after the best eval checkpoint.
- Loss alone was not enough; fixed-prompt behavior was the main judge.
- After Stage 2B.2, training a new v2 adapter from scratch regressed on
  previously solved prompts. Continuing from v1 with `--init_adapter_path` and
  a low learning rate was safer.

Command used:

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

### Stage 4B: Three-Way Comparison

Goal:

- Compare base, public-SFT, and custom/mixed-SFT on the same fixed prompt set.
- Record wins, regressions, overfitting signs, and bad cases.
- Turn the result into an interview-ready data pipeline narrative.

Status: completed.

Artifacts:

- Script: `scripts/compare_three_outputs.py`
- Raw output: `reports/compare_outputs_three_way_custom.jsonl`
- Report: `reports/stage4b_three_way_comparison_report.md`

Result:

- Custom-SFT strongly improved 6 of 8 fixed technical prompts.
- Remaining weak prompts:
  - why public-SFT failure motivates Stage 2B
  - why loss alone is not enough

Recommended next step:

- Review the Stage 2B.2 patch result and do one more focused Stage 2B.3 patch
  for the loss-vs-behavior prompt before DPO.

### Stage 2B.2 / Stage 3B.2 / Stage 4B.2: Badcase Patch Loop

Goal:

- Patch the two remaining Stage 4B weak prompts.
- Avoid losing the good behavior already learned by the v1 custom adapter.
- Treat fixed-prompt comparison as a regression suite.

Status: completed.

Artifacts:

- Data/report: `reports/stage2b2_badcase_patch_report.md`
- Scratch v2 comparison: `reports/compare_outputs_three_way_custom_v2.jsonl`
- Scratch v2 best-checkpoint comparison:
  `reports/compare_outputs_three_way_custom_v2_checkpoint100.jsonl`
- Low-LR continuation comparison:
  `reports/compare_outputs_three_way_custom_v3_from_v1_patch.jsonl`
- Current best local adapter:
  `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`

Result:

- v2 trained from scratch for 5 epochs regressed on core LoRA/SFT prompts.
- v2 trained from scratch for 10 epochs and evaluated at checkpoint 100 still
  regressed despite lower loss.
- v3 continued from `outputs/sft_lora_qwen05b_custom` with `--lr 5e-5` for 2
  epochs and preserved or improved 7/8 fixed prompts.
- The remaining weak prompt is now mainly: why loss alone is insufficient.

Lesson:

- Small badcase patches can cause regressions if retrained from scratch.
- A safer small-data workflow is: start from the best adapter, use lower LR,
  train briefly, then rerun the fixed-prompt regression suite.

### Stage 2B.3 / Stage 3B.3 / Stage 4B.3: SFT Stability Gate Before DPO

Goal:

- Try to patch the final loss-vs-behavior badcase.
- Preserve the seven prompts that v3 already handled well.
- Stop before DPO and review the tradeoff with the user.

Status: completed as a gate, but not accepted as a replacement adapter.

Artifacts:

- Report: `reports/stage2b3_sft_stability_gate_report.md`
- Full-data v4 comparison:
  `reports/compare_outputs_three_way_custom_v4_stage2b3_loss_patch.jsonl`
- Focused-patch v5 comparison:
  `reports/compare_outputs_three_way_custom_v5_stage2b3_focused_patch.jsonl`
- Balanced-patch v6 comparison:
  `reports/compare_outputs_three_way_custom_v6_stage2b3_balanced_patch.jsonl`
- Adapter interpolation helper: `scripts/interpolate_lora_adapters.py`

Result:

- v4 preserved most old behavior but still did not fix the loss-vs-behavior
  prompt.
- v5 fixed the loss-vs-behavior prompt but overfit and regressed several old
  prompts.
- v6 lowered the update strength but still destabilized multiple prompts.
- Interpolation between v3 and v5 did not fix the loss prompt in spot checks.
- The current best adapter remains
  `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`.

DPO gate:

- Start Stage 5 from v3, not v4/v5/v6.
- Split Stage 5 into DPO data preparation, tiny DPO smoke test, behavior check,
  and only then larger DPO.

### Stage 5: DPO

Goal:

- Start from `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`.
- Build a tiny preference dataset first.
- Run minimal DPO after the tiny dataset exists.
- Save the first tiny adapter to `outputs/dpo_lora_qwen05b_tiny`.

Status: Stage 5A data preparation, Stage 5B tiny DPO smoke test, and Stage 5C
behavior comparison are complete. Stage 5D larger DPO is blocked because Stage
5C did not pass.

Report:

```text
reports/stage5_dpo_plan.md
reports/stage5a_dpo_tiny_data_report.md
reports/stage5b_tiny_dpo_smoke_report.md
reports/stage5c_tiny_dpo_behavior_report.md
```

### Stage 5A: Tiny DPO Data Preparation

Goal:

- Build `data/processed/dpo_tiny_train.jsonl`.
- Start with 20 to 50 preference pairs.
- Include the exact loss-vs-behavior prompt, public-SFT motivation, and replay
  prompts for LoRA/SFT/DPO, data pipeline, DPO VRAM, and interview narrative.
- Prefer rejected answers that resemble real bad outputs from base/public/v4/v5/v6.

Status: completed.

Artifacts:

```text
scripts/prepare_tiny_dpo_data.py
data/processed/dpo_tiny_train.jsonl
reports/stage5a_dpo_tiny_data_report.md
```

Result:

- Preference pairs: 33
- Unique prompts: 33
- Exact loss-vs-behavior prompt included.
- Repair pairs cover loss-vs-behavior and public-SFT motivation.
- Replay pairs cover LoRA/SFT/DPO concepts, data pipeline, DPO VRAM risk, and
  interview narrative.
- Tokenizer spot check with the current v3 adapter tokenizer:
  max prompt tokens 29, max prompt+chosen tokens 100, max prompt+rejected tokens
  69.
- No DPO training was run in Stage 5A.

### Stage 5B: Tiny DPO Smoke Test

Goal:

- Verify memory feasibility on 8 GB VRAM.
- Use `configs/dpo_qwen05b.yaml`.
- Keep `batch_size=1`, `max_length=256`, `max_prompt_length=128`, tiny data,
  and minimal eval.

User should report:

- Dedicated VRAM peak.
- Shared GPU memory growth.
- System RAM growth.
- Step speed.
- Any CUDA OOM, Windows native crash, or severe slowdown.

Status: completed.

Artifacts:

```text
scripts/train_dpo.py
configs/dpo_qwen05b.yaml
outputs/dpo_lora_qwen05b_tiny
reports/stage5b_tiny_dpo_smoke_report.md
```

Result:

- Used 33 Stage 5A preference pairs.
- Completed 4 optimizer steps in about 32.8 seconds.
- Train loss: 0.9319.
- Torch max allocated memory: 2.179 GB.
- Torch max reserved memory: 4.059 GB.
- No CUDA OOM or native `python.exe` crash was observed.
- Output adapter saved and reloaded successfully.
- This is only a smoke test; behavior quality must be checked in Stage 5C.

### Stage 5C: Tiny DPO Behavior Check

Goal:

- Compare fixed prompts after tiny DPO.
- Accept tiny DPO only if prompt 7 improves without badly regressing the other
  seven prompts.

Status: completed, not accepted.

Artifacts:

```text
scripts/compare_four_outputs.py
reports/compare_outputs_four_way_dpo_tiny.jsonl
reports/stage5c_tiny_dpo_behavior_report.md
```

Result:

- Clear pass: 5 / 8 fixed prompts.
- Watch: 1 / 8 fixed prompts.
- Fail: 2 / 8 fixed prompts.
- Prompt 7, the exact loss-vs-behavior prompt, remained weak.
- Prompt 4, public-SFT motivation, regressed with unsupported claims.
- Do not expand DPO yet; revise preference data first.

### Stage 5D: Larger DPO

Goal:

- Only if Stage 5B/5C pass, expand to 50-100 pairs first and 100-200 pairs
  later.
- Keep the same VRAM safeguards and fixed-prompt regression checks.

VRAM note:

- Naive DPO can require more memory than SFT because it compares chosen and
  rejected answers and usually needs reference-policy scoring.
- On 8 GB VRAM, start with a tiny DPO smoke test only: 20 to 50 pairs,
  `batch_size=1`, short `max_length`, short `max_prompt_length`, minimal eval,
  and PEFT/reference-model sharing where possible.
- See `reports/vram_and_dpo_plan.md`.
- See `reports/stage5_dpo_plan.md`.

### Stage 6: Final Interview Package

Goal:

- README with commands.
- Experiment log.
- Loss observations.
- Before/after examples.
- Data pipeline report covering public download, custom crawling, cleaning, and
  conversion.
- Learning notebook: `notebooks/04_full_pipeline_learning.ipynb`.
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
