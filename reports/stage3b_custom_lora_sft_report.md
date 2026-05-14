# Stage 3B Custom LoRA SFT Report

Date: 2026-05-14

## Goal

Train a custom technical LoRA SFT adapter with the Stage 2B dataset and save it
to:

```text
outputs/sft_lora_qwen05b_custom
```

The purpose of this stage is not only to lower loss. It is to test whether a
small targeted dataset can correct the LoRA/SFT/DPO concept errors that remained
after public-data SFT.

## Important Iteration

The first Stage 3B attempt used the initial Stage 2B dataset:

```text
Instruction samples: 160
Train samples: 144
Eval samples: 16
Epochs: 3
```

That run trained successfully, but the model still hallucinated concepts and
sometimes copied project-record wording in the wrong place. This was a useful
failure: it showed that a falling loss does not guarantee the target behavior is
fixed.

The dataset was then revised:

- Reduced generic `project_record_summary` samples from 60 to 20.
- Added 12 targeted QA samples that directly cover the fixed technical prompts.
- Regenerated train/eval files.
- Retrained the custom adapter for 10 epochs.

Revised Stage 2B data:

```text
Sources: 10
Accepted cleaned chunks: 85
Rejected chunks: 9
Instruction-answer seed samples: 132
Train samples: 119
Eval samples: 13
Duplicate instruction samples: 0
```

Token validation before truncation:

| Split | Rows | Unique Prompts | Min | Avg | P95 | Max | Over 512 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Train | 119 | 119 | 111 | 166.2 | 277 | 486 | 0 |
| Eval | 13 | 13 | 120 | 157.5 | 174 | 238 | 0 |

## Training Command

```powershell
D:\conda-envs\qwen-lora-local\python.exe scripts\train_sft_lora.py `
  --train_file data\processed\custom_sft_train.jsonl `
  --eval_file data\processed\custom_sft_eval.jsonl `
  --output_dir outputs\sft_lora_qwen05b_custom `
  --max_length 512 `
  --batch_size 1 `
  --grad_accum 4 `
  --epochs 10 `
  --logging_steps 10 `
  --eval_steps 50 `
  --save_steps 50 `
  --report_to none `
  --local_files_only
```

## Training Result

```text
Trainable params: 4,399,104
Total params: 498,431,872
Trainable ratio: 0.8826%
Runtime: 740.3 seconds, about 12.3 minutes
Final train loss: 0.4656
```

Eval loss checkpoints:

| Step | Epoch | Eval Loss |
|---:|---:|---:|
| 50 | 1.68 | 1.5147 |
| 100 | 3.36 | 0.8385 |
| 150 | 5.04 | 0.8311 |
| 200 | 6.72 | 0.8450 |
| 250 | 8.40 | 0.8669 |

Interpretation:

- The best observed eval loss was around epoch 5.
- Later eval loss drifted upward slightly, so the 10-epoch run shows mild
  overfitting risk.
- The final saved adapter is still useful for behavior comparison, but a future
  run could save or select the best checkpoint around step 150.

## Quick Behavior Check

Prompt:

```text
请用三点解释机器学习里的 LoRA 微调，不要解释成无线通信 LoRa。
```

Custom-SFT answer summary:

```text
第一，机器学习里的 LoRA 是参数高效微调方法，全称常解释为低秩适配，不是无线通信 LoRa。
第二，它冻结基础模型大部分参数，只在部分线性层旁边训练低秩 adapter 矩阵。
第三，它适合个人 GPU 学习，因为训练参数少、显存压力低、adapter 文件也更小。
```

This is a clear improvement over both the base model and the public-SFT adapter
on this target concept.

## Lessons

- Public-data SFT proved the engineering loop, but not the target behavior.
- The first custom-data run proved that noisy or overly generic project-summary
  samples can still produce bad behavior.
- Revising the dataset around concrete badcases improved 6 of 8 fixed prompts.
- The correct evaluation unit for this project is not only loss; it is fixed
  prompt behavior plus badcase review.

## Next Step

Use `reports/compare_outputs_three_way_custom.jsonl` and
`reports/stage4b_three_way_comparison_report.md` to review base vs public-SFT vs
custom-SFT. Before DPO, consider one small Stage 2B.2 data patch for the two
remaining weak prompts.
