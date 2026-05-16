# Next Chat Handoff After Stage 6

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
best DPO candidate because it reached 7 / 8 fixed prompts. Later v7/v8 also
stayed at 7 / 8 and did not beat v6; SFT repair probes either missed prompt 7
or regressed old prompts.

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
| Stage 5H prompt-7 design | 278 train / 55 eval candidate data plus 24-prompt expanded gate | Data/eval design completed before more training |
| Stage 5I expanded v6 eval | v6 scored 7 / 24 expanded prompts and 0 / 13 loss-vs-behavior prompts | v6 not accepted |
| Stage 5J DPO v7 | preference eval accuracy 1.0, fixed gate 7 / 8 | prompt 7 still failed |
| Stage 5K/5N/5O/5P SFT probes | Stage 5N stable 7 / 8; Stage 5O passed prompt 7 but regressed to 4 / 8; Stage 5P ended 6 / 8 | no SFT repair accepted |
| Stage 5M DPO v8 | preference eval accuracy 1.0, fixed gate 7 / 8 | not better than v6 |
| Stage 6 final package | final interview narrative, before/after examples, failure review, resume bullets | completed; no more blind DPO |

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

3. Preference metrics are not behavior gates. v6, v7, and v8 can look strong
   on preference metrics, but still fail prompt 7 under fixed-prompt scoring.

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
| Good eval but failed behavior | v6/v7/v8 preference metrics looked strong but prompt 7 failed | keep structured fixed-prompt scoring as final gate |

## Current Key Files

Core reports:

```text
reports/project_context_for_next_chat.md
reports/next_chat_handoff_stage5g.md
reports/stage5g_naive_dpo_v6_report.md
reports/stage5j_to_5p_prompt7_repair_report.md
reports/final_project_summary_zh.md
reports/stage6_final_interview_package.md
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
scripts/score_expanded_behavior_outputs.py
scripts/prepare_larger_dpo_v6_data.py
scripts/prepare_stage5h_prompt7_data.py
scripts/prepare_stage5n_prompt7_micro_sft_data.py
```

Latest DPO config and data:

```text
configs/dpo_qwen05b_v6_naive.yaml
data/processed/dpo_larger_v6_train.jsonl
data/processed/dpo_larger_v6_eval.jsonl
reports/compare_outputs_four_way_dpo_naive_v6.jsonl
```

Stage 5H-5P artifacts:

```text
scripts/prepare_stage5h_prompt7_data.py
scripts/score_expanded_behavior_outputs.py
scripts/prepare_stage5n_prompt7_micro_sft_data.py
data/processed/dpo_stage5h_prompt7_train.jsonl
data/processed/dpo_stage5h_prompt7_eval.jsonl
data/processed/dpo_stage5m_exact_prompt7_train.jsonl
data/processed/dpo_stage5m_exact_prompt7_eval.jsonl
data/processed/sft_stage5n_prompt7_micro_train.jsonl
data/processed/sft_stage5o_prompt7_exact_train.jsonl
data/samples/custom_technical_prompts_expanded_stage5h.jsonl
reports/stage5h_prompt7_data_and_eval_design.md
reports/stage5j_to_5p_prompt7_repair_report.md
reports/final_project_summary_zh.md
reports/stage6_final_interview_package.md
```

## Next Stage Proposal

### Stage 6: Final Interview Package

Stage 6 packaging is complete. Continue polishing the presentation rather than
running more blind training:

- refine the final experiment narrative;
- polish before/after examples;
- explain why loss and preference accuracy were insufficient;
- keep SFT v3 as the conservative checkpoint and DPO v6 as the best DPO
  artifact;
- only resume training after designing a broader prompt-7 curriculum with
  stronger replay protection.

## Suggested Prompt For The Next Empty Chat

You can copy this:

```text
请先阅读这个项目：
D:\coding\qwen lorar sft\qwen-local-lora-sft-dpo

请重点阅读：
reports/next_chat_handoff_stage5g.md
reports/project_context_for_next_chat.md
reports/stage5g_naive_dpo_v6_report.md
reports/stage5j_to_5p_prompt7_repair_report.md
reports/final_project_summary_zh.md
reports/stage6_final_interview_package.md
reports/stage5_structured_behavior_score_report.md
reports/stage5_dpo_plan.md
PROJECT_RUNBOOK.md
README.zh-CN.md
README.md
notebooks/04_full_pipeline_learning.ipynb

读完后，请先用中文总结当前状态、推荐 checkpoint、最好 DPO 候选、剩余问题和下一阶段计划。重点阅读项目最终总结和 Stage 6 最终面试包，继续完善面试讲述、简历 bullet、before/after 示例或 demo flow。不要继续盲目加 DPO step；如果要恢复训练，先设计更宽的 prompt 7 curriculum 和回归保护。
```
