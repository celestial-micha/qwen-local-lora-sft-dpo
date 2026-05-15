# Stage 5C Tiny DPO Behavior Report

Date: 2026-05-15

## Scope

Stage 5C compares the tiny-DPO adapter against the same fixed prompt suite used
in Stage 4B. This is the behavior gate after the Stage 5B memory smoke test.

Compared variants:

```text
base model
public-SFT: outputs/sft_lora_qwen05b_public
custom-SFT v3: outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
DPO-tiny: outputs/dpo_lora_qwen05b_tiny
```

Raw output:

```text
reports/compare_outputs_four_way_dpo_tiny.jsonl
```

Script:

```text
scripts/compare_four_outputs.py
```

## Command

```powershell
$env:HF_HOME=(Resolve-Path -LiteralPath ".hf_cache").Path
Remove-Item Env:TRANSFORMERS_CACHE -ErrorAction SilentlyContinue
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"

D:\conda-envs\qwen-lora-local\python.exe scripts\compare_four_outputs.py `
  --prompt_file data\samples\custom_technical_prompts.jsonl `
  --public_adapter_path outputs\sft_lora_qwen05b_public `
  --custom_adapter_path outputs\sft_lora_qwen05b_custom_v3_from_v1_patch `
  --dpo_adapter_path outputs\dpo_lora_qwen05b_tiny `
  --output_file reports\compare_outputs_four_way_dpo_tiny.jsonl `
  --max_new_tokens 128 `
  --temperature 0 `
  --local_files_only
```

The comparison loads only one model variant at a time to avoid holding multiple
models or adapters in GPU memory.

## Summary

Stage 5C does not pass the behavior gate.

What worked:

- DPO-tiny preserved the LoRA prompt.
- DPO-tiny preserved the SFT-vs-LoRA prompt.
- DPO-tiny preserved the DPO-vs-SFT prompt.
- DPO-tiny preserved the custom data pipeline prompt.
- DPO-tiny preserved or slightly improved the DPO VRAM prompt.

What did not work:

- The exact loss-vs-behavior prompt did not become reliably correct.
- The public-SFT motivation prompt regressed from the concise v3 answer into a
  confused answer that mentions irrelevant ideas like "from zero" and "three to
  six months".
- The interview data-pipeline answer remained mostly usable, but became slightly
  more tangled than v3.

This means Stage 5B proved that tiny DPO can run on the local 8GB GPU, but this
first tiny-DPO dataset/training setup did not improve behavior enough to justify
larger DPO yet.

## Prompt-Level Judgment

| # | Prompt Area | v3 -> DPO-tiny | Judgment |
|---:|---|---|---|
| 1 | LoRA definition | unchanged and correct | pass |
| 2 | SFT and LoRA relation | unchanged and correct | pass |
| 3 | DPO vs SFT | unchanged and correct | pass |
| 4 | public-SFT motivation | worse; confused extra claims | fail |
| 5 | data collection pipeline | unchanged and correct | pass |
| 6 | 8GB DPO VRAM risk | slightly more specific with reference policy | pass |
| 7 | loss vs behavior | still weak and partly confused | fail |
| 8 | interview data pipeline | mostly preserved, slightly tangled | watch |

Result:

```text
Clear pass: 5 / 8
Watch: 1 / 8
Fail: 2 / 8
Core success criterion: not met
```

## Key Examples

The desired Stage 5C outcome was that prompt 7 would explicitly say loss is
necessary but not sufficient, and that fixed-prompt behavior/regression tests
are required.

Instead, DPO-tiny answered:

```text
只能先说公开数据跑通，但 Stage 4A 发现 public-SFT 没修正 LoRA/SFT/DPO 概念误解，所以进入 Stage 2B。Stage 2B 的目标是纠正概念误解，而不是只用 loss 判断项目是否通过。第一版 public-SFT 需要再做三到六个月的资料补习。
```

This is more on-topic than the worst v3 failure, but it is still not a clean
answer and introduces an unsupported "three to six months" claim.

Prompt 4 also regressed:

```text
因为公开数据跑通不等于目标领域行为已经解决。Stage 2B 做的是从零开始建模型，所以这时候遇到的错误不是笼统说的模型架构错，而是说：公开数据跑通但没修正概念误解，说明 Stage 4A 需要做三到六个月的自采集技术资料工作。
```

The first sentence is good, but the rest is confused. Stage 2B is not "building
the model from zero", and the "three to six months" claim is not part of the
project record.

## Decision

Do not move to larger DPO yet.

Stage 5B passed the memory/runtime smoke test, but Stage 5C failed the behavior
gate. The next improvement should be data-level and evaluation-level, not simply
more DPO steps.

Recommended next options:

- Revise Stage 5A preference data for prompts 4 and 7 with shorter, stricter
  rejected answers and stronger chosen answers.
- Add explicit rejected patterns for unsupported claims such as "from zero" and
  "three to six months".
- Keep replay pairs, but reduce ambiguity in public-SFT motivation and
  loss-vs-behavior pairs.
- Rerun tiny DPO only after the preference data is revised.
- Keep Stage 5D blocked until Stage 5C passes.
