# 给初学者看的项目学习报告

这份报告是写给“还不完全懂大模型训练，但想把项目讲清楚”的自己看的。

## 1. 我们到底在做什么

我们现在做的是一个很小但完整的大模型微调项目。

模型：

```text
Qwen/Qwen2.5-0.5B-Instruct
```

硬件：

```text
本地 RTX 4060 Laptop GPU
```

目标：

```text
先跑通 LoRA SFT，再用公开数据训练，再做自采集数据清洗和训练，之后再做 DPO。
```

这不是为了马上训练出很强的模型，而是为了真正理解：

- 模型怎么加载。
- 数据怎么变成训练格式。
- LoRA 微调到底训练了哪些参数。
- adapter 怎么保存和加载。
- SFT 前后怎么对比。
- 遇到环境问题时怎么排查。
- 公开数据和自采集数据分别解决什么问题。
- 爬取来的文本如何清洗、筛选并变成 instruction-answer 数据。

面试时，这比“我跑过一个别人的 demo”更有说服力。

## 2. 什么是 Qwen2.5-0.5B-Instruct

Qwen 是通义千问系列开源模型。

`0.5B` 表示模型大约 5 亿参数。

`Instruct` 表示它已经做过指令微调，可以直接按照用户问题回答。

我们选它是因为：

1. 模型小，本地 4060 能跑。
2. 下载和训练都比较快。
3. 适合学习完整流程。
4. 后续可以迁移到更大的 Qwen 模型。

## 3. 什么是 LoRA

LoRA 是一种参数高效微调方法。

普通全量微调会更新模型大部分参数，成本很高。

LoRA 的做法是：

```text
冻结原模型参数
只在部分线性层上插入小的低秩矩阵
训练这些小矩阵
```

所以它的优点是：

- 显存需求低。
- 训练速度快。
- adapter 文件小。
- 适合个人 GPU 学习。

我们 smoke test 中看到：

```text
trainable params: 4,399,104
all params: 498,431,872
trainable%: 0.8826
```

这说明我们只训练了不到 1% 的参数。

这里很容易混淆一点：

```text
LoRA 不是和 SFT 并列的训练目标。
LoRA 是“怎么训练”：只训练少量 adapter 参数。
SFT 是“用什么目标训练”：用 instruction-answer 数据做有监督学习。
```

所以我们现在做的不是“只做 SFT，没做 LoRA”，而是：

```text
用 LoRA 方法做 SFT 微调，也就是 LoRA SFT。
```

## 4. 什么是 SFT

SFT 是 supervised fine-tuning，有监督微调。

它的数据大概长这样：

```json
{
  "messages": [
    {"role": "system", "content": "你是一个中文助手。"},
    {"role": "user", "content": "请解释什么是LoRA微调。"},
    {"role": "assistant", "content": "LoRA是一种参数高效微调方法……"}
  ]
}
```

SFT 的目的不是让模型凭空变聪明，而是让模型学习一种目标回答方式。

比如我们希望模型能正确解释：

- LoRA
- SFT
- DPO
- adapter
- loss
- batch size
- gradient accumulation

现在 base model 会把 LoRA 解释成无线通信 LoRa 或其他错误概念，这就是我们后续训练要改善的点。

## 5. 什么是 DPO

DPO 是 direct preference optimization，直接偏好优化。

它不是普通问答数据，而是成对偏好数据：

```json
{
  "prompt": "为什么第一次学习微调适合用小模型？",
  "chosen": "小模型下载快、显存压力小、迭代快，适合理解完整流程。",
  "rejected": "因为小模型便宜，随便跑就行。"
}
```

DPO 让模型更偏向 chosen，远离 rejected。

但我们现在还不急着做 DPO。

原因：

```text
先把 SFT 跑稳，再做 DPO。
```

如果 SFT 数据和训练都没做好，DPO 只会放大混乱。

## 6. 我们这次遇到了什么大坑

最麻烦的问题是 Windows 弹窗：

```text
python.exe - 应用程序错误
内存不能为 read
```

这不是普通 Python 报错。

普通 Python 报错会有 traceback，能看到哪一行错了。

这个弹窗说明：

```text
Python 进程直接崩溃了。
```

这种问题通常来自底层原生库，比如：

- PyTorch
- tokenizers
- safetensors
- accelerate
- 版本不兼容的二进制包

我们最后发现，原来的包太新：

```text
transformers 5.8.1
peft 0.19.1
trl 1.4.0
huggingface-hub 1.14.0
```

在 Windows 原生训练路径里不稳定。

解决方式是降到更保守的稳定版本：

