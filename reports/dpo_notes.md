# DPO Notes

Use this report after DPO training.

Current status: Stage 5 is planned but not run yet. The first DPO run should
start from `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch` and should be a
tiny smoke test, not full DPO.

Detailed plan: `reports/stage5_dpo_plan.md`

## VRAM Risk

Observed local memory:

- LoRA SFT training: about `5.5 GB / 8 GB`
- Adapter inference: about `1.2 GB / 8 GB`

DPO can use more memory than SFT because it compares `chosen` and `rejected`
answers and usually needs reference-policy scoring. A naive implementation with
two full model copies may exceed 8 GB VRAM or fall back into shared memory,
which would slow training heavily.

Stage 5 split:

- Stage 5A: prepare `data/processed/dpo_tiny_train.jsonl`.
- Stage 5B: run tiny DPO with `configs/dpo_qwen05b.yaml`.
- Stage 5C: compare fixed prompts after tiny DPO.
- Stage 5D: expand DPO only if memory and behavior are acceptable.

First DPO should be a smoke test:

- 20 to 50 pairs
- `batch_size=1`
- short `max_length`, initially 256
- short `max_prompt_length`, initially 128
- minimal or disabled eval during the first test
- LoRA/PEFT reference sharing where possible

Detailed plan: `reports/vram_and_dpo_plan.md`

Conservative local config: `configs/dpo_qwen05b.yaml`

## Preference Data

- Number of pairs: start with 20-50.
- Chosen style: concise, correct, project-specific answers.
- Rejected style: real or realistic bad outputs from base/public/v4/v5/v6.
- Required topics: loss-vs-behavior, public-SFT motivation, LoRA/SFT/DPO replay,
  data pipeline, 8GB DPO memory risk.

## Memory Observations To Record

- Dedicated GPU memory peak:
- Shared GPU memory growth:
- System RAM growth:
- Step speed:
- CUDA OOM or native crash:
- Machine usability:

## Training

- Final loss:
- Reward margin:
- Problems:

## Observations
