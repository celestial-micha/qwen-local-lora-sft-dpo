# Stage 5J-5P Prompt-7 Repair Report

Date: 2026-05-16

## Scope

This report records the post-Stage-5H repair loop for prompt 7:

```text
为什么不能只看 loss 判断一次 SFT 是否成功？
```

Stage 5H deliberately designed stronger data and an expanded behavior gate
before additional training. Stages 5J through 5P then tested whether that design
could produce a checkpoint that passes prompt 7 without regressing the other
fixed prompts.

## Summary Table

| Stage | Artifact | Result | Decision |
|---|---|---|---|
| 5I | v6 on 24-prompt expanded gate | DPO v6 passed 7 / 24; loss-vs-behavior 0 / 13 | Expanded gate confirms v6 is not accepted |
| 5J | `outputs/dpo_lora_qwen05b_v7_stage5h` | DPO preference eval accuracy 1.0; fixed gate 7 / 8; prompt 7 still failed | Reject as accepted checkpoint |
| 5K | `outputs/sft_lora_qwen05b_stage5k_prompt7_repair` | Direct SFT repair scored 1 / 8 on the custom variant | Reject due to severe regression |
| 5M | `outputs/dpo_lora_qwen05b_v8_stage5m_from_v6` | Exact-failure DPO from v6 scored 7 / 8; prompt 7 improved to score 3 but still failed | Not better than v6 |
| 5N | `outputs/sft_lora_qwen05b_stage5n_prompt7_micro_from_v6` | Micro-SFT from v6 scored 7 / 8; old prompts preserved; prompt 7 still failed | Diagnostic only |
| 5O | `outputs/sft_lora_qwen05b_stage5o_prompt7_exact_from_5n` | Prompt 7 passed, but fixed gate fell to 4 / 8 | Reject due to over-specialization |
| 5P | `outputs/sft_lora_qwen05b_stage5p_prompt7_balanced_from_5n` | Balanced half-epoch probe scored 6 / 8; prompt 7 failed again | Stop training loop |

## Key Results

Stage 5I expanded scoring:

```text
Input: reports/compare_outputs_four_way_dpo_naive_v6_expanded_stage5h.jsonl
Score report: reports/stage5i_expanded_behavior_score_v6_report.md
DPO v6 expanded result: 7 / 24 prompts
DPO v6 loss-vs-behavior result: 0 / 13 prompts
```

Stage 5J DPO v7:

```text
Config: configs/dpo_qwen05b_v7_stage5h.yaml
Train/eval pairs: 278 / 55
Output: outputs/dpo_lora_qwen05b_v7_stage5h
Optimizer steps: 69
Final train loss: about 0.1768
Eval loss: about 0.0595
Eval preference accuracy: 1.0000
Fixed behavior: 7 / 8
Remaining failure: prompt 7
```

Stage 5M DPO v8:

```text
Config: configs/dpo_qwen05b_v8_stage5m_from_v6.yaml
Train/eval pairs: 162 / 41
Output: outputs/dpo_lora_qwen05b_v8_stage5m_from_v6
Optimizer steps: 40
Final train loss: about 0.0907
Eval loss: about 0.0481
Eval preference accuracy: 1.0000
Fixed behavior: 7 / 8
Remaining failure: prompt 7
```

Stage 5N/5O/5P SFT repair probes:

```text
Stage 5N: 116 train / 13 eval, from DPO v6, fixed behavior 7 / 8.
Stage 5O: 196 train / 13 eval, from Stage 5N, fixed behavior 4 / 8.
Stage 5P: same Stage 5O data, half epoch from Stage 5N, fixed behavior 6 / 8.
```

## Interpretation

- Loss and preference metrics are now clearly supporting metrics only. DPO v7
  and v8 both reached preference accuracy 1.0, yet neither passed the visible
  prompt-7 gate.
- Prompt 7 can be forced to pass with direct exact SFT, but the 0.5B adapter
  then loses neighboring behaviors. Stage 5O is the clearest example.
- The best stable DPO experiment artifact remains
  `outputs/dpo_lora_qwen05b_naive_v6`, but it is still not an accepted
  replacement for the conservative SFT checkpoint.
- The conservative recommended checkpoint remains
  `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`.

## Decision

Stop the Stage 5 training loop here. Do not add another DPO step just because
train/eval metrics look good. The next useful stage is analysis and packaging:

- preserve Stage 5H expanded gate as the behavior test;
- keep v6 as the best DPO candidate artifact, not the default recommendation;
- write the interview story around why loss/preference accuracy did not pass
  behavior gates;
- only resume training after designing a broader curriculum that teaches prompt
  7 without exact-prompt over-specialization.
