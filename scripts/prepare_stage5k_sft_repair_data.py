"""Convert Stage 5H preference data into Stage 5K SFT repair data.

DPO v7 can score the preference eval well while still failing the visible
loss-vs-behavior prompt. This helper turns the chosen answers from Stage 5H into
chat-format SFT examples so a low-learning-rate continuation can directly teach
the desired explanation without discarding replay coverage.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_SYSTEM_PROMPT = (
    "你是一个清晰、严谨、适合初学者的大模型微调中文助教。"
    "回答时优先解释 LoRA、SFT、DPO、数据清洗、显存和实验复盘。"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Stage 5K SFT repair data.")
    parser.add_argument("--dpo_train_file", default="data/processed/dpo_stage5h_prompt7_train.jsonl")
    parser.add_argument("--dpo_eval_file", default="data/processed/dpo_stage5h_prompt7_eval.jsonl")
    parser.add_argument("--sft_train_file", default="data/processed/sft_stage5k_prompt7_repair_train.jsonl")
    parser.add_argument("--sft_eval_file", default="data/processed/sft_stage5k_prompt7_repair_eval.jsonl")
    parser.add_argument("--report_file", default="reports/stage5k_sft_repair_data_report.md")
    parser.add_argument("--system_prompt", default=DEFAULT_SYSTEM_PROMPT)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            for key in ["prompt", "chosen"]:
                if not str(row.get(key, "")).strip():
                    raise ValueError(f"Missing/empty {key} in {path}:{line_no}")
            rows.append(row)
    if not rows:
        raise ValueError(f"No rows loaded from {path}")
    return rows


def to_sft_rows(rows: list[dict[str, Any]], system_prompt: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        prompt = str(row["prompt"]).strip()
        answer = str(row["chosen"]).strip()
        key = (prompt, answer)
        if key in seen:
            continue
        seen.add(key)
        output.append(
            {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": answer},
                ],
                "source_type": str(row.get("source_type", "stage5k_from_stage5h_chosen")),
                "prompt_area": str(row.get("prompt_area", "")),
            }
        )
    return output


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def count_prompt7(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if row.get("prompt_area") == "Loss vs behavior")


def render_report(train_rows: list[dict[str, Any]], eval_rows: list[dict[str, Any]], train_file: Path, eval_file: Path) -> str:
    return f"""# Stage 5K SFT Repair Data Report

Date: 2026-05-16

## Scope

Stage 5K converts Stage 5H preference data into chat-format SFT repair data.
This is a response to DPO v7 failing the visible prompt-7 behavior gate despite
good preference metrics.

## Outputs

```text
{train_file.as_posix()}
{eval_file.as_posix()}
```

## Summary

- Train rows: {len(train_rows)}
- Eval rows: {len(eval_rows)}
- Loss-vs-behavior train rows: {count_prompt7(train_rows)}
- Loss-vs-behavior eval rows: {count_prompt7(eval_rows)}

## Design

- Uses the Stage 5H chosen answers as direct SFT targets.
- Keeps replay rows from the Stage 5H distribution so prompt-7 repair does not
  overwrite LoRA/SFT/DPO, data-pipeline, DPO-VRAM, public-SFT motivation, or
  interview-narrative behavior.
- Intended use is low-learning-rate continuation from
  `outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`, not from DPO v7.
"""


def main() -> None:
    args = parse_args()
    train_rows = to_sft_rows(read_jsonl(Path(args.dpo_train_file)), args.system_prompt)
    eval_rows = to_sft_rows(read_jsonl(Path(args.dpo_eval_file)), args.system_prompt)
    train_file = Path(args.sft_train_file)
    eval_file = Path(args.sft_eval_file)
    report_file = Path(args.report_file)
    write_jsonl(train_file, train_rows)
    write_jsonl(eval_file, eval_rows)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(render_report(train_rows, eval_rows, train_file, eval_file), encoding="utf-8")
    print(f"Wrote {len(train_rows)} Stage 5K SFT train rows to {train_file}")
    print(f"Wrote {len(eval_rows)} Stage 5K SFT eval rows to {eval_file}")
    print(f"Wrote report to {report_file}")


if __name__ == "__main__":
    main()
