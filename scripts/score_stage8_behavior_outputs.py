"""Score Stage 8 expanded behavior outputs with transparent keyword gates."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Criterion:
    name: str
    any_of: tuple[str, ...]


@dataclass(frozen=True)
class AreaRubric:
    prompt_area: str
    required: tuple[Criterion, ...]
    forbidden: tuple[Criterion, ...]
    min_score_to_pass: int = 3
    max_forbidden_to_pass: int = 0


AREA_RUBRICS: dict[str, AreaRubric] = {
    "LoRA 定义与边界": AreaRubric(
        prompt_area="LoRA 定义与边界",
        required=(
            Criterion("lora", ("LoRA", "低秩适配", "Low-Rank")),
            Criterion("parameter efficient", ("参数高效", "少量参数", "小规模参数")),
            Criterion("adapter", ("adapter", "适配器")),
            Criterion("frozen base", ("冻结", "基础模型大部分", "不更新全部")),
            Criterion("not wireless", ("不是无线通信", "不要解释成无线通信", "无线通信 LoRa")),
        ),
        forbidden=(
            Criterion("wireless as main concept", ("远距离通信协议", "无线通信协议", "Long Range")),
            Criterion("full fine-tune claim", ("全量重训", "重新训练全部参数")),
        ),
        min_score_to_pass=4,
    ),
    "SFT 与 LoRA 关系": AreaRubric(
        prompt_area="SFT 与 LoRA 关系",
        required=(
            Criterion("sft supervised", ("SFT", "有监督微调", "supervised fine-tuning")),
            Criterion("objective/data", ("训练目标", "数据形式", "instruction-answer", "chat")),
            Criterion("lora method", ("LoRA", "参数高效", "adapter")),
            Criterion("relationship", ("用 LoRA", "执行 SFT", "目标", "方法")),
        ),
        forbidden=(
            Criterion("wrong expansion", ("Shortest", "Flipping Time", "网络安全缩写")),
            Criterion("mutual exclusion", ("互斥", "不能一起使用")),
        ),
        min_score_to_pass=4,
    ),
    "DPO 与 SFT 区别": AreaRubric(
        prompt_area="DPO 与 SFT 区别",
        required=(
            Criterion("sft answer imitation", ("SFT", "标准答案", "模仿", "instruction-answer")),
            Criterion("dpo preference", ("DPO", "偏好", "preference")),
            Criterion("chosen rejected", ("chosen", "rejected", "偏好对")),
            Criterion("sft first", ("先做 SFT", "基础回答能力", "基础能力")),
        ),
        forbidden=(
            Criterion("data preprocessing", ("Data Preprocessing", "数据预处理")),
            Criterion("data protection", ("数据保护", "Data Privacy")),
        ),
        min_score_to_pass=4,
    ),
    "public-SFT 诊断价值": AreaRubric(
        prompt_area="public-SFT 诊断价值",
        required=(
            Criterion("public baseline", ("public-SFT", "公开数据", "基线", "baseline")),
            Criterion("engineering proof", ("训练", "保存", "加载", "链路", "跑通")),
            Criterion("not fixed", ("没有修正", "没修正", "仍", "不等于")),
            Criterion("stage2b", ("Stage 2B", "自采集", "技术数据", "定向")),
        ),
        forbidden=(
            Criterion("from scratch", ("从零训练完整模型", "从零重训")),
            Criterion("overclaim fixed", ("全部修好", "彻底解决")),
            Criterion("invented duration", ("三到六个月", "很多个月")),
        ),
        min_score_to_pass=4,
    ),
    "自采集技术数据管线": AreaRubric(
        prompt_area="自采集技术数据管线",
        required=(
            Criterion("source metadata", ("source_id", "来源", "标题", "URL", "metadata")),
            Criterion("clean", ("清洗", "网页噪声", "广告", "导航")),
            Criterion("dedup filter", ("去重", "筛选")),
            Criterion("instruction conversion", ("instruction-answer", "问答", "chat JSONL")),
            Criterion("split", ("train", "eval", "held-out", "验证集")),
        ),
        forbidden=(
            Criterion("tabular only", ("缺失值填充", "标准化", "归一化")),
            Criterion("raw web dump", ("网页全文直接", "直接塞进训练集")),
        ),
        min_score_to_pass=4,
    ),
    "DPO 显存风险": AreaRubric(
        prompt_area="DPO 显存风险",
        required=(
            Criterion("chosen rejected", ("chosen", "rejected", "偏好对")),
            Criterion("reference", ("reference", "参考模型", "reference policy")),
            Criterion("memory risk", ("显存", "8GB", "OOM", "共享内存")),
            Criterion("mitigation", ("小 batch", "batch_size=1", "短 max_length", "LoRA", "少量")),
            Criterion("smoke boundary", ("smoke", "可跑不等于", "不证明行为质量")),
        ),
        forbidden=(
            Criterion("no oom equals quality", ("无 OOM 就说明质量", "跑通就代表成功")),
            Criterion("fabricated memory", ("batch_size=4GB", "每 epoch 0.1GB")),
        ),
        min_score_to_pass=4,
    ),
    "loss 与行为验收": AreaRubric(
        prompt_area="loss 与行为验收",
        required=(
            Criterion("loss signal", ("loss", "平均", "训练目标", "优化信号", "指标")),
            Criterion("not sufficient", ("不充分", "必要但不充分", "不能只看", "不够")),
            Criterion("fixed behavior", ("固定 prompt", "固定问题", "行为", "输出")),
            Criterion("badcase regression", ("badcase", "坏例", "回归", "旧能力")),
            Criterion("project example", ("public-SFT", "DPO", "preference accuracy", "LoRA/SFT/DPO")),
        ),
        forbidden=(
            Criterion("loss only", ("只要 loss", "loss 降低就说明", "loss 好看就")),
            Criterion("preference only", ("preference accuracy 到 1.0 就说明",)),
            Criterion("loss useless", ("loss 完全没有意义",)),
        ),
        min_score_to_pass=4,
    ),
    "固定 Prompt 与扩展评测": AreaRubric(
        prompt_area="固定 Prompt 与扩展评测",
        required=(
            Criterion("fixed comparable", ("固定 prompt", "同一批", "同题", "可比")),
            Criterion("expanded heldout", ("扩展", "held-out", "改写", "96")),
            Criterion("scoring", ("结构化评分", "required", "forbidden", "评分")),
            Criterion("regression", ("回归", "旧能力", "regression")),
        ),
        forbidden=(
            Criterion("single prompt enough", ("只测一条", "一个 prompt 就")),
            Criterion("pilot as benchmark", ("8 题就是完整 benchmark", "7/8 就是大评测")),
        ),
        min_score_to_pass=3,
    ),
    "checkpoint 选择与拒绝理由": AreaRubric(
        prompt_area="checkpoint 选择与拒绝理由",
        required=(
            Criterion("checkpoint", ("checkpoint", "adapter", "模型")),
            Criterion("behavior stable", ("稳定", "行为", "固定 prompt")),
            Criterion("reject regression", ("拒绝", "回归", "旧题")),
            Criterion("not metric only", ("不能只看", "loss", "preference accuracy")),
        ),
        forbidden=(
            Criterion("metric only accept", ("只因为 eval loss", "只因为 preference accuracy")),
        ),
        min_score_to_pass=3,
    ),
    "面试叙事与边界": AreaRubric(
        prompt_area="面试叙事与边界",
        required=(
            Criterion("pipeline", ("链路", "闭环", "数据")),
            Criterion("pilot boundary", ("pilot", "7/8", "旧结果", "边界")),
            Criterion("stage8 scale", ("1500", "160", "96", "Stage 8")),
            Criterion("honesty", ("不能", "不要", "重新评测", "重新训练")),
        ),
        forbidden=(
            Criterion("mix old and new", ("旧 checkpoint 已经在 96", "直接当作 Stage 8 通过率")),
        ),
        min_score_to_pass=3,
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score Stage 8 behavior comparison outputs.")
    parser.add_argument("--input_file", required=True)
    parser.add_argument("--output_jsonl", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--report_file", required=True)
    parser.add_argument("--run_id", default=None)
    return parser.parse_args()


def criterion_hit(answer: str, criterion: Criterion) -> bool:
    lowered = answer.lower()
    return any(fragment.lower() in lowered for fragment in criterion.any_of)


NEGATION_MARKERS = (
    "不是",
    "不能",
    "不要",
    "不应",
    "避免",
    "错误说法",
    "错误理解",
    "误区",
    "wrong",
    "not",
    "do not",
    "should not",
)


def criterion_forbidden_hit(answer: str, criterion: Criterion) -> bool:
    lowered = answer.lower()
    for fragment in criterion.any_of:
        needle = fragment.lower()
        start = 0
        while True:
            index = lowered.find(needle, start)
            if index < 0:
                break
            left_context = lowered[max(0, index - 24) : index]
            if not any(marker.lower() in left_context for marker in NEGATION_MARKERS):
                return True
            start = index + len(needle)
    return False


def answer_keys(row: dict[str, Any]) -> list[str]:
    keys = [key for key in row if key.endswith("_answer")]
    if not keys:
        raise ValueError("No *_answer keys found in comparison row")
    return keys


def score_answer(prompt_area: str, answer: str) -> dict[str, Any]:
    if prompt_area not in AREA_RUBRICS:
        raise ValueError(f"No rubric for prompt_area={prompt_area!r}")
    rubric = AREA_RUBRICS[prompt_area]
    required_hits = [criterion.name for criterion in rubric.required if criterion_hit(answer, criterion)]
    required_missing = [criterion.name for criterion in rubric.required if not criterion_hit(answer, criterion)]
    forbidden_hits = [
        criterion.name for criterion in rubric.forbidden if criterion_forbidden_hit(answer, criterion)
    ]
    score = len(required_hits) - 2 * len(forbidden_hits)
    passed = score >= rubric.min_score_to_pass and len(forbidden_hits) <= rubric.max_forbidden_to_pass
    return {
        "score": score,
        "passed": passed,
        "required_hits": required_hits,
        "required_missing": required_missing,
        "forbidden_hits": forbidden_hits,
    }


def read_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if "prompt" not in row or "prompt_area" not in row:
                raise ValueError(f"Missing prompt/prompt_area in {path}:{line_no}")
            rows.append(row)
    if not rows:
        raise ValueError(f"No rows loaded from {path}")
    return rows


def build_score_rows(input_file: Path, run_id: str | None) -> list[dict[str, Any]]:
    rows = read_rows(input_file)
    keys = answer_keys(rows[0])
    scored: list[dict[str, Any]] = []
    actual_run_id = run_id or input_file.stem
    for index, row in enumerate(rows, start=1):
        prompt_area = str(row["prompt_area"]).strip()
        for key in keys:
            result = score_answer(prompt_area, str(row[key]))
            scored.append(
                {
                    "run_id": actual_run_id,
                    "source_file": input_file.as_posix(),
                    "prompt_index": index,
                    "prompt_id": row.get("prompt_id", f"row_{index:03d}"),
                    "prompt_area": prompt_area,
                    "variant": key,
                    "score": result["score"],
                    "passed": result["passed"],
                    "required_hits": result["required_hits"],
                    "required_missing": result["required_missing"],
                    "forbidden_hits": result["forbidden_hits"],
                    "prompt": row["prompt"],
                    "answer": row[key],
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
        "prompt_id",
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
                    "prompt_id": row["prompt_id"],
                    "prompt_area": row["prompt_area"],
                    "variant": row["variant"],
                    "score": row["score"],
                    "passed": row["passed"],
                    "required_missing": "; ".join(row["required_missing"]),
                    "forbidden_hits": "; ".join(row["forbidden_hits"]),
                }
            )


def summarize(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for row in rows:
        variant = str(row["variant"])
        area = str(row["prompt_area"])
        item = summary.setdefault(
            variant,
            {
                "passes": 0,
                "count": 0,
                "total_score": 0,
                "area": {},
                "failures": [],
            },
        )
        item["count"] += 1
        item["passes"] += int(bool(row["passed"]))
        item["total_score"] += int(row["score"])
        area_item = item["area"].setdefault(area, {"passes": 0, "count": 0})
        area_item["count"] += 1
        area_item["passes"] += int(bool(row["passed"]))
        if not row["passed"]:
            item["failures"].append(
                f"{row['prompt_id']}[{area}] missing={','.join(row['required_missing']) or '-'}"
            )
    return summary


def render_report(rows: list[dict[str, Any]], jsonl_path: Path, csv_path: Path) -> str:
    summary = summarize(rows)
    table = ["| Variant | Passed | Total Score | Weakest Areas |", "|---|---:|---:|---|"]
    for variant, item in sorted(summary.items()):
        weak_areas = []
        for area, area_item in sorted(item["area"].items()):
            if area_item["passes"] < area_item["count"]:
                weak_areas.append(f"{area} {area_item['passes']}/{area_item['count']}")
        table.append(
            f"| `{variant}` | {item['passes']} / {item['count']} | {item['total_score']} | "
            f"{', '.join(weak_areas) if weak_areas else '-'} |"
        )

    detail = ["| Variant | Prompt ID | Area | Score | Missing | Forbidden |", "|---|---|---|---:|---|---|"]
    for row in rows:
        if row["passed"]:
            continue
        missing = ", ".join(row["required_missing"]) if row["required_missing"] else "-"
        forbidden = ", ".join(row["forbidden_hits"]) if row["forbidden_hits"] else "-"
        detail.append(
            f"| `{row['variant']}` | {row['prompt_id']} | {row['prompt_area']} | "
            f"{row['score']} | {missing} | {forbidden} |"
        )

    return f"""# Stage 8 Expanded Behavior Score Report

Date: 2026-07-03

## Scope

This report scores Stage 8 expanded behavior outputs with transparent
keyword-based gates. It is a reproducible helper, not a final LLM judge.
Failures should be reviewed manually before data patching.

Outputs:

```text
{jsonl_path.as_posix()}
{csv_path.as_posix()}
```

## Summary

{chr(10).join(table)}

## Failed Checks

{chr(10).join(detail)}
"""


def main() -> None:
    args = parse_args()
    scored = build_score_rows(Path(args.input_file), args.run_id)
    output_jsonl = Path(args.output_jsonl)
    output_csv = Path(args.output_csv)
    report_file = Path(args.report_file)
    write_jsonl(output_jsonl, scored)
    write_csv(output_csv, scored)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(render_report(scored, output_jsonl, output_csv), encoding="utf-8")
    print(f"Wrote {len(scored)} score rows to {output_jsonl}")
    print(f"Wrote CSV to {output_csv}")
    print(f"Wrote report to {report_file}")


if __name__ == "__main__":
    main()
