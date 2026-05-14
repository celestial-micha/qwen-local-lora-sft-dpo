# VRAM And DPO Plan

Date: 2026-05-14

## Current Observation

Local hardware:

```text
NVIDIA GeForce RTX 4060 Laptop GPU
8 GB VRAM
```

Observed memory use:

- LoRA SFT training on Qwen2.5-0.5B: about `5.5 GB / 8 GB`
- Adapter inference test: about `1.2 GB / 8 GB`
- Stage 3B custom LoRA SFT also completed on the same 8 GB GPU with
  `batch_size=1`, `grad_accum=4`, and `max_length=512`.

This is a healthy result for SFT, but it does not mean naive DPO will fit
comfortably.

## Why DPO Uses More Memory

DPO usually compares two answers for the same prompt:

- `chosen`
- `rejected`

Training also needs a reference policy. A naive implementation may effectively
need both:

- the trainable policy model
- the frozen reference model

That can be much heavier than SFT. Even if the reference model is frozen, its
forward pass and activations still cost memory unless the implementation shares
the base model efficiently or avoids storing unnecessary gradients.

## 8 GB Feasibility Judgment

For this project:

- DPO is probably feasible as a small smoke test.
- DPO is risky if implemented naively with two full model copies.
- DPO should wait until the remaining Stage 4B custom-SFT badcases are reviewed
  or patched.
- The first DPO run should be deliberately tiny: 20 to 50 pairs, short lengths,
  batch size 1, and no large eval loop.

## Memory Reduction Playbook

Use these before trying bigger DPO runs:

- Keep the base model small: stay with `Qwen/Qwen2.5-0.5B-Instruct`.
- Use LoRA/PEFT adapters, not full fine-tuning.
- Prefer DPO implementations that can share the base model or disable the
  adapter for reference scoring instead of loading a second full model.
- Use `batch_size=1`.
- Use gradient accumulation instead of larger per-device batch size.
- Reduce `max_length` first to `256` for smoke tests.
- Reduce `max_prompt_length` first to `128` or `192`.
- Keep DPO pairs short and focused.
- Use fp16 or bf16 depending on local support.
- Turn off TensorBoard/W&B logging if it adds overhead.
- Keep eval very small or disable frequent eval during the first DPO smoke run.
- Save fewer checkpoints.
- Clear old model processes before starting DPO.
- Avoid running notebooks, training scripts, and inference scripts at the same
  time.

Use carefully if still needed:

- Gradient checkpointing can reduce activation memory, but this project has
  already seen LoRA + gradient-checkpointing edge cases on Windows. Enable it
  only after a tiny smoke test and confirm gradients are valid.
- CPU offload can prevent out-of-memory errors, but it may cause exactly the
  slow dedicated-VRAM-to-shared-memory behavior we want to avoid. Use it as a
  fallback, not the first choice.

## First DPO Smoke Target

Initial target after Stage 3B:

```text
pairs: 20-50
max_length: 256
max_prompt_length: 128
batch_size: 1
gradient_accumulation_steps: 8
epochs: 1
eval: disabled or tiny
save_steps: high enough to avoid frequent checkpoint writes
```

The conservative config has been reflected in:

```text
configs/dpo_qwen05b.yaml
```

Important config choices:

- `sft_adapter_path: outputs/sft_lora_qwen05b_custom`
- `max_length: 256`
- `max_prompt_length: 128`
- `per_device_train_batch_size: 1`
- `gradient_accumulation_steps: 8`
- `report_to: none`

Success criteria:

- No CUDA out-of-memory error.
- No Windows `python.exe` process-level crash.
- GPU dedicated memory stays below the hard limit without falling heavily into
  shared memory.
- Loss logs are produced.
- Adapter can be saved and loaded.

## Interview Talking Point

Useful phrasing:

> SFT on Qwen2.5-0.5B with LoRA used about 5.5 GB of an 8 GB RTX 4060, while
> adapter inference used about 1.2 GB. DPO is more memory-sensitive because it
> compares chosen/rejected responses and often needs a reference policy. So I
> planned DPO as a later tiny smoke test with LoRA, short sequence lengths,
> batch size 1, gradient accumulation, minimal eval, and reference-model memory
> sharing where possible.
