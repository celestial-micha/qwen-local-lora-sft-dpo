"""Prepare Stage 5A.2 revised tiny DPO preference data.

This keeps the original Stage 5A data intact and creates a v2 file with focused
repairs for the two Stage 5C failures:

- public-SFT motivation drift
- loss-vs-behavior still not being explained cleanly
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


FOCUSED_REVISION_PAIRS: list[dict[str, str]] = [
    {
        "category": "public_sft_motivation_v2",
        "prompt": "为什么 public-SFT adapter 没修正 LoRA/SFT/DPO 概念误解，反而说明 Stage 2B 有必要？",
        "chosen": "因为 public-SFT 只证明通用 instruction 数据能把 LoRA SFT 链路跑通，不代表它覆盖了本项目关心的 LoRA/SFT/DPO 技术概念。Stage 4A 发现概念仍错，所以 Stage 2B 要补自采集技术数据，定向覆盖这些 badcase。",
        "rejected": "因为 Stage 2B 是从零开始建模型，所以 public-SFT 没修好概念就说明要做三到六个月的自采集资料工作。",
    },
    {
        "category": "public_sft_motivation_v2",
        "prompt": "为什么 public-SFT adapter 没修正 LoRA/SFT/DPO 概念误解，反而说明 Stage 2B 有必要？",
        "chosen": "这说明问题不在训练链路是否能跑，而在数据是否覆盖目标概念。public-SFT 作为基线有价值：它证明工程链路正常，同时暴露出通用数据没有教会 LoRA/SFT/DPO，因此需要 Stage 2B 的定向技术数据。",
        "rejected": "这说明 public-SFT 已经失败，应该抛弃 SFT，直接换成完整 DPO 或更大模型，不需要继续做数据管线。",
    },
    {
        "category": "public_sft_motivation_v2",
        "prompt": "public-SFT 没修好目标概念时，下一步为什么是补数据而不是立刻扩大训练？",
        "chosen": "因为 Stage 4A 的失败是目标概念覆盖不足，不是训练命令没跑通。盲目扩大训练会继续学习同一类通用数据，未必修正 LoRA/SFT/DPO 误解；更合理的是补充定向技术数据并重新做固定 prompt 对比。",
        "rejected": "只要训练步数更多，public-SFT 自然会学会所有技术概念。数据覆盖不是主要问题。",
    },
    {
        "category": "public_sft_motivation_v2",
        "prompt": "怎样一句话概括 public-SFT 和 Stage 2B 的关系？",
        "chosen": "public-SFT 是工程基线和问题发现器，Stage 2B 是针对固定 badcase 的数据修复步骤；两者是前后衔接，不是互相否定。",
        "rejected": "public-SFT 是失败实验，Stage 2B 是重新从零训练一个模型，所以两者没有继承关系。",
    },
    {
        "category": "public_sft_motivation_v2",
        "prompt": "回答 public-SFT motivation 时，哪些说法应该避免？",
        "chosen": "应该避免说 Stage 2B 是从零建模型、避免编造三到六个月的周期、避免把 public-SFT 说成毫无价值。正确说法是：public-SFT 跑通工程链路并暴露数据覆盖不足，因此需要定向技术数据。",
        "rejected": "可以说 Stage 2B 要从零开始建模型，也可以估计要三到六个月，只要大方向是继续收集数据就行。",
    },
    {
        "category": "public_sft_motivation_v2",
        "prompt": "Stage 4A 的 public-SFT 结果为什么是一个有用的失败？",
        "chosen": "它有用是因为它把问题定位清楚了：训练、保存、加载都能跑，失败集中在目标技术概念没有被通用数据覆盖。这让 Stage 2B 的数据建设有明确方向，而不是盲目换模型或堆参数。",
        "rejected": "它有用是因为失败越多越能证明模型很难训练，所以后面应该尽量少做评测，多训练几个 epoch。",
    },
    {
        "category": "loss_behavior_v2",
        "prompt": "为什么不能只看 loss 判断一次 SFT 是否成功？",
        "chosen": "不能只看 loss，因为 loss 只是训练/验证样本上的平均拟合信号，是必要参考但不充分。SFT 是否成功还要看固定 prompt 行为、目标概念是否正确、badcase 是否减少，以及旧能力有没有回归。本项目里 public-SFT 能训练完成但仍误解 LoRA/SFT/DPO，说明必须做行为评测。",
        "rejected": "只要 loss 降低，SFT 就成功。固定 prompt 只是主观观察，不应该影响结论。",
    },
    {
        "category": "loss_behavior_v2",
        "prompt": "为什么不能只看 loss 判断一次 SFT 是否成功？",
        "chosen": "loss 可以告诉我们优化过程有没有异常，但不能保证模型在目标问题上答对。这个项目的判断标准是 loss 加固定 prompt 回归测试：既要看训练指标，也要看 LoRA/SFT/DPO、数据管线和 DPO 显存这些目标 prompt 是否更正确、更稳定。",
        "rejected": "loss 是最客观指标，所以只要 loss 好看，即使目标 prompt 答错，也可以认为训练成功。",
    },
    {
        "category": "loss_behavior_v2",
        "prompt": "为什么不能只看 loss 判断一次 SFT 是否成功？",
        "chosen": "因为小数据微调可能出现局部拟合：loss 下降，但模型只是记住了训练样本，或者把某些旧能力冲坏了。所以要把固定 prompt 当作回归测试，确认新 adapter 不只是指标好看，而是真的解决目标 badcase。",
        "rejected": "如果 loss 下降但固定 prompt 变差，那通常说明 prompt 设计不好，不影响 SFT 成功。",
    },
    {
        "category": "loss_behavior_v2",
        "prompt": "如果一个 SFT run 的 loss 很低，但 LoRA/SFT/DPO 概念仍然答错，应该怎么复盘？",
        "chosen": "应该说这个 run 在优化指标上可运行，但目标行为没有通过。复盘重点是数据覆盖、样本质量、是否有回归，以及固定 prompt 对比，而不是把低 loss 直接当作成功。",
        "rejected": "应该说模型已经成功，只是用户问题太难。下一步直接扩大 DPO 就能解决。",
    },
    {
        "category": "loss_behavior_v2",
        "prompt": "在这个项目里，loss、固定 prompt、badcase review 三者怎样配合？",
        "chosen": "loss 用来监控训练是否正常，固定 prompt 用来比较目标行为是否改善，badcase review 用来决定下一轮补什么数据。三者合起来才构成微调闭环。",
        "rejected": "三者里只有 loss 是训练指标，固定 prompt 和 badcase review 更像展示材料，不应该指导数据迭代。",
    },
    {
        "category": "loss_behavior_v2",
        "prompt": "为什么 Stage 5C 不能只看 DPO train loss？",
        "chosen": "DPO train loss 只能说明偏好优化在数据上跑起来了，不能说明 DPO-tiny 在固定技术 prompt 上更好。Stage 5C 必须看行为：prompt 7 是否修好，其他 7 个 prompt 是否回归，回答是否只是更啰嗦而不是更正确。",
        "rejected": "DPO train loss 低就说明偏好学习成功。固定 prompt 对比可以等扩大 DPO 后再做。",
    },
    {
        "category": "anti_unsupported_claim_v2",
        "prompt": "如果 DPO 后回答里出现“从零开始建模型”或“三到六个月”这类项目记录里没有的说法，应该如何处理？",
        "chosen": "应该判为无依据回归，把它写进 rejected pattern。这个项目要讲可复现和可解释，所以回答必须忠于已有实验记录：Stage 2B 是自采集技术数据，不是从零建模型；项目也没有三到六个月这个结论。",
        "rejected": "这些说法虽然没有记录，但听起来更像真实项目经验，可以保留，让回答更丰富。",
    },
    {
        "category": "anti_unsupported_claim_v2",
        "prompt": "DPO 偏好数据里的 rejected answer 应该惩罚哪些近似但错误的说法？",
        "chosen": "应该惩罚概念错、因果错和无依据扩写。例如把 Stage 2B 说成从零建模型、编造三到六个月周期、把 public-SFT 说成毫无价值、或把 loss 当唯一成功标准。",
        "rejected": "只需要惩罚完全胡说的回答。近似但有细节扩写的回答可以当 chosen，因为它更长。",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare revised Stage 5A.2 tiny DPO data.")
    parser.add_argument("--base_file", default="data/processed/dpo_tiny_train.jsonl")
    parser.add_argument("--output_file", default="data/processed/dpo_tiny_v2_train.jsonl")
    parser.add_argument("--report_file", default="reports/stage5a2_dpo_tiny_v2_data_report.md")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            try:
                rows.append(
                    {
                        "prompt": str(row["prompt"]).strip(),
                        "chosen": str(row["chosen"]).strip(),
                        "rejected": str(row["rejected"]).strip(),
                    }
                )
            except KeyError as exc:
                raise ValueError(f"Missing key in {path}:{line_no}: {exc}") from exc
    if not rows:
        raise ValueError(f"No rows loaded from {path}")
    return rows


def validate_rows(rows: list[dict[str, str]]) -> None:
    for index, row in enumerate(rows, start=1):
        for key in ["prompt", "chosen", "rejected"]:
            if not row.get(key, "").strip():
                raise ValueError(f"row {index} has empty {key}")
        if row["chosen"] == row["rejected"]:
            raise ValueError(f"row {index} chosen equals rejected")


def write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def length_stats(values: list[int]) -> dict[str, float | int]:
    return {
        "min": min(values),
        "avg": round(mean(values), 1),
        "max": max(values),
    }


def render_report(base_rows: list[dict[str, str]], all_rows: list[dict[str, str]], output_file: Path) -> str:
    focused_counts = Counter(pair["category"] for pair in FOCUSED_REVISION_PAIRS)
    prompt_counts = Counter(row["prompt"] for row in all_rows)
    prompt_lengths = [len(row["prompt"]) for row in all_rows]
    chosen_lengths = [len(row["chosen"]) for row in all_rows]
    rejected_lengths = [len(row["rejected"]) for row in all_rows]

    focused_lines = "\n".join(
        f"- `{category}`: {count}" for category, count in sorted(focused_counts.items())
    )
    repeated_focus = "\n".join(
        f"- {prompt}: {count}"
        for prompt, count in prompt_counts.items()
        if count > 1 and ("loss" in prompt or "public-SFT" in prompt)
    )

    return f"""# Stage 5A.2 Tiny DPO v2 Data Report

