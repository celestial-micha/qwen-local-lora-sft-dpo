# Stage 5B Tiny DPO Smoke Test Report

Date: 2026-05-15

## Scope

Stage 5B ran only a tiny DPO smoke test. This was not a full DPO training run
and should not be treated as a final model-quality result.

Start adapter:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

Tiny preference data:

```text
data/processed/dpo_tiny_train.jsonl
```

Output adapter:

```text
outputs/dpo_lora_qwen05b_tiny
```

## Command

```powershell
$env:HF_HOME=(Resolve-Path -LiteralPath ".hf_cache").Path
Remove-Item Env:TRANSFORMERS_CACHE -ErrorAction SilentlyContinue
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"

D:\conda-envs\qwen-lora-local\python.exe scripts\train_dpo.py `
  --config configs\dpo_qwen05b.yaml `
  --local_files_only
```

Important cache note:

- A first attempt failed before training because `TRANSFORMERS_CACHE` was pointed
  at `.hf_cache` instead of letting `HF_HOME` resolve the hub cache under
  `.hf_cache/hub`.
- The successful run used `HF_HOME=.hf_cache` and removed `TRANSFORMERS_CACHE`.

## Config

```text
model_name: Qwen/Qwen2.5-0.5B-Instruct
sft_adapter_path: outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
dpo_file: data/processed/dpo_tiny_train.jsonl
output_dir: outputs/dpo_lora_qwen05b_tiny
max_length: 256
max_prompt_length: 128
per_device_train_batch_size: 1
gradient_accumulation_steps: 8
learning_rate: 5.0e-5
num_train_epochs: 1
beta: 0.1
logging_steps: 10
save_steps: 200
report_to: none
```

The training script applies the Qwen chat template to each prompt at runtime and
keeps the stored DPO data schema as plain `prompt/chosen/rejected`.

## Result

```text
Rows: 33
Optimizer steps: 4
Train runtime: 32.8 seconds
Runtime measured by script: 33.0 seconds
Train samples/second: 1.007
Train steps/second: 0.122
Approx step time: 8.2 seconds
Train loss: 0.9319
Epoch shown by trainer: 0.97
```

Trainable parameters:

```text
trainable params: 4,399,104
all params: 498,431,872
trainable ratio: 0.8826%
```

GPU observations:

```text
nvidia-smi before run: 25 MiB / 8188 MiB
torch before train: allocated 0.944 GB, reserved 1.002 GB
torch max during run: allocated 2.179 GB, reserved 4.059 GB
nvidia-smi after run: 25 MiB / 8188 MiB
```

The script does not measure Windows shared GPU memory directly. No CUDA OOM,
native `python.exe` crash, or severe slowdown was observed during this tiny run.

Save/load check:

```text
outputs/dpo_lora_qwen05b_tiny/adapter_model.safetensors
outputs/dpo_lora_qwen05b_tiny/adapter_config.json
```

The saved adapter was reloaded successfully with `PeftModel.from_pretrained`.

## Warnings

During adapter save, PEFT attempted a remote config lookup for
`Qwen/Qwen2.5-0.5B-Instruct`, hit the disabled proxy, and ignored the lookup.
The adapter still saved and reloaded successfully. Future runs can avoid the
warning by using a resolved local snapshot path as `model_name`, but this is not
a blocker for the smoke test result.

## Stage 5B Decision

Stage 5B memory/runtime smoke test passed on this tiny setup:

- DPO training started.
- Four optimizer steps completed.
- No OOM or native crash occurred.
- The output adapter was saved.
- The output adapter can be loaded.

This does not prove behavior quality. The next stage is Stage 5C: compare base,
public-SFT, custom-SFT v3, and tiny-DPO on the fixed prompt suite before any
larger DPO.
