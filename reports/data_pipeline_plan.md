# Data Pipeline Plan

Date: 2026-05-14

## Project Story

The project should not stop at downloading one public dataset. The stronger
interview story is a two-loop plan:

```text
Loop A: public instruction dataset
  -> convert
  -> train LoRA SFT
  -> compare base vs SFT
  -> prove the training pipeline is stable

Loop B: self-collected data
  -> crawl or collect preferred content
  -> clean and filter
  -> rewrite into instruction-answer samples
  -> train or continue-train LoRA SFT
  -> compare against Loop A
```

This order is intentional. The public dataset loop keeps the first real SFT run
controlled and reproducible. After that, the custom data loop becomes a data
engineering and model-behavior improvement story, rather than a debugging mess
where training bugs and dirty data are mixed together.

## Current Decision

Use the current `llm-wizard/alpaca-gpt4-data-zh` dataset as the first real SFT
baseline. Do not discard it.

The public-data LoRA SFT adapter has now been trained, loaded, and compared.
Stage 4A showed that it did not fix LoRA/SFT/DPO concept confusion. Next, add
the self-collected technical-data pipeline.

Terminology note:

- SFT is the supervised fine-tuning objective.
- LoRA is the parameter-efficient method used to train adapters.
- The current and next adapters are LoRA SFT adapters.

## Target Final Pipeline

```text
Stage 0: project scaffold and environment
Stage 1: base inference and demo smoke test
Stage 2A: public SFT dataset baseline
Stage 3A: real LoRA SFT on public data
Stage 4A: base vs public-SFT comparison
Stage 2B: self-collected data crawling and cleaning
Stage 3B: LoRA SFT using custom technical data
Stage 4B: compare base vs public-SFT vs custom-SFT
Stage 5: DPO after SFT behavior is stable
Stage 6: interview package
```

## Stage 2A: Public Dataset Baseline

Status: completed.

Purpose:

- Prove that data conversion, tokenization, training, saving, and loading work
  on a real dataset.
- Keep data quality and format risk low.
- Create a baseline adapter for later comparison.

Current artifacts:

- Raw: `data/raw/alpaca_gpt4_data_zh_1200.jsonl`
- Train: `data/processed/sft_train.jsonl`
- Eval: `data/processed/sft_eval.jsonl`
- Report: `reports/stage2_sft_data_report.md`

## Stage 3A: Public Dataset SFT

Status: completed.

Goal:

- Train `outputs/sft_lora_qwen05b_public`.
- Record train loss, eval loss, training time, and any memory issues.
- Run fixed prompts through both base and SFT adapter.

Result:

- Adapter: `outputs/sft_lora_qwen05b_public`
- Final train loss: 1.7558
- Eval loss at step 100: 1.8263
- Report: `reports/stage3a_public_lora_sft_report.md`

Key finding:

- General public instruction data did not fix LoRA/SFT/DPO technical concept
  confusion. This makes Stage 2B necessary, not optional.

Recommended command:

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

## Stage 4A: Public-SFT Comparison

Status: completed.

Artifacts:

- `reports/compare_outputs_public_sft.jsonl`
- `reports/compare_base_sft.md`
- `reports/stage4a_public_sft_comparison_report.md`

Finding:

- The public-data adapter did not fix the project-specific LoRA/SFT/DPO concept
  mistakes.
- This is useful negative evidence. It shows why a targeted custom technical
  dataset is necessary.

## Stage 2B: Self-Collected Data Pipeline

Status: completed, revised after Stage 3B feedback, patched in Stage 2B.2, and
expanded in Stage 2B.3 for the DPO-before stability gate.

Purpose:

- Demonstrate real data work: collection, cleaning, filtering, formatting, and
  dataset versioning.
- Build a small dataset that reflects the user's preferred topics and answer
  style.
- Avoid pretending that model tuning is only `load_dataset(...)`.

Suggested first scope:

- 100 to 300 cleaned samples for the first custom-data pass.
- Chinese technical learning content is a good first topic because it matches
  this project: LoRA, SFT, DPO, model training, CUDA, Hugging Face, debugging,
  and experiment reporting.
