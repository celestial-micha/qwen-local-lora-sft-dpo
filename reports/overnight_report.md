# Overnight Report

Date: 2026-05-14

## 1. Direction Reset

The project has been reset from the previous large military/Colab-first plan to
a minimal local learning project:

```text
qwen-local-lora-sft-dpo
```

New goal:

> Use the local RTX 4060 Laptop GPU to run a small, clear Qwen2.5-0.5B LoRA SFT
> workflow first, then add DPO only after SFT is stable.

This is a better interview-prep plan because it is smaller, easier to finish,
and easier to explain.

## 2. Important Environment Finding

The earlier `python.exe` popup was not a normal Python exception. It was a
Windows process-level crash:

```text
python.exe - application error
memory could not be read
```

This means Python may terminate before raising an exception. The likely trigger
is importing heavy ML packages together on Windows. To avoid this, I changed
`scripts/check_env.py` so it no longer imports `transformers`, `peft`, `trl`, or
other heavy packages. It now reads installed package versions from metadata.

Result:

```text
scripts/check_env.py now runs successfully.
```

## 3. Confirmed Local Environment

From the user's earlier check and the revised env script:

```text
Python: 3.10.20
Torch: 2.5.1
CUDA available: True
GPU: NVIDIA GeForce RTX 4060 Laptop GPU
GPU memory: 8 GB
transformers: 5.8.1
datasets: 4.8.5
accelerate: 1.13.0
peft: 0.19.1
trl: 1.4.0
gradio: 6.14.0
```

Note:

The current environment is usable, but because there were process-level crashes,
we should move carefully:

1. Verify base inference first.
2. Verify demo data preparation.
3. Run the smallest possible LoRA SFT smoke test.
4. Only then expand dataset size.
5. Add DPO later.

## 4. Files Created or Updated

Core docs:

- `README.md`
- `PROJECT_RUNBOOK.md`
- `requirements.txt`
- `environment.yml`
- `.gitignore`

Configs:

- `configs/sft_qwen05b.yaml`
- `configs/dpo_qwen05b.yaml`

Scripts:

- `scripts/check_env.py`
- `scripts/infer.py`
- `scripts/prepare_data.py`
- `scripts/train_sft_lora.py`
- `scripts/compare_outputs.py`
- `scripts/train_dpo.py`

Notebooks:

- `notebooks/00_env_check.ipynb`
- `notebooks/01_base_infer.ipynb`
- `notebooks/02_prepare_demo_data.ipynb`
- `notebooks/03_sft_lora_smoke.ipynb`

Reports:

- `reports/experiment_log.md`
- `reports/compare_base_sft.md`
- `reports/dpo_notes.md`
- `reports/overnight_report.md`

Sample data:

- `data/samples/smoke_prompts.jsonl`
- `data/samples/dpo_toy.jsonl`

Generated local demo data:

- `data/processed/sft_train.jsonl`
- `data/processed/sft_eval.jsonl`

These processed files are ignored by git by default.

## 5. What Was Verified

Passed:

```text
All script syntax checks passed.
All notebook JSON checks passed.
scripts/check_env.py runs successfully without importing heavy packages.
scripts/prepare_data.py --demo generated train/eval data successfully.
```

Demo data result:

```text
Raw samples: 5
Valid samples: 5
Train samples: 4
Eval samples: 1
Dropped samples: 0
Duplicate prompts: 0
```

Not run yet:

```text
Base Qwen model download/inference.
LoRA SFT training.
DPO training.
```

I intentionally did not run model download or training after the crash reports,
because the next safe step should be run visibly by the user.

## 6. Recommended Next Morning Steps

Open a fresh PowerShell:

```powershell
conda activate qwen-lora-local
cd "D:\coding\qwen lorar sft\qwen-local-lora-sft-dpo"
$env:HF_HOME="$PWD\.hf_cache"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"
```

Step 1: run the safe env check:

```powershell
python scripts/check_env.py
```

Step 2: confirm CUDA separately:

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda')"
```

Step 3: run base inference:

```powershell
python scripts/infer.py --prompt "请用三点解释什么是LoRA微调。" --max_new_tokens 256
```

The first run will download `Qwen/Qwen2.5-0.5B-Instruct` into `.hf_cache`.
This may take a while.

Step 4: if base inference succeeds, run local-cache inference:

```powershell
python scripts/infer.py --prompt "请解释SFT和DPO的区别。" --max_new_tokens 256 --local_files_only
```

Step 5: prepare demo data again if needed:

```powershell
python scripts/prepare_data.py --demo --train_file data\processed\sft_train.jsonl --eval_file data\processed\sft_eval.jsonl
```

Step 6: only after base inference works, run the tiny LoRA SFT smoke test:

```powershell
python scripts/train_sft_lora.py `
  --train_file data\processed\sft_train.jsonl `
  --eval_file data\processed\sft_eval.jsonl `
  --output_dir outputs\sft_lora_qwen05b_demo `
  --max_length 384 `
  --batch_size 1 `
  --grad_accum 2 `
  --epochs 1 `
  --logging_steps 1 `
  --eval_steps 5 `
  --save_steps 5 `
  --report_to none
```

## 7. If python.exe Crashes Again

Do not keep retrying the same command repeatedly.

Record:

1. Which command was running.
2. Whether the crash happened during import, model download, model load, or training.
3. Whether any traceback appeared before the popup.

Most likely fallback paths:

1. Pin more conservative package versions.
2. Use Python 3.10 with stable `transformers`, `peft`, and `accelerate` versions.
3. Move only the training step to WSL2 or Colab if Windows native remains unstable.

## 8. Current Recommendation

Continue with the local 4060 plan, but keep the next step small:

```text
Base inference first. Then tiny demo SFT. Then real SFT data.
```

DPO should wait until LoRA SFT is demonstrably stable.

## 9. Final Update On 2026-05-16

This report is now a historical early-project snapshot. The project has since
completed public-SFT, custom-SFT, DPO v1-v8 probes, expanded behavior scoring,
and Stage 6 packaging.

Final decision:

```text
Recommended checkpoint: outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
Best DPO artifact:      outputs/dpo_lora_qwen05b_naive_v6
Final summary:          reports/final_project_summary_zh.md
Interview package:      reports/stage6_final_interview_package.md
```

The key final lesson is that lower loss and high preference accuracy were not
enough. The project accepted only behavior-gated results, and stopped training
when prompt 7 could not be fixed without old-prompt regression.
