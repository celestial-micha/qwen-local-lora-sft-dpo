# Qwen 本地 LoRA / SFT / DPO 最小项目

中文 | [English](README.md)

这是一个用本地 RTX 4060 Laptop GPU 学习和展示 Qwen 小模型 LoRA 微调、
SFT 有监督微调，以及后续 DPO 偏好优化的最小可复现项目。

这里的关系是：SFT 是训练目标和数据形式，LoRA 是参数高效微调方法。
所以当前核心训练不是“只做 SFT 没做 LoRA”，而是“用 LoRA adapter 来做 SFT”，
也就是 LoRA SFT。

项目第一版使用：

```text
Qwen/Qwen2.5-0.5B-Instruct
```

核心目标不是一开始做很大的领域模型，而是先把一条真正能讲清楚、能复现、
能写进简历和面试讲述的训练链路跑通。数据路线分成两个闭环：先用公开中文
instruction 数据集跑通可复现基线，再做自采集数据的爬取、清洗、筛选、
转换和二次 SFT 对比。

## 当前状态

已经完成：

- 本地 RTX 4060 CUDA 环境验证。
- 修复并稳定了 Windows 本地训练环境。
- Qwen2.5-0.5B base 推理跑通。
- demo SFT 数据生成跑通。
- 最小 LoRA SFT smoke test 跑通。
- LoRA adapter 保存和加载跑通。
- base vs SFT 对比结果已经生成。
- 已从 `llm-wizard/alpaca-gpt4-data-zh` 准备真实 Stage 2A SFT 数据。
- Stage 3A 公开数据 LoRA SFT 已跑通，adapter 保存到 `outputs/sft_lora_qwen05b_public`。
- Stage 4A base vs public-SFT 对比已完成。
- 已新增总流程学习 notebook：`notebooks/04_full_pipeline_learning.ipynb`。
- Stage 2B 自采集技术数据已完成第一版，生成 144 条 train 和 16 条 eval。

还没有完成：

- Stage 3B custom-data LoRA SFT 训练。
- DPO 数据和 DPO 训练。
- 多卡训练说明或实验。

## 为什么改成这个项目

之前的计划太大：军事大模型、Colab、DPO、安全评测、Gradio、多卡扩展全都想做。
这个方向长期可以做，但不适合作为第一个要在面试前完成的项目。

现在我们改成最小步子：

```text
环境检查
  -> Qwen base 推理
  -> 公开 SFT 数据准备
  -> 公开数据 LoRA SFT
  -> base vs public-SFT 对比
  -> 自采集数据爬取和清洗
  -> custom/mixed LoRA SFT
  -> base vs public-SFT vs custom-SFT 对比
  -> 后续 DPO
```

这样项目更容易完成，也更容易在面试里讲清楚。

为什么不直接先做爬虫数据：公开数据集先跑通，可以把训练链路和数据工程问题拆开。
等公开数据 SFT 能训练、保存、加载和对比之后，再引入自采集数据，面试时就能讲清楚
“先建立稳定基线，再做数据清洗和定制化改进”。

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

准备真实 Stage 2A 公开 SFT 数据：

```powershell
python scripts\download_hf_sft_data.py `
  --dataset_name llm-wizard/alpaca-gpt4-data-zh `
  --split train `
  --output_file data\raw\alpaca_gpt4_data_zh_1200.jsonl `
  --max_samples 1200 `
  --seed 42

python scripts\prepare_data.py `
  --input_file data\raw\alpaca_gpt4_data_zh_1200.jsonl `
  --train_file data\processed\sft_train.jsonl `
  --eval_file data\processed\sft_eval.jsonl `
  --eval_ratio 0.1 `
  --max_samples 1200 `
  --min_answer_chars 20 `
  --seed 42
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

运行 Stage 4A public-SFT 对比：

```powershell
python scripts\compare_outputs.py `
  --prompt_file data\samples\smoke_prompts.jsonl `
  --adapter_path outputs\sft_lora_qwen05b_public `
  --output_file reports\compare_outputs_public_sft.jsonl `
  --max_new_tokens 96 `
  --local_files_only
```

准备 Stage 2B 自采集技术数据：

```powershell
python scripts\prepare_custom_technical_data.py `
  --raw_sources_file data\raw\custom_sources.jsonl `
  --cleaned_chunks_file data\raw\custom_cleaned_chunks.jsonl `
  --instruction_seed_file data\raw\custom_instruction_seed.jsonl `
  --train_file data\processed\custom_sft_train.jsonl `
  --eval_file data\processed\custom_sft_eval.jsonl `
  --eval_ratio 0.1 `
  --max_doc_samples 60 `
  --seed 42
```

## 学习型 Notebook

主 notebook：

```text
notebooks/04_full_pipeline_learning.ipynb
```

它的作用是把整个项目变成可以逐格运行的学习路线图。目前覆盖环境检查、base 推理、
公开数据准备、public LoRA SFT、Stage 4A 对比、Stage 2B 自采集技术数据准备和 DPO 显存说明。
耗时训练 cell 默认用开关关闭，避免误运行。

## 重要文档

- [下次聊天先读这个](reports/project_context_for_next_chat.md)
- [Windows 环境问题排查报告](reports/windows_debug_report.md)
- [给初学者看的中文学习报告](reports/beginner_learning_report_zh.md)
- [base vs SFT demo 输出](reports/compare_outputs_demo.jsonl)
- [数据管线计划](reports/data_pipeline_plan.md)
- [Stage 2A SFT 数据报告](reports/stage2_sft_data_report.md)
- [Stage 3A public LoRA SFT 报告](reports/stage3a_public_lora_sft_report.md)
- [Stage 4A public-SFT 对比报告](reports/stage4a_public_sft_comparison_report.md)
- [Stage 2B 自采集技术数据报告](reports/stage2b_custom_technical_data_report.md)
- [显存与 DPO 计划](reports/vram_and_dpo_plan.md)

## 下一步

下一步不是 DPO，也不是多卡，而是 Stage 3B：用自采集技术数据训练 custom LoRA SFT。

1. 使用 `data/processed/custom_sft_train.jsonl` 和 `data/processed/custom_sft_eval.jsonl`。
2. 保存 adapter 到 `outputs/sft_lora_qwen05b_custom`。
3. 用 `data/samples/custom_technical_prompts.jsonl` 做 base vs public-SFT vs custom-SFT 三方对比。
4. 等 SFT 两个闭环都稳定了，再进入 tiny DPO smoke test。
