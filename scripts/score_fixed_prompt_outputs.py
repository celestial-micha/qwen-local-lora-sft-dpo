"""Score fixed-prompt comparison outputs with simple reproducible rules.

This is a lightweight Stage 5 evaluation helper. It does not use an LLM judge;
instead it records transparent keyword-based checks for required concepts and
known-bad phrases. The goal is to make DPO behavior gates reproducible enough to
compare runs before any larger training.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ANSWER_KEYS = [
    "base_answer",
    "public_sft_answer",
    "custom_sft_v3_answer",
    "dpo_tiny_answer",
]


@dataclass(frozen=True)
class Criterion:
    name: str
    any_of: tuple[str, ...]


@dataclass(frozen=True)
class PromptRubric:
    prompt_area: str
    required: tuple[Criterion, ...]
    forbidden: tuple[Criterion, ...]
    min_score_to_pass: int = 3
    max_forbidden_to_pass: int = 0


RUBRICS: dict[int, PromptRubric] = {
    1: PromptRubric(
        prompt_area="LoRA definition",
        required=(
            Criterion("parameter-efficient", ("参数高效", "parameter-efficient")),
            Criterion("low-rank", ("低秩", "low-rank")),
            Criterion("not wireless LoRa", ("不是无线通信", "不要解释成无线通信")),
            Criterion("frozen base model", ("冻结基础模型", "冻结大部分")),
            Criterion("adapter/linear layers", ("adapter", "线性层")),
        ),
        forbidden=(
            Criterion("wrong LoRA expansion", ("Local Recurrent", "Local Reinforcement", "Long Range")),
            Criterion("adapter-state confusion", ("基础 adapter 稳定 state", "固定 prompt 上增加")),
        ),
        min_score_to_pass=4,
    ),
    2: PromptRubric(
        prompt_area="SFT and LoRA relation",
        required=(
            Criterion("supervised fine-tuning", ("supervised fine-tuning", "有监督微调")),
            Criterion("training objective/data form", ("训练目标", "数据形式")),
            Criterion("LoRA parameter-efficient", ("参数高效", "少量更新")),
            Criterion("LoRA SFT relation", ("用 LoRA adapter 来执行 SFT", "LoRA adapter 来执行 SFT")),
        ),
        forbidden=(
            Criterion("network/shortest expansion", ("Shortest", "Flipping Time", "Flawed Link")),
            Criterion("architecture confusion", ("LoRA是SFT的一个子集", "它们在本项目里对应 DPO")),
        ),
        min_score_to_pass=4,
    ),
    3: PromptRubric(
        prompt_area="DPO vs SFT",
        required=(
            Criterion("SFT imitation", ("instruction-answer", "模仿目标回答", "标准回答")),
            Criterion("DPO preference pairs", ("chosen/rejected", "偏好对")),
            Criterion("prefer chosen", ("更偏向", "远离坏回答", "更喜欢的回答")),
            Criterion("SFT before DPO", ("先做 SFT", "通常先做 SFT", "基础回答能力")),
        ),
        forbidden=(
            Criterion("data preprocessing expansion", ("Data Preprocessing", "Synthesis of Features")),
            Criterion("security/privacy expansion", ("Data Privacy", "Security Framework")),
            Criterion("DPO object confusion", ("数据保护对象", "DPO 指数据保护")),
            Criterion("SFT safety metric confusion", ("SFT 指安全",)),
        ),
        min_score_to_pass=4,
    ),
    4: PromptRubric(
        prompt_area="Public-SFT motivation",
        required=(
            Criterion("public baseline", ("公开数据", "public-SFT", "基线")),
            Criterion("engineering loop works", ("跑通", "工程链路", "训练链路")),
            Criterion("target concepts not solved", ("不等于目标", "没有覆盖", "没修正", "仍误解")),
            Criterion("Stage 2B data repair", ("Stage 2B", "自采集", "技术数据", "定向")),
        ),
        forbidden=(
            Criterion("from-zero claim", ("从零", "重新从零")),
            Criterion("invented duration", ("三到六个月", "很多个月")),
            Criterion("public adapter fixes concepts", ("public-SFT adapter 用来补足", "基线 adapter，用来补足")),
            Criterion("robustness-only claim", ("不是 LoRA/SFT/DPO 的目标，而是让 model 更健壮",)),
            Criterion("long-stack confusion", ("long stack",)),
        ),
        min_score_to_pass=4,
    ),
    5: PromptRubric(
        prompt_area="Data pipeline",
        required=(
            Criterion("source metadata", ("source_id", "标题", "路径", "URL", "来源")),
            Criterion("cleaning", ("清洗", "网页噪声", "导航栏", "广告")),
            Criterion("dedup/filter", ("去重", "筛选")),
            Criterion("instruction-answer conversion", ("instruction-answer", "问答", "对话样本")),
            Criterion("Qwen chat JSONL", ("Qwen chat JSONL", "chat JSONL")),
        ),
        forbidden=(
            Criterion("generic sensor data", ("传感器", "摄像头")),
            Criterion("tabular preprocessing confusion", ("缺失值", "标准化", "归一化")),
        ),
        min_score_to_pass=4,
    ),
    6: PromptRubric(
        prompt_area="DPO VRAM risk",
        required=(
            Criterion("chosen/rejected memory", ("chosen/rejected", "比较 chosen")),
            Criterion("reference policy", ("reference", "reference policy")),
            Criterion("8GB risk", ("8GB", "爆显存", "OOM", "共享内存", "很慢")),
            Criterion("small batch/short length", ("batch_size=1", "小 batch", "短 max_length", "短 max_prompt_length")),
            Criterion("LoRA/small pairs", ("LoRA", "少量 pair", "少 eval")),
        ),
        forbidden=(
            Criterion("fabricated memory numbers", ("2.5-3.5GB/epoch", "0.1-0.2GB/epoch", "batch_size=4GB")),
            Criterion("memory leak generic", ("内存泄漏", "内存置换")),
        ),
        min_score_to_pass=4,
    ),
    7: PromptRubric(
        prompt_area="Loss vs behavior",
        required=(
            Criterion("loss average signal", ("平均拟合", "训练目标", "优化", "指标")),
            Criterion("not sufficient", ("不充分", "不能只看 loss", "只看 loss 不够")),
            Criterion("fixed prompt behavior", ("固定 prompt", "行为")),
            Criterion("badcase/regression", ("badcase", "回归", "旧能力")),
            Criterion("public-SFT example", ("public-SFT", "LoRA/SFT/DPO")),
        ),
        forbidden=(
            Criterion("invented duration", ("三到六个月", "很多个月")),
            Criterion("DPO metric confusion", ("DPO 是目标完成比例", "DPO train loss 低就说明")),
            Criterion("adapter-loss confusion", ("全量 loss、adapter loss", "public-SFT 和 custom-SFT 的变化")),
        ),
        min_score_to_pass=4,
    ),
    8: PromptRubric(
        prompt_area="Interview data pipeline",
        required=(
            Criterion("public baseline", ("公开数据集", "可复现基线")),
            Criterion("train/save/load", ("训练", "保存", "加载")),
            Criterion("Stage 4A badcase", ("Stage 4A", "没修正")),
            Criterion("Stage 2B pipeline", ("Stage 2B", "采集", "清洗", "去重", "筛选")),
            Criterion("instruction-answer", ("instruction-answer", "三方对比")),
        ),
        forbidden=(
            Criterion("tokenizer/storage confusion", ("Hugging Face Tokenizers", "Tokenizers 上")),
            Criterion("base adapter/public adapter confusion", ("base adapter 和 public adapter", "安全开始")),
            Criterion("generic business data", ("SQL数据库", "大数据处理")),
        ),
        min_score_to_pass=4,
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score fixed-prompt JSONL outputs.")
    parser.add_argument(
        "--input_files",
        nargs="+",
        default=[
            "reports/compare_outputs_four_way_dpo_tiny.jsonl",
            "reports/compare_outputs_four_way_dpo_tiny_v2.jsonl",
            "reports/compare_outputs_four_way_dpo_tiny_v3.jsonl",
            "reports/compare_outputs_four_way_dpo_candidate_v4.jsonl",
            "reports/compare_outputs_four_way_dpo_candidate_v5.jsonl",
            "reports/compare_outputs_four_way_dpo_naive_v6.jsonl",
        ],
    )
    parser.add_argument("--output_jsonl", default="reports/stage5_structured_behavior_scores.jsonl")
    parser.add_argument("--output_csv", default="reports/stage5_structured_behavior_scores.csv")
    parser.add_argument("--report_file", default="reports/stage5_structured_behavior_score_report.md")
    return parser.parse_args()


def run_id_from_path(path: Path) -> str:
    name = path.stem
    if "stage5p" in name:
        return "stage5p_prompt7_balanced_sft"
    if "stage5o" in name:
        return "stage5o_prompt7_exact_sft"
    if "stage5n" in name:
        return "stage5n_prompt7_micro_sft"
    if "v8" in name or "stage5m" in name:
        return "dpo_v8_stage5m"
    if "stage5k" in name:
        return "stage5k_sft_repair"
    if "v7" in name or "stage5h" in name:
        return "dpo_v7_stage5h"
    if "naive_v6" in name or name.endswith("_v6"):
        return "dpo_naive_v6"
    if "candidate_v5" in name or name.endswith("_v5"):
        return "dpo_candidate_v5"
    if "candidate_v4" in name or name.endswith("_v4"):
        return "dpo_candidate_v4"
    if name.endswith("_v3"):
        return "dpo_tiny_v3"
    if name.endswith("_v2"):
        return "dpo_tiny_v2"
    return "dpo_tiny_v1"


def criterion_hit(text: str, criterion: Criterion) -> bool:
    lowered = text.lower()
    return any(fragment.lower() in lowered for fragment in criterion.any_of)


def score_answer(prompt_index: int, answer: str) -> dict[str, Any]:
    rubric = RUBRICS[prompt_index]
    required_hits = [criterion.name for criterion in rubric.required if criterion_hit(answer, criterion)]
    required_missing = [criterion.name for criterion in rubric.required if not criterion_hit(answer, criterion)]
    forbidden_hits = [criterion.name for criterion in rubric.forbidden if criterion_hit(answer, criterion)]
    score = len(required_hits) - 2 * len(forbidden_hits)
    passed = score >= rubric.min_score_to_pass and len(forbidden_hits) <= rubric.max_forbidden_to_pass
    return {
        "prompt_area": rubric.prompt_area,
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
    if len(rows) != 8:
        raise ValueError(f"Expected 8 fixed prompts in {path}, got {len(rows)}")
    return rows


def build_score_rows(paths: list[Path]) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for path in paths:
        run_id = run_id_from_path(path)
        rows = read_rows(path)
        for prompt_index, row in enumerate(rows, start=1):
            for variant in ANSWER_KEYS:
                result = score_answer(prompt_index, str(row[variant]))
                scored.append(
                    {
                        "run_id": run_id,
                        "source_file": path.as_posix(),
                        "prompt_index": prompt_index,
                        "prompt": row["prompt"],
                        "prompt_area": result["prompt_area"],
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
        "prompt_area",
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
                    "prompt_area": row["prompt_area"],
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
        item = summary.setdefault(key, {"total_score": 0, "passes": 0, "failures": []})
        item["total_score"] += int(row["score"])
        item["passes"] += int(bool(row["passed"]))
        if not row["passed"]:
            item["failures"].append(f"{row['prompt_index']}: {row['prompt_area']}")
    return summary


def render_report(rows: list[dict[str, Any]], jsonl_path: Path, csv_path: Path, input_paths: list[Path]) -> str:
    summary = summarize(rows)
    preferred_run_order = [
        "dpo_tiny_v1",
        "dpo_tiny_v2",
        "dpo_tiny_v3",
        "dpo_candidate_v4",
        "dpo_candidate_v5",
        "dpo_naive_v6",
        "dpo_v7_stage5h",
        "stage5k_sft_repair",
        "dpo_v8_stage5m",
        "stage5n_prompt7_micro_sft",
        "stage5o_prompt7_exact_sft",
        "stage5p_prompt7_balanced_sft",
    ]
    present_runs = {row["run_id"] for row in rows}
    run_order = [run_id for run_id in preferred_run_order if run_id in present_runs]
    run_order.extend(sorted(present_runs - set(run_order)))
    variant_order = ANSWER_KEYS
    table_lines = [
        "| Run | Variant | Passed Prompts | Total Score | Failed Areas |",
        "|---|---|---:|---:|---|",
    ]
    for run_id in run_order:
        for variant in variant_order:
            item = summary[(run_id, variant)]
            failures = ", ".join(item["failures"]) if item["failures"] else "-"
            table_lines.append(
                f"| {run_id} | `{variant}` | {item['passes']} / 8 | {item['total_score']} | {failures} |"
            )

    dpo_rows = [row for row in rows if row["variant"] == "dpo_tiny_answer"]
    dpo_lines = [
        "| Run | Prompt | Area | Score | Pass | Missing | Forbidden |",
        "|---|---:|---|---:|---|---|---|",
    ]
    for row in dpo_rows:
        missing = ", ".join(row["required_missing"]) if row["required_missing"] else "-"
        forbidden = ", ".join(row["forbidden_hits"]) if row["forbidden_hits"] else "-"
        dpo_lines.append(
            f"| {row['run_id']} | {row['prompt_index']} | {row['prompt_area']} | {row['score']} | {row['passed']} | {missing} | {forbidden} |"
        )
    input_lines = "\n".join(path.as_posix() for path in input_paths)

    return f"""# Stage 5 Structured Behavior Score Report

