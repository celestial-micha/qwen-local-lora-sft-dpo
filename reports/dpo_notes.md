# DPO Notes

Use this report after DPO training.

Current status: DPO is intentionally deferred until public-SFT and custom/mixed
SFT are stable.

## VRAM Risk

Observed local memory:

- LoRA SFT training: about `5.5 GB / 8 GB`
- Adapter inference: about `1.2 GB / 8 GB`

DPO can use more memory than SFT because it compares `chosen` and `rejected`
answers and usually needs reference-policy scoring. A naive implementation with
two full model copies may exceed 8 GB VRAM or fall back into shared memory,
which would slow training heavily.

First DPO should be a smoke test:

- 20 to 50 pairs
- `batch_size=1`
- short `max_length`, initially 256
- short `max_prompt_length`, initially 128
- minimal or disabled eval during the first test
- LoRA/PEFT reference sharing where possible

Detailed plan: `reports/vram_and_dpo_plan.md`

## Preference Data

- Number of pairs:
- Chosen style:
- Rejected style:

## Training

- Final loss:
- Reward margin:
- Problems:

## Observations
