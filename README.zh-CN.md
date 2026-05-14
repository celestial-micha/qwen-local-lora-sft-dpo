# Qwen 本地 LoRA / SFT / DPO 最小项目

中文 | [English](README.md)

这是一个用本地 RTX 4060 Laptop GPU 学习和展示 Qwen 小模型 LoRA 微调、
SFT 有监督微调，以及后续 DPO 偏好优化的最小可复现项目。

项目第一版使用：

```text
Qwen/Qwen2.5-0.5B-Instruct
```

核心目标不是一开始做很大的领域模型，而是先把一条真正能讲清楚、能复现、
能写进简历和面试讲述的训练链路跑通。

## 当前状态

已经完成：

- 本地 RTX 4060 CUDA 环境验证。
- 修复并稳定了 Windows 本地训练环境。
- Qwen2.5-0.5B base 推理跑通。
- demo SFT 数据生成跑通。
- 最小 LoRA SFT smoke test 跑通。
- LoRA adapter 保存和加载跑通。
- base vs SFT 对比结果已经生成。

还没有完成：

- 500-2000 条真实 SFT 数据准备。
- 有实际效果的 SFT 训练。
- DPO 数据和 DPO 训练。
- 多卡训练说明或实验。

## 为什么改成这个项目

之前的计划太大：军事大模型、Colab、DPO、安全评测、Gradio、多卡扩展全都想做。
这个方向长期可以做，但不适合作为第一个要在面试前完成的项目。

现在我们改成最小步子：

```text
环境检查
  -> Qwen base 推理
  -> SFT 数据准备
  -> LoRA SFT
  -> adapter 加载
  -> base vs SFT 对比
  -> 后续 DPO
```

这样项目更容易完成，也更容易在面试里讲清楚。

## 稳定环境版本

当前训练环境稳定在：

```text
Python 3.10
torch==2.5.1+cu124
transformers==4.46.3
accelerate==1.1.1
peft==0.13.2
datasets==3.1.0
trl==0.12.2
huggingface-hub==0.26.5
fsspec==2024.9.0
```

注意：训练环境里暂时不装 `gradio`。如果后续做 demo，建议单独建一个 demo 环境。

## 快速运行

```powershell
conda activate qwen-lora-local
cd "D:\coding\qwen lorar sft\qwen-local-lora-sft-dpo"
$env:HF_HOME=(Resolve-Path -LiteralPath ".hf_cache").Path
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"
```

检查环境：

```powershell
python scripts/check_env.py
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda')"
```

运行 base 推理：

```powershell
python scripts/infer.py --prompt "请用三点解释什么是LoRA微调。" --max_new_tokens 128 --local_files_only
```

生成 demo SFT 数据：

```powershell
python scripts/prepare_data.py --demo --train_file data\processed\sft_train.jsonl --eval_file data\processed\sft_eval.jsonl
```

运行最小 LoRA SFT smoke test：

```powershell
python scripts/train_sft_lora.py `
  --train_file data\processed\sft_train.jsonl `
  --eval_file data\processed\sft_eval.jsonl `
  --output_dir outputs\sft_lora_qwen05b_demo `
  --max_length 256 `
  --batch_size 1 `
  --grad_accum 1 `
  --epochs 1 `
  --logging_steps 1 `
  --eval_steps 2 `
  --save_steps 2 `
  --report_to none `
  --local_files_only
```

生成 base vs SFT 对比：

```powershell
python scripts/compare_outputs.py `
  --adapter_path outputs\sft_lora_qwen05b_demo `
  --output_file reports\compare_outputs_demo.jsonl `
  --max_new_tokens 48
```

## 重要文档

- [下次聊天先读这个](reports/project_context_for_next_chat.md)
- [Windows 环境问题排查报告](reports/windows_debug_report.md)
- [给初学者看的中文学习报告](reports/beginner_learning_report_zh.md)
- [base vs SFT demo 输出](reports/compare_outputs_demo.jsonl)

## 下一步

下一步不是 DPO，也不是多卡，而是准备真正的 SFT 数据：

1. 选择一个常见中文 instruction 数据集。
2. 取 500-2000 条样本。
3. 转成 Qwen chat JSONL 格式。
4. 跑一次有意义的 LoRA SFT。
5. 用固定 prompt 对比 base 和 SFT。
6. 等 SFT 稳了，再进入 DPO。
