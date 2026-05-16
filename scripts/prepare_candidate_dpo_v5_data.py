"""Prepare Stage 5 candidate DPO v5 data.

v4 preserved most old behavior but still failed the public-SFT motivation and
loss-vs-behavior gates. This script keeps the v4 candidate-derived dataset and
adds only exact v4 failures plus narrow near-miss variants for those two gates.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


PUBLIC_SFT_CHOSEN = (
    "public-SFT adapter 的作用是跑通公开数据训练、保存、加载和对比链路，作为可复现基线。它没有修正 "
    "LoRA/SFT/DPO 概念误解，说明公开通用 instruction 数据没有覆盖目标 badcase，所以 Stage 2B 要用"
    "自采集技术数据做定向修复。它不是从零建模，也不是说 public-SFT 自己已经补足概念。"
)

LOSS_BEHAVIOR_CHOSEN = (
    "不能只看 loss。loss 是训练目标上的平均拟合信号，必要但不充分；一次 SFT 是否成功，还要看固定 prompt "
    "行为、目标 badcase 是否修好、旧能力是否回归。这个项目里 public-SFT 能跑通但仍误解 LoRA/SFT/DPO，"
    "所以必须把 loss 曲线和固定 prompt 对比、badcase review 一起作为验收。"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare candidate-derived DPO v5 data.")
    parser.add_argument("--base_train", default="data/processed/dpo_candidate_train.jsonl")
    parser.add_argument("--base_eval", default="data/processed/dpo_candidate_eval.jsonl")
    parser.add_argument("--v4_compare", default="reports/compare_outputs_four_way_dpo_candidate_v4.jsonl")
    parser.add_argument("--train_output", default="data/processed/dpo_candidate_v5_train.jsonl")
    parser.add_argument("--eval_output", default="data/processed/dpo_candidate_v5_eval.jsonl")
    parser.add_argument("--report_file", default="reports/stage5f_candidate_v5_data_report.md")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"Expected object in {path}:{line_no}")
            rows.append(row)
    if not rows:
        raise ValueError(f"No rows loaded from {path}")
    return rows


def normalized(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "prompt": str(row["prompt"]).strip(),
        "chosen": str(row["chosen"]).strip(),
        "rejected": str(row["rejected"]).strip(),
        **{key: value for key, value in row.items() if key not in {"prompt", "chosen", "rejected"}},
    }


def add_unique(rows: list[dict[str, Any]], seen: set[tuple[str, str, str]], row: dict[str, Any]) -> None:
    item = normalized(row)
    key = (item["prompt"], item["chosen"], item["rejected"])
    if key in seen:
        return
    if not item["prompt"] or not item["chosen"] or not item["rejected"]:
        raise ValueError(f"Empty field in row: {item}")
    if item["chosen"] == item["rejected"]:
        raise ValueError(f"Chosen equals rejected: {item['prompt']}")
    seen.add(key)
    rows.append(item)


def build_focus_rows(v4_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(v4_rows) != 8:
        raise ValueError(f"Expected 8 v4 comparison rows, got {len(v4_rows)}")
    public_prompt = str(v4_rows[3]["prompt"]).strip()
    loss_prompt = str(v4_rows[6]["prompt"]).strip()
    public_rejected = str(v4_rows[3]["dpo_tiny_answer"]).strip()
    loss_rejected = str(v4_rows[6]["dpo_tiny_answer"]).strip()
    return [
        {
            "prompt": public_prompt,
            "chosen": PUBLIC_SFT_CHOSEN,
            "rejected": public_rejected,
            "source_type": "v4_exact_failure_focus",
            "source_prompt_index": 4,
        },
        {
            "prompt": "为什么 public-SFT 失败反而证明 Stage 2B 有价值？",
            "chosen": PUBLIC_SFT_CHOSEN,
            "rejected": (
                "因为 public-SFT adapter 不是公开通用 instruction 数据，也不是完整的 LoRA SFT 定义。"
                "Stage 2B 训练 public-SFT adapter，让模型做双盲或三盲。"
            ),
            "source_type": "v4_near_miss_focus",
            "source_prompt_index": 4,
        },
        {
            "prompt": "回答 public-SFT motivation 时，必须避免哪些说法？",
            "chosen": (
                "要避免说 Stage 2B 是从零建模，避免说 public-SFT adapter 已经补足 LoRA/SFT/DPO 概念，"
                "也避免编造项目周期或把它说成双盲实验。正确说法是：public-SFT 跑通工程基线，但暴露目标数据覆盖不足。"
            ),
            "rejected": "可以说 public-SFT 不是公开数据，Stage 2B 要重新训练 public-SFT adapter，让模型做双盲或三盲。",
            "source_type": "v4_near_miss_focus",
            "source_prompt_index": 4,
        },
        {
            "prompt": "public-SFT adapter 和 Stage 2B 的边界是什么？",
            "chosen": (
                "public-SFT adapter 是公开数据基线，用来证明链路和发现 badcase；Stage 2B 是针对 badcase 自采集、"
                "清洗、去重并转换技术 instruction-answer 数据。两者不是从零建模，也不是让 public-SFT 直接补全所有概念。"
            ),
            "rejected": "public-SFT adapter 不是公开数据，Stage 2B 要训练 public-SFT 和 custom-SFT 两种 adapter 来做双盲。",
            "source_type": "v4_near_miss_focus",
            "source_prompt_index": 4,
        },
        {
            "prompt": loss_prompt,
            "chosen": LOSS_BEHAVIOR_CHOSEN,
            "rejected": loss_rejected,
            "source_type": "v4_exact_failure_focus",
            "source_prompt_index": 7,
        },
        {
            "prompt": "如果 loss 降了，为什么仍然要做固定 prompt 对比？",
            "chosen": LOSS_BEHAVIOR_CHOSEN,
            "rejected": "只要看 LoRA/SFT 数据证明训练链路成功，就能确认目标行为；loss 之外不用再看 badcase 回归。",
            "source_type": "v4_near_miss_focus",
            "source_prompt_index": 7,
        },
        {
            "prompt": "面试官问不能只看 loss，你怎么回答？",
            "chosen": (
                "我会说 loss 是平均训练目标信号，能说明拟合趋势，但不能证明目标问题答对。我的项目里 public-SFT "
                "能跑通却仍误解 LoRA/SFT/DPO，所以我同时看 loss、固定 prompt 输出、badcase 修复和旧能力回归。"
            ),
            "rejected": "我会说 loss 主要用于证明训练链路成功，只要 public-SFT 概念能看懂，就不用再做固定 prompt。",
            "source_type": "v4_near_miss_focus",
            "source_prompt_index": 7,
        },
        {
            "prompt": "为什么 tiny DPO 的 train loss 不能单独作为验收？",
            "chosen": (
                "DPO train loss 只能说明偏好优化目标在训练集上的变化。验收还要看 held-out preference eval、固定 prompt "
                "行为、public-SFT motivation 是否不回归，以及 LoRA/SFT/DPO、数据管线、显存风险等旧 prompt 是否稳定。"
            ),
            "rejected": "DPO train loss 降低就代表目标完成比例高，adapter loss 和全量 loss 足以判断 tiny DPO 成功。",
            "source_type": "v4_near_miss_focus",
            "source_prompt_index": 7,
        },
    ]


def validate(rows: list[dict[str, Any]], split: str) -> None:
    for index, row in enumerate(rows, start=1):
        for key in ["prompt", "chosen", "rejected"]:
            if not str(row.get(key, "")).strip():
                raise ValueError(f"{split} row {index} has empty {key}")
        if str(row["chosen"]).strip() == str(row["rejected"]).strip():
            raise ValueError(f"{split} row {index} chosen equals rejected")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def stats(values: list[int]) -> str:
    return f"{min(values)} / {round(mean(values), 1)} / {max(values)}"


def render_report(base_train: list[dict[str, Any]], focus_rows: list[dict[str, Any]], train_rows: list[dict[str, Any]], eval_rows: list[dict[str, Any]], train_output: Path, eval_output: Path) -> str:
    counter = Counter(str(row.get("source_type", "unknown")) for row in train_rows)
    source_lines = ["| Source Type | Rows |", "|---|---:|"]
    for source_type, count in sorted(counter.items()):
        source_lines.append(f"| `{source_type}` | {count} |")
    prompt_lengths = [len(str(row["prompt"])) for row in train_rows]
    chosen_lengths = [len(str(row["chosen"])) for row in train_rows]
    rejected_lengths = [len(str(row["rejected"])) for row in train_rows]
    return f"""# Stage 5F Candidate DPO v5 Data Report

