# Stage 5A.3 Tiny DPO v3 Data Report

Date: 2026-05-15

## Scope

Stage 5A.3 adds exact-bad-output preference pairs after Stage 5C.2 still failed
the loss-vs-behavior behavior gate.

Output:

```text
data/processed/dpo_tiny_v3_train.jsonl
```

## Dataset Summary

- Base v2 rows: 47
- Added exact repair rows: 10
- Total v3 rows: 57
- Unique prompts: 45
- Prompt length min/avg/max chars: 12 / 35.2 / 63
- Chosen length min/avg/max chars: 69 / 118.5 / 189
- Rejected length min/avg/max chars: 36 / 56.1 / 156

## Design Change

The rejected answers now include the actual failed DPO-tiny v2 outputs for the
loss-vs-behavior and public-SFT motivation prompts. The chosen answers are short
and explicit:

- loss is necessary but not sufficient
- fixed prompt behavior is the gate
- public-SFT is a baseline and badcase finder
- Stage 2B is data repair, not building a model from zero
- unsupported project-duration claims must be rejected

Stage 5B.3 should still start from the same SFT v3 adapter, not from a previous
DPO adapter.