Date: 2026-05-16

## Scope

This report applies a transparent keyword-based scoring script to the fixed
prompt comparison outputs from Stage 5C, Stage 5C.2, Stage 5C.3, and any
candidate-derived follow-up runs included on the command line.

It is not an LLM judge. It is a reproducible gate helper that checks required
concepts and known-bad phrases for each fixed prompt.

Inputs:

```text
{input_lines}
```

Outputs:

```text
{jsonl_path.as_posix()}
{csv_path.as_posix()}
```

## Summary Table

{chr(10).join(table_lines)}

## DPO Candidate Prompt Scores

{chr(10).join(dpo_lines)}

## Decision

The structured scores support the manual Stage 5 decision:

- DPO-tiny v1 and v2 preserved several prompts, but both failed the
  public-SFT motivation and loss-vs-behavior gates.
- DPO-tiny v3 pushed harder but introduced broad regressions.
- Candidate-derived v4 recovered stability relative to v3 but still failed
  public-SFT motivation and loss-vs-behavior.
- Focused candidate v5 did not fix those two gates and weakened the
  loss-vs-behavior answer again.
- Larger naive v6 is the best DPO candidate so far at 7 / 8 prompts. It fixed
  public-SFT motivation, but still failed the core loss-vs-behavior gate.
- Stage 5H/5J/5M showed that larger prompt-7 preference data and exact-failure
  DPO-on-DPO repair can improve wording but still did not pass prompt 7.
- Stage 5K direct SFT repair is rejected because it regressed older prompts.
- Stage 5N stayed stable at 7 / 8 but still missed prompt 7; Stage 5O passed
  prompt 7 only by regressing older prompts; Stage 5P did not find a stable
  middle point.
- No DPO or SFT repair adapter has fully passed the fixed-prompt gate yet.
- Further training expansion remains blocked until prompt 7 can pass without
  old-prompt regression.

Recommended checkpoint remains:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```
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
    report_file.write_text(render_report(scored_rows, output_jsonl, output_csv, paths), encoding="utf-8")
    print(f"Wrote {len(scored_rows)} score rows to {output_jsonl}")
    print(f"Wrote CSV to {output_csv}")
    print(f"Wrote report to {report_file}")


if __name__ == "__main__":
    main()
