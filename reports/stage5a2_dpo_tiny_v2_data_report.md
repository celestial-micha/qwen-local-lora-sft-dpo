# Stage 5A.2 Tiny DPO v2 Data Report

Date: 2026-05-15

## Scope

Stage 5A.2 revises the tiny DPO preference data after Stage 5C failed the
behavior gate. It keeps the original Stage 5A data intact and adds focused pairs
for the two weak areas.

Output:

```text
data/processed/dpo_tiny_v2_train.jsonl
```

## Dataset Summary

- Base Stage 5A rows: 33
- Added focused rows: 14
- Total v2 rows: 47
- Unique prompts: 42
- Duplicate focus prompts are intentional.

Focused additions:

- `anti_unsupported_claim_v2`: 2
- `loss_behavior_v2`: 6
- `public_sft_motivation_v2`: 6

Repeated focused prompts:

- 为什么不能只看 loss 判断一次 SFT 是否成功？: 4
- 为什么 public-SFT adapter 没修正 LoRA/SFT/DPO 概念误解，反而说明 Stage 2B 有必要？: 3

Character-length checks:

| Field | Min | Avg | Max |
|---|---:|---:|---:|
| prompt | 12 | 35.5 | 63 |
| chosen | 69 | 115.0 | 189 |
| rejected | 36 | 51.4 | 65 |

## Design Changes

The v2 data explicitly rejects Stage 5C failure patterns:

- saying Stage 2B is "building the model from zero"
- inventing "three to six months"
- treating public-SFT as worthless instead of as a baseline and badcase finder
- treating loss as the only success criterion
- delaying fixed-prompt behavior checks until after larger DPO

The chosen answers are shorter and stricter than the rejected answers. They
emphasize that public-SFT validates the engineering loop but exposes target-data
coverage gaps, and that loss is necessary but not sufficient without fixed
prompt behavior checks.

## Next Gate

Run Stage 5B.2 tiny DPO from the same SFT v3 adapter:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

Then rerun Stage 5C.2 before considering any larger DPO.
