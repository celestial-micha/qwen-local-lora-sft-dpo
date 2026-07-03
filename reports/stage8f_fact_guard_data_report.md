# Stage 8F Fact-Guard SFT Data Report

Date: 2026-07-03

## Purpose

Stage 8E SFT v2 improved the expanded behavior score, but manual review still
found project-fact drift. This v3 data patch keeps the expanded scale while
making answers shorter, more factual, and less likely to repeat bad concepts as
if they were true.

## Outputs

```text
data/processed/custom_sft_expanded_v3_train.jsonl
data/processed/custom_sft_expanded_v3_eval.jsonl
```

## Size

- Train rows: 1500
- Train unique prompts: 493
- Eval rows: 160
- Eval unique prompts: 160

## Area Balance

- LoRA 定义与边界: train 176, eval 20
- SFT 与 LoRA 关系: train 187, eval 20
- DPO 与 SFT 区别: train 201, eval 20
- public-SFT 诊断价值: train 180, eval 20
- 自采集技术数据管线: train 189, eval 20
- DPO 显存风险: train 192, eval 20
- loss 与行为验收: train 197, eval 20
- 固定 Prompt 与扩展评测: train 178, eval 20

## Intended Training

Continue from the Stage 8E v2 SFT adapter with a lower learning rate:

```text
outputs/sft_lora_qwen05b_stage8_expanded_v2
  -> outputs/sft_lora_qwen05b_stage8_expanded_v3
```
