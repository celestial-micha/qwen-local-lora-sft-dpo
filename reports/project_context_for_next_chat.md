# Project Context For Next Chat

如果开启新的聊天，请先让 Codex 阅读这个文件。

## 当前项目

项目目录：

```text
D:\coding\qwen lorar sft\qwen-local-lora-sft-dpo
```

项目名称：

```text
qwen-local-lora-sft-dpo
```

当前目标：

> 在本地 RTX 4060 Laptop GPU 上，用 Qwen2.5-0.5B-Instruct 跑通 LoRA SFT，
> 再逐步扩展到真实 SFT 数据、DPO、多卡训练说明。

旧方向已经废弃：

```text
qwen-military-posttraining
军事/战略大模型
Colab-first workflow
```

现在不追求一开始做很大的垂直领域模型，而是用最小步子把完整训练链路做精。

## 当前保留文件

工作区根目录目前主要保留：

```text
2_nanochat_train_val_all.ipynb
qwen-local-lora-sft-dpo/
README.md
```

`2_nanochat_train_val_all.ipynb` 是早期 Colab 跑 nanochat 的学习记录。

`qwen-local-lora-sft-dpo/` 是当前要继续推进的主项目。

## 环境

conda 环境：

```text
qwen-lora-local
```

Python 路径：

```text
D:\conda-envs\qwen-lora-local\python.exe
```

硬件：

```text
NVIDIA GeForce RTX 4060 Laptop GPU
8 GB VRAM
```

稳定版本：

```text
torch==2.5.1+cu124
transformers==4.46.3
accelerate==1.1.1
peft==0.13.2
datasets==3.1.0
trl==0.12.2
huggingface-hub==0.26.5
fsspec==2024.9.0
```

注意：

- 不要升级到 `transformers 5.8.1`、`peft 0.19.1`、`trl 1.4.0` 那组高版本。
- 那组高版本在 Windows 原生训练路径中触发过 `python.exe` 进程级崩溃。
- 当前训练环境里不要装 Gradio。以后做 demo 时另建环境。

## 每次运行前设置

PowerShell：

```powershell
conda activate qwen-lora-local
cd "D:\coding\qwen lorar sft\qwen-local-lora-sft-dpo"
$env:HF_HOME=(Resolve-Path -LiteralPath ".hf_cache").Path
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"
```

## 已经完成

### 1. 环境检查

```powershell
python scripts/check_env.py
```

可以正常输出版本信息。

CUDA 检查：

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda')"
```

已确认：

```text
2.5.1+cu124
True
NVIDIA GeForce RTX 4060 Laptop GPU
```

### 2. Base 推理

```powershell
python scripts/infer.py --prompt "请用三点解释什么是LoRA微调。" --max_new_tokens 64 --local_files_only
```

已跑通。

观察：

base model 会把机器学习里的 LoRA 解释成无线通信 LoRa 或其他错误概念。
这正好是后续 SFT 的 before case。

### 3. Demo SFT 数据

```powershell
python scripts/prepare_data.py --demo --train_file data\processed\sft_train.jsonl --eval_file data\processed\sft_eval.jsonl
```

已跑通：

```text
Raw samples: 5
Valid samples: 5
Train samples: 4
Eval samples: 1
```

### 4. LoRA SFT smoke test

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

已跑通：

```text
trainable params: 4,399,104
all params: 498,431,872
trainable%: 0.8826
final train loss: 3.7685
final eval loss: 3.5056
adapter saved to: outputs\sft_lora_qwen05b_demo
```

### 5. Adapter 加载推理

```powershell
python scripts/infer.py --prompt "请用三点解释什么是LoRA微调。" --max_new_tokens 80 --adapter_path outputs\sft_lora_qwen05b_demo --local_files_only
```

已跑通。

注意：

demo adapter 效果仍然不好，因为只训练了 4 条样本。这个结果只能证明训练链路通了。

### 6. Base vs SFT 对比

```powershell
python scripts/compare_outputs.py `
  --adapter_path outputs\sft_lora_qwen05b_demo `
  --output_file reports\compare_outputs_demo.jsonl `
  --max_new_tokens 48
```

已跑通：

```text
reports\compare_outputs_demo.jsonl
```

## 遇到的问题和解决方案

详细见：

```text
reports/windows_debug_report.md
```

核心问题：

1. 高版本 Hugging Face 栈在 Windows 原生训练路径下触发 `python.exe` 进程级崩溃。
2. `D:\hf_cache` 对当前进程不可写。
3. `transformers 4.x` 和 `5.x` 的 `from_pretrained` dtype 参数不同。
4. `apply_chat_template` 在不同版本中返回类型不同。
5. LoRA + gradient checkpointing 默认打开时出现无梯度问题。
6. Windows 子进程输出中文时出现编码问题。
7. 不加 `--local_files_only` 时，会尝试走无效代理 `127.0.0.1:9` 访问 Hugging Face。

已修复：

1. 降级到稳定训练栈。
2. 改用项目内 `.hf_cache`。
3. `infer.py` 兼容 Transformers 4.x / 5.x。
4. 默认关闭 gradient checkpointing。
5. `compare_outputs.py` 默认使用 local files only。
6. 对比脚本设置 UTF-8 输出容错。

## 下一步

下一步不是 DPO，不是多卡，不是 Gradio。

下一步是：

```text
Stage 2: 准备真实 SFT 数据
```

建议目标：

1. 选择常见中文 instruction 数据集。
2. 取 500-2000 条。
3. 转成 Qwen chat JSONL。
4. 训练一次真实 LoRA SFT。
5. 固定 20 个 prompt 做 base vs SFT 对比。
6. 写一份初版实验报告。

只有真实 SFT 稳了，再进入：

```text
DPO
多卡说明
Gradio demo
```
