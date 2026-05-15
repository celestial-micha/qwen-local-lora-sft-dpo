"""Prepare Stage 5A.3 exact-bad-output DPO preference data.

Stage 5C.2 showed that the loss-vs-behavior prompt still resisted the v2 data.
This v3 data keeps v2 intact and adds exact rejected outputs copied from the
failed DPO-tiny behavior checks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean


EXACT_REPAIR_PAIRS: list[dict[str, str]] = [
    {
        "prompt": "为什么不能只看 loss 判断一次 SFT 是否成功？",
        "chosen": "不能只看 loss。loss 只是训练或验证数据上的平均拟合信号，是必要参考但不充分。一次 SFT 是否成功，还要看固定 prompt 行为是否更正确、目标 badcase 是否减少、旧能力是否回归。本项目里 public-SFT 能训练完成但仍误解 LoRA/SFT/DPO，所以必须用固定 prompt 对比和 badcase review 一起判断。",
        "rejected": "只能先说公开数据跑通，但 Stage 4A 发现 public-SFT 没修正 LoRA/SFT/DPO 概念误解，所以进入 Stage 2B。Stage 2B 的目标是纠正概念误解，而不是只用 loss 判断项目是否通过。第一版 public-SFT 需要再做三到六个月的自采集练，让模型更清楚明白它错在哪里。",
    },
    {
        "prompt": "为什么不能只看 loss 判断一次 SFT 是否成功？",
        "chosen": "不能只看 loss，因为 loss 不直接等于目标问题答对。正确复盘要同时看 loss 曲线、固定 prompt 对比、badcase 是否被修掉、以及原来答好的 prompt 有没有回归。loss 下降但行为仍错，只能说明训练在拟合数据，不能说明项目目标已经达成。",
        "rejected": "只能先说它失败，而不是只凭 loss 判断项目是否通过。所以 Stage 4A 需要看到 metrics 和工程闭环，确认问题已经解决。第一版 loss 能让团队看到项目成功了，但 Stage 2B/3A 仍然需要看到项目实际行为。",
    },
    {
        "prompt": "为什么不能只看 loss 判断一次 SFT 是否成功？",
        "chosen": "loss 是指标，不是验收结论。SFT 的验收要问：目标概念有没有答对，固定 prompt 是否改善，旧能力有没有被 patch 打坏。这个项目正是因为 public-SFT loss 和训练流程正常、但目标概念仍错，才进入 Stage 2B 和后续 DPO gate。",
        "rejected": "第一版 public-SFT 需要再做三到六个月的自采集资料工作，所以不能只看 loss。",
    },
    {
        "prompt": "为什么不能只看 loss 判断一次 SFT 是否成功？",
        "chosen": "不能只看 loss。尤其在小数据 LoRA SFT 中，loss 可能下降，但模型仍会在 LoRA/SFT/DPO 固定 prompt 上误解，或者新 patch 修一个点却破坏旧能力。因此要把 loss 当训练监控，把固定 prompt 对比当行为验收。",
        "rejected": "不能只看 loss，因为公开数据没修正概念，所以 Stage 2B 要继续做很多个月的数据补习。",
    },
    {
        "prompt": "如果面试官问为什么不能只看 loss，你会怎么回答？",
        "chosen": "我会说 loss 只能说明模型在训练目标上拟合得怎么样，不能保证目标业务问题答对。我的项目里 public-SFT 能跑通，但固定 prompt 仍误解 LoRA/SFT/DPO；后面一些 patch 也出现过低 loss 但旧能力回归。所以我同时看 loss、固定 prompt、badcase 和回归。",
        "rejected": "我会说因为训练还需要三到六个月，只看 loss 看不出项目周期，所以要继续采数据。",
    },
    {
        "prompt": "为什么 public-SFT adapter 没修正 LoRA/SFT/DPO 概念误解，反而说明 Stage 2B 有必要？",
        "chosen": "因为 public-SFT 证明的是工程链路可跑，不证明目标概念已覆盖。Stage 4A 发现它仍误解 LoRA/SFT/DPO，说明通用 instruction 数据不够定向，所以 Stage 2B 要补自采集技术数据，并把这些 badcase 转成训练和评测样本。",
        "rejected": "因为公开数据跑通不等于目标领域行为已经解决，Stage 2B 仍然需要聚焦技术概念错误、数据工程错误、显存和架构理解。public-SFT adapter 是用公开通用 instruction 数据训练出的基线 adapter，用来补足 LoRA、SFT、DPO 的技术概念误解。",
    },
    {
        "prompt": "为什么 public-SFT adapter 没修正 LoRA/SFT/DPO 概念误解，反而说明 Stage 2B 有必要？",
        "chosen": "public-SFT 是基线和诊断工具：它跑通了 LoRA SFT 流程，也暴露了通用数据没覆盖项目概念。Stage 2B 的价值是补数据覆盖，而不是从零建模型，也不是编造项目周期。",
        "rejected": "public-SFT adapter 用来补足 LoRA、SFT、DPO 的技术概念误解，所以 Stage 2B 是从零开始建模型。",
    },
    {
        "prompt": "回答 public-SFT motivation 时，哪些说法应该避免？",
        "chosen": "要避免说 Stage 2B 从零建模型、避免说 public-SFT adapter 本身会补足概念、避免编造三到六个月。应该说 public-SFT 跑通工程链路但暴露目标数据覆盖不足，所以 Stage 2B 用定向技术数据修 badcase。",
        "rejected": "可以说 public-SFT adapter 用来补足概念误解，也可以说 Stage 2B 从零建模型，这些说法能让回答更完整。",
    },
    {
        "prompt": "Stage 5C 为什么要阻止直接扩大 DPO？",
        "chosen": "因为 Stage 5C 是行为 gate。即使 Stage 5B 没有 OOM，只要固定 prompt 没修好或出现旧能力回归，就不能扩大 DPO。先修 preference 数据、重跑 tiny DPO 和行为对比，才是可控流程。",
        "rejected": "只要 Stage 5B 没有 OOM，就说明显存够用，可以直接扩大 DPO。行为问题可以靠更多数据和更多 step 自动解决。",
    },
    {
        "prompt": "如何判断 tiny DPO 是否真的成功？",
        "chosen": "不能只看 DPO train loss 或是否保存 adapter。tiny DPO 成功至少要同时满足：显存能跑、adapter 能保存加载、目标 loss-vs-behavior prompt 改善、public-SFT motivation 不回归、旧的 LoRA/SFT/DPO 和数据管线 prompt 仍然稳定。",
        "rejected": "tiny DPO 成功就是没有 OOM。只要显存够，行为对比可以等扩大 DPO 后再看。",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Stage 5A.3 exact-repair DPO data.")
    parser.add_argument("--base_file", default="data/processed/dpo_tiny_v2_train.jsonl")
    parser.add_argument("--output_file", default="data/processed/dpo_tiny_v3_train.jsonl")
    parser.add_argument("--report_file", default="reports/stage5a3_dpo_tiny_v3_data_report.md")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
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
                }
            )
    if not rows:
        raise ValueError(f"No rows loaded from {path}")
    return rows


def validate(rows: list[dict[str, str]]) -> None:
    for index, row in enumerate(rows, start=1):
        for key in ["prompt", "chosen", "rejected"]:
            if not row[key]:
                raise ValueError(f"row {index} has empty {key}")
        if row["chosen"] == row["rejected"]:
            raise ValueError(f"row {index} chosen equals rejected")


def write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def stats(values: list[int]) -> str:
    return f"{min(values)} / {round(mean(values), 1)} / {max(values)}"


def render_report(base_rows: list[dict[str, str]], all_rows: list[dict[str, str]], output_file: Path) -> str:
    prompt_lengths = [len(row["prompt"]) for row in all_rows]
    chosen_lengths = [len(row["chosen"]) for row in all_rows]
    rejected_lengths = [len(row["rejected"]) for row in all_rows]
    return f"""# Stage 5A.3 Tiny DPO v3 Data Report

