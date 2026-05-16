# Stage 5G Larger Naive DPO v6 Report

Date: 2026-05-16

## Scope

Stage 5G is the first larger DPO probe after the tiny v1/v2/v3 and
candidate-derived v4/v5 loops. It intentionally uses a larger preference set and
a separate frozen reference model instead of relying on the PEFT shared
reference path.

Starting adapter:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

Output adapter:

```text
outputs/dpo_lora_qwen05b_naive_v6
```

The output adapter is a local experiment artifact because `outputs/` is
git-ignored.

## Artifacts

```text
scripts/prepare_larger_dpo_v6_data.py
configs/dpo_qwen05b_v6_naive.yaml
data/processed/dpo_larger_v6_train.jsonl
data/processed/dpo_larger_v6_eval.jsonl
reports/stage5g_larger_dpo_v6_data_report.md
reports/compare_outputs_four_way_dpo_naive_v6.jsonl
reports/stage5_structured_behavior_score_report.md
```

The training script now supports:

```text
separate_ref_model: true
```

## Data

```text
Train rows: 192
Eval rows: 24
Topics: 8 balanced replay/evaluation areas
```

The dataset mixes previous preference rows with generated replay rows covering:

- LoRA definition
- SFT/LoRA relation
- DPO/SFT distinction
- public-SFT motivation
- data pipeline
- DPO VRAM risk
- loss-vs-behavior
- interview narrative

## Training Result

The true separate-reference run completed without OOM:

```text
Optimizer steps: 48
Train runtime: 270.8 seconds
Runtime seconds including save: 271.4
Final train loss: 0.2418
Final eval loss: 0.0474
Final eval preference accuracy: 1.0000
Max allocated VRAM: 3.415 GB
Max reserved VRAM: 8.686 GB
Adapter reload: passed
```

The run did reserve more memory than the shared-reference tiny runs, but it did
not crash. This confirms that the local machine can handle a larger naive DPO
probe for Qwen2.5-0.5B with LoRA.

Implementation note: an earlier dry run exposed that argparse's default
`False` was overriding `separate_ref_model: true`. The script was fixed by
using `default=None`, then the real separate-reference run above was executed.

## Fixed-Prompt Behavior

Structured score for the DPO answer:

```text
dpo_naive_v6: 7 / 8 prompts passed
Total score: 34
Failed area: prompt 7, loss-vs-behavior
```

Important behavior changes:

- Prompt 4 public-SFT motivation passed again.
- Old replay prompts for LoRA/SFT/DPO, data pipeline, DPO VRAM, and interview
  narrative stayed stable.
- Prompt 7 improved relative to v5, but still did not pass. It mentions that
  loss alone is insufficient, but it does not clearly include the full average
  training signal, fixed-prompt behavior, and badcase/regression framing.

## Decision

v6 is the best DPO candidate so far, but it is not a complete Stage 5 pass
because the core loss-vs-behavior gate still fails.

Recommended checkpoint remains conservative:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

The useful conclusion is sharper now:

- Hardware is not the blocker for this model size.
- Preference metrics can look excellent while a fixed behavior gate still
  catches a conceptual gap.
- The next improvement should target prompt 7 with better held-out phrasings and
  possibly SFT-side data cleanup, not just more steps on the same preference
  distribution.
