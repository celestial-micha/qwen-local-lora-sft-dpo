# Stage 5H Prompt-7 Data And Expanded Eval Design

Date: 2026-05-16

## Scope

Stage 5H does not run DPO training. It prepares stronger loss-vs-behavior
preference/eval data and a larger behavior gate so the next run cannot pass by
only memorizing the original prompt 7 wording.

## Outputs

```text
data/processed/dpo_stage5h_prompt7_train.jsonl
data/processed/dpo_stage5h_prompt7_eval.jsonl
data/samples/custom_technical_prompts_expanded_stage5h.jsonl
```

## Dataset Summary

- Train rows: 278
- Eval rows: 55
- Prompt-7 train rows: 72
- Prompt-7 eval rows: 24
- Train prompt length min/avg/max chars: 15 / 31.8 / 63
- Train chosen length min/avg/max chars: 47 / 120.9 / 191
- Train rejected length min/avg/max chars: 21 / 53.2 / 253

## Train Sources

| Source Type | Rows |
|---|---:|
| `stage5g_train:base:dpo_tiny_train.jsonl` | 16 |
| `stage5g_train:base:dpo_tiny_v2_train.jsonl` | 14 |
| `stage5g_train:base:dpo_tiny_v3_train.jsonl` | 10 |
| `stage5g_train:curated_guardrail` | 8 |
| `stage5g_train:custom_sft_known_gap_vs_curated` | 1 |
| `stage5g_train:failed_candidate_vs_curated` | 3 |
| `stage5g_train:failed_candidate_vs_custom_sft` | 8 |
| `stage5g_train:generated_data_pipeline` | 16 |
| `stage5g_train:generated_dpo_vram` | 16 |
| `stage5g_train:generated_dpo_vs_sft` | 16 |
| `stage5g_train:generated_interview_narrative` | 16 |
| `stage5g_train:generated_lora_definition` | 15 |
| `stage5g_train:generated_loss_vs_behavior` | 15 |
| `stage5g_train:generated_public_sft_motivation` | 15 |
| `stage5g_train:generated_sft_lora_relation` | 15 |
| `stage5g_train:v4_exact_failure_focus` | 2 |
| `stage5g_train:v4_near_miss_focus` | 6 |
| `stage5h_prompt7_train_eval_loss_only` | 9 |
| `stage5h_prompt7_train_invented_duration` | 9 |
| `stage5h_prompt7_train_loss_only` | 9 |
| `stage5h_prompt7_train_loss_useless` | 9 |
| `stage5h_prompt7_train_missing_badcase` | 9 |
| `stage5h_prompt7_train_missing_regression` | 9 |
| `stage5h_prompt7_train_preference_metric_only` | 9 |
| `stage5h_prompt7_train_public_sft_overclaim` | 9 |
| `stage5h_replay_data_pipeline` | 2 |
| `stage5h_replay_dpo_vram_risk` | 2 |
| `stage5h_replay_dpo_vs_sft` | 2 |
| `stage5h_replay_interview_data_pipeline` | 2 |
| `stage5h_replay_lora_definition` | 2 |
| `stage5h_replay_public-sft_motivation` | 2 |
| `stage5h_replay_sft_and_lora_relation` | 2 |

## Expanded Behavior Gate

- Expanded prompts: 24
- Original fixed prompts preserved: 8 / 8
- Loss-vs-behavior prompts total: 13
- Stage 5H loss-vs-behavior holdouts: 12
- Additional replay holdouts: 4

Recommended future gate rule:

1. Keep the original 8 fixed prompts as regression tests.
2. Require every loss-vs-behavior held-out prompt to include loss as an average
   training objective signal, "necessary but not sufficient", fixed-prompt
   behavior, badcase/regression review, and a project example such as
   public-SFT or DPO v6.
3. Reject runs that pass prompt 7 but regress old LoRA/SFT/DPO, data-pipeline,
   DPO-VRAM, public-SFT motivation, or interview-narrative prompts.
4. Treat preference eval accuracy as a useful metric, not the final behavior
   gate.

## Design Notes

- The base distribution is Stage 5G v6, because it is the strongest DPO
  candidate so far and already contains broad replay coverage.
- Stage 5H adds varied prompt-7 phrasings around train loss, eval loss,
  preference metrics, fixed prompts, badcase review, regression, public-SFT,
  and DPO v6.
- Rejected answers are near-misses: they often sound plausible but omit one
  required concept or over-trust a metric.
- Extra replay rows are kept so the prompt-7 repair signal does not overwrite
  the seven previously stable areas.

## Future Commands

Generate data and the expanded prompt suite:

```powershell
python scripts\prepare_stage5h_prompt7_data.py
```

After a future DPO v7 run exists, compare it on the expanded suite:

```powershell
python scripts\compare_four_outputs.py `
  --prompt_file data\samples\custom_technical_prompts_expanded_stage5h.jsonl `
  --dpo_adapter_path outputs\dpo_lora_qwen05b_v7_stage5h `
  --output_file reports\compare_outputs_four_way_dpo_v7_stage5h_expanded.jsonl `
  --max_new_tokens 160 `
  --temperature 0 `
  --local_files_only

python scripts\score_expanded_behavior_outputs.py `
  --input_files reports\compare_outputs_four_way_dpo_v7_stage5h_expanded.jsonl
```
