# Stage 4A Public-SFT Comparison Report

Date: 2026-05-14

## Goal

Compare the base Qwen2.5-0.5B-Instruct model with the Stage 3A public-data
LoRA SFT adapter.

This stage answers a practical question:

```text
Did a general public instruction dataset fix the specific LoRA/SFT/DPO concept
confusion that motivated this project?
```

## Inputs

- Base model: `Qwen/Qwen2.5-0.5B-Instruct`
- Adapter: `outputs/sft_lora_qwen05b_public`
- Prompt file: `data/samples/smoke_prompts.jsonl`
- Raw comparison output: `reports/compare_outputs_public_sft.jsonl`

## Command

```powershell
$env:HF_HOME=(Resolve-Path -LiteralPath ".hf_cache").Path
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"

D:\conda-envs\qwen-lora-local\python.exe scripts\compare_outputs.py `
  --prompt_file data\samples\smoke_prompts.jsonl `
  --adapter_path outputs\sft_lora_qwen05b_public `
  --output_file reports\compare_outputs_public_sft.jsonl `
  --max_new_tokens 96 `
  --local_files_only
```

## Result Summary

| Prompt | Base Result | Public-SFT Result | Stage 4A Judgment |
|---|---|---|---|
| `请用三点解释什么是LoRA微调。` | Mistakenly describes LoRA as weight sharing and multimodal learning. | Worse: explains LoRA as long-range communication and device tuning. | Not fixed. |
| `为什么小模型更适合第一次学习SFT？` | Gives a very short generic answer. | Longer answer, but drifts into Keras/TensorFlow and generic ML claims. | Partially better fluency, still not targeted. |
| `请解释SFT和DPO的区别。` | Explains SFT/DPO as unrelated cybersecurity/data-protection terms. | Explains SFT/DPO as unrelated communication/phrasing terms. | Not fixed. |

## Key Finding

Stage 3A succeeded as an engineering milestone but not as a target-behavior
milestone.

The public Chinese instruction dataset proved that the local LoRA SFT pipeline
can train, save, load, and run inference. However, it did not teach the model
the specific technical meanings we care about:

- LoRA as parameter-efficient fine-tuning
- SFT as supervised fine-tuning
- DPO as direct preference optimization
- The relationship between data format, training objective, adapter training,
  and evaluation

This is exactly why Stage 2B is necessary. A broad general instruction dataset
improves neither every domain concept nor every project-specific explanation.
The next dataset needs targeted technical-learning examples.

## Interview Narrative

Useful phrasing:

> I first trained a public-data LoRA SFT baseline to verify the engineering
> pipeline. The adapter trained and loaded correctly, but fixed-prompt
> evaluation showed it still confused LoRA, SFT, and DPO. That failure was
> useful: it proved that generic instruction data was not enough for the target
> behavior, so I moved to a custom technical-data loop with crawling, cleaning,
> filtering, and instruction-answer rewriting.

## Next Step

Proceed to Stage 2B:

```text
self-collected technical data
  -> clean and deduplicate
  -> convert into instruction-answer samples
  -> train custom or mixed LoRA SFT
  -> compare base vs public-SFT vs custom-SFT
```
