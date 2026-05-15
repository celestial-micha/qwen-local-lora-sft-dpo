"""Prepare Stage 5A tiny DPO preference data.

The first DPO dataset is intentionally small and hand-curated. It is not meant
to be a final preference corpus; it is a controlled smoke-test dataset for the
Stage 5B memory and behavior probe.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


START_ADAPTER = "outputs/sft_lora_qwen05b_custom_v3_from_v1_patch"


PAIRS: list[dict[str, str]] = [
    {
        "category": "loss_vs_behavior",
        "prompt": "为什么不能只看 loss 判断一次 SFT 是否成功？",
        "chosen": "不能只看 loss，因为 loss 只是训练目标上的平均拟合信号，不等于目标 prompt 的实际回答已经正确。本项目里 public-SFT 能训练完成，v2 也有更低 loss 的迹象，但固定 prompt 仍会误解或回归，所以要同时看 train/eval loss、固定 prompt 对比、badcase review 和旧能力是否保住。",
        "rejected": "只要 loss 降低，就说明 SFT 已经成功。固定 prompt 的回答可以以后再看，训练指标已经足够证明模型变好了。",
    },
    {
        "category": "loss_vs_behavior",
        "prompt": "如果一个 adapter 的 eval loss 很低，但固定技术 prompt 回答变差了，应该怎么判断？",
        "chosen": "应该判为行为不通过，至少不能直接替代当前 best adapter。eval loss 只能说明验证集平均拟合好，固定 prompt 变差说明目标行为或旧能力发生回归，需要保留原 adapter，补充数据或改用更保守的训练/DPO 设计。",
        "rejected": "eval loss 低就代表模型泛化更好，固定 prompt 变差只是偶然现象，可以直接把它作为新版本。",
    },
    {
        "category": "loss_vs_behavior",
        "prompt": "为什么 Stage 2B.2 的 v2 低 loss 结果仍然不推荐？",
        "chosen": "因为 v2 从头训练后在核心 LoRA/SFT prompt 上回归，说明它虽然学到了新补丁或局部数据，却破坏了旧 adapter 已经稳定的行为。这个结果证明小数据 patch 要看固定 prompt 回归测试，而不是只看 loss。",
        "rejected": "v2 不推荐主要是因为训练时间太短。如果 loss 更低，就应该直接继续训练更多 epoch，行为回归不用单独分析。",
    },
    {
        "category": "loss_vs_behavior",
        "prompt": "为什么 v5 修好了 loss prompt，却仍然不能作为 Stage 5 起点？",
        "chosen": "v5 修好了单个 loss-vs-behavior prompt，但多个旧 prompt 明显回归，说明 focused patch 过强、过窄，学到的是局部答案而不是稳定能力。Stage 5 起点要优先整体稳定，所以仍用 v3。",
        "rejected": "只要 v5 修好了最后一个 prompt，它就是最好的起点。旧 prompt 回归说明模型更专注了，不影响进入 DPO。",
    },
    {
        "category": "loss_vs_behavior",
        "prompt": "SFT 实验复盘时，loss 和行为评测分别承担什么角色？",
        "chosen": "loss 用来判断训练是否在优化、是否异常发散；行为评测用来判断目标问题是否真的被解决。两者要一起看：loss 正常但行为错误，说明数据或训练目标不够；行为改善但旧 prompt 回归，也不能算稳定成功。",
        "rejected": "loss 是唯一客观指标，行为评测太主观。只要训练曲线下降，复盘时就可以认为实验通过。",
    },
    {
        "category": "loss_vs_behavior",
        "prompt": "为什么固定 prompt 回归测试比单次生成样例更可靠？",
        "chosen": "固定 prompt 让 base、public-SFT、custom-SFT 和后续 DPO 在同一问题上对比，能暴露概念误解、旧能力回归和风格漂移。单次随手生成容易换题、换难度，无法判断改进来自模型还是来自问题变化。",
        "rejected": "单次生成样例已经能看出模型好不好，固定 prompt 太机械，而且会让模型过拟合几个问题。",
    },
    {
        "category": "loss_vs_behavior",
        "prompt": "如何向面试官解释“loss 下降但模型回答仍错”的现象？",
        "chosen": "我会说 loss 衡量的是训练数据上的平均 token 预测，不等于真实业务 prompt 的正确性。如果数据没有覆盖目标概念，或者 patch 破坏了旧能力，loss 仍可能下降。所以我用固定 prompt、三方对比和 badcase review 来补足指标。",
        "rejected": "loss 下降但回答错，说明推理代码有问题；训练本身已经成功，不需要再检查数据或行为。",
    },
    {
        "category": "public_sft_motivation",
        "prompt": "为什么 public-SFT adapter 没修正 LoRA/SFT/DPO 概念误解，反而说明 Stage 2B 有必要？",
        "chosen": "因为 public-SFT 证明的是训练链路能跑通，不等于目标领域行为已经解决。Stage 4A 发现它仍误解 LoRA/SFT/DPO，说明公开通用 instruction 数据没有覆盖这些项目概念，所以需要 Stage 2B 自采集技术数据做定向补足。",
        "rejected": "public-SFT 没修好概念，说明 SFT 这条路线失败了。Stage 2B 没有必要，应该直接换更大的模型或直接做 DPO。",
    },
    {
        "category": "public_sft_motivation",
        "prompt": "public-SFT 在这个项目里的价值是什么？",
        "chosen": "它是可控基线：先验证数据转换、tokenizer、LoRA 训练、adapter 保存和加载都能工作，再用固定 prompt 暴露目标概念 badcase。它的价值不是最终质量，而是把工程问题和数据问题分开。",
        "rejected": "public-SFT 的价值就是让模型最终可用。只要它训练完成，后面的 custom 数据和对比都可以省略。",
    },
    {
        "category": "public_sft_motivation",
        "prompt": "为什么不能直接把 public-SFT 失败理解成训练脚本失败？",
        "chosen": "因为训练脚本已经完成了训练、保存和加载，指标也正常记录。失败发生在目标行为上：通用数据没有教会模型本项目关心的 LoRA/SFT/DPO 概念。这个区别决定下一步是补数据，而不是先重写训练脚本。",
        "rejected": "如果 public-SFT 回答不好，最可能是脚本错了。应该先大改训练代码，而不是检查数据覆盖和 prompt 对比。",
    },
    {
        "category": "public_sft_motivation",
        "prompt": "Stage 4A 的 badcase 怎样驱动 Stage 2B 数据建设？",
        "chosen": "Stage 4A 把 public-SFT 的概念误解记录成固定 prompt，然后 Stage 2B 围绕这些 prompt 收集和改写 LoRA、SFT、DPO、显存和实验复盘内容。也就是说，badcase 不是结尾，而是下一轮数据设计的输入。",
        "rejected": "Stage 4A 只是展示结果，不影响数据建设。Stage 2B 应该尽量随机收集更多文本，数量越多越好。",
    },
    {
        "category": "public_sft_motivation",
        "prompt": "为什么 Stage 2B 不是盲目堆更多数据？",
        "chosen": "Stage 2B 是围绕固定 badcase 的数据闭环：采集相关技术内容，清洗噪声，去重筛选，再改写成 instruction-answer。它强调覆盖目标概念和可复盘来源，而不是把无关网页文本直接堆进训练集。",
        "rejected": "Stage 2B 的重点就是尽量多爬网页。数据越多越能解决问题，清洗和来源记录不是重点。",
    },
    {
        "category": "lora_sft_dpo_replay",
        "prompt": "请用三点解释机器学习里的 LoRA 微调，不要解释成无线通信 LoRa。",
        "chosen": "第一，机器学习里的 LoRA 通常指低秩适配，是参数高效微调方法，不是无线通信 LoRa。第二，它冻结基础模型大部分权重，只训练插入到线性层旁边的低秩 adapter。第三，它适合个人 GPU，因为可训练参数少、显存压力低、adapter 文件小。",
        "rejected": "LoRA 是一种远距离无线通信技术，也可以用于机器学习模型之间传输数据。微调时主要优化通信距离和网络延迟。",
    },
    {
        "category": "lora_sft_dpo_replay",
        "prompt": "SFT 是什么？它和 LoRA 是什么关系？",
        "chosen": "SFT 是 supervised fine-tuning，描述的是用标准回答数据做有监督微调的训练目标和数据形式。LoRA 是参数高效微调方法，描述的是如何少量更新参数。LoRA SFT 就是用 LoRA adapter 来执行 SFT。",
        "rejected": "SFT 是 LoRA 的一种网络结构缩写，LoRA 是 SFT 的子模块。两者都是模型架构，和训练数据格式关系不大。",
    },
    {
        "category": "lora_sft_dpo_replay",
        "prompt": "DPO 和 SFT 的区别是什么？为什么通常先做 SFT 再做 DPO？",
        "chosen": "SFT 用 instruction-answer 数据教模型先形成基础回答能力；DPO 用 chosen/rejected 偏好对让模型更偏向好回答、远离坏回答。通常先 SFT，因为基础行为不稳时，DPO 可能放大混乱，而不是稳定改进。",
        "rejected": "DPO 是数据预处理，SFT 是特征合成。通常直接做 DPO 就行，SFT 对模型回答能力没有基础作用。",
    },
    {
        "category": "lora_sft_dpo_replay",
        "prompt": "LoRA adapter 和完整模型是什么关系？",
        "chosen": "LoRA adapter 不是完整模型，而是一组小的增量权重。推理时仍需要加载基础模型，再把 adapter 加到指定层上。这样可以让训练和分发更轻量，但不能把 adapter 单独当成完整可推理模型。",
        "rejected": "LoRA adapter 就是训练后的完整模型。只要有 adapter 文件，就不需要基础模型也能直接推理。",
    },
    {
        "category": "lora_sft_dpo_replay",
        "prompt": "Qwen chat JSONL 训练样本为什么要有 system、user、assistant 三段？",
        "chosen": "system 定义助手角色和回答风格，user 是用户指令，assistant 是要学习的目标回答。训练时脚本会把对话套进 Qwen chat template，并主要对 assistant 部分计算标签，这样模型学习的是如何回答用户问题。",
        "rejected": "三段只是为了文件看起来整齐。训练时 system、user、assistant 没区别，模型会把所有文本都当答案背下来。",
    },
    {
        "category": "lora_sft_dpo_replay",
        "prompt": "为什么 DPO 数据要写 chosen/rejected，而不是只写一个标准答案？",
        "chosen": "DPO 优化的是偏好差异，需要同一个 prompt 下好回答和坏回答的对比。chosen 告诉模型靠近什么，rejected 告诉模型远离什么；只写标准答案更像 SFT，不能表达“这个近似但错误的回答不要学”。",
        "rejected": "DPO 其实和 SFT 一样，只要写一个标准答案就可以。rejected 字段可有可无，不影响训练目标。",
    },
    {
        "category": "data_pipeline",
        "prompt": "请解释自采集技术数据从采集、清洗、去重、筛选到 instruction-answer 转换的流程。",
        "chosen": "先采集来源并保留 source_id、标题、路径或 URL；再清洗网页噪声、导航栏、广告、重复空白和无关内容；接着去重和筛选，只保留 LoRA/SFT/DPO、显存和实验复盘相关内容；最后改写成明确的 instruction-answer，再转成 Qwen chat JSONL。",
        "rejected": "先把网页全部下载下来，然后直接丢进训练脚本。模型会自己学会哪些内容有用，所以不需要清洗、去重或改写成问答。",
    },
    {
        "category": "data_pipeline",
        "prompt": "为什么要保留 source_id、标题、路径或 URL 这些 source metadata？",
        "chosen": "metadata 让样本可追溯：知道内容从哪里来、为什么可信、后续出现 badcase 时能回到来源修订。它也让面试讲述更清楚，证明数据不是凭空拼出来的，而是有采集、清洗和筛选过程。",
        "rejected": "source metadata 对训练没有直接帮助，可以全部删掉。只要最后 JSONL 能读，来源信息不重要。",
    },
    {
        "category": "data_pipeline",
        "prompt": "自采集数据为什么要去重？",
        "chosen": "去重能避免同一段内容反复出现，导致模型过度记忆某种表达或让小数据分布被少数样本支配。尤其是 tiny 项目里，每条样本权重都很高，重复数据会放大偏差。",
        "rejected": "重复数据可以增加训练轮数的效果，所以越重复越好。去重会让数据量变少，不应该做。",
    },
    {
        "category": "data_pipeline",
        "prompt": "为什么不要把原始资料直接当 SFT 样本？",
        "chosen": "原始资料通常有网页噪声、段落跳跃和非问答结构。SFT 需要模型学习“收到什么指令，应该如何回答”，所以要把资料改写成明确 prompt 和目标 answer，并控制长度、主题和质量。",
        "rejected": "原始资料信息最多，直接训练最好。改写成 instruction-answer 会丢失细节，所以不需要转换。",
    },
    {
        "category": "data_pipeline",
        "prompt": "badcase 在这个项目的数据管线里起什么作用？",
        "chosen": "badcase 是下一轮数据建设的方向。Stage 4A 发现概念误解后，Stage 2B 补目标技术数据；Stage 2B.2/2B.3 发现剩余弱点后，再做 patch 和 replay。这样数据不是盲目扩张，而是被评测结果驱动。",
        "rejected": "badcase 只是失败案例，记录一下就行。后续数据管线应该尽量避开这些问题，免得模型继续学错。",
    },
    {
        "category": "dpo_vram_and_stage_gate",
        "prompt": "8GB 显存下做 DPO 有什么风险？应该怎样降低显存压力？",
        "chosen": "DPO 比 SFT 更吃显存，因为它要比较 chosen/rejected，并通常需要 reference policy 评分。8GB 下朴素双模型 DPO 可能 OOM 或落到共享内存导致很慢。第一版要用小模型、LoRA、batch_size=1、短 max_length、短 max_prompt_length、少量 pair、少 eval，并尽量共享 reference。",
        "rejected": "DPO 和 SFT 显存差不多。既然 LoRA SFT 能跑，就可以直接用大 batch、长序列和完整数据做 DPO。",
    },
    {
        "category": "dpo_vram_and_stage_gate",
        "prompt": "为什么 Stage 5 要拆成 5A/5B/5C/5D，而不是直接完整 DPO？",
        "chosen": "因为当前只有 8GB 显存，且 SFT patch 已证明小更新也可能导致回归。5A 先准备 tiny preference 数据，5B 验证显存和稳定性，5C 检查固定 prompt 行为，只有通过后 5D 才扩大。这是把风险拆小。",
        "rejected": "拆分没有必要。DPO 本来就是为了提高模型质量，所以应该一次性用完整数据训练，训练完再看结果。",
    },
    {
        "category": "dpo_vram_and_stage_gate",
        "prompt": "Stage 5B tiny DPO smoke test 需要记录哪些信息？",
        "chosen": "需要记录专用显存峰值、共享显存是否增长、系统内存增长、step 速度、是否 CUDA OOM、是否出现 Windows python.exe 原生崩溃，以及机器是否明显卡顿。这些决定后续能不能扩大 DPO。",
        "rejected": "只要训练命令能启动，就说明 Stage 5B 通过。显存、内存和 step 速度不用记录，失败时再说。",
    },
    {
        "category": "dpo_vram_and_stage_gate",
        "prompt": "Stage 5B 应该从哪个 SFT adapter 开始？为什么？",
        "chosen": "应该从 outputs/sft_lora_qwen05b_custom_v3_from_v1_patch 开始。v3 保住或改善 7/8 个固定 prompt；v4 没修好最后 badcase，v5 虽修好但旧能力回归，v6 仍不稳，所以 v3 是当前最安全的 DPO 起点。",
        "rejected": "应该从 v5 开始，因为它修好了最后一个 prompt。即使其他 prompt 回归，DPO 会自动修复这些问题。",
    },
    {
        "category": "dpo_vram_and_stage_gate",
        "prompt": "Stage 5B 的停止条件是什么？",
        "chosen": "如果出现 CUDA OOM、共享显存大量增长导致严重变慢、Windows 原生崩溃、step time 不可接受，或者输出 adapter 无法保存/加载，就应该停止，不继续扩大 DPO。tiny smoke test 的目标是先验证可行性。",
        "rejected": "DPO 训练一旦开始就应该跑完。即使共享显存暴涨或机器卡住，也说明模型正在努力训练，不需要中途停止。",
    },
    {
        "category": "dpo_vram_and_stage_gate",
        "prompt": "DPO 里的 reference policy 为什么会影响显存？",
        "chosen": "DPO 需要比较当前 policy 相对 reference policy 对 chosen/rejected 的偏好变化。朴素实现可能需要额外加载或评分 reference 行为，因此显存和计算会高于普通 SFT。8GB 下要优先考虑 PEFT/reference 共享和短序列。",
        "rejected": "reference policy 只是一个配置名，不会真正占用显存。DPO 的显存主要只取决于数据文件大小。",
    },
    {
        "category": "interview_narrative",
        "prompt": "如果面试官问你这个项目的数据管线，你会怎么讲？",
        "chosen": "我会先说 public 数据用来建立可复现基线，证明 LoRA SFT 的训练、保存、加载能跑通。然后 Stage 4A 暴露 LoRA/SFT/DPO 概念 badcase，于是 Stage 2B 做自采集技术数据：采集、清洗、去重、筛选、转 instruction-answer，再训练 custom-SFT 并三方对比。",
        "rejected": "我会说主要是下载一个公开数据集，然后直接训练模型。后面的自采集、清洗和 badcase 分析不是重点，可以不讲。",
    },
    {
        "category": "interview_narrative",
        "prompt": "如何用一句话概括 Stage 2B.3 到 Stage 5 的决策？",
        "chosen": "我没有为了修一个 prompt 就替换掉整体不稳的 adapter，而是把 v3 保留为当前最稳 SFT 起点，再把 DPO 拆成 tiny 数据、显存 smoke test 和行为回归检查。",
        "rejected": "Stage 2B.3 说明 SFT 不行，所以我直接进入完整 DPO，用偏好训练解决所有问题。",
    },
    {
        "category": "interview_narrative",
        "prompt": "为什么这个项目适合用来讲“可复现、可解释”的微调学习链路？",
        "chosen": "因为它从环境验证、base 推理、public-SFT 基线、自采集数据、custom-SFT、固定 prompt 对比，到 tiny DPO gate 都有明确产物和报告。每一步都能解释为什么做、做出了什么、下一步由哪个 badcase 驱动。",
        "rejected": "因为它训练了一个 adapter，所以天然可复现、可解释。只要最后模型能回答，就不需要保留中间报告。",
    },
    {
        "category": "interview_narrative",
        "prompt": "为什么 tiny DPO 成功后也不能马上宣布最终完成？",
        "chosen": "tiny DPO 只是验证 8GB 环境能否跑通，以及少量偏好数据是否改善目标 prompt。之后还要做 Stage 5C 固定 prompt 对比，确认没有旧能力回归；只有行为和显存都可接受，才考虑 Stage 5D 扩大数据。",
        "rejected": "tiny DPO 只要能保存 adapter，就说明最终完成。固定 prompt 对比和扩大前复盘没有必要。",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Stage 5A tiny DPO data.")
    parser.add_argument("--output_file", default="data/processed/dpo_tiny_train.jsonl")
    parser.add_argument("--report_file", default="reports/stage5a_dpo_tiny_data_report.md")
    return parser.parse_args()


def pair_for_training(pair: dict[str, str]) -> dict[str, str]:
    return {
        "prompt": pair["prompt"],
        "chosen": pair["chosen"],
        "rejected": pair["rejected"],
    }


def validate_pairs(pairs: list[dict[str, str]]) -> None:
    required = {"category", "prompt", "chosen", "rejected"}
    missing_messages: list[str] = []
    for idx, pair in enumerate(pairs, start=1):
        missing = required - set(pair)
        if missing:
            missing_messages.append(f"row {idx} missing {sorted(missing)}")
        for key in required & set(pair):
            if not pair[key].strip():
                missing_messages.append(f"row {idx} has empty {key}")
        if pair.get("chosen", "").strip() == pair.get("rejected", "").strip():
            missing_messages.append(f"row {idx} chosen equals rejected")

    if missing_messages:
        raise ValueError("; ".join(missing_messages))

    exact_prompt = "为什么不能只看 loss 判断一次 SFT 是否成功？"
    if not any(pair["prompt"] == exact_prompt for pair in pairs):
        raise ValueError("exact loss-vs-behavior prompt is missing")

    categories = {pair["category"] for pair in pairs}
    required_categories = {
        "loss_vs_behavior",
        "public_sft_motivation",
        "lora_sft_dpo_replay",
        "data_pipeline",
        "dpo_vram_and_stage_gate",
        "interview_narrative",
    }
    missing_categories = required_categories - categories
    if missing_categories:
        raise ValueError(f"missing categories: {sorted(missing_categories)}")


def length_stats(values: list[int]) -> dict[str, float | int]:
    return {
        "min": min(values),
        "avg": round(mean(values), 1),
        "max": max(values),
    }


def render_report(pairs: list[dict[str, str]], output_file: Path) -> str:
    category_counts = Counter(pair["category"] for pair in pairs)
    prompt_lengths = [len(pair["prompt"]) for pair in pairs]
    chosen_lengths = [len(pair["chosen"]) for pair in pairs]
    rejected_lengths = [len(pair["rejected"]) for pair in pairs]
    unique_prompts = len({pair["prompt"] for pair in pairs})

    category_lines = "\n".join(
        f"- `{category}`: {count}" for category, count in sorted(category_counts.items())
    )

    return f"""# Stage 5A Tiny DPO Data Report

