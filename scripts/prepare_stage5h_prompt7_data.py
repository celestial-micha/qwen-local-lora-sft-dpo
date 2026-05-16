"""Prepare Stage 5H prompt-7 repair data and an expanded behavior gate.

Stage 5H is a data/evaluation design step, not a training step. It starts from
the Stage 5G v6 preference distribution, adds stronger loss-vs-behavior pairs,
keeps replay rows for the other fixed prompts, and writes a held-out expanded
behavior prompt suite for future DPO v7 evaluation.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


BASE_TRAIN_FILE = Path("data/processed/dpo_larger_v6_train.jsonl")
BASE_EVAL_FILE = Path("data/processed/dpo_larger_v6_eval.jsonl")
ORIGINAL_PROMPT_FILE = Path("data/samples/custom_technical_prompts.jsonl")

FIXED_AREAS = [
    "LoRA definition",
    "SFT and LoRA relation",
    "DPO vs SFT",
    "Public-SFT motivation",
    "Data pipeline",
    "DPO VRAM risk",
    "Loss vs behavior",
    "Interview data pipeline",
]

PROMPT7_TRAIN_PROMPTS = [
    "为什么不能只看 loss 判断一次 SFT 是否成功？",
    "train loss 降了，为什么还不能说这次 SFT 成功？",
    "eval loss 更低时，为什么仍要看固定 prompt 行为？",
    "面试官问 loss 和真实输出的关系，你怎么解释？",
    "为什么平均训练目标不能替代 badcase review？",
    "public-SFT 训练跑通但概念仍错，这说明 loss 指标缺了什么？",
    "如果一个 adapter loss 很好看，但 LoRA/SFT/DPO 仍答错，怎么复盘？",
    "为什么固定 prompt gate 要和 train/eval loss 一起看？",
    "为什么不能用 DPO eval preference accuracy 直接替代行为验收？",
    "SFT patch 后 prompt 7 变好但旧 prompt 回归，loss 能看出来吗？",
    "如何解释 loss 是必要但不充分的训练信号？",
    "为什么小数据 SFT 低 loss 可能只是记住样本而不是学会行为？",
    "为什么目标概念问题要靠固定问题和 held-out 改写来验收？",
    "当 loss 下降但模型开始编造训练周期时，应该怎么判断？",
    "为什么 badcase 和 regression 比单个 loss 数字更适合作为项目验收？",
    "为什么 Stage 5G eval accuracy 1.0 仍然不能宣布 DPO 成功？",
    "一次 SFT 是否成功，除了 loss 还要检查哪些行为证据？",
    "为什么公开数据 baseline 的 loss 不能证明 LoRA/SFT/DPO 概念学对了？",
    "如何向初学者解释 loss 曲线和固定 prompt 对比的分工？",
    "为什么 prompt 7 不能只靠重复原句训练来修？",
    "loss 指标、固定 prompt、badcase review 三者各自回答什么问题？",
    "为什么要看旧能力回归，而不是只看新 prompt 有没有答对？",
    "如果 train loss 下降、eval loss 也下降，但输出仍跑题，下一步该查什么？",
    "为什么 behavior gate 是 SFT/DPO 后训练里的最后验收，而不只是附加展示？",
]

PROMPT7_EVAL_PROMPTS = [
    "如果 SFT 的 eval loss 看起来不错，但固定问题仍答错，你会怎么解释？",
    "为什么说 loss 是平均信号，而不是目标行为的充分证明？",
    "如何判断一次 LoRA SFT 是真的学会了概念，而不是只把 loss 压低？",
    "为什么要把 public-SFT 的失败案例放进 SFT/DPO 验收里？",
    "DPO v6 偏好 eval 已经 1.0，为什么 prompt 7 失败仍然重要？",
    "请区分 train loss、eval loss、固定 prompt gate 在项目复盘中的作用。",
    "如果新数据修好了 loss-vs-behavior，但 LoRA 定义退化了，算成功吗？",
    "为什么 held-out prompt 改写比只测原始 prompt 更可靠？",
    "请用项目例子说明低 loss 与行为正确之间的差距。",
    "如果模型回答不能只看 loss，但没提 badcase 和旧能力回归，问题在哪里？",
    "为什么后训练验收要看输出样例，而不能只看 Trainer 里的指标？",
    "如何用一句话总结 loss、偏好指标和行为 gate 的关系？",
]

PROMPT7_CHOSEN = [
    "不能只看 loss。loss 是训练目标上的平均拟合信号，必要但不充分；一次 SFT 是否成功，还要看固定 prompt 行为、目标 badcase 是否修好、旧能力是否回归。这个项目里 public-SFT 能训练完成但仍误解 LoRA/SFT/DPO，所以必须把 loss 曲线和行为 gate 一起验收。",
    "loss 下降只能说明模型在当前训练目标上平均更贴近标签，不保证目标概念已经答对。验收时要同时看 train/eval loss、固定 prompt 对比、badcase review、public-SFT 到 custom-SFT 的行为变化，以及旧 prompt 是否回归。",
    "loss 是优化过程的信号，不是最终用户可见行为的充分证明。小数据补丁可能压低 loss，却让旧能力退化；DPO preference accuracy 也可能很好看，但固定 prompt 仍失败。因此要用 held-out prompt 和结构化行为评分做最后 gate。",
    "正确复盘应该分层：loss 回答训练有没有在平均目标上收敛；固定 prompt 回答目标行为是否正确；badcase review 回答具体错误是否修好；regression check 回答旧能力是否保住。缺一层都不能宣布 SFT 成功。",
]

PROMPT7_REJECTED = [
    (
        "loss_only",
        "只要 train loss 降低，就说明 SFT 已经成功。固定 prompt 只是展示用，不需要作为验收标准。",
    ),
    (
        "eval_loss_only",
        "eval loss 比 train loss 更客观，所以只要 eval loss 好看，就可以不用再看具体输出行为。",
    ),
    (
        "preference_metric_only",
        "DPO eval preference accuracy 到 1.0 就说明模型已经完全成功，prompt 7 偶尔失败不重要。",
    ),
    (
        "missing_regression",
        "只要新的 loss-vs-behavior 问题答对，就算成功；LoRA、SFT、DPO 等旧 prompt 回归也可以忽略。",
    ),
    (
        "missing_badcase",
        "loss 下降后只需要看总体指标，不需要检查 badcase，因为坏例子通常只是个别噪声。",
    ),
    (
        "public_sft_overclaim",
        "public-SFT 已经证明概念都修好了，所以后面 loss 降低就等于目标行为也变好了。",
    ),
    (
        "loss_useless",
        "loss 完全没有意义，训练是否成功只能凭人工主观感觉判断，不需要看 train/eval 指标。",
    ),
    (
        "invented_duration",
        "loss 下降后还要继续三到六个月数据补习，固定 prompt 和 badcase review 都不重要。",
    ),
]

REPLAY_ROWS = [
    {
        "prompt_area": "LoRA definition",
        "prompt": "用一句话说明机器学习里的 LoRA，顺便排除无线通信误解。",
        "chosen": "机器学习里的 LoRA 是 Low-Rank Adaptation，一种参数高效微调方法：冻结基础模型大部分权重，只训练少量低秩 adapter，不是无线通信里的 LoRa。",
        "rejected": "LoRA 是 Long Range 无线通信协议，本项目主要训练远距离通信知识。",
    },
    {
        "prompt_area": "LoRA definition",
        "prompt": "为什么 LoRA 适合本地 8GB 显存学习微调？",
        "chosen": "因为 LoRA 只更新少量 adapter 参数，基础模型大部分冻结，训练参数和显存压力都比全量微调小，更适合本地 8GB GPU 做学习实验。",
        "rejected": "因为 LoRA 会重新训练全部基础模型参数，所以 8GB 显存可以直接训练完整模型。",
    },
    {
        "prompt_area": "LoRA definition",
        "prompt": "LoRA adapter 和基础模型权重是什么关系？",
        "chosen": "基础模型权重大部分保持冻结，LoRA adapter 是附加在部分线性层上的小规模可训练参数，保存时通常只保存 adapter。",
        "rejected": "LoRA adapter 是一个新的基础模型，训练后会覆盖所有原始权重。",
    },
    {
        "prompt_area": "SFT and LoRA relation",
        "prompt": "SFT 和 LoRA 是同一类东西吗？",
        "chosen": "不是。SFT 是有监督微调的训练目标和数据形式，LoRA 是参数高效更新方法；LoRA SFT 是用 LoRA adapter 来执行 SFT。",
        "rejected": "是同一类东西，LoRA 是 SFT 的子网络，所以二者不能一起使用。",
    },
    {
        "prompt_area": "SFT and LoRA relation",
        "prompt": "为什么项目里说训练的是 LoRA SFT？",
        "chosen": "因为训练目标是 SFT，用 instruction-answer 样本学习回答；实现方式是 LoRA，只更新少量 adapter 参数。",
        "rejected": "因为 LoRA SFT 指先做 DPO，再让模型学习无线 LoRa 协议。",
    },
    {
        "prompt_area": "SFT and LoRA relation",
        "prompt": "用数据和参数更新两个角度区分 SFT 与 LoRA。",
        "chosen": "SFT 关注数据形式和训练目标，通常是 instruction-answer；LoRA 关注参数更新方式，只训练少量低秩 adapter。",
        "rejected": "SFT 关注网络路由，LoRA 关注安全框架，二者都不是训练方法。",
    },
    {
        "prompt_area": "DPO vs SFT",
        "prompt": "DPO 的 chosen/rejected 对和 SFT 的标准答案有什么区别？",
        "chosen": "SFT 用标准答案让模型模仿；DPO 用同一 prompt 下的 chosen/rejected 偏好对，让模型更偏向 chosen、远离 rejected。",
        "rejected": "DPO 是数据保护对象，不需要 chosen/rejected，只需要看 loss。",
    },
    {
        "prompt_area": "DPO vs SFT",
        "prompt": "为什么基础回答能力不稳时不能直接 DPO？",
        "chosen": "基础能力不稳时，DPO 容易放大错误偏好或让旧能力回归，所以通常先 SFT 建立可用回答，再用固定 prompt gate 检查能否进入 DPO。",
        "rejected": "DPO 可以完全替代 SFT，基础模型不会回答也没关系。",
    },
    {
        "prompt_area": "DPO vs SFT",
        "prompt": "这个项目为什么先做 tiny DPO smoke test？",
        "chosen": "先验证显存、保存、加载和基本训练路径，再用固定 prompt 行为 gate 判断质量；硬件可跑不代表 DPO 行为已经成功。",
        "rejected": "tiny DPO 没有 OOM 就等于 DPO 成功，不需要行为评测。",
    },
    {
        "prompt_area": "Public-SFT motivation",
        "prompt": "public-SFT 在这个项目里证明了什么，又没证明什么？",
        "chosen": "它证明公开数据能跑通训练、保存、加载和对比链路；但没有证明 LoRA/SFT/DPO 目标概念已修正，这正是 Stage 2B 自采集技术数据的动机。",
        "rejected": "它证明所有目标概念都修好了，所以 Stage 2B 是从零重新建模。",
    },
    {
        "prompt_area": "Public-SFT motivation",
        "prompt": "为什么 public-SFT 失败不是项目失败？",
        "chosen": "因为 public-SFT 是基线和诊断步骤。它暴露目标 badcase，说明通用数据覆盖不足，从而指导 Stage 2B 做定向技术数据修复。",
        "rejected": "因为 public-SFT 失败说明要做三到六个月数据收集，越久越成功。",
    },
    {
        "prompt_area": "Public-SFT motivation",
        "prompt": "回答 public-SFT motivation 时要避开什么说法？",
        "chosen": "要避免说从零建模、public-SFT 已补足概念、训练周期越长越好；应强调它是可复现基线和 badcase 发现工具。",
        "rejected": "应该说 public-SFT adapter 用来补足概念，Stage 2B 是从零训练完整模型。",
    },
    {
        "prompt_area": "Data pipeline",
        "prompt": "自采集技术数据为什么要保留 source_id 和标题？",
        "chosen": "source_id、标题和路径让样本可追溯，便于复盘清洗、去重、筛选和 instruction-answer 转换过程。",
        "rejected": "来源信息会干扰模型，应该全部删除，只保留网页全文。",
    },
    {
        "prompt_area": "Data pipeline",
        "prompt": "从网页资料到 Qwen chat JSONL 要做哪些步骤？",
        "chosen": "先采集并保留元数据，再清洗网页噪声、去重、筛选，最后改写成 instruction-answer 或 Qwen chat JSONL，并用固定 prompt 回归检查。",
        "rejected": "只要做缺失值填充、标准化和归一化，像处理传感器表格一样即可。",
    },
    {
        "prompt_area": "Data pipeline",
        "prompt": "为什么不能把网页全文直接塞进训练集？",
        "chosen": "网页全文常有导航、广告、重复和无关段落，不清洗转换会制造噪声；需要筛选并改写成稳定的训练样本。",
        "rejected": "网页全文越多越好，模型会自动忽略所有噪声。",
    },
    {
        "prompt_area": "DPO VRAM risk",
        "prompt": "DPO 为什么比 SFT 更吃显存？",
        "chosen": "DPO 通常同时处理 chosen/rejected，并要和 reference policy 对比，因此比普通 SFT 更吃显存；8GB 下要短序列、小 batch、少 eval 先试。",
        "rejected": "DPO 显存问题主要是内存泄漏，和 chosen/rejected 或 reference 无关。",
    },
    {
        "prompt_area": "DPO VRAM risk",
        "prompt": "8GB 显存下 DPO 的第一步应该怎么做？",
        "chosen": "先用 LoRA、batch_size=1、短 max_length/max_prompt_length、小 preference set 和少量 eval 做 smoke test，再看行为 gate。",
        "rejected": "直接扩大数据和 batch，因为 tiny DPO 没 OOM 就代表质量过关。",
    },
    {
        "prompt_area": "DPO VRAM risk",
        "prompt": "DPO 训练跑通后还要检查什么？",
        "chosen": "要检查 adapter 是否可加载、固定 prompt 是否改善、旧能力是否回归，以及偏好指标和实际输出是否一致。",
        "rejected": "只要 GPU 没 OOM，就不用再看输出。",
    },
    {
        "prompt_area": "Interview data pipeline",
        "prompt": "面试里如何讲 public-SFT 到 custom-SFT 的闭环？",
        "chosen": "先用公开数据跑通可复现基线；Stage 4A 发现目标概念没修正；再用 Stage 2B 自采集、清洗、去重并转 instruction-answer，训练 custom-SFT 后三方对比。",
        "rejected": "主要讲下载公开数据直接训练，后面不需要 badcase 驱动的数据修复。",
    },
    {
        "prompt_area": "Interview data pipeline",
        "prompt": "如何解释为什么没有直接扩大 DPO？",
        "chosen": "因为硬件可跑不等于行为通过。项目先做 tiny smoke test，再用固定 prompt gate 检查 badcase 和旧能力，未通过前不直接扩大 DPO。",
        "rejected": "因为显存足够，所以扩大 DPO 后行为问题会自动消失。",
    },
    {
        "prompt_area": "Interview data pipeline",
        "prompt": "请用复盘口吻总结这条训练链路。",
        "chosen": "公开数据验证工程链路，自采集技术数据修目标 badcase，custom-SFT 做行为提升，DPO 先做显存 smoke test 和固定 prompt gate，再决定是否扩大。",
        "rejected": "这条链路主要是换模型和调参数，不需要数据清洗、对比和行为 gate。",
    },
]

EXPANDED_PROMPT7_PROMPTS = [
    "如果 SFT 的 eval loss 看起来不错，但固定问题仍答错，你会怎么解释？",
    "为什么说 loss 是平均信号，而不是目标行为的充分证明？",
    "如何判断一次 LoRA SFT 是真的学会了概念，而不是只把 loss 压低？",
    "为什么要把 public-SFT 的失败案例放进 SFT/DPO 验收里？",
    "DPO v6 偏好 eval 已经 1.0，为什么 prompt 7 失败仍然重要？",
    "请区分 train loss、eval loss、固定 prompt gate 在项目复盘中的作用。",
    "如果新数据修好了 loss-vs-behavior，但 LoRA 定义退化了，算成功吗？",
    "为什么 held-out prompt 改写比只测原始 prompt 更可靠？",
    "请用项目例子说明低 loss 与行为正确之间的差距。",
    "如果模型回答不能只看 loss，但没提 badcase 和旧能力回归，问题在哪里？",
    "为什么后训练验收要看输出样例，而不能只看 Trainer 里的指标？",
    "如何用一句话总结 loss、偏好指标和行为 gate 的关系？",
]

EXPANDED_REPLAY_PROMPTS = [
    {
        "prompt_id": "replay_public_sft_motivation_01",
        "prompt_area": "Public-SFT motivation",
        "prompt": "public-SFT 的失败为什么是数据工程线索，而不是训练链路失败？",
    },
    {
        "prompt_id": "replay_dpo_vram_01",
        "prompt_area": "DPO VRAM risk",
        "prompt": "tiny DPO 能跑通后，为什么还不能跳过行为 gate？",
    },
    {
        "prompt_id": "replay_data_pipeline_01",
        "prompt_area": "Data pipeline",
        "prompt": "自采集技术数据从原文到 instruction-answer，中间最容易出什么问题？",
    },
    {
        "prompt_id": "replay_interview_narrative_01",
        "prompt_area": "Interview data pipeline",
        "prompt": "面试中怎样把 badcase、数据修复和固定 prompt gate 串起来？",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Stage 5H prompt-7 data and eval suite.")
    parser.add_argument("--base_train_file", default=str(BASE_TRAIN_FILE))
    parser.add_argument("--base_eval_file", default=str(BASE_EVAL_FILE))
    parser.add_argument("--original_prompt_file", default=str(ORIGINAL_PROMPT_FILE))
    parser.add_argument("--train_output", default="data/processed/dpo_stage5h_prompt7_train.jsonl")
    parser.add_argument("--eval_output", default="data/processed/dpo_stage5h_prompt7_eval.jsonl")
    parser.add_argument(
        "--expanded_prompt_output",
        default="data/samples/custom_technical_prompts_expanded_stage5h.jsonl",
    )
    parser.add_argument("--report_file", default="reports/stage5h_prompt7_data_and_eval_design.md")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path}:{line_no}") from exc
            rows.append(row)
    if not rows:
        raise ValueError(f"No rows loaded from {path}")
    return rows


def add_unique(rows: list[dict[str, Any]], seen: set[tuple[str, str, str]], row: dict[str, Any]) -> None:
    item = {
        "prompt": str(row["prompt"]).strip(),
        "chosen": str(row["chosen"]).strip(),
        "rejected": str(row["rejected"]).strip(),
        "source_type": str(row.get("source_type", "unknown")),
    }
    if "prompt_area" in row:
        item["prompt_area"] = str(row["prompt_area"]).strip()
    key = (item["prompt"], item["chosen"], item["rejected"])
    if key in seen:
        return
    if not item["prompt"] or not item["chosen"] or not item["rejected"]:
        raise ValueError(f"Empty prompt/chosen/rejected in row: {row}")
    if item["chosen"] == item["rejected"]:
        raise ValueError(f"chosen equals rejected for prompt: {item['prompt']}")
    seen.add(key)
    rows.append(item)


def prompt7_rows(prompts: list[str], pairs_per_prompt: int, split: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for prompt_index, prompt in enumerate(prompts):
        for pair_index in range(pairs_per_prompt):
            chosen = PROMPT7_CHOSEN[(prompt_index + pair_index) % len(PROMPT7_CHOSEN)]
            rejected_type, rejected = PROMPT7_REJECTED[(prompt_index * pairs_per_prompt + pair_index) % len(PROMPT7_REJECTED)]
            rows.append(
                {
                    "prompt": prompt,
                    "chosen": chosen,
                    "rejected": rejected,
                    "source_type": f"stage5h_prompt7_{split}_{rejected_type}",
                    "prompt_area": "Loss vs behavior",
                }
            )
    return rows


def replay_rows(split: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, row in enumerate(REPLAY_ROWS):
        target_split = "eval" if index % 3 == 0 else "train"
        if target_split != split:
            continue
        rows.append(
            {
                "prompt": row["prompt"],
                "chosen": row["chosen"],
                "rejected": row["rejected"],
                "source_type": f"stage5h_replay_{row['prompt_area'].lower().replace(' ', '_')}",
                "prompt_area": row["prompt_area"],
            }
        )
    return rows


def load_base_rows(path: Path, prefix: str) -> list[dict[str, Any]]:
    loaded: list[dict[str, Any]] = []
    for row in read_jsonl(path):
        item = dict(row)
        item["source_type"] = f"{prefix}:{item.get('source_type', path.name)}"
        loaded.append(item)
    return loaded


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_expanded_prompt_suite(original_prompt_file: Path) -> list[dict[str, Any]]:
    original_rows = read_jsonl(original_prompt_file)
    if len(original_rows) != 8:
        raise ValueError(f"Expected 8 original prompts in {original_prompt_file}, got {len(original_rows)}")

    suite: list[dict[str, Any]] = []
    for index, row in enumerate(original_rows, start=1):
        suite.append(
            {
                "prompt_id": f"fixed_{index:02d}",
                "prompt_area": FIXED_AREAS[index - 1],
                "source": "original_fixed_prompt",
                "prompt": str(row["prompt"]).strip(),
            }
        )

    for index, prompt in enumerate(EXPANDED_PROMPT7_PROMPTS, start=1):
        suite.append(
            {
                "prompt_id": f"stage5h_p7_holdout_{index:02d}",
                "prompt_area": "Loss vs behavior",
                "source": "stage5h_prompt7_holdout",
                "must_cover": [
                    "loss average signal",
                    "not sufficient",
                    "fixed prompt behavior",
                    "badcase/regression",
                    "public-SFT or DPO v6 example",
                ],
                "prompt": prompt,
            }
        )

    for row in EXPANDED_REPLAY_PROMPTS:
        suite.append({**row, "source": "stage5h_replay_holdout"})

    return suite


def validate_dpo_rows(rows: list[dict[str, Any]], split: str) -> None:
    for index, row in enumerate(rows, start=1):
        for key in ["prompt", "chosen", "rejected"]:
            if not str(row[key]).strip():
                raise ValueError(f"{split} row {index} has empty {key}")
        if row["chosen"] == row["rejected"]:
            raise ValueError(f"{split} row {index} chosen equals rejected")


def stats(values: list[int]) -> str:
    return f"{min(values)} / {round(mean(values), 1)} / {max(values)}"


def source_table(rows: list[dict[str, Any]]) -> str:
    counter = Counter(str(row.get("source_type", "unknown")) for row in rows)
    lines = ["| Source Type | Rows |", "|---|---:|"]
    for source_type, count in sorted(counter.items()):
        lines.append(f"| `{source_type}` | {count} |")
    return "\n".join(lines)


def render_report(
    train_rows: list[dict[str, Any]],
    eval_rows: list[dict[str, Any]],
    expanded_rows: list[dict[str, Any]],
    train_output: Path,
    eval_output: Path,
    expanded_prompt_output: Path,
) -> str:
    prompt_lengths = [len(str(row["prompt"])) for row in train_rows]
    chosen_lengths = [len(str(row["chosen"])) for row in train_rows]
    rejected_lengths = [len(str(row["rejected"])) for row in train_rows]
    prompt7_train = sum(1 for row in train_rows if row.get("prompt_area") == "Loss vs behavior")
    prompt7_eval = sum(1 for row in eval_rows if row.get("prompt_area") == "Loss vs behavior")
    expanded_loss_total = sum(1 for row in expanded_rows if row["prompt_area"] == "Loss vs behavior")
    expanded_prompt7_holdout = sum(1 for row in expanded_rows if row.get("source") == "stage5h_prompt7_holdout")
    expanded_replay_holdout = sum(1 for row in expanded_rows if row.get("source") == "stage5h_replay_holdout")
    return f"""# Stage 5H Prompt-7 Data And Expanded Eval Design

