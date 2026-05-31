# Qwen Local LoRA SFT DPO

[中文](README.zh-CN.md) | English

A minimal local post-training project for learning and demonstrating LoRA SFT
and later DPO with `Qwen/Qwen2.5-0.5B-Instruct` on an RTX 4060 laptop GPU.

Terminology note: SFT is the supervised fine-tuning objective and data format.
LoRA is the parameter-efficient tuning method. The current training path is
LoRA SFT: supervised fine-tuning implemented by training LoRA adapters.

This project intentionally starts small. The goal is not to build a large
domain model first, but to finish a clean, reproducible, explainable training
pipeline that can be discussed in interviews. The completed technical-data loop
proved the local LoRA SFT/DPO workflow. The next planned loop is a safety
assistance project: evaluate over-refusal and unsafe over-answering, build
graded safety data, run LoRA SFT, protect older capabilities with regression
prompts, and use DPO only for concrete badcases.

## Learning Walkthrough Notebooks

For readers who want to understand the project from first principles, see
`project_learning_notebooks_zh/`. This folder is a Chinese learning walkthrough,
not a training output directory. It explains the project by starting from
concrete questions:

- how Qwen is cached, loaded, and used for one inference call;
- how the tokenizer and Qwen chat template turn messages into token IDs;
- how SFT JSONL examples become training labels and where loss is computed;
- how LoRA is attached to Qwen through PEFT adapters;
- how adapters are saved, loaded, and evaluated with fixed prompts;
- how DPO uses `prompt` / `chosen` / `rejected` preference rows;
- why the final accepted checkpoint is based on behavior gates, not only loss
  or preference accuracy.

The notebooks are safe for study by default: they mostly read project files and
print annotated code snippets. Any real inference cell is guarded by a
`RUN = False` or `RUN_INFERENCE = False` switch.

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
- Stage 2B custom technical data prepared and revised through Stage 2B.3: 142 train and 15 eval samples, plus a 28-row focused patch file.
- Stage 3B custom-data LoRA SFT completed and saved `outputs/sft_lora_qwen05b_custom`.
- Stage 4B base vs public-SFT vs custom-SFT comparison completed.
- Stage 2B.2 badcase patch tested. Training v2 from scratch regressed, while low-learning-rate continuation from v1 produced `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch` and preserved or improved 7/8 fixed prompts.
- Stage 2B.3 SFT stability gate completed before DPO. It generated 142 train / 15 eval samples plus a 28-row focused patch file, but v4/v5/v6 patch attempts were not stable enough to replace v3.
- Stage 5A tiny DPO preference data completed: `data/processed/dpo_tiny_train.jsonl` with 33 pairs. The Stage 5B start adapter remains `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`.
- Stage 5B tiny DPO smoke test completed and saved `outputs/dpo_lora_qwen05b_tiny`. It ran 4 optimizer steps in about 32.8 seconds, with no OOM/native crash, and the adapter reload check passed.
- Stage 5C fixed-prompt behavior comparison completed, but the behavior gate did not pass. DPO-tiny clearly preserved 5/8 prompts, had 1 watch prompt, and failed 2/8 prompts.
- Stage 5 follow-up revision loop completed. DPO v2/v3/v4/v5/v6 all ran without OOM. Larger naive DPO v6 is the best DPO candidate so far at 7/8 fixed prompts, but still fails the loss-vs-behavior prompt.
- Stage 5 structured behavior scoring completed. It confirms custom-SFT v3 passes 7/8 prompts; DPO v1/v2/v4/v5 pass 6/8; DPO v3 passes 1/8; and naive DPO v6 passes 7/8.
- Stage 5H prompt-7 repair data/eval design completed. It created a 278-row train preference file, a 55-row held-out eval file, a 24-prompt expanded behavior suite, and a metadata-based expanded scorer.
- Stage 5I-5P prompt-7 repair loop completed. DPO v7 and v8 reached preference accuracy 1.0 but still failed fixed prompt 7; direct SFT probes could either preserve old prompts while missing prompt 7 or force prompt 7 while regressing old prompts. No new adapter is accepted.
- Stage 6 final interview package completed. It summarizes the final narrative, before/after examples, failure review, resume bullets, and the boundary against blind DPO expansion.

