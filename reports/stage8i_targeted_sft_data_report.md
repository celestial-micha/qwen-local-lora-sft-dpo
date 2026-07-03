# Stage 8I Targeted SFT v4 Data Report

Date: 2026-07-03

## Purpose

Stage 8E SFT v2 remains the strongest expanded candidate, but it has two weak
areas: DPO vs SFT and public-SFT diagnostic value. This patch targets those
weak areas and replays the six stronger areas to reduce regression risk.

## Outputs

```text
data/processed/custom_sft_expanded_v4_targeted_train.jsonl
data/processed/custom_sft_expanded_v4_targeted_eval.jsonl
```

## Size

- Train rows: 1500
- Eval rows: 160

## Area Balance

- DPO 与 SFT 区别: train 484, eval 38
- DPO 显存风险: train 91, eval 14
- LoRA 定义与边界: train 87, eval 14
- SFT 与 LoRA 关系: train 79, eval 13
- loss 与行为验收: train 85, eval 14
- public-SFT 诊断价值: train 491, eval 40
- 固定 Prompt 与扩展评测: train 88, eval 13
- 自采集技术数据管线: train 95, eval 14
