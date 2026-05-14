# Windows Debug Report

Date: 2026-05-14

## Problem

The original local environment repeatedly crashed with a Windows popup:

```text
python.exe - application error
memory could not be read
```

This was not a normal Python exception. It was a native process crash, so Python
could not provide a traceback.

## Root Cause

The environment had a very new Hugging Face stack:

```text
transformers 5.8.1
accelerate 1.13.0
peft 0.19.1
trl 1.4.0
huggingface-hub 1.14.0
```

This stack worked for some imports and base inference, but was unstable in the
Windows native training path. Repeatedly changing project code could not fix a
native crash caused by package/runtime instability.

There was also a separate cache permission problem:

```text
D:\hf_cache
```

was readable but not writable by the current process. The project now uses a
project-local cache:

```text
.hf_cache
```

## Fix

The environment was downgraded to a more conservative local training stack:

```text
torch 2.5.1+cu124
transformers 4.46.3
accelerate 1.1.1
peft 0.13.2
datasets 3.1.0
trl 0.12.2
huggingface-hub 0.26.5
fsspec 2024.9.0
```

Gradio was removed from this environment because it required a newer
`huggingface-hub` than the stable training stack. If needed later, Gradio should
run in a separate demo environment.

## Additional Code Fixes

1. `infer.py` now supports both Transformers 4.x and 5.x dtype argument names.
2. `infer.py` now handles both Tensor and BatchEncoding outputs from
   `apply_chat_template`.
3. `train_sft_lora.py` no longer enables gradient checkpointing by default.
4. `compare_outputs.py` now uses `--local_files_only` by default.
5. `compare_outputs.py` now tolerates Windows subprocess output encoding issues.

## Verified Results

Environment:

```text
pip check: No broken requirements found.
torch: 2.5.1+cu124
CUDA: 12.4
GPU: NVIDIA GeForce RTX 4060 Laptop GPU
```

Base inference:

```text
python scripts/infer.py --prompt "请用三点解释什么是LoRA微调。" --max_new_tokens 64 --local_files_only
```

Result: runs successfully.

Demo data:

```text
python scripts/prepare_data.py --demo --train_file data\processed\sft_train.jsonl --eval_file data\processed\sft_eval.jsonl
```

Result:

```text
Train samples: 4
Eval samples: 1
```

LoRA SFT smoke test:

```text
python scripts/train_sft_lora.py --train_file data\processed\sft_train.jsonl --eval_file data\processed\sft_eval.jsonl --output_dir outputs\sft_lora_qwen05b_demo --max_length 256 --batch_size 1 --grad_accum 1 --epochs 1 --logging_steps 1 --eval_steps 2 --save_steps 2 --report_to none --local_files_only
```

Result:

```text
trainable params: 4,399,104
all params: 498,431,872
trainable%: 0.8826
final train loss: 3.7685
final eval loss: 3.5056
adapter saved to: outputs\sft_lora_qwen05b_demo
```

Adapter inference:

```text
python scripts/infer.py --prompt "请用三点解释什么是LoRA微调。" --adapter_path outputs\sft_lora_qwen05b_demo --local_files_only
```

Result: runs successfully.

Comparison:

```text
python scripts/compare_outputs.py --adapter_path outputs\sft_lora_qwen05b_demo --output_file reports\compare_outputs_demo.jsonl --max_new_tokens 48
```

Result:

```text
reports\compare_outputs_demo.jsonl
```

## Quality Note

The demo adapter does not produce good answers yet. This is expected because it
trained on only 4 examples. The purpose of this smoke test was to prove:

1. Local CUDA works.
2. Qwen base inference works.
3. LoRA adapter training works.
4. Adapter saving/loading works.
5. Output comparison works.

The next useful project step is not DPO. The next useful step is a real SFT
dataset of 500 to 2000 clean examples.

## Next Step

Implement Stage 2 real data preparation:

1. Choose a common Chinese instruction dataset.
2. Convert it to Qwen chat JSONL.
3. Train LoRA on 500 to 2000 samples.
4. Compare base vs SFT on fixed prompts.
