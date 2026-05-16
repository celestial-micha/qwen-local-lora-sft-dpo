# Stage 5M Exact Prompt-7 DPO Data Report

Date: 2026-05-16

## Scope

Stage 5M prepares a deliberate exact-failure DPO repair set. It uses actual
failed prompt-7 outputs from DPO v6, DPO v7, and Stage 5K SFT repair as
rejected answers, then mixes compact replay pairs for the seven stable areas.

## Outputs

```text
data/processed/dpo_stage5m_exact_prompt7_train.jsonl
data/processed/dpo_stage5m_exact_prompt7_eval.jsonl
```

## Summary

- Train rows: 162
- Eval rows: 41
- Start adapter for the intended probe: `outputs/dpo_lora_qwen05b_naive_v6`
- This is a deliberate DPO-on-DPO repair probe, not the conservative default
  recommendation.