Date: 2026-05-15

## Scope

Stage 5A is complete. This stage only prepares a tiny DPO preference dataset; it
does not run DPO training.

Start adapter for the next stage remains:

```text
{START_ADAPTER}
```

## Output

```text
{output_file.as_posix()}
```

Schema:

```json
{{"prompt": "...", "chosen": "...", "rejected": "..."}}
```

## Dataset Summary

- Rows: {len(pairs)}
- Unique prompts: {unique_prompts}
- Target range from plan: 20-50 preference pairs
- Exact loss-vs-behavior prompt included: yes
- Public-SFT motivation pairs included: yes
- LoRA/SFT/DPO replay pairs included: yes
- Data-pipeline and DPO-VRAM pairs included: yes
- Rejected answers are written as realistic badcase or near-miss answers, based
  on base/public/v4/v5/v6 failure patterns where possible.

Category counts:

{category_lines}

Character-length checks:

| Field | Min | Avg | Max |
|---|---:|---:|---:|
| prompt | {length_stats(prompt_lengths)["min"]} | {length_stats(prompt_lengths)["avg"]} | {length_stats(prompt_lengths)["max"]} |
| chosen | {length_stats(chosen_lengths)["min"]} | {length_stats(chosen_lengths)["avg"]} | {length_stats(chosen_lengths)["max"]} |
| rejected | {length_stats(rejected_lengths)["min"]} | {length_stats(rejected_lengths)["avg"]} | {length_stats(rejected_lengths)["max"]} |