Date: 2026-05-15

## Scope

Stage 5A.2 revises the tiny DPO preference data after Stage 5C failed the
behavior gate. It keeps the original Stage 5A data intact and adds focused pairs
for the two weak areas.

Output:

```text
{output_file.as_posix()}
```

## Dataset Summary

- Base Stage 5A rows: {len(base_rows)}
- Added focused rows: {len(FOCUSED_REVISION_PAIRS)}
- Total v2 rows: {len(all_rows)}
- Unique prompts: {len(set(row["prompt"] for row in all_rows))}
- Duplicate focus prompts are intentional.

Focused additions:

{focused_lines}

Repeated focused prompts:

{repeated_focus}

Character-length checks:

| Field | Min | Avg | Max |
|---|---:|---:|---:|
| prompt | {length_stats(prompt_lengths)["min"]} | {length_stats(prompt_lengths)["avg"]} | {length_stats(prompt_lengths)["max"]} |
| chosen | {length_stats(chosen_lengths)["min"]} | {length_stats(chosen_lengths)["avg"]} | {length_stats(chosen_lengths)["max"]} |
| rejected | {length_stats(rejected_lengths)["min"]} | {length_stats(rejected_lengths)["avg"]} | {length_stats(rejected_lengths)["max"]} |

## Design Changes

