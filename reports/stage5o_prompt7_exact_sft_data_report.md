# Stage 5O Prompt-7 Micro-SFT Data Report

Date: 2026-05-16

## Scope

Stage 5O is a conservative micro-SFT repair from a stable previous adapter. It
exists because:

- Stage 5H/5J prompt-7 preference data gave clean DPO preference metrics but
  did not pass the visible fixed prompt.
- Stage 5K broad direct SFT repair regressed older fixed prompts.
- Stage 5M exact-failure DPO from v6 improved wording but still missed
  "not sufficient" and "badcase/regression".

## Outputs

```text
data/processed/sft_stage5o_prompt7_exact_train.jsonl
data/processed/sft_stage5o_prompt7_exact_eval.jsonl
```

## Summary

- Train rows: 196
- Eval rows: 13
- Prompt-7 train rows: 154
- Replay train rows: 42
- Prompt-7 eval rows: 6

## Design

- Intended init adapter: `outputs/sft_lora_qwen05b_stage5n_prompt7_micro_from_v6`.
- Do not train from the rejected Stage 5K SFT adapter.
- Use direct prompt-7 SFT targets that explicitly contain:
  - loss as an average training/eval optimization signal;
  - necessary but not sufficient / cannot only look at loss;
  - fixed prompt behavior;
  - badcase, regression, and old-capability checks;
  - the public-SFT LoRA/SFT/DPO project example.
- Keep replay rows for fixed prompts 1-6 and 8 to reduce regression risk.
- The original fixed prompt 7 is included as a direct repair target; the
  expanded Stage 5H prompt suite remains the held-out behavior gate.