Date: 2026-05-16

## Scope

Stage 5H does not run DPO training. It prepares stronger loss-vs-behavior
preference/eval data and a larger behavior gate so the next run cannot pass by
only memorizing the original prompt 7 wording.

## Outputs

```text
{train_output.as_posix()}
{eval_output.as_posix()}
{expanded_prompt_output.as_posix()}
```

## Dataset Summary

- Train rows: {len(train_rows)}
- Eval rows: {len(eval_rows)}
- Prompt-7 train rows: {prompt7_train}
- Prompt-7 eval rows: {prompt7_eval}
- Train prompt length min/avg/max chars: {stats(prompt_lengths)}
- Train chosen length min/avg/max chars: {stats(chosen_lengths)}
- Train rejected length min/avg/max chars: {stats(rejected_lengths)}

## Train Sources

{source_table(train_rows)}

## Expanded Behavior Gate

- Expanded prompts: {len(expanded_rows)}
- Original fixed prompts preserved: 8 / 8
- Loss-vs-behavior prompts total: {expanded_loss_total}
- Stage 5H loss-vs-behavior holdouts: {expanded_prompt7_holdout}
- Additional replay holdouts: {expanded_replay_holdout}

Recommended future gate rule:

1. Keep the original 8 fixed prompts as regression tests.
2. Require every loss-vs-behavior held-out prompt to include loss as an average
   training objective signal, "necessary but not sufficient", fixed-prompt
   behavior, badcase/regression review, and a project example such as
   public-SFT or DPO v6.
