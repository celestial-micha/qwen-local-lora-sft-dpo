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
4. 第一版曾生成 144 条 train 和 16 条 eval，但 Stage 3B 初跑后发现它仍然有幻觉。
5. 后来我们减少泛化的项目总结样本，加入更直接的 targeted QA，先修订成 119 条 train 和 13 条 eval。
6. Stage 2B.2 又补了 8 条 badcase 样本，数据变成 126 条 train 和 14 条 eval。
7. Stage 2B.3 继续补 loss-vs-behavior 和 replay 样本，当前数据变成 142 条 train 和 15 条 eval，另有 28 条 focused patch。
8. 再训练 custom adapter，并对比 base、public-SFT、custom-SFT 三种输出。

最后再写 badcase、改进分析，并在 SFT 稳定后进入 DPO。

## 9. 下一步怎么学

现在已经完成了一轮 custom-SFT。下一步先做一件事：

```text
检查和理解 Stage 3B/4B 结果，再决定是否补一小轮数据
```

不要同时做 DPO、多卡、Gradio。

建议顺序：

1. 公开数据 SFT 已经跑通，Stage 4A 也已经确认 public-SFT 没修正 LoRA/SFT/DPO 概念误解。
2. Stage 2B 已经完成并修订；Stage 2B.3 后当前是 157 条 seed，切成 142 条 train 和 15 条 eval。
3. Stage 3B 已经训练出 `outputs/sft_lora_qwen05b_custom`，final train loss 是 0.4656。
4. Stage 4B 三方对比显示 custom-SFT 明显改善 6/8 个固定技术 prompt。
5. Stage 2B.2 又补了 8 条 badcase 样本，当前数据变成 126 条 train 和 14 条 eval。
6. 这次最重要的经验是：从头训练 v2 反而回归，低学习率从 v1 续训的 v3 更稳，改善或保留了 7/8 个 prompt。
7. Stage 2B.3 继续尝试修“为什么不能只看 loss”：v4 没修好，v5 修好了但破坏旧能力，v6 仍然不稳。
8. 当前最好 adapter 仍然是 v3，原因是它整体最稳，虽然不是完美。
9. Stage 5 已拆分：先准备 tiny DPO 数据，再跑 tiny DPO smoke test，观察显存/内存和速度，再决定是否扩大 DPO。

显存上也要有概念：

```text
LoRA SFT 训练约 5.5GB / 8GB
adapter 推理约 1.2GB / 8GB
DPO 可能更高，第一版只能小样本、短序列、batch_size=1 做 smoke test
```

这次 Stage 3B/4B/Stage 2B.2/2B.3 的最大收获是：loss 下降只是一个信号，真正要看的还是固定 prompt 行为。第一版 custom 数据训练后仍有幻觉，我们就回到数据侧减少噪声、增加 targeted QA；Stage 2B.2 发现从头重训会破坏旧能力；Stage 2B.3 又发现强行修一个 prompt 会让其他 prompt 回归。这就是一个更真实的数据改进闭环：不仅会加数据，还会做回归测试、训练策略选择和 DPO 前 gate。接下来的 DPO 也不能一口吃成胖子，要先 tiny smoke test，看 8GB 显存能不能承受。

## 10. 面试时可以怎么讲

可以这样讲：

> 我没有一开始追求大模型规模，而是先用 Qwen2.5-0.5B-Instruct 在本地 RTX 4060 上搭了一条最小 post-training 链路。过程中我完成了环境配置、模型加载、LoRA adapter 训练、adapter 保存和加载、base/SFT 输出对比。最开始 Windows 原生环境里 Hugging Face 高版本栈触发了 python.exe 级别崩溃，我通过版本回退、缓存目录调整和脚本兼容修改，把训练链路稳定下来。数据上我先用公开中文 Alpaca 风格数据集建立可复现基线；这个 public-SFT adapter 能训练成功，但固定 prompt 发现它仍然误解 LoRA/SFT/DPO。于是我做了 Stage 2B 自采集技术数据：从项目技术报告和概念种子中采集、清洗、去重、筛选并转成 instruction-answer。第一版 custom 数据训练后仍有幻觉，我又根据 badcase 减少泛化项目总结样本、加入 targeted QA，重新训练 custom-SFT。Stage 4B 三方对比显示 custom-SFT 改善了 6/8 个固定技术 prompt；后来 Stage 2B.2 加了 8 条 badcase patch，发现从头训练 v2 会回归，而从 v1 低学习率续训的 v3 能保留或改善 7/8 个 prompt。Stage 2B.3 又尝试修最后的 loss-vs-behavior prompt，结果发现 v5 虽然修好了单点，却破坏多个旧 prompt，所以我选择 v3 作为 DPO 起点，并把 Stage 5 拆成 tiny DPO 数据、tiny DPO smoke test、固定 prompt 对比和更大 DPO 四步。显存方面，LoRA SFT 约占 5.5GB/8GB，DPO 更吃显存，所以我会先用短序列、小 batch、小样本验证 8GB 是否能承受，再考虑扩大 DPO。

这段话的重点是：

- 你不是只跑 demo。
- 你知道 LoRA/SFT/DPO 的位置。
- 你遇到过真实环境问题。
- 你有排查和收敛能力。
- 你不只是下载数据，还能讲清楚数据采集、清洗和转换。
- 你能解释为什么 public-SFT 没解决目标问题，以及下一步怎么用数据修正。
- 你对显存和 DPO 风险有预案。
- 你知道下一步怎么迭代。

## 11. 2026-05-16 最终更新

项目后来已经继续完成 Stage 5 和 Stage 6：

- Stage 5 tiny DPO、candidate DPO、larger naive DPO、Stage 5H prompt 7 数据
  设计、expanded behavior gate、DPO v7/v8、SFT repair probes 都已经跑完。
- DPO 硬件可行：8GB RTX 4060 Laptop GPU 可以跑 Qwen2.5-0.5B LoRA DPO，
  包括 separate frozen reference 的 v6。
- 行为没有完全通过：DPO v6/v7/v8 都停在固定 prompt 7 / 8，prompt 7
  仍然失败。
- Stage 5O 证明 exact SFT 可以强行修 prompt 7，但会把旧题打坏，所以不能
  只看单题通过。
- Stage 6 已完成最终面试包。

最终推荐：

```text
保守推荐 checkpoint: outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
最好 DPO artifact:   outputs/dpo_lora_qwen05b_naive_v6
最终总结:             reports/final_project_summary_zh.md
面试包:               reports/stage6_final_interview_package.md
```

现在这份 beginner report 应理解为“学习过程记录”。真正最终结论以
`reports/final_project_summary_zh.md` 和
`reports/stage6_final_interview_package.md` 为准。