- Avoid copyrighted full-text book/article replication. Prefer short excerpts,
  public documentation, own notes, permissive sources, or manually written
  summaries.

Planned raw files:

- `data/raw/custom_sources.jsonl`: one source document or crawled page per row
- `data/raw/custom_cleaned_chunks.jsonl`: cleaned and deduplicated text chunks
- `data/raw/custom_instruction_seed.jsonl`: candidate instruction-answer rows

Planned processed files:

- `data/processed/custom_sft_train.jsonl`
- `data/processed/custom_sft_eval.jsonl`
- optional mixed dataset: `data/processed/mixed_sft_train.jsonl`

Current result:

- Script: `scripts/prepare_custom_technical_data.py`
- Sources: 10 project-owned technical notes
- Accepted cleaned chunks: 96
- Rejected chunks: 12
- Instruction-answer seed samples: 157
- Train samples: 142
- Eval samples: 15
- Stage 2B.3 focused patch train samples: 28
- Report: `reports/stage2b_custom_technical_data_report.md`
- Patch report: `reports/stage2b2_badcase_patch_report.md`
- Stability gate report: `reports/stage2b3_sft_stability_gate_report.md`

The first pass uses project-owned notes plus curated LoRA/SFT/DPO concept seeds.
This keeps the dataset reproducible and avoids copying long external web pages.
The script keeps an optional URL input path for future crawling iterations.

Stage 3B feedback:

- The initial 160-sample version was too generic and produced hallucinated
  answers after training.
- The revised version reduces generic project-record summaries and adds targeted
  QA samples for the exact badcases.
- Stage 2B.2 adds 8 focused badcase samples for public-SFT motivation and
  loss-vs-behavior. It also teaches an important engineering lesson: data
  patches need regression testing because a small patch can still break old
  behavior if retrained from scratch.
- Stage 2B.3 adds a narrower loss-vs-behavior patch plus replay samples, and
  confirms that "fix one prompt without regressions" is the real DPO gate.
- This demonstrates the real data loop: train, compare fixed prompts, find
  badcases, then patch the dataset.

## Stage 3B: Custom-Data SFT

Status: completed for the custom-only adapter.

Goal:

- Train `outputs/sft_lora_qwen05b_custom`.
- Compare it against the base model and `outputs/sft_lora_qwen05b_public`.
- Use `data/samples/custom_technical_prompts.jsonl` as the fixed technical
  prompt set.

Result:

- Adapter: `outputs/sft_lora_qwen05b_custom`
- Trainable params: 4,399,104
- Final train loss: 0.4656
- Best observed eval loss: 0.8311 around epoch 5
- Runtime: about 12.3 minutes
- Report: `reports/stage3b_custom_lora_sft_report.md`

Important note:

- The 10-epoch run improved target behavior, but eval loss started drifting up
  after the best checkpoint. This is a small-data overfitting signal.
- Stage 2B.2 then tested three variants. Stage 2B.3 tested additional v4/v5/v6
  patch attempts. The current best local adapter remains
  `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`.

## Stage 4B: Three-Way Comparison

Status: completed.

Artifacts:

- `scripts/compare_three_outputs.py`
- `reports/compare_outputs_three_way_custom.jsonl`
- `reports/stage4b_three_way_comparison_report.md`

Finding:

- Custom-SFT strongly improved 6 of 8 fixed technical prompts.
- Two prompts remain weak: the Stage 2B motivation explanation and the
  loss-vs-behavior explanation.
- Stage 2B.2 improved the Stage 2B motivation prompt when the model was
  continued from v1, but the loss-vs-behavior prompt remained weak.
- Stage 2B.3 fixed the loss prompt only in an overfit focused run that broke old
  prompts, so Stage 5 should start from v3 and begin with tiny DPO rather than
  larger DPO.

## Stage 2B.2 Result: Patch, Retrain, Regression Test

Stage 2B.2 was intentionally small: 8 new samples targeting the two remaining
badcases. The results were useful because they showed both a failure mode and a
safer workflow.