3. Reject runs that pass prompt 7 but regress old LoRA/SFT/DPO, data-pipeline,
   DPO-VRAM, public-SFT motivation, or interview-narrative prompts.
4. Treat preference eval accuracy as a useful metric, not the final behavior
   gate.

## Design Notes

- The base distribution is Stage 5G v6, because it is the strongest DPO
  candidate so far and already contains broad replay coverage.
- Stage 5H adds varied prompt-7 phrasings around train loss, eval loss,
  preference metrics, fixed prompts, badcase review, regression, public-SFT,
  and DPO v6.
- Rejected answers are near-misses: they often sound plausible but omit one
  required concept or over-trust a metric.
- Extra replay rows are kept so the prompt-7 repair signal does not overwrite
  the seven previously stable areas.

## Future Commands

Generate data and the expanded prompt suite:

```powershell
python scripts\\prepare_stage5h_prompt7_data.py
```

After a future DPO v7 run exists, compare it on the expanded suite:

```powershell
python scripts\\compare_four_outputs.py `
  --prompt_file data\\samples\\custom_technical_prompts_expanded_stage5h.jsonl `
  --dpo_adapter_path outputs\\dpo_lora_qwen05b_v7_stage5h `
  --output_file reports\\compare_outputs_four_way_dpo_v7_stage5h_expanded.jsonl `
  --max_new_tokens 160 `
  --temperature 0 `
  --local_files_only

python scripts\\score_expanded_behavior_outputs.py `
  --input_files reports\\compare_outputs_four_way_dpo_v7_stage5h_expanded.jsonl
