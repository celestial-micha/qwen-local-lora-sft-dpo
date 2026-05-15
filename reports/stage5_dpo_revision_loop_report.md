# Stage 5 DPO Revision Loop Report

Date: 2026-05-15

## Scope

This report records the follow-up loop after Stage 5C showed that the first
tiny-DPO adapter could run but did not pass the fixed-prompt behavior gate.

The loop tried two preference-data revisions:

- Stage 5A.2 / 5B.2 / 5C.2: focused v2 data for public-SFT motivation and
  loss-vs-behavior.
- Stage 5A.3 / 5B.3 / 5C.3: exact-bad-output v3 data using failed DPO outputs
  as rejected answers.

All DPO runs still started from the same SFT adapter:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

## Stage 5A.2 Data Revision

Output:

```text
data/processed/dpo_tiny_v2_train.jsonl
reports/stage5a2_dpo_tiny_v2_data_report.md
configs/dpo_qwen05b_v2.yaml
```

Summary:

```text
Base rows: 33
Added focused rows: 14
Total rows: 47
Unique prompts: 42
Max prompt+chosen tokens: 100
Max prompt+rejected tokens: 69
```

Design:

- Add stricter public-SFT motivation pairs.
- Add stricter loss-vs-behavior pairs.
- Reject unsupported phrases like "from zero" and "three to six months".

## Stage 5B.2 Tiny DPO

Output:

```text
outputs/dpo_lora_qwen05b_tiny_v2
```

Result:

```text
Rows: 47
Optimizer steps: 5
Train runtime: 43.9 seconds
Script runtime: 44.3 seconds
Train loss: 0.8345
torch max allocated: 2.180 GB
torch max reserved: 3.844 GB
OOM/native crash: no
Adapter reload check: passed
```

## Stage 5C.2 Behavior Check

Raw output:

```text
reports/compare_outputs_four_way_dpo_tiny_v2.jsonl
```

Judgment:

```text
Prompt 1 LoRA: pass
Prompt 2 SFT/LoRA: pass
Prompt 3 DPO/SFT: pass
Prompt 4 public-SFT motivation: watch/fail
Prompt 5 data pipeline: pass
Prompt 6 DPO VRAM: pass
Prompt 7 loss-vs-behavior: fail
Prompt 8 interview data pipeline: watch
```

Finding:

- v2 removed some of the worst public-SFT motivation phrasing, but still did not
  answer prompt 4 cleanly.
- Prompt 7 remained weak and again introduced an unsupported "three to six
  months" phrase.
- Stage 5C.2 did not pass.

## Stage 5A.3 Exact-Bad-Output Data Revision

Output:

```text
data/processed/dpo_tiny_v3_train.jsonl
reports/stage5a3_dpo_tiny_v3_data_report.md
configs/dpo_qwen05b_v3.yaml
```

Summary:

```text
Base v2 rows: 47
Added exact repair rows: 10
Total rows: 57
Unique prompts: 45
Max prompt+chosen tokens: 101
Max prompt+rejected tokens: 102
```

Design:

- Use actual failed DPO-tiny v2 answers as rejected examples.
- Keep chosen answers short and explicit.
- Run two short epochs to test whether a stronger update can move prompt 7.

## Stage 5B.3 Tiny DPO

Output:

```text
outputs/dpo_lora_qwen05b_tiny_v3
```

Result:

```text
Rows: 57
Epochs: 2
Optimizer steps: 14
Train runtime: 64.7 seconds
Script runtime: 65.0 seconds
Train loss: 1.1842
Logged rewards/accuracies at step 10: 0.75
torch max allocated: 2.191 GB
torch max reserved: 3.969 GB
OOM/native crash: no
Adapter reload check: passed
```

## Stage 5C.3 Behavior Check

Raw output:

```text
reports/compare_outputs_four_way_dpo_tiny_v3.jsonl
```

Judgment:

```text
Prompt 1 LoRA: regressed
Prompt 2 SFT/LoRA: regressed
Prompt 3 DPO/SFT: regressed badly
Prompt 4 public-SFT motivation: regressed badly
Prompt 5 data pipeline: mostly ok
Prompt 6 DPO VRAM: regressed badly
Prompt 7 loss-vs-behavior: improved topic, still confused
Prompt 8 interview data pipeline: regressed
```

Finding:

- v3 DPO moved the target prompt more than v1/v2, but it did so by damaging
  neighboring concepts.
- The answer to prompt 7 still did not cleanly state the intended rubric.
- Several stable v3 SFT behaviors were broken, especially DPO-vs-SFT and 8GB
  VRAM explanations.
- Stage 5C.3 failed more clearly than Stage 5C.2.

## Final Decision For This Loop

Do not continue to Stage 5D larger DPO.

The hardware feasibility gate passed repeatedly:

- 33-row DPO: passed
- 47-row DPO: passed
- 57-row, 2-epoch DPO: passed

The behavior gate did not pass:

- v1 DPO did not fix prompt 7 and regressed prompt 4.
- v2 DPO still did not fix prompt 7.
- v3 DPO pushed harder but caused broad regressions.

The current recommended model checkpoint remains the SFT adapter:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

The DPO adapters are useful experiment artifacts, not recommended replacements:

```text
outputs/dpo_lora_qwen05b_tiny
outputs/dpo_lora_qwen05b_tiny_v2
outputs/dpo_lora_qwen05b_tiny_v3
```

## Next Technical Direction

The next useful move is not "more DPO". Better options:

- Build a cleaner preference dataset from generated candidate outputs, with
  fewer hand-written near-misses and more direct pairs from actual model
  failures.
- Add a small held-out preference validation set before training.
- Consider evaluating DPO candidates with a structured scoring script instead of
  only manual report writing.
- If staying with this 0.5B model, accept that the loss-vs-behavior meta prompt
  may be near a small-model capacity/fragility limit.
- Keep fixed-prompt regression gates mandatory before any larger DPO.

## Interview Narrative

Useful phrasing:

> The important result was not just that DPO ran. The 8GB machine handled several
> tiny DPO runs without OOM, but the behavior gate caught regressions. That is
> exactly why I split DPO into data preparation, smoke testing, and fixed-prompt
> validation before scaling. In this run, hardware was not the blocker; behavior
> stability was.
