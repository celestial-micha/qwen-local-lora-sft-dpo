# Stage 3A Public LoRA SFT Report

Date: 2026-05-14

## What Was Trained

This stage trained a LoRA adapter with an SFT objective:

- SFT describes the training objective and data format: supervised
  instruction-answer learning.
- LoRA describes the parameter-efficient tuning method: freeze the base model
  and train small adapter matrices.
- Therefore this project is doing LoRA SFT, meaning supervised fine-tuning
  implemented through LoRA adapters.

## Data

- Train file: `data/processed/sft_train.jsonl`
- Eval file: `data/processed/sft_eval.jsonl`
- Source dataset: `llm-wizard/alpaca-gpt4-data-zh`
- Train samples: 1,003
- Eval samples: 111

## Command

```powershell
$env:HF_HOME=(Resolve-Path -LiteralPath ".hf_cache").Path
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"

D:\conda-envs\qwen-lora-local\python.exe scripts\train_sft_lora.py `
  --train_file data\processed\sft_train.jsonl `
  --eval_file data\processed\sft_eval.jsonl `
  --output_dir outputs\sft_lora_qwen05b_public `
  --max_length 512 `
  --batch_size 1 `
  --grad_accum 8 `
  --epochs 1 `
  --logging_steps 10 `
  --eval_steps 100 `
  --save_steps 100 `
  --report_to none `
  --local_files_only
```

## Training Result

- Trainable parameters: 4,399,104
- Total parameters: 498,431,872
- Trainable ratio: 0.8826%
- Train samples per second: 0.686
- Train steps per second: 0.085
- Runtime: 1,462.28 seconds, about 24.4 minutes
- Final train loss: 1.7558
- Eval loss at step 100: 1.8263
- Output adapter: `outputs/sft_lora_qwen05b_public`

The adapter was saved successfully and loaded successfully for inference.

## Fixed-Prompt Comparison

Comparison output:

```text
reports/compare_outputs_public_sft.jsonl
```

Prompts tested:

- `请用三点解释什么是LoRA微调。`
- `为什么小模型更适合第一次学习SFT？`
- `请解释SFT和DPO的区别。`

Observation:

- The public-data adapter did not fix the key technical concept mistakes.
- Both base and public-SFT still confused LoRA/SFT/DPO with unrelated meanings
  such as wireless LoRa, software functions, firewalls, and disaster recovery.
- This is useful evidence that a general instruction dataset is not enough for
  the target technical-learning behavior.

## Conclusion

Stage 3A succeeded as an engineering milestone:

- Real public-data LoRA SFT ran end to end.
- The adapter saved and loaded correctly.
- Training was stable on the local RTX 4060 Laptop GPU.

Stage 3A did not solve the target-domain behavior:

- The model still needs custom technical data about LoRA, SFT, DPO, Hugging
  Face, CUDA/Windows debugging, and experiment reporting.

This directly motivates Stage 2B:

```text
self-collected technical data
  -> clean and filter
  -> convert to instruction-answer samples
  -> train custom or mixed LoRA SFT
  -> compare base vs public-SFT vs custom-SFT
```
