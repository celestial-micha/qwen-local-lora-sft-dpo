# Next Chat Handoff After Stage 5G

Date: 2026-05-16

## Read This First

This is the compact handoff for a new empty chat. The project directory is:

```text
D:\coding\qwen lorar sft\qwen-local-lora-sft-dpo
```

The current conservative recommended checkpoint is still:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

The best DPO experiment artifact so far is:

```text
outputs/dpo_lora_qwen05b_naive_v6
```

Do not confuse those two statements. The SFT v3 adapter remains the conservative
recommendation because it is stable and well understood. DPO naive v6 is the
best DPO candidate because it reached 7 / 8 fixed prompts, but it still failed
the core loss-vs-behavior prompt.

## One-Sentence Project Story

This project builds a local, reproducible Qwen2.5-0.5B LoRA SFT/DPO learning
pipeline on an RTX 4060 Laptop GPU, using fixed prompts and structured scoring
to show that loss and preference metrics are not enough unless behavior gates
also pass.

## Experiment Timeline

| Stage | Result | Decision |
|---|---|---|
| Stage 1 base inference | Qwen2.5-0.5B loads locally; base confuses LoRA/SFT/DPO with unrelated concepts | Use fixed badcases to drive data |
| Stage 2A public data | `llm-wizard/alpaca-gpt4-data-zh`, 1003 train / 111 eval | Good baseline data |
| Stage 3A public SFT | `outputs/sft_lora_qwen05b_public`; final train loss 1.7558 | Training pipeline works |
| Stage 4A public compare | public-SFT still fails target technical concepts | Need custom technical data |
| Stage 2B custom data | 142 train / 15 eval, plus later 28-row focused patch | Badcase-driven data loop works |
| Stage 3B custom SFT v1 | `outputs/sft_lora_qwen05b_custom`; improved 6 / 8 fixed prompts | Good base for patching |
| Stage 3B.2 v3 continuation | `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`; 7 / 8 fixed prompts | Current conservative checkpoint |
| Stage 2B.3 SFT patch attempts | v4 did not fix prompt 7; v5 fixed prompt 7 but regressed old prompts; v6 still unstable; interpolation did not help | Keep SFT v3 |
| Stage 5 DPO v1/v2/v3 | all ran without OOM; v1/v2 scored 6 / 8; v3 scored 1 / 8 | Tiny DPO data too brittle |
| Stage 5 candidate v4/v5 | both ran without OOM; both scored 6 / 8 | Candidate data helped stability but not enough |
| Stage 5G naive v6 | 192 train / 24 eval, separate frozen reference model, no OOM, scored 7 / 8 | Best DPO candidate; still not full pass |
| Stage 5H prompt-7 design | 278 train / 55 eval candidate data plus 24-prompt expanded gate; no training run | Ready for review before DPO v7 |

## DPO Run Table

| Run | Data | Ref Mode | Steps | Runtime | Final Eval | VRAM | Behavior |
|---|---:|---|---:|---:|---|---|---|
| DPO v1 | 33 train | PEFT/shared | 4 | 32.8s | no eval split | max allocated 2.179 GB | 6 / 8 structured |
| DPO v2 | 47 train | PEFT/shared | 5 | 43.9s | no eval split | max allocated 2.180 GB | 6 / 8 structured |
| DPO v3 | 57 train | PEFT/shared | 14 | 64.7s | no eval split | max allocated 2.191 GB | 1 / 8 structured |
| Candidate v4 | 20 train / 5 eval | PEFT/shared | 2 | 28.0s | eval acc 0.8000 | max allocated 2.456 GB | 6 / 8 structured |
| Candidate v5 | 28 train / 7 eval | PEFT/shared | 7 | 49.7s | eval acc 0.8571 | max allocated 2.486 GB | 6 / 8 structured |
| Naive v6 | 192 train / 24 eval | separate frozen ref | 48 | 271.4s | eval acc 1.0000 | max allocated 3.415 GB, max reserved 8.686 GB | 7 / 8 structured |

## Important Findings

1. Hardware is not the main blocker for Qwen2.5-0.5B LoRA DPO on this machine.
   Even the larger separate-reference v6 run completed without OOM.

2. Data size and replay balance matter. Moving from tiny/focused sets to a
   192-row balanced set improved behavior from 6 / 8 to 7 / 8 and fixed
   public-SFT motivation.

3. Preference metrics are not behavior gates. v6 reached eval preference
   accuracy 1.0, but still failed prompt 7 under fixed-prompt scoring.

4. Prompt 7 is the real remaining conceptual bottleneck:

```text
为什么不能只看 loss 判断一次 SFT 是否成功？
```

The model often says "不能只看 loss", but fails to clearly include all required
ideas: loss as an average training objective signal, fixed-prompt behavior,
badcase review, old-capability regression, and the public-SFT example.

5. Narrow patches can regress old behavior. This happened in SFT v5 and DPO v3.
   Replay coverage and held-out checks are mandatory.

## Problems Encountered And Fixes

