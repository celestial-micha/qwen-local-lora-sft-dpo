"""Prepare a larger Stage 5G DPO preference dataset.

This is the first intentionally larger DPO probe after the tiny candidate loops.
It balances replay topics with the two stubborn gates so a larger/naive DPO run
does not only memorize prompt 4 and prompt 7.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


TOPICS: dict[str, dict[str, list[str]]] = {
    "lora_definition": {
        "prompts": [
            "机器学习里的 LoRA 是什么？请不要解释成无线通信。",
            "面试里如何用三点解释 LoRA 微调？",
            "为什么这个项目说 LoRA 是参数高效微调？",
            "解释 LoRA adapter 和冻结基础模型的关系。",
        ],
        "chosen": [
            "LoRA 是 Low-Rank Adaptation，是一种参数高效微调方法。它通常冻结基础模型大部分权重，只训练少量低秩 adapter 矩阵，所以不是无线通信里的 LoRa，也不是重新训练整套模型。",
            "可以说三点：第一，LoRA 是低秩适配；第二，大部分基础模型参数冻结，只更新少量 adapter；第三，它减少显存和训练成本，适合本地 GPU 学习。",
        ],
        "rejected": [
            "LoRA 主要是 Long Range 无线通信协议，本项目训练的是让模型理解远距离通信。",
            "LoRA 是重新训练全部基础模型参数，所以 adapter state 会固定在 prompt 上。",
            "LoRA 是 Local Reinforcement Algorithm，重点是让模型在网络安全任务里变得更稳。",
            "LoRA 是一个完整大模型架构，SFT 只是它的一个子层。",
        ],
    },
    "sft_lora_relation": {
        "prompts": [
            "SFT 和 LoRA 是什么关系？",
            "为什么说 LoRA SFT 不是两个互斥概念？",
            "用项目语言解释 supervised fine-tuning 和 LoRA。",
            "LoRA adapter 在 SFT 训练中承担什么角色？",
        ],
        "chosen": [
            "SFT 是 supervised fine-tuning，描述训练目标和 instruction-answer 数据形式。LoRA 是参数高效微调方法，描述如何少量更新参数；LoRA SFT 就是用 LoRA adapter 来执行 SFT。",
            "SFT 学目标回答，LoRA 控制更新方式。项目里基础模型大部分冻结，只训练 LoRA adapter，让有监督微调可以在本地显存内完成。",
        ],
        "rejected": [
            "LoRA 是 SFT 的子网络，所以两者不能同时使用。",
            "SFT 是安全指标，LoRA 是 DPO 后自动生成的数据保护对象。",
            "LoRA SFT 指先做 DPO 再让模型学会无线 LoRa 协议。",
            "SFT 是 Flipping Time，LoRA 是 Shortest Link，两者都是网络概念。",
        ],
    },
    "dpo_vs_sft": {
        "prompts": [
            "DPO 和 SFT 的训练信号有什么不同？",
            "为什么通常先做 SFT，再考虑 DPO？",
            "请解释 chosen/rejected preference pair 的作用。",
            "这个项目里 DPO 为什么不能替代 SFT 基础能力？",
        ],
        "chosen": [
            "SFT 用 instruction-answer 样本教模型模仿标准答案；DPO 用 chosen/rejected 偏好对，让模型更偏向 chosen、远离 rejected。通常先 SFT 建立基础回答能力，再用 DPO 做偏好优化。",
            "DPO 的信号不是单个标准答案，而是同一 prompt 下哪个回答更好。基础回答能力不稳时直接 DPO 容易放大混乱，所以本项目先做 SFT，再用固定 prompt gate 决定是否 DPO。",
        ],
        "rejected": [
            "DPO 是 Data Privacy Object，主要优化数据保护，不需要 chosen/rejected。",
            "SFT 和 DPO 都只看 loss，谁 loss 低谁就成功。",
            "DPO 可以在基础模型完全不会回答时直接替代 SFT。",
            "SFT 是安全框架指标，DPO 是目标完成比例，二者不用训练数据。",
        ],
    },
    "public_sft_motivation": {
        "prompts": [
            "为什么 public-SFT adapter 没修正 LoRA/SFT/DPO 概念误解，反而说明 Stage 2B 有必要？",
            "public-SFT 在这个项目里到底是什么定位？",
            "回答 public-SFT motivation 时，哪些说法要避免？",
            "为什么公开数据跑通不等于目标行为已经解决？",
        ],
        "chosen": [
            "public-SFT 是公开数据基线，用来证明训练、保存、加载和对比链路能跑通。它没有修正 LoRA/SFT/DPO 概念误解，说明公开通用 instruction 数据没有覆盖目标 badcase，所以 Stage 2B 需要自采集技术数据做定向修复。",
            "public-SFT 的价值是建立可复现基线和暴露 badcase，不是最终答案。正确复盘是：工程链路跑通，但目标概念仍未覆盖，因此进入 Stage 2B 数据修复；不要说从零建模，也不要说 public-SFT 已经补足概念。",
        ],
        "rejected": [
            "public-SFT adapter 用来补足 LoRA/SFT/DPO 概念误解，所以 Stage 2B 是从零重新建模型。",
            "public-SFT 失败说明要做三到六个月自采集，训练周期越长就越正确。",
            "public-SFT 不是公开数据基线，而是让 model 更健壮的双盲或三盲实验。",
            "公开数据跑通就说明目标行为已经解决，后面只需要扩大 DPO。",
        ],
    },
    "data_pipeline": {
        "prompts": [
            "自采集技术数据应该怎样清洗和转换？",
            "为什么要保留 source_id、标题、路径或 URL？",
            "从网页资料到 Qwen chat JSONL，中间要做哪些步骤？",
            "如何避免自采集数据变成一堆脏文本？",
        ],
        "chosen": [
            "先保留 source_id、标题、路径或 URL 等来源元数据，再清洗网页噪声、导航栏和广告，之后去重、筛选，最后改写为 instruction-answer 或 Qwen chat JSONL，并用固定 prompt 做回归检查。",
            "来源元数据让样本可追溯；清洗去掉无关噪声；去重筛掉重复段落；转换成问答或 chat JSONL 后，才能稳定用于 SFT/DPO 和后续复盘。",
        ],
        "rejected": [
            "主要做缺失值填充、归一化和标准化，像处理表格传感器数据一样即可。",
            "来源元数据不重要，网页路径和标题会干扰模型训练，应该全部删除。",
            "只要把网页全文复制进训练集，模型自然会学会项目流程。",
            "数据管线主要是 SQL 大数据处理，不需要 instruction-answer 转换。",
        ],
    },
    "dpo_vram": {
        "prompts": [
            "为什么 DPO 比 SFT 更容易吃显存？",
            "8GB 显存下跑 DPO 应该注意什么？",
            "chosen/rejected 和 reference policy 为什么会增加 DPO 成本？",
            "tiny DPO 没 OOM 能不能直接说明成功？",
        ],
        "chosen": [
            "DPO 要比较 chosen/rejected，并且通常需要 reference policy 评分，所以比普通 SFT 更吃显存。8GB 下应先用 LoRA、batch_size=1、短 max_length/max_prompt_length、少量 pair 和少量 eval 做 smoke test。",
            "没 OOM 只说明资源基本可跑，不说明行为成功。还要检查 adapter 是否可加载、固定 prompt 是否改善、旧能力是否回归，以及 DPO 输出是否真的更正确。",
        ],
        "rejected": [
            "DPO 每个 epoch 只增加 0.1GB 显存，batch_size=4GB 就够了。",
            "只要有共享显存，DPO 行为问题就会自动解决。",
            "tiny DPO 没 OOM 就代表 DPO 已经成功，不需要固定 prompt gate。",
            "DPO 的显存问题主要是内存泄漏，和 chosen/rejected 或 reference policy 无关。",
        ],
    },
    "loss_vs_behavior": {
        "prompts": [
            "为什么不能只看 loss 判断一次 SFT 是否成功？",
            "如果 loss 下降，为什么仍然要做固定 prompt 对比？",
            "面试官问不能只看 loss，你怎么回答？",
            "为什么 tiny DPO 的 train loss 不能单独作为验收？",
        ],
        "chosen": [
            "不能只看 loss。loss 是训练目标上的平均拟合信号，必要但不充分；一次 SFT 是否成功，还要看固定 prompt 行为、目标 badcase 是否修好、旧能力是否回归。这个项目里 public-SFT 能跑通但仍误解 LoRA/SFT/DPO，所以必须把 loss 曲线和固定 prompt 对比一起验收。",
            "loss 下降只能说明训练目标在平均意义上改善，不能证明目标 prompt 答对。验收要同时看固定 prompt、badcase review、public-SFT/custom-SFT/DPO 对比和旧能力回归。",
        ],
        "rejected": [
            "只要 loss 降低，就说明 SFT 已经成功，固定 prompt 只是展示用。",
            "DPO train loss 低就说明目标完成比例高，不需要再看输出行为。",
            "只要看代码、模型和 config 能说明 loss 下降，就不用看 badcase 回归。",
            "loss 下降后还要继续三到六个月数据补习，固定 prompt 不重要。",
        ],
    },
    "interview_narrative": {
        "prompts": [
            "面试里如何讲这个 LoRA SFT / DPO 项目？",
            "如何把 public-SFT、Stage 2B 和 custom-SFT 串成项目叙事？",
            "如何解释这个项目为什么没有直接扩大 DPO？",
            "请用复盘口吻总结这条训练链路。",
        ],
        "chosen": [
            "我会说先用公开数据跑通可复现基线，证明训练、保存、加载和对比链路；Stage 4A 发现 public-SFT 没修正目标概念 badcase；于是 Stage 2B 自采集、清洗、去重并转换技术 instruction-answer 数据，再训练 custom-SFT 并做三方对比。",
            "DPO 部分我不会说直接扩大训练，而是说先做 tiny smoke test 验证显存和 adapter 保存，再做固定 prompt gate。硬件可跑不代表行为通过，只有 badcase 修复且旧能力不回归，才考虑更大 DPO。",
        ],
        "rejected": [
            "这个项目主要是下载公开数据后直接训练，public-SFT 已经解决所有概念问题。",
            "面试里重点讲 SQL 大数据和 Tokenizers，不需要讲 Stage 4A badcase。",
            "因为 8GB 显存够用，所以 DPO 可以直接扩大，行为问题会自动消失。",
            "base adapter 和 public adapter 从安全开始，后面不需要自采集技术数据。",
        ],
    },
}


BASE_FILES = [
    Path("data/processed/dpo_tiny_train.jsonl"),
    Path("data/processed/dpo_tiny_v2_train.jsonl"),
    Path("data/processed/dpo_tiny_v3_train.jsonl"),
    Path("data/processed/dpo_candidate_train.jsonl"),
    Path("data/processed/dpo_candidate_v5_train.jsonl"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare larger Stage 5G DPO data.")
    parser.add_argument("--train_output", default="data/processed/dpo_larger_v6_train.jsonl")
    parser.add_argument("--eval_output", default="data/processed/dpo_larger_v6_eval.jsonl")
    parser.add_argument("--report_file", default="reports/stage5g_larger_dpo_v6_data_report.md")
    parser.add_argument("--max_train_rows", type=int, default=192)
    parser.add_argument("--max_eval_rows", type=int, default=24)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            rows.append(
                {
                    "prompt": str(row["prompt"]).strip(),
                    "chosen": str(row["chosen"]).strip(),
                    "rejected": str(row["rejected"]).strip(),
                    "source_type": str(row.get("source_type", f"base:{path.name}")),
                }
            )
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
    key = (item["prompt"], item["chosen"], item["rejected"])
    if key in seen:
        return
    if not item["prompt"] or not item["chosen"] or not item["rejected"]:
        raise ValueError(f"Empty field in row: {item}")
    if item["chosen"] == item["rejected"]:
        raise ValueError(f"Chosen equals rejected for prompt: {item['prompt']}")
    seen.add(key)
    rows.append(item)


def generated_rows(split: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for topic, data in TOPICS.items():
        for prompt_index, prompt in enumerate(data["prompts"]):
            for chosen_index, chosen in enumerate(data["chosen"]):
                for rejected_index, rejected in enumerate(data["rejected"]):
                    slot = (prompt_index + chosen_index + rejected_index) % 4
                    target_split = "eval" if slot == 0 else "train"
                    if target_split != split:
                        continue
                    rows.append(
                        {
                            "prompt": prompt,
                            "chosen": chosen,
                            "rejected": rejected,
                            "source_type": f"generated_{topic}",
                        }
                    )
    return rows


def trim_balanced(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if len(rows) <= limit:
        return rows
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        buckets.setdefault(str(row["source_type"]), []).append(row)
    selected: list[dict[str, Any]] = []
    keys = sorted(buckets)
    cursor = 0
    while len(selected) < limit and any(buckets.values()):
        key = keys[cursor % len(keys)]
        if buckets[key]:
            selected.append(buckets[key].pop(0))
        cursor += 1
    return selected


def validate(rows: list[dict[str, Any]], split: str) -> None:
    for index, row in enumerate(rows, start=1):
        for key in ["prompt", "chosen", "rejected"]:
            if not str(row[key]).strip():
                raise ValueError(f"{split} row {index} has empty {key}")
        if row["chosen"] == row["rejected"]:
            raise ValueError(f"{split} row {index} chosen equals rejected")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def stats(values: list[int]) -> str:
    return f"{min(values)} / {round(mean(values), 1)} / {max(values)}"


def render_report(train_rows: list[dict[str, Any]], eval_rows: list[dict[str, Any]], train_output: Path, eval_output: Path) -> str:
    counter = Counter(str(row["source_type"]) for row in train_rows)
    source_lines = ["| Source Type | Rows |", "|---|---:|"]
    for source_type, count in sorted(counter.items()):
        source_lines.append(f"| `{source_type}` | {count} |")
    prompt_lengths = [len(str(row["prompt"])) for row in train_rows]
    chosen_lengths = [len(str(row["chosen"])) for row in train_rows]
    rejected_lengths = [len(str(row["rejected"])) for row in train_rows]
    return f"""# Stage 5G Larger DPO v6 Data Report

