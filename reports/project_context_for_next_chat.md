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
> 再逐步扩展到公开数据 SFT、自采集数据清洗与 SFT、DPO、多卡训练说明。

旧方向已经废弃：

```text
qwen-military-posttraining
军事/战略大模型
Colab-first workflow
```

现在不追求一开始做很大的垂直领域模型，而是用最小步子把完整训练链路做精。
数据路线不要停在“下载一个数据集”。当前决策是：

```text
先用公开中文 instruction 数据集跑通可复现 SFT 基线
再做自采集/爬虫数据的清洗、筛选、转换和 custom/mixed SFT
最后比较 base、public-SFT、custom-SFT
```

原因：公开数据集先跑通可以控制变量，证明训练链路稳定；自采集数据放在后面，
可以单独讲清楚数据工程能力，包括爬取、清洗、去重、筛选、转 instruction-answer。

术语说明：

```text
SFT = 有监督微调目标和数据形式
LoRA = 参数高效微调方法
当前训练 = 用 LoRA adapter 做 SFT，也就是 LoRA SFT
```

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

显存观察：

```text
公开数据 LoRA SFT 训练约 5.5GB / 8GB
adapter 推理约 1.2GB / 8GB
DPO 会更吃显存，后续只能先做很小的 smoke test
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

### 7. Stage 2 真实 SFT 数据准备

已选择常见中文 instruction 数据集：

```text
llm-wizard/alpaca-gpt4-data-zh
```

已新增下载脚本：

```text
scripts/download_hf_sft_data.py
```

已生成本地 raw 快照：

```text
data/raw/alpaca_gpt4_data_zh_1200.jsonl
```

已转换成 Qwen chat JSONL：

```text
data/processed/sft_train.jsonl
data/processed/sft_eval.jsonl
```

转换结果：

```text
Raw samples: 1200
Valid samples: 1114
Train samples: 1003
Eval samples: 111
Dropped samples: 86
Duplicate prompts: 0
```

校验结果：

```text
Role order: system -> user -> assistant
Qwen tokenizer encoding: passed
Train token length before truncation: min 47, avg 177.5, p95 314, max 531
Eval token length before truncation: min 50, avg 179.2, p95 319, max 555
```

报告：

```text
reports/stage2_sft_data_report.md
```

### 8. 数据管线新计划

新增计划文档：

```text
reports/data_pipeline_plan.md
```

后续阶段调整为：

```text
Stage 3A: 用公开数据集训练 LoRA adapter
Stage 4A: base vs public-SFT 对比
Stage 2B: 自采集数据爬取和清洗
Stage 3B: 用 custom 或 mixed 数据训练 LoRA adapter
Stage 4B: base vs public-SFT vs custom-SFT 三方对比
Stage 5: SFT 稳定后再做 DPO
```

Stage 2B 初始建议：

```text
先做 100-300 条高质量自采集样本
主题优先选择中文技术学习内容：LoRA、SFT、DPO、Hugging Face、CUDA/Windows 调试、实验记录、面试讲述
不要直接复制大段受版权保护文章，优先用公开文档、自己的笔记、摘要和短摘录
```

### 9. Stage 3A 公开数据 LoRA SFT

已完成真实 LoRA SFT 训练：

```text
outputs/sft_lora_qwen05b_public
```

训练结果：

```text
Train samples: 1003
Eval samples: 111
Trainable params: 4,399,104
Trainable%: 0.8826
Runtime: about 24.4 minutes
Final train loss: 1.7558
Eval loss at step 100: 1.8263
```

已生成对比：

```text
reports/compare_outputs_public_sft.jsonl
```

报告：

```text
reports/stage3a_public_lora_sft_report.md
```

重要观察：

```text
public-SFT adapter 能训练、保存、加载，但仍然把 LoRA/SFT/DPO 误解成无线通信、
软件功能、防火墙、灾备计划等无关概念。
```

结论：

```text
公开通用 instruction 数据集可以证明训练链路，但不能解决目标技术概念。
这正好说明 Stage 2B 自采集技术数据是必要的。
```

### 10. Stage 4A base vs public-SFT 对比

已完成固定 prompt 对比：

```text
reports/compare_outputs_public_sft.jsonl
reports/compare_base_sft.md
reports/stage4a_public_sft_comparison_report.md
```

结论：

```text
Stage 4A 确认 public-SFT 没有修正 LoRA/SFT/DPO 的技术概念误解。
这不是项目失败，而是下一阶段做自采集技术数据的依据。
```

### 11. 学习型总流程 notebook

新增：

```text
notebooks/04_full_pipeline_learning.ipynb
```

用途：

```text
把环境检查、base 推理、公开数据准备、LoRA SFT、Stage 4A 对比、
后续爬虫/清洗/DPO 规划串成可逐格运行的学习路线。
耗时训练 cell 默认用开关关闭。
```

### 12. DPO 显存计划

新增：

```text
reports/vram_and_dpo_plan.md
```

核心判断：

```text
8GB 可能能做 tiny DPO smoke test，但朴素 DPO 风险较高。
第一版 DPO 应该 20-50 pair、batch_size=1、短 max_length、短 max_prompt_length、少 eval。
优先使用 LoRA/PEFT 和 reference 共享，避免加载两份完整模型。
```

### 13. Stage 2B 自采集技术数据

已完成第一版 Stage 2B：

```text
scripts/prepare_custom_technical_data.py
```

这版没有直接抓取外部长网页，而是先用项目自有技术报告和手工概念种子构建数据。
原因：

```text
1. 可复现，不依赖外网。
2. 避免复制受版权保护长文章。
3. 仍然完整覆盖采集、清洗、筛选、去重、转 instruction-answer。
4. 脚本保留 --url_file，后续可以接入你选定的网页来源继续爬取。
```

输出：

```text
data/raw/custom_sources.jsonl
data/raw/custom_cleaned_chunks.jsonl
data/raw/custom_instruction_seed.jsonl
data/processed/custom_sft_train.jsonl
data/processed/custom_sft_eval.jsonl
data/samples/custom_technical_prompts.jsonl
```

统计：

```text
Sources: 10
Accepted cleaned chunks: 81
Rejected chunks: 9
Instruction-answer seed samples: 160
Train samples: 144
Eval samples: 16
Duplicate instruction samples: 0
Token length before truncation: train max 510, eval max 391, no rows over 512
```

报告：

```text
reports/stage2b_custom_technical_data_report.md
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
Stage 3B: 用自采集技术数据训练 custom LoRA SFT adapter
```

建议目标：

1. 使用 `data/processed/custom_sft_train.jsonl` 和 `data/processed/custom_sft_eval.jsonl`。
2. 输出目录用 `outputs/sft_lora_qwen05b_custom`。
3. 先用 `epochs=3`、`batch_size=1`、`grad_accum=4` 做小数据训练。
4. 用 `data/samples/custom_technical_prompts.jsonl` 做 base vs public-SFT vs custom-SFT 三方对比。
5. 重点看 LoRA/SFT/DPO 概念是否被修正，不要只看 loss。

只有 public-SFT 和 custom/mixed-SFT 两个闭环都稳了，再进入：

```text
DPO
多卡说明
Gradio demo
```