| Problem | Symptom | Fix / Lesson |
|---|---|---|
| Windows dependency instability | earlier native `python.exe` crashes in training stack | keep pinned versions: transformers 4.46.3, peft 0.13.2, trl 0.12.2 |
| Hugging Face cache confusion | setting `TRANSFORMERS_CACHE=.hf_cache` made model lookup fail | use `HF_HOME=.hf_cache`; remove `TRANSFORMERS_CACHE` |
| PEFT remote config warning | save/load tries Hugging Face remote config and proxy refuses | harmless warning; adapter still saves/reloads |
| From-scratch SFT regression | v2 from scratch damaged solved prompts | continue from best adapter with low LR instead |
| Focused patch overfit | v5 fixed one prompt but regressed several others | add replay and use fixed-prompt gate |
| Tiny DPO brittleness | v1/v2/v4/v5 stuck at 6 / 8, v3 regressed badly | increase data diversity and held-out eval |
| Argparse override bug | config `separate_ref_model: true` became `false` in logs | set argparse store_true default to `None`; rerun true separate-reference v6 |
| Good eval but failed behavior | v6 eval accuracy 1.0 but prompt 7 failed | keep structured fixed-prompt scoring as final gate |

## Current Key Files

Core reports:

```text
reports/project_context_for_next_chat.md
reports/next_chat_handoff_stage5g.md
reports/stage5g_naive_dpo_v6_report.md
reports/stage5_structured_behavior_score_report.md
reports/stage5_dpo_plan.md
reports/experiment_log.md
PROJECT_RUNBOOK.md
README.md
README.zh-CN.md
notebooks/04_full_pipeline_learning.ipynb
```

Core scripts:

```text
scripts/train_sft_lora.py
scripts/train_dpo.py
scripts/compare_four_outputs.py
scripts/score_fixed_prompt_outputs.py
scripts/prepare_larger_dpo_v6_data.py
```

Latest DPO config and data:

```text
configs/dpo_qwen05b_v6_naive.yaml
data/processed/dpo_larger_v6_train.jsonl
data/processed/dpo_larger_v6_eval.jsonl
reports/compare_outputs_four_way_dpo_naive_v6.jsonl
```

Stage 5H design artifacts:

```text
scripts/prepare_stage5h_prompt7_data.py
scripts/score_expanded_behavior_outputs.py
data/processed/dpo_stage5h_prompt7_train.jsonl
data/processed/dpo_stage5h_prompt7_eval.jsonl
data/samples/custom_technical_prompts_expanded_stage5h.jsonl
reports/stage5h_prompt7_data_and_eval_design.md
```

## Next Stage Proposal

### Stage 5H: Prompt 7 Repair Data

Goal: make a cleaner loss-vs-behavior preference/eval set without breaking the
other seven prompts.

Status: data/eval design completed on 2026-05-16; do not treat this as a DPO
result because no DPO v7 training has been run yet.

Suggested work:

- Review `reports/stage5h_prompt7_data_and_eval_design.md`.
- Check the 278-row train and 55-row eval preference files.
- Keep the 72 new prompt-7 train pairs and 24 held-out prompt-7 eval pairs
  only if their near-miss rejected answers look realistic.
- Keep replay rows for prompts 1-6 and 8.
- Do not rely only on generated train preference accuracy.

### Stage 5I: Expanded Behavior Gate

Goal: avoid overfitting the 8 fixed prompts.

Suggested work:

- Use `data/samples/custom_technical_prompts_expanded_stage5h.jsonl`.
- Keep the old 8 prompts unchanged as regression tests.
- Use `scripts/score_expanded_behavior_outputs.py` for metadata-based scoring.
- Require prompt-7 held-outs to pass before accepting DPO v7.

### Stage 5J: DPO v7 Probe

Only after Stage 5H/5I data exists:

- Start from SFT v3 again, not from DPO v6.
- Use separate frozen reference model again.
- Use roughly 200-300 train pairs and 40 eval pairs.
- Conservative starting config: max_length 384, max_prompt_length 160,
  batch size 1, grad_accum 4, learning rate 5e-6 to 8e-6, beta 0.08.
- Run fixed-prompt and expanded-prompt behavior checks immediately after
  training.

### Stage 6: Final Interview Package

After DPO behavior is either passed or intentionally stopped:

- Create a final experiment narrative.
- Create before/after examples.
- Write resume/interview bullets.
- Produce a small model-card style report for the best SFT and best DPO
  artifacts.

## Suggested Prompt For The Next Empty Chat

You can copy this:

```text
请先阅读这个项目：
D:\coding\qwen lorar sft\qwen-local-lora-sft-dpo

请重点阅读：
reports/next_chat_handoff_stage5g.md
reports/project_context_for_next_chat.md
reports/stage5g_naive_dpo_v6_report.md
reports/stage5_structured_behavior_score_report.md
reports/stage5_dpo_plan.md
PROJECT_RUNBOOK.md
README.zh-CN.md
README.md
notebooks/04_full_pipeline_learning.ipynb

读完后，请先用中文总结当前状态、推荐 checkpoint、最好 DPO 候选、剩余问题和下一阶段计划。然后审核 Stage 5H 已生成的 prompt 7 preference/eval 数据和 expanded behavior gate：确认数据分布、near-miss rejected answers 和 scorer 规则是否合理。不要直接继续加 DPO step；只有数据和评测设计通过后，才从 SFT v3 出发准备 DPO v7。
```
