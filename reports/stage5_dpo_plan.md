# Stage 5 DPO Plan

Date: 2026-05-15

## Decision Before Stage 5

Stage 5 will start from:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

Reason:

- v3 preserves or improves 7 of 8 fixed prompts.
- v4 did not fix the remaining loss-vs-behavior prompt.
- v5 fixed that prompt but overfit and regressed several older prompts.
- v6 reduced update strength but remained unstable.
- adapter interpolation did not fix the primary prompt in spot checks.

This means v3 is not perfect, but it is the safest SFT checkpoint for a tiny DPO
experiment.

## Why v4 / v5 / v6 Were Not Accepted

### v4: Full Stage 2B.3 Data Continuation

Likely issue:

- The full dataset diluted the new loss-vs-behavior signal.
- The update was cautious enough to preserve most old behavior, but too weak to
  reliably change the final badcase.
- Prompt 4 became wordier, showing that even mild updates can shift style.

Future fix:

- Use preference pairs where the chosen answer explicitly says "loss is
  necessary but not sufficient" and the rejected answer sounds like the v3/v4
  failure.
- Keep replay prompts in the DPO set so preference optimization does not drift.

### v5: Focused Patch

Likely issue:

- The focused patch repeated the exact loss prompt too strongly.
- The learning rate and four epochs made the adapter over-specialize.
- The small 0.5B model has limited capacity, so a narrow patch can overwrite
  neighboring behaviors.

Future fix:

- Avoid single-prompt overtraining.
- Use a broader preference dataset with near-miss rejected answers instead of
  more SFT repetition.
- Keep the first DPO run tiny and evaluate old prompts immediately.

### v6: Lower-Strength Focused Patch

Likely issue:

- Lowering LR/epochs reduced the damage but did not solve the core problem.
- The patch data was still narrow, so the update direction remained biased.

Future fix:

- If doing more SFT later, use a broader replay set and possibly more varied
  phrasing around the loss concept.
- For now, DPO is a better next experiment because it can compare chosen vs
  rejected answers for the same prompt.

### Adapter Interpolation

Likely issue:

- Linear interpolation of LoRA weights is not guaranteed to interpolate behavior
  cleanly.
- The v5 delta contained both the useful loss-prompt behavior and harmful
  regressions, so small alpha did not isolate only the useful part.

Future fix:

- Treat interpolation as a quick probe, not the main strategy.
- Prefer data-level preference optimization and regression testing.

## Stage 5 Split

### Stage 5A: DPO Data Preparation

Status:

```text
completed on 2026-05-15
```

Goal:

- Build a tiny preference dataset before any DPO training.

Target size:

```text
20-50 pairs
```

Initial file:

```text
data/processed/dpo_tiny_train.jsonl
```

Current result:

```text
Rows: 33
Unique prompts: 33
Generator: scripts/prepare_tiny_dpo_data.py
Report: reports/stage5a_dpo_tiny_data_report.md
DPO training: not run yet
```

Pair design:

- Include the exact loss-vs-behavior prompt.
- Include public-SFT motivation.
- Include LoRA/SFT/DPO replay prompts.
- Include data-pipeline and DPO-VRAM prompts.
- For each pair, make the rejected answer resemble a real bad output from
  base/public/v4/v5/v6 where possible.

Expected schema:

```json
{
  "prompt": "为什么不能只看 loss 判断一次 SFT 是否成功？",
  "chosen": "不能只看 loss，因为 loss 只是平均训练目标上的拟合信号...",
  "rejected": "只要 loss 降低，就说明 SFT 已经成功。"
}
```

### Stage 5B: Tiny DPO Smoke Test

Goal:

- Verify the 8GB RTX 4060 can run DPO without OOM, Windows native crash, or
  heavy shared-memory fallback.

Candidate config:

```text
configs/dpo_qwen05b.yaml
```

Conservative settings:

```text
sft_adapter_path: outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
dpo_file: data/processed/dpo_tiny_train.jsonl
output_dir: outputs/dpo_lora_qwen05b_tiny
max_length: 256
max_prompt_length: 128
per_device_train_batch_size: 1
gradient_accumulation_steps: 8
num_train_epochs: 1
```

User should record:

- Dedicated GPU memory peak.
- Shared GPU memory growth, if any.
- System RAM growth.
- Step speed.
- Whether there is CUDA OOM or `python.exe` native crash.
- Whether the machine becomes unusably slow.

Stop conditions:

- CUDA out of memory.
- Dedicated VRAM spills heavily into shared memory.
- Windows native crash.
- Step time becomes impractically slow.
- Output adapter cannot be saved or loaded.

### Stage 5C: Tiny DPO Behavior Check

Goal:

- Compare base vs public-SFT vs custom-SFT v3 vs DPO-tiny on the same fixed
  prompts.

Success criteria:

- The loss-vs-behavior prompt improves.
- The seven previously stable prompts do not regress badly.
- DPO answers are not just more verbose; they should be more correct.

### Stage 5D: Larger DPO Only If Tiny Works

Only consider this after Stage 5B/5C pass.

Possible larger target:

```text
50-100 pairs first
100-200 pairs later
```

Still keep:

- `batch_size=1`
- short sequences
- minimal eval
- LoRA/PEFT reference sharing if possible
- fixed-prompt regression tests after training

## Interview Narrative

Useful phrasing:

> I did not jump from SFT directly into full DPO. First, I treated SFT output as
> a stability gate. v4/v5/v6 showed that patching one prompt can regress other
> prompts, so I kept v3 as the safest SFT checkpoint. Then I split DPO into a
> tiny smoke test for memory feasibility and behavior validation before any
> larger preference optimization.