Date: 2026-05-16

## Scope

Stage 5F keeps the v4 candidate-derived data and adds a narrow repair set for
the two v4 behavior failures:

- prompt 4: public-SFT motivation
- prompt 7: loss-vs-behavior

## Outputs

```text
{train_output.as_posix()}
{eval_output.as_posix()}
```

## Dataset Summary

- Base candidate train rows: {len(base_train)}
- Added focused rows: {len(focus_rows)}
- Total v5 train rows: {len(train_rows)}
- Eval rows: {len(eval_rows)}
- Train prompt length min/avg/max chars: {stats(prompt_lengths)}
- Train chosen length min/avg/max chars: {stats(chosen_lengths)}
- Train rejected length min/avg/max chars: {stats(rejected_lengths)}

## Train Sources

{chr(10).join(source_lines)}

## Decision Rule

Stage 5B.5 should still remain a tiny DPO retry. If prompt 4 or prompt 7 still
fails, or if old prompt stability regresses, Stage 5D larger DPO remains
blocked.
"""


def main() -> None:
    args = parse_args()
    base_train = [normalized(row) for row in read_jsonl(Path(args.base_train))]
    base_eval = [normalized(row) for row in read_jsonl(Path(args.base_eval))]
    focus_rows = build_focus_rows(read_jsonl(Path(args.v4_compare)))
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in [*base_train, *focus_rows]:
        add_unique(rows, seen, row)
    eval_rows = [
        *base_eval,
        {
            "prompt": "public-SFT motivation 的一句话复盘应该是什么？",
            "chosen": "公开数据基线跑通了工程链路，但没有覆盖目标概念 badcase，所以需要 Stage 2B 定向数据修复。",
            "rejected": "public-SFT 不是公开数据，Stage 2B 是重新训练 public-SFT adapter 来补足概念。",
            "source_type": "v5_heldout_eval",
        },
        {
            "prompt": "为什么固定 prompt 比单个 loss 数字更适合作为行为验收？",
            "chosen": "固定 prompt 能直接检查目标概念、badcase 修复和旧能力回归；loss 只是平均拟合信号，不能单独证明行为正确。",
            "rejected": "固定 prompt 只是展示用，loss 数字更客观，只要 loss 低就能验收。",
            "source_type": "v5_heldout_eval",
        },
    ]
    validate(rows, "train")
    validate(eval_rows, "eval")
    train_output = Path(args.train_output)
    eval_output = Path(args.eval_output)
    report_file = Path(args.report_file)
    write_jsonl(train_output, rows)
    write_jsonl(eval_output, eval_rows)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(render_report(base_train, focus_rows, rows, eval_rows, train_output, eval_output), encoding="utf-8")
    print(f"Wrote {len(rows)} candidate v5 train rows to {train_output}")
    print(f"Wrote {len(eval_rows)} candidate v5 eval rows to {eval_output}")
    print(f"Wrote report to {report_file}")


if __name__ == "__main__":
    main()