## Design Notes

The tiny dataset intentionally mixes two kinds of pairs:

- Repair pairs for the final weak area: loss-vs-behavior and public-SFT
  motivation.
- Replay pairs for behaviors that v3 already handled well: LoRA/SFT/DPO
  concepts, data pipeline, DPO VRAM risk, and interview narrative.

This mirrors the Stage 2B.3 lesson: optimizing one weak prompt without replay
can regress older behavior. Stage 5B should therefore treat this data as a tiny
memory-and-behavior probe, not as a final preference corpus.

## Next Gate

Do not start full DPO from this report alone. The next step is Stage 5B only:
run a tiny DPO smoke test with `configs/dpo_qwen05b.yaml`, record dedicated GPU
memory, shared GPU memory, system RAM, step speed, and any OOM/native crash.
Then Stage 5C must compare fixed prompts before any larger DPO.
"""


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    output_file = Path(args.output_file)
    report_file = Path(args.report_file)

    validate_pairs(PAIRS)
    rows = [pair_for_training(pair) for pair in PAIRS]
    write_jsonl(output_file, rows)

    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(render_report(PAIRS, output_file), encoding="utf-8")

    print(f"Wrote {len(rows)} DPO preference pairs to {output_file}")
    print(f"Wrote report to {report_file}")


if __name__ == "__main__":
    main()
