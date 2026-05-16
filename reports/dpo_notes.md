# DPO Notes

Final status as of 2026-05-16: DPO has been run through multiple probes
(v1-v8). The main conclusion is no longer "how to start DPO"; it is that DPO is
memory-feasible on this machine, but behavior gates still decide acceptance.

Best DPO artifact:

```text
outputs/dpo_lora_qwen05b_naive_v6
```

Conservative recommended checkpoint:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

Do not treat any DPO adapter as the default accepted model yet.

Detailed plan and outcome:

- `reports/stage5_dpo_plan.md`
- `reports/stage5g_naive_dpo_v6_report.md`
- `reports/stage5j_to_5p_prompt7_repair_report.md`
- `reports/final_project_summary_zh.md`

## VRAM Risk

Observed local memory:

- LoRA SFT training: about `5.5 GB / 8 GB`
- Adapter inference: about `1.2 GB / 8 GB`

DPO can use more memory than SFT because it compares `chosen` and `rejected`
answers and usually needs reference-policy scoring. A naive implementation with
two full model copies may exceed 8 GB VRAM or fall back into shared memory,
which would slow training heavily.

Stage 5 split, now completed:

- Stage 5A: prepare `data/processed/dpo_tiny_train.jsonl`.
- Stage 5B: run tiny DPO with `configs/dpo_qwen05b.yaml`.
- Stage 5C: compare fixed prompts after tiny DPO.
- Stage 5D-G: expand DPO cautiously; v6 became the best DPO artifact.
- Stage 5H-I: design and run expanded prompt-7 behavior gate.
- Stage 5J/M: run DPO v7/v8 prompt-7 repair probes.
- Stage 5K/N/O/P: run SFT repair probes and stop when regression appears.

Original DPO smoke-test rules were:

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

## Final DPO Results

| Run | Result |
|---|---|
| DPO v1/v2 | no OOM, fixed gate 6 / 8 |
| DPO v3 | no OOM, broad regression, fixed gate 1 / 8 |
| Candidate v4/v5 | no OOM, fixed gate 6 / 8 |
| Naive v6 | separate frozen reference, eval accuracy 1.0, fixed gate 7 / 8 |
| DPO v7 | Stage 5H data, eval accuracy 1.0, fixed gate 7 / 8 |
| DPO v8 | exact-failure data from v6, eval accuracy 1.0, fixed gate 7 / 8 |

## Observations

- Hardware is not the main blocker for Qwen2.5-0.5B LoRA DPO on the RTX 4060
  Laptop GPU.
- Preference accuracy can reach 1.0 while prompt 7 still fails.
- DPO expansion should stop when behavior gates stop improving.
- Future DPO should only resume after a broader prompt-7 curriculum and stronger
  replay protection are designed.
