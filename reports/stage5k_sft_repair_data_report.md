# Stage 5K SFT Repair Data Report

Date: 2026-05-16

## Scope

Stage 5K converts Stage 5H preference data into chat-format SFT repair data.
This is a response to DPO v7 failing the visible prompt-7 behavior gate despite
good preference metrics.

## Outputs

```text
data/processed/sft_stage5k_prompt7_repair_train.jsonl
data/processed/sft_stage5k_prompt7_repair_eval.jsonl
```

## Summary

- Train rows: 193
- Eval rows: 55
- Loss-vs-behavior train rows: 72
- Loss-vs-behavior eval rows: 24

## Design

- Uses the Stage 5H chosen answers as direct SFT targets.
- Keeps replay rows from the Stage 5H distribution so prompt-7 repair does not
  overwrite LoRA/SFT/DPO, data-pipeline, DPO-VRAM, public-SFT motivation, or
  interview-narrative behavior.
- Intended use is low-learning-rate continuation from
  `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`, not from DPO v7.