```text
transformers 4.46.3
peft 0.13.2
accelerate 1.1.1
datasets 3.1.0
trl 0.12.2
```

同时恢复 CUDA 版 PyTorch：

```text
torch 2.5.1+cu124
```

## 7. 我们现在跑通了什么

我们已经跑通了完整 smoke test：

```text
环境检查
  -> base model 推理
  -> demo 数据准备
  -> LoRA SFT 训练
  -> adapter 保存
  -> adapter 加载推理
  -> base vs SFT 对比
```

这说明工程链路是通的。

但注意：

```text
模型效果现在还不好。
```

这很正常，因为 demo 只用了 4 条训练样本。

这个阶段的意义是：

```text
证明代码、环境、GPU、训练、保存、加载都能工作。
```

现在还新增了一个总流程学习 notebook：

```text
notebooks/04_full_pipeline_learning.ipynb
```

它的作用是让你按格子一步一步复现环境检查、base 推理、数据准备、LoRA SFT、
Stage 4A 对比、Stage 2B 自采集技术数据，以及后续 DPO 的计划。

## 8. 为什么现在还不能说项目完成

因为 smoke test 只是“流程打通”。

真正的项目还需要两个数据闭环：

第一个闭环是公开数据集：

1. 准备 500-2000 条干净 SFT 数据。
2. 跑一次真实 LoRA SFT。
3. 固定 prompt 对比 base 和 public-SFT。
4. 记录 loss、训练时间、显存占用。

第二个闭环是自采集数据：

1. 爬取或收集自己喜欢的中文技术学习内容。
2. 清洗网页噪声、导航栏、广告、重复文本和无关内容。
3. 把清洗后的内容改写成 instruction-answer 样本。
4. 当前第一版已经生成 144 条 train 和 16 条 eval。
5. 下一步训练 custom 或 mixed adapter。
6. 对比 base、public-SFT、custom-SFT 三种输出。

最后再写 badcase、改进分析，并在 SFT 稳定后进入 DPO。

## 9. 下一步怎么学

下一步只做一件事：

```text
用自采集技术数据训练 custom LoRA SFT adapter
```

不要同时做 DPO、多卡、Gradio。

建议顺序：

1. 公开数据 SFT 已经跑通，Stage 4A 也已经确认 public-SFT 没修正 LoRA/SFT/DPO 概念误解。
2. Stage 2B 已经完成第一版：160 条 seed，切成 144 条 train 和 16 条 eval。
3. 接下来训练 custom 或 mixed adapter，并做三方对比。
4. 对比时重点看 LoRA/SFT/DPO 概念是否被修正，不要只看 loss。
5. DPO 放到最后，因为它更吃显存，也更依赖前面的 SFT 数据质量。

显存上也要有概念：

```text
LoRA SFT 训练约 5.5GB / 8GB
adapter 推理约 1.2GB / 8GB
DPO 可能更高，第一版只能小样本、短序列、batch_size=1 做 smoke test
```

## 10. 面试时可以怎么讲

可以这样讲：

> 我没有一开始追求大模型规模，而是先用 Qwen2.5-0.5B-Instruct 在本地 RTX 4060 上搭了一条最小 post-training 链路。过程中我完成了环境配置、模型加载、LoRA adapter 训练、adapter 保存和加载、base/SFT 输出对比。最开始 Windows 原生环境里 Hugging Face 高版本栈触发了 python.exe 级别崩溃，我通过版本回退、缓存目录调整和脚本兼容修改，把训练链路稳定下来。数据上我先用公开中文 Alpaca 风格数据集建立可复现基线；这个 public-SFT adapter 能训练成功，但固定 prompt 发现它仍然误解 LoRA/SFT/DPO。于是我做了 Stage 2B 自采集技术数据：从项目技术报告和概念种子中采集、清洗、去重、筛选并转成 instruction-answer，生成 144 条 train 和 16 条 eval，下一步用它训练 custom-SFT。显存方面，LoRA SFT 约占 5.5GB/8GB，DPO 更吃显存，所以我计划先用短序列、小 batch、小样本做 DPO smoke test。

这段话的重点是：

- 你不是只跑 demo。
- 你知道 LoRA/SFT/DPO 的位置。
- 你遇到过真实环境问题。
- 你有排查和收敛能力。
- 你不只是下载数据，还能讲清楚数据采集、清洗和转换。
- 你能解释为什么 public-SFT 没解决目标问题，以及下一步怎么用数据修正。
- 你对显存和 DPO 风险有预案。
- 你知道下一步怎么迭代。