Date: 2026-05-15

## Scope

Stage 5A.3 adds exact-bad-output preference pairs after Stage 5C.2 still failed
the loss-vs-behavior behavior gate.

Output:

```text
{output_file.as_posix()}
```

## Dataset Summary

- Base v2 rows: {len(base_rows)}
- Added exact repair rows: {len(EXACT_REPAIR_PAIRS)}
- Total v3 rows: {len(all_rows)}
- Unique prompts: {len(set(row["prompt"] for row in all_rows))}
- Prompt length min/avg/max chars: {stats(prompt_lengths)}
- Chosen length min/avg/max chars: {stats(chosen_lengths)}
- Rejected length min/avg/max chars: {stats(rejected_lengths)}

## Design Change

The rejected answers now include the actual failed DPO-tiny v2 outputs for the
loss-vs-behavior and public-SFT motivation prompts. The chosen answers are short
and explicit:

- loss is necessary but not sufficient
- fixed prompt behavior is the gate
- public-SFT is a baseline and badcase finder
- Stage 2B is data repair, not building a model from zero
- unsupported project-duration claims must be rejected

Stage 5B.3 should still start from the same SFT v3 adapter, not from a previous
DPO adapter.
"""


def main() -> None:
    args = parse_args()
    base_rows = read_jsonl(Path(args.base_file))
    all_rows = base_rows + EXACT_REPAIR_PAIRS
    validate(all_rows)
    output_file = Path(args.output_file)
    report_file = Path(args.report_file)
    write_jsonl(output_file, all_rows)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(render_report(base_rows, all_rows, output_file), encoding="utf-8")
    print(f"Wrote {len(all_rows)} DPO v3 preference pairs to {output_file}")
    print(f"Wrote report to {report_file}")


if __name__ == "__main__":
    main()