```
"""


def main() -> None:
    args = parse_args()
    train_output = Path(args.train_output)
    eval_output = Path(args.eval_output)
    expanded_prompt_output = Path(args.expanded_prompt_output)
    report_file = Path(args.report_file)

    train_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []
    seen_train: set[tuple[str, str, str]] = set()
    seen_eval: set[tuple[str, str, str]] = set()

    for row in load_base_rows(Path(args.base_train_file), "stage5g_train"):
        add_unique(train_rows, seen_train, row)
    for row in prompt7_rows(PROMPT7_TRAIN_PROMPTS, pairs_per_prompt=3, split="train"):
        add_unique(train_rows, seen_train, row)
    for row in replay_rows("train"):
        add_unique(train_rows, seen_train, row)

    for row in load_base_rows(Path(args.base_eval_file), "stage5g_eval"):
        add_unique(eval_rows, seen_eval, row)
    for row in prompt7_rows(PROMPT7_EVAL_PROMPTS, pairs_per_prompt=2, split="eval"):
        add_unique(eval_rows, seen_eval, row)
    for row in replay_rows("eval"):
        add_unique(eval_rows, seen_eval, row)

    expanded_rows = build_expanded_prompt_suite(Path(args.original_prompt_file))
    validate_dpo_rows(train_rows, "train")
    validate_dpo_rows(eval_rows, "eval")

    write_jsonl(train_output, train_rows)
    write_jsonl(eval_output, eval_rows)
    write_jsonl(expanded_prompt_output, expanded_rows)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(
        render_report(train_rows, eval_rows, expanded_rows, train_output, eval_output, expanded_prompt_output),
        encoding="utf-8",
    )

    print(f"Wrote {len(train_rows)} Stage 5H train rows to {train_output}")
    print(f"Wrote {len(eval_rows)} Stage 5H eval rows to {eval_output}")
    print(f"Wrote {len(expanded_rows)} expanded behavior prompts to {expanded_prompt_output}")
    print(f"Wrote report to {report_file}")


if __name__ == "__main__":
    main()
