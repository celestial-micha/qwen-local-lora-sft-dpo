# Stage 8D Badcase Data Patch Report

Date: 2026-07-03

## Why This Patch Exists

Stage 8B used the first expanded SFT data and reached good-looking training
metrics, but Stage 8C behavior scoring regressed:

```text
old custom-SFT v3: 21 / 96
Stage 8B SFT:      19 / 96
```

Manual spot checks showed stage mixing, invented project facts, and regression
on LoRA/SFT/DPO definitions. This proves the project should not accept a
checkpoint just because eval loss improved.

## Patch Design

- Replace loose meta templates with direct concept, correction, and replay rows.
- Cover the same core areas as the 96-prompt behavior suite.
- Include explicit anti-hallucination instructions:
  do not invent stage IDs, durations, memory numbers, or pass rates.
- Keep the scale resume-friendly while making the data cleaner.

## Outputs

```text
data/processed/custom_sft_expanded_v2_train.jsonl
data/processed/custom_sft_expanded_v2_eval.jsonl
```

## Dataset Size

- Train rows: 1500
- Eval rows: 160

## Next Step

Train a conservative v2 SFT adapter from the old stable checkpoint, not from
the regressed Stage 8B adapter:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
  -> outputs/sft_lora_qwen05b_stage8_expanded_v2
```
