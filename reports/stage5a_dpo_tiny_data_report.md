# Stage 5A Tiny DPO Data Report

Date: 2026-05-15

## Scope

Stage 5A is complete. This stage only prepares a tiny DPO preference dataset; it
does not run DPO training.

Start adapter for the next stage remains:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

## Output

```text
data/processed/dpo_tiny_train.jsonl
```

Schema:

```json
{"prompt": "...", "chosen": "...", "rejected": "..."}
```

## Dataset Summary

- Rows: 33
- Unique prompts: 33
- Target range from plan: 20-50 preference pairs
- Exact loss-vs-behavior prompt included: yes
- Public-SFT motivation pairs included: yes
- LoRA/SFT/DPO replay pairs included: yes
- Data-pipeline and DPO-VRAM pairs included: yes
- Rejected answers are written as realistic badcase or near-miss answers, based
  on base/public/v4/v5/v6 failure patterns where possible.

Category counts:

- `data_pipeline`: 5
- `dpo_vram_and_stage_gate`: 6
- `interview_narrative`: 4
- `lora_sft_dpo_replay`: 6
- `loss_vs_behavior`: 7
- `public_sft_motivation`: 5

Character-length checks:

| Field | Min | Avg | Max |
|---|---:|---:|---:|
| prompt | 12 | 33.2 | 63 |
| chosen | 75 | 119.2 | 189 |
| rejected | 39 | 52.7 | 65 |

## Design Notes

The tiny dataset intentionally mixes two kinds of pairs:

- Repair pairs for the final weak area: loss-vs-behavior and public-SFT
  motivation.
- Replay pairs for behaviors that v3 already handled well: LoRA/SFT/DPO
  concepts, data pipeline, DPO VRAM risk, and interview narrative.

This mirrors the Stage 2B.3 lesson: optimizing one weak prompt without replay
can regress older behavior. Stage 5B should therefore treat this data as a tiny
memory-and-behavior probe, not as a final preference corpus.

## Next Gate

Do not start full DPO from this report alone. The next step is Stage 5B only:
run a tiny DPO smoke test with `configs/dpo_qwen05b.yaml`, record dedicated GPU
memory, shared GPU memory, system RAM, step speed, and any OOM/native crash.
Then Stage 5C must compare fixed prompts before any larger DPO.