Not completed yet:

- A fully accepted DPO adapter. v6 is promising, but not a complete pass.
- A stable prompt-7 repair that passes without old-prompt regression.
- Multi-GPU notes or experiments.
- Stage 7 safety-assistance data, evaluation, SFT, and DPO loop.

Planned next direction:

- Stage 7 will use a safety-sensitive but help-oriented task: improving the
  model's ability to provide bounded help instead of either refusing too much
  or giving unsafe details.
- The first artifact is not training data. It is a held-out evaluation suite
  with risk levels, expected behavior, and transparent scoring rules.
- The first SFT target is about 1,500 examples across risk levels and answer
  skills, with a separate held-out eval set.
- DPO will be used after SFT only for answers that still fail the behavior
  gate, using `prompt` / `chosen` / `rejected` preference pairs.
- Every accepted adapter must pass both the new safety gate and old technical
  regression prompts.

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

## Stage 7 Planned Safety Loop

The next interview-facing project is:

```text
Safety-sensitive assistance improvement:
from over-refusal to bounded, useful help
```

The model will be evaluated on two failure modes:

- over-refusal: the user asks for legitimate help in a risky situation, but the
  model refuses without useful support;
- unsafe over-answering: the model gives operational or dangerous details when
  it should refuse that part and redirect to safe alternatives.

The planned loop is:

```text
baseline generation
  -> graded safety evaluation suite
  -> structured safety scorer
  -> badcase analysis
  -> 1,500-row SFT data construction
  -> LoRA SFT
  -> safety gate + old technical regression gate
  -> DPO data from remaining badcases
  -> DPO training
  -> final acceptance or rollback
```

Planned files:

```text
data/safety/eval_safety_prompts.jsonl
data/safety/sft_safety_train.jsonl
data/safety/sft_safety_eval.jsonl
data/safety/dpo_safety_train.jsonl
scripts/prepare_safety_sft_data.py
scripts/score_safety_outputs.py
reports/stage7_safety_eval_design.md
reports/stage7_safety_baseline_report.md
```

The safety policy for this project is deliberately conservative: train the
model to refuse concrete harmful instructions, preserve useful non-dangerous
support, encourage emergency or professional help when appropriate, and explain
safe next steps without giving operational harm details.

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

Prepare Stage 2B.3 data and focused patch file:

```powershell
python scripts\prepare_custom_technical_data.py `
  --raw_sources_file data\raw\custom_sources.jsonl `
  --cleaned_chunks_file data\raw\custom_cleaned_chunks.jsonl `
  --instruction_seed_file data\raw\custom_instruction_seed.jsonl `
  --train_file data\processed\custom_sft_train.jsonl `
  --eval_file data\processed\custom_sft_eval.jsonl `
  --stage2b3_patch_train_file data\processed\custom_sft_stage2b3_patch_train.jsonl `
  --stage2b3_loss_repeats 12 `
  --eval_ratio 0.1 `
  --max_doc_samples 20 `
  --seed 42
```

Stage 5A data and planned first DPO config:

```text
data/processed/dpo_tiny_train.jsonl
configs/dpo_qwen05b.yaml
```

It starts from:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

Stage 5H prompt-7 data and expanded behavior gate:

```text
data/processed/dpo_stage5h_prompt7_train.jsonl
data/processed/dpo_stage5h_prompt7_eval.jsonl
data/samples/custom_technical_prompts_expanded_stage5h.jsonl
scripts/score_expanded_behavior_outputs.py
```

Stage 5J-5P repair-loop artifacts:

```text
configs/dpo_qwen05b_v7_stage5h.yaml
configs/dpo_qwen05b_v8_stage5m_from_v6.yaml
data/processed/dpo_stage5m_exact_prompt7_train.jsonl
data/processed/sft_stage5n_prompt7_micro_train.jsonl
data/processed/sft_stage5o_prompt7_exact_train.jsonl
reports/stage5j_to_5p_prompt7_repair_report.md
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

Continue Stage 3B from the best custom adapter after the Stage 2B.2 badcase
patch:

```powershell
python scripts\train_sft_lora.py `
  --init_adapter_path outputs\sft_lora_qwen05b_custom `
  --train_file data\processed\custom_sft_train.jsonl `
  --eval_file data\processed\custom_sft_eval.jsonl `
  --output_dir outputs\sft_lora_qwen05b_custom_v3_from_v1_patch `
  --max_length 512 `
  --batch_size 1 `
  --grad_accum 4 `
  --epochs 2 `
  --lr 5e-5 `
  --logging_steps 10 `
  --eval_steps 30 `
  --save_steps 30 `
  --report_to none `
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
Stage 3B custom LoRA SFT, Stage 4B three-way comparison, Stage 2B.2 badcase
patch regression testing, Stage 2B.3 SFT stability gating, Stage 5 tiny DPO
smoke tests, candidate-derived DPO retries, a larger naive DPO probe, and DPO
VRAM notes.
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
- [Stage 2B.2 badcase patch report](reports/stage2b2_badcase_patch_report.md)
- [Stage 2B.3 SFT stability gate report](reports/stage2b3_sft_stability_gate_report.md)
- [Stage 5 DPO plan](reports/stage5_dpo_plan.md)
- [Stage 5A tiny DPO data report](reports/stage5a_dpo_tiny_data_report.md)
- [Stage 5B tiny DPO smoke report](reports/stage5b_tiny_dpo_smoke_report.md)
- [Stage 5C tiny DPO behavior report](reports/stage5c_tiny_dpo_behavior_report.md)
- [Stage 5 DPO revision loop report](reports/stage5_dpo_revision_loop_report.md)
- [Stage 5 candidate DPO v4/v5 report](reports/stage5_candidate_dpo_v4_v5_report.md)
- [Stage 5 larger naive DPO v6 report](reports/stage5g_naive_dpo_v6_report.md)
- [Stage 5H prompt-7 data and expanded eval design](reports/stage5h_prompt7_data_and_eval_design.md)
- [Stage 5J-5P prompt-7 repair report](reports/stage5j_to_5p_prompt7_repair_report.md)
- [Final project summary zh](reports/final_project_summary_zh.md)
- [Stage 6 final interview package](reports/stage6_final_interview_package.md)
- [Next chat handoff after Stage 5G](reports/next_chat_handoff_stage5g.md)
- [Stage 5 structured behavior score report](reports/stage5_structured_behavior_score_report.md)
- [VRAM and DPO plan](reports/vram_and_dpo_plan.md)

## Next Step

Stage 5A/B/C through Stage 5P are complete, and Stage 6 packaging is complete.
v6 remains the best DPO candidate artifact at 7/8 fixed prompts, but the core
loss-vs-behavior gate still did not pass in any accepted adapter:

1. Review `reports/stage5_dpo_revision_loop_report.md`.
2. Review `reports/stage5_candidate_dpo_v4_v5_report.md`.
3. Review `reports/stage5g_naive_dpo_v6_report.md`.
4. Review `reports/stage5_structured_behavior_score_report.md`.
5. Review `reports/stage5j_to_5p_prompt7_repair_report.md`.
6. Review `reports/final_project_summary_zh.md`.
7. Review `reports/stage6_final_interview_package.md`.
8. Keep `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch` as the conservative recommended checkpoint.
9. Treat DPO v6 as the best DPO artifact, not the default recommendation.
10. Stop adding technical-task DPO/SFT steps until a broader prompt-7 curriculum is designed.
11. Start Stage 7 by designing the safety evaluation suite before generating training data.
12. Build the first safety scorer and baseline report, then use the observed failures to construct SFT data.

## Next Chat

For a new empty chat, start by asking the assistant to read:

```text
reports/next_chat_handoff_stage5g.md
reports/project_context_for_next_chat.md
reports/stage5g_naive_dpo_v6_report.md
reports/stage5j_to_5p_prompt7_repair_report.md
reports/final_project_summary_zh.md
reports/stage6_final_interview_package.md
reports/stage5_structured_behavior_score_report.md
PROJECT_RUNBOOK.md
notebooks/04_full_pipeline_learning.ipynb
```

Then continue with analysis/packaging, not more blind DPO. The important story
is that loss and preference accuracy were insufficient without behavior-gate
success.
