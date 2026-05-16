"""Score expanded Stage 5H behavior comparison outputs.

The fixed Stage 5 scorer is intentionally row-index based for the original
8-prompt suite. This scorer uses prompt metadata, so it can evaluate the
expanded Stage 5H suite that keeps the original prompts and adds held-out
loss-vs-behavior variants.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from score_fixed_prompt_outputs import ANSWER_KEYS, Criterion, PromptRubric, RUBRICS, criterion_hit


AREA_RUBRICS: dict[str, PromptRubric] = {rubric.prompt_area: rubric for rubric in RUBRICS.values()}
AREA_RUBRICS["Loss vs behavior"] = PromptRubric(
    prompt_area="Loss vs behavior",
    required=(
        Criterion("loss average signal", ("平均", "平均拟合", "训练目标", "优化目标", "指标")),
        Criterion("not sufficient", ("不充分", "必要但不充分", "不能只看 loss", "只看 loss 不够", "不够")),
        Criterion("fixed prompt behavior", ("固定 prompt", "固定问题", "行为", "behavior gate", "输出")),
        Criterion("badcase/regression", ("badcase", "坏例", "回归", "旧能力")),
        Criterion("project example", ("public-SFT", "Stage 4A", "DPO v6", "preference accuracy", "LoRA/SFT/DPO")),
        Criterion("metric split", ("train/eval loss", "eval loss", "train loss", "偏好", "指标")),
    ),
    forbidden=(
        Criterion("loss-only claim", ("只要 loss 降低", "loss 降低就说明", "loss 好看就可以")),
        Criterion("preference-only claim", ("preference accuracy 到 1.0 就说明", "DPO train loss 低就说明")),
        Criterion("fixed prompts unimportant", ("固定 prompt 不重要", "固定 prompt 只是展示")),
        Criterion("loss useless", ("loss 完全没有意义", "loss 完全没用")),
        Criterion("invented duration", ("三到六个月", "很多个月")),
    ),
    min_score_to_pass=5,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score expanded Stage 5H behavior JSONL outputs.")
    parser.add_argument(
        "--input_files",
        nargs="+",
        default=["reports/compare_outputs_four_way_dpo_v7_stage5h_expanded.jsonl"],
    )
    parser.add_argument("--output_jsonl", default="reports/stage5h_expanded_behavior_scores.jsonl")
    parser.add_argument("--output_csv", default="reports/stage5h_expanded_behavior_scores.csv")
    parser.add_argument("--report_file", default="reports/stage5h_expanded_behavior_score_report.md")
    return parser.parse_args()


def run_id_from_path(path: Path) -> str:
    stem = path.stem
    if "stage5p" in stem:
        return "stage5p_prompt7_balanced_sft"
    if "stage5o" in stem:
        return "stage5o_prompt7_exact_sft"
    if "stage5n" in stem:
        return "stage5n_prompt7_micro_sft"
    if "v8" in stem or "stage5m" in stem:
        return "dpo_v8_stage5m"
    if "stage5k" in stem:
        return "stage5k_sft_repair"
    if "naive_v6" in stem or stem.endswith("_v6"):
        return "dpo_naive_v6"
    if "v7" in stem or "stage5h" in stem:
        return "dpo_v7_stage5h"
    if "candidate_v5" in stem or stem.endswith("_v5"):
        return "dpo_candidate_v5"
    if "candidate_v4" in stem or stem.endswith("_v4"):
        return "dpo_candidate_v4"
    if stem.endswith("_v3"):
        return "dpo_tiny_v3"
    if stem.endswith("_v2"):
        return "dpo_tiny_v2"
    return stem


def infer_prompt_area(row: dict[str, Any], index: int, path: Path) -> str:
    prompt_area = str(row.get("prompt_area", "")).strip()
    if prompt_area:
        return prompt_area
    if index in RUBRICS:
        return RUBRICS[index].prompt_area
    raise ValueError(f"Missing prompt_area for expanded prompt in {path}:{index}")


def score_answer(prompt_area: str, answer: str) -> dict[str, Any]:
    if prompt_area not in AREA_RUBRICS:
        raise ValueError(f"No rubric for prompt_area={prompt_area!r}")
    rubric = AREA_RUBRICS[prompt_area]
    required_hits = [criterion.name for criterion in rubric.required if criterion_hit(answer, criterion)]
    required_missing = [criterion.name for criterion in rubric.required if not criterion_hit(answer, criterion)]
    forbidden_hits = [criterion.name for criterion in rubric.forbidden if criterion_hit(answer, criterion)]
    score = len(required_hits) - 2 * len(forbidden_hits)
    passed = score >= rubric.min_score_to_pass and len(forbidden_hits) <= rubric.max_forbidden_to_pass
    return {
        "score": score,
        "required_hits": required_hits,
        "required_missing": required_missing,
        "forbidden_hits": forbidden_hits,
        "passed": passed,
    }


def read_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            for key in ["prompt", *ANSWER_KEYS]:
                if key not in row:
                    raise ValueError(f"Missing {key} in {path}:{line_no}")
            rows.append(row)
    if not rows:
        raise ValueError(f"No rows loaded from {path}")
    return rows


def build_score_rows(paths: list[Path]) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for path in paths:
        run_id = run_id_from_path(path)
        rows = read_rows(path)
        for prompt_index, row in enumerate(rows, start=1):
            prompt_area = infer_prompt_area(row, prompt_index, path)
            for variant in ANSWER_KEYS:
                result = score_answer(prompt_area, str(row[variant]))
                scored.append(
                    {
                        "run_id": run_id,
                        "source_file": path.as_posix(),
                        "prompt_index": prompt_index,
                        "prompt_id": row.get("prompt_id", f"row_{prompt_index:02d}"),
                        "prompt_area": prompt_area,
                        "prompt_source": row.get("source", ""),
                        "prompt": row["prompt"],
                        "variant": variant,
                        "score": result["score"],
                        "passed": result["passed"],
                        "required_hits": result["required_hits"],
                        "required_missing": result["required_missing"],
                        "forbidden_hits": result["forbidden_hits"],
                        "answer": row[variant],
                    }
                )
    return scored


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "run_id",
        "prompt_index",
        "prompt_id",
        "prompt_area",
        "prompt_source",
        "variant",
        "score",
        "passed",
        "required_missing",
        "forbidden_hits",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "run_id": row["run_id"],
                    "prompt_index": row["prompt_index"],
                    "prompt_id": row["prompt_id"],
                    "prompt_area": row["prompt_area"],
                    "prompt_source": row["prompt_source"],
                    "variant": row["variant"],
                    "score": row["score"],
                    "passed": row["passed"],
                    "required_missing": "; ".join(row["required_missing"]),
                    "forbidden_hits": "; ".join(row["forbidden_hits"]),
                }
            )


def summarize(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    summary: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["run_id"], row["variant"])
        item = summary.setdefault(
            key,
            {
                "total_score": 0,
                "passes": 0,
                "count": 0,
                "loss_passes": 0,
                "loss_count": 0,
                "failures": [],
            },
        )
        item["count"] += 1
        item["total_score"] += int(row["score"])
        item["passes"] += int(bool(row["passed"]))
        if row["prompt_area"] == "Loss vs behavior":
            item["loss_count"] += 1
            item["loss_passes"] += int(bool(row["passed"]))
        if not row["passed"]:
            item["failures"].append(f"{row['prompt_id']}: {row['prompt_area']}")
    return summary


def render_report(rows: list[dict[str, Any]], jsonl_path: Path, csv_path: Path) -> str:
    summary = summarize(rows)
    run_order = sorted({row["run_id"] for row in rows})
    variant_order = ANSWER_KEYS
    table_lines = [
        "| Run | Variant | Passed Prompts | Loss-vs-Behavior Passed | Total Score | Failed Areas |",
        "|---|---|---:|---:|---:|---|",
    ]
    for run_id in run_order:
        for variant in variant_order:
            item = summary[(run_id, variant)]
            failures = ", ".join(item["failures"]) if item["failures"] else "-"
            table_lines.append(
                f"| {run_id} | `{variant}` | {item['passes']} / {item['count']} | "
                f"{item['loss_passes']} / {item['loss_count']} | {item['total_score']} | {failures} |"
            )

    dpo_rows = [row for row in rows if row["variant"] == "dpo_tiny_answer"]
    detail_lines = [
        "| Prompt ID | Area | Score | Pass | Missing | Forbidden |",
        "|---|---|---:|---|---|---|",
    ]
    for row in dpo_rows:
        missing = ", ".join(row["required_missing"]) if row["required_missing"] else "-"
        forbidden = ", ".join(row["forbidden_hits"]) if row["forbidden_hits"] else "-"
        detail_lines.append(
            f"| {row['prompt_id']} | {row['prompt_area']} | {row['score']} | "
            f"{row['passed']} | {missing} | {forbidden} |"
        )

    return f"""# Stage 5H/5I Expanded Behavior Score Report