| Variant | Output | Result |
|---|---|---|
| v2 scratch, 5 epochs | `outputs/sft_lora_qwen05b_custom_v2` | Regressed on core LoRA/SFT prompts |
| v2 scratch, 10 epochs checkpoint 100 | `outputs/sft_lora_qwen05b_custom_v2_10ep/checkpoint-100` | Still regressed despite better loss |
| v3 continue from v1, 2 epochs, low LR | `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch` | Preserved or improved 7/8 prompts |

The data lesson:

```text
Do not judge a patch only by loss.
Use the fixed prompts as a regression suite.
Prefer low-learning-rate continuation or replay when preserving old behavior matters.
```

## Stage 2B.3 Result: SFT Gate Before DPO

Stage 2B.3 tried to fix the final loss-vs-behavior prompt while preserving the
other seven fixed prompts.

| Variant | Output | Result |
|---|---|---|
| v4 full Stage 2B.3 data | `outputs/sft_lora_qwen05b_custom_v4_stage2b3_loss_patch` | Mostly preserved old behavior but did not fix prompt 7 |
| v5 focused patch | `outputs/sft_lora_qwen05b_custom_v5_stage2b3_focused_patch` | Fixed prompt 7 but regressed several old prompts |
| v6 lower-strength focused patch | `outputs/sft_lora_qwen05b_custom_v6_stage2b3_balanced_patch` | Still unstable |
| v7 interpolation probe | local alpha 0.15/0.25/0.40 adapters | Spot-check did not fix prompt 7 |

The gate decision:

```text
Do not start DPO automatically.
Review v3 vs the failed v4/v5/v6 attempts with the user first.
```

After review, the Stage 5 decision is to start DPO from v3 and split DPO into
small stages:

```text
Stage 5A: tiny preference data
Stage 5B: tiny DPO smoke test
Stage 5C: fixed-prompt DPO behavior check
Stage 5D: larger DPO only if tiny works
```

See `reports/stage5_dpo_plan.md`.

## Cleaning Rules

Minimum cleaning checklist:

- Remove navigation bars, ads, cookie banners, repeated footers, and boilerplate.
- Normalize whitespace and punctuation.
- Drop very short chunks and very long chunks.
- Deduplicate exact and near-duplicate text.
- Keep source URL or source note for traceability.
- Filter unsafe, low-quality, spam-like, or off-topic content.
- Convert only useful content into instruction-answer pairs.
- Keep a small manual review file of accepted and rejected examples.

## Custom Instruction Formats

The custom dataset should not be only raw scraped text. Convert it into tasks
that teach the target behavior:

```json
{
  "instruction": "用三点解释 LoRA 微调为什么适合个人 GPU 学习。",
  "input": "",
  "output": "第一，LoRA 只训练少量 adapter 参数..."
}
```

Good task types:

- Concept explanation
- Step-by-step debugging
- Command explanation
- Experiment-log summarization
- Before/after output analysis
- Beginner-friendly analogy
- Interview-style project explanation

## Comparison Plan

Use the same fixed prompt set across three models:

- Base Qwen
- Public-data SFT adapter
- Custom or mixed-data SFT adapter

The final report should answer:

- Did the public-data SFT improve general instruction following?
- Did custom data improve the target style or topic accuracy?
- Did custom data introduce overfitting, verbosity, or hallucination?
- Which examples became better, worse, or unchanged?

Current Stage 4B answer:

- Public-data SFT proved the training pipeline but did not fix target concepts.
- Custom-data SFT fixed most target concepts, especially LoRA/SFT/DPO and DPO
  VRAM-risk prompts.
- Stage 2B.2 showed that badcase patches can regress if trained from scratch.
- Stage 2B.3 shows the remaining loss-vs-behavior badcase is hard to patch with
  tiny SFT updates without regression, which should be discussed before DPO.

## Interview Talking Points

Short version:

> I first used a public Chinese Alpaca-style dataset to establish a reproducible
> LoRA SFT baseline. After the baseline trained and loaded correctly, I built a
> second data loop for self-collected content: crawling, boilerplate removal,
> deduplication, filtering, converting into instruction-answer pairs, and then
> comparing a custom-data adapter against the public-data adapter.

This tells a better story than simply saying "I downloaded a dataset and
fine-tuned a model."