Date: 2026-05-16

## Scope

Stage 5G prepares a larger preference dataset for a more naive DPO probe with a
separate reference model. It keeps replay coverage for all fixed-prompt topics
instead of only repeating the two stubborn prompts.

## Outputs

```text
{train_output.as_posix()}
{eval_output.as_posix()}
```

## Dataset Summary

- Train rows: {len(train_rows)}
- Eval rows: {len(eval_rows)}
- Train prompt length min/avg/max chars: {stats(prompt_lengths)}
- Train chosen length min/avg/max chars: {stats(chosen_lengths)}
- Train rejected length min/avg/max chars: {stats(rejected_lengths)}

## Train Sources

{chr(10).join(source_lines)}

## Design

- Reuses previous tiny DPO and candidate-derived preference rows.
- Adds balanced generated replay rows for eight topics:
  LoRA definition, SFT/LoRA relation, DPO/SFT distinction, public-SFT
  motivation, data pipeline, DPO VRAM risk, loss-vs-behavior, and interview
  narrative.
- Holds out a separate eval split so preference metrics are not only training
  set metrics.
"""


def main() -> None:
    args = parse_args()
    train_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []
    seen_train: set[tuple[str, str, str]] = set()
    seen_eval: set[tuple[str, str, str]] = set()

    for path in BASE_FILES:
        for row in read_jsonl(path):
            add_unique(train_rows, seen_train, row)
    for row in generated_rows("train"):
        add_unique(train_rows, seen_train, row)
    for row in generated_rows("eval"):
        add_unique(eval_rows, seen_eval, row)

    train_rows = trim_balanced(train_rows, args.max_train_rows)
    eval_rows = trim_balanced(eval_rows, args.max_eval_rows)
    validate(train_rows, "train")
    validate(eval_rows, "eval")

    train_output = Path(args.train_output)
    eval_output = Path(args.eval_output)
    report_file = Path(args.report_file)
    write_jsonl(train_output, train_rows)
    write_jsonl(eval_output, eval_rows)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(render_report(train_rows, eval_rows, train_output, eval_output), encoding="utf-8")
    print(f"Wrote {len(train_rows)} larger DPO train rows to {train_output}")
    print(f"Wrote {len(eval_rows)} larger DPO eval rows to {eval_output}")
    print(f"Wrote report to {report_file}")


if __name__ == "__main__":
    main()