Date: 2026-05-16

## Scope

This report scores expanded Stage 5H/5I comparison outputs. The scorer uses
`prompt_area` metadata when available and falls back to the original fixed
8-prompt row order only for legacy comparison files.

It is still a transparent keyword gate helper, not an LLM judge.

Outputs:

```text
{jsonl_path.as_posix()}
{csv_path.as_posix()}
```

## Summary Table

{chr(10).join(table_lines)}

## DPO Candidate Prompt Scores

{chr(10).join(detail_lines)}

## Gate Interpretation

- A future DPO adapter should pass the original fixed prompts and the expanded
  loss-vs-behavior holdouts.
- Prompt 7 answers must not merely say "cannot only look at loss"; they should
  include the average-objective nature of loss, why that is not sufficient,
  fixed-prompt behavior, badcase/regression review, and a project example such
  as public-SFT or DPO v6.
- Preference accuracy, train loss, and eval loss remain supporting metrics, not
  final acceptance criteria.
"""


def main() -> None:
    args = parse_args()
    paths = [Path(path) for path in args.input_files]
    scored_rows = build_score_rows(paths)
    output_jsonl = Path(args.output_jsonl)
    output_csv = Path(args.output_csv)
    report_file = Path(args.report_file)
    write_jsonl(output_jsonl, scored_rows)
    write_csv(output_csv, scored_rows)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(render_report(scored_rows, output_jsonl, output_csv), encoding="utf-8")
    print(f"Wrote {len(scored_rows)} expanded score rows to {output_jsonl}")
    print(f"Wrote CSV to {output_csv}")
    print(f"Wrote report to {report_file}")


if __name__ == "__main__":
    main()
