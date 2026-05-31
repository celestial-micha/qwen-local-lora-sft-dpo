# Project Learning Notebooks 中文学习导览

我们现在开始学习这个项目，我们学习策略的策略是“越少越多”：先读通一个真实入口，再进入下一层。

## 推荐顺序

0. `00_START_项目总架构_入口出口和代码地图.ipynb`
1. `01_SFT_LoRA最小训练闭环_从一条数据到adapter.ipynb`
2. `02_自己构造5条SFT数据_训练一个自己的LoRA.ipynb`
3. `03_训练后怎么用infer加载adapter并对比.ipynb`
4. `04_模型评估闭环_从回答到行为门禁.ipynb`
5. `05_继续DPO训练_从preference数据到安全验收.ipynb`

## 每个文件的学习目标

- `01`：只看 `scripts/train_sft_lora.py`，搞懂 SFT JSONL 如何变成 LoRA adapter。
- `02`：自己构造 5 条 messages 数据，理解怎么喂给训练脚本。
- `03`：回到 `scripts/infer.py`，理解训练后的 adapter 怎么加载和对比。
- `04`：只看 `compare_four_outputs.py` 和 `score_*`，搞懂为什么评估不能只看 loss。
- `05`：只看 `train_dpo.py`、`configs/dpo_*.yaml` 和 preference JSONL，搞懂继续 DPO 前后必须怎么验收。

## 安全说明

默认不训练、不写文件、不推理。涉及写文件、训练、推理的格子都有 `WRITE_FILES=False`、`RUN_TINY_TRAINING=False` 或 `RUN_COMPARE=False` 开关。