The v2 data explicitly rejects Stage 5C failure patterns:

- saying Stage 2B is "building the model from zero"
- inventing "three to six months"
- treating public-SFT as worthless instead of as a baseline and badcase finder
- treating loss as the only success criterion
- delaying fixed-prompt behavior checks until after larger DPO

The chosen answers are shorter and stricter than the rejected answers. They
emphasize that public-SFT validates the engineering loop but exposes target-data
coverage gaps, and that loss is necessary but not sufficient without fixed
prompt behavior checks.

## Next Gate

Run Stage 5B.2 tiny DPO from the same SFT v3 adapter:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

Then rerun Stage 5C.2 before considering any larger DPO.
"""


def main() -> None:
    args = parse_args()
    base_file = Path(args.base_file)
    output_file = Path(args.output_file)
    report_file = Path(args.report_file)

    base_rows = read_jsonl(base_file)
    focused_rows = [
        {"prompt": row["prompt"], "chosen": row["chosen"], "rejected": row["rejected"]}
        for row in FOCUSED_REVISION_PAIRS
    ]
    all_rows = base_rows + focused_rows
    validate_rows(all_rows)

    write_jsonl(output_file, all_rows)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(render_report(base_rows, all_rows, output_file), encoding="utf-8")

    print(f"Wrote {len(all_rows)} DPO v2 preference pairs to {output_file}")
    print(f"Wrote report to {report_file}")


if __name__ == "__main__":
    main()
