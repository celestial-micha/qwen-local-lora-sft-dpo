"""Prepare Stage 5 candidate-derived tiny DPO preference data.

This pass uses real failed DPO candidate outputs from Stage 5C/5C.2/5C.3 as
rejected answers. It also keeps a small held-out preference eval split so the
next DPO smoke run can report train and eval behavior rather than only whether
the adapter saves successfully.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


COMPARE_FILES = {
    "dpo_tiny_v1": Path("reports/compare_outputs_four_way_dpo_tiny.jsonl"),
    "dpo_tiny_v2": Path("reports/compare_outputs_four_way_dpo_tiny_v2.jsonl"),
    "dpo_tiny_v3": Path("reports/compare_outputs_four_way_dpo_tiny_v3.jsonl"),
}


CURATED_CHOSEN_BY_INDEX = {
    1: (
        "LoRA 在本项目里指 Low-Rank Adaptation，是一种参数高效微调方法。它通常冻结基础模型大部分权重，"
        "只在部分线性层旁边训练低秩 adapter，所以不是无线通信里的 LoRa，也不是重新训练整套模型。"
    ),
    2: (
        "SFT 是 supervised fine-tuning，核心是用 instruction-answer 样本让模型模仿目标回答。LoRA 是执行 SFT "
        "时的一种参数高效方式：基础模型冻结大部分参数，只训练少量 LoRA adapter。"
    ),
    3: (
        "SFT 学的是标准答案的模仿；DPO 学的是 chosen/rejected 偏好对，让模型更偏向 chosen、远离 rejected。"
        "工程上通常先用 SFT 建立基础回答能力，再用 DPO 做偏好对齐。"
    ),
    4: (
        "public-SFT adapter 的意义是先跑通公开数据训练、保存、加载和对比链路，作为可复现基线。它没有修正 "
        "LoRA/SFT/DPO 概念误解，说明公开通用 instruction 数据没有覆盖目标 badcase，所以 Stage 2B 需要自采集"
        "技术数据做定向修复，而不是从零建模或编造项目周期。"
    ),
    5: (
        "自采集技术数据应保留 source_id、标题、路径或 URL 等来源元数据，先清洗网页噪声、导航和广告，再去重、"
        "筛选，最后转换成 instruction-answer 或 Qwen chat JSONL，用固定 prompt 做回归检查。"
    ),
    6: (
        "DPO 比 SFT 更容易占显存，因为每个样本要同时处理 chosen/rejected，并且还涉及 reference policy 对比。"
        "8GB 显存下应先用 LoRA、小 batch、短 max_length/max_prompt_length 和少量 preference pairs 做 tiny smoke test；"
        "必要时才依赖共享内存，但不能把它当成行为通过的证据。"
    ),
    7: (
        "不能只看 loss。loss 是训练目标上的平均拟合信号，必要但不充分；一次 SFT 是否成功，还要看固定 prompt "
        "行为、目标 badcase 是否修好、旧能力是否回归。这个项目里 public-SFT 能跑通但仍误解 LoRA/SFT/DPO，"
        "所以必须把 loss 曲线和固定 prompt 对比一起作为验收。"
    ),
    8: (
        "面试里可以说：先用公开数据跑通可复现基线，确认训练、保存、加载和三方对比链路；Stage 4A 发现公开基线"
        "没修正目标概念 badcase；于是 Stage 2B 采集、清洗、去重并转换技术 instruction-answer 数据，再用固定 prompt "
        "回归验证。"
    ),
}


GUARDRAIL_PAIRS = [
    {
        "prompt": "面试里如何解释 LoRA，不要把它说成无线通信？",
        "chosen": CURATED_CHOSEN_BY_INDEX[1],
        "rejected": "LoRA 主要是 Long Range 无线通信技术，本项目训练的是让模型学会更稳定的 adapter state。",
        "source_type": "curated_guardrail",
    },
    {
        "prompt": "SFT 和 LoRA 在本项目中是什么关系？",
        "chosen": CURATED_CHOSEN_BY_INDEX[2],
        "rejected": "LoRA 是 SFT 的一个子网络结构，SFT 则是 DPO 后面自动生成的安全指标。",
        "source_type": "curated_guardrail",
    },
    {
        "prompt": "用一句话区分 SFT 和 DPO 的训练信号。",
        "chosen": CURATED_CHOSEN_BY_INDEX[3],
        "rejected": "DPO 是 Data Privacy Object，主要看数据保护是否完成；SFT 是安全框架指标。",
        "source_type": "curated_guardrail",
    },
    {
        "prompt": "为什么 public-SFT 是基线而不是最终答案？",
        "chosen": CURATED_CHOSEN_BY_INDEX[4],
        "rejected": "public-SFT adapter 用来补足 LoRA/SFT/DPO 的概念误解，所以 Stage 2B 是从零重新建模型。",
        "source_type": "curated_guardrail",
    },
    {
        "prompt": "为什么 DPO tiny smoke test 通过不等于可以直接扩大训练？",
        "chosen": (
            "tiny DPO 跑通只能说明显存、保存和加载链路可用。是否扩大训练还要看固定 prompt 行为："
            "目标 badcase 是否改善、public-SFT motivation 是否没有回归、旧能力是否稳定。"
        ),
        "rejected": "只要 DPO tiny 没有 OOM，就说明显存足够，行为问题可以等扩大训练后自动解决。",
        "source_type": "curated_guardrail",
    },
    {
        "prompt": "如何描述 DPO 的显存风险，避免编造数字？",
        "chosen": CURATED_CHOSEN_BY_INDEX[6],
        "rejected": "DPO 每个 epoch 只增加 0.1-0.2GB 显存，batch_size=4GB 就够了，所以不用太担心 OOM。",
        "source_type": "curated_guardrail",
    },
    {
        "prompt": "如果训练 loss 降了，为什么仍要看固定 prompt？",
        "chosen": CURATED_CHOSEN_BY_INDEX[7],
        "rejected": "DPO train loss 低就说明目标完成比例高，全量 loss 和 adapter loss 已经足够判断模型成功。",
        "source_type": "curated_guardrail",
    },
    {
        "prompt": "如何把这个项目的数据流程讲给面试官？",
        "chosen": CURATED_CHOSEN_BY_INDEX[8],
        "rejected": "主要讲 Hugging Face Tokenizers 和 SQL 大数据处理，base adapter 与 public adapter 安全开始即可。",
        "source_type": "curated_guardrail",
    },
]


EVAL_PAIRS = [
    {
        "prompt": "如果 public-SFT 跑通但还答错 LoRA/SFT/DPO，下一步应该怎么判断？",
        "chosen": (
            "应把它当作基线和 badcase 发现器：训练链路已经跑通，但目标概念没有被公开数据覆盖。下一步应进入 "
            "Stage 2B/Stage 5 的数据修复和固定 prompt 回归，而不是说 public-SFT 已经补足概念。"
        ),
        "rejected": "public-SFT 跑通说明 adapter 已经补足概念，后面只要扩大训练或重新从零建模即可。",
        "source_type": "heldout_eval",
    },
    {
        "prompt": "为什么 loss 下降后还可能需要 badcase review？",
        "chosen": (
            "loss 下降只是平均训练目标改善，不能保证目标 prompt 答对。badcase review 用来检查固定行为、概念修复"
            "和回归风险，尤其要看 public-SFT、custom-SFT、DPO 之间的输出对比。"
        ),
        "rejected": "loss 下降就说明项目成功，badcase review 只是在训练没跑通或显存 OOM 时才需要。",
        "source_type": "heldout_eval",
    },
    {
        "prompt": "DPO tiny 结果没 OOM，为什么仍然不能直接宣布成功？",
        "chosen": (
            "没 OOM 只证明运行资源基本可用。成功还需要 adapter 可加载、目标 prompt 改善、旧能力不回归，"
            "并且结构化评分和人工复盘都没有发现关键失败。"
        ),
        "rejected": "没 OOM 就说明 DPO 成功，行为检查可以等 full DPO 以后再做。",
        "source_type": "heldout_eval",
    },
    {
        "prompt": "讲 LoRA 时，哪两个点最容易说错？",
        "chosen": (
            "第一，不要把 LoRA 说成无线通信 LoRa；第二，不要说它重新训练全部参数。这里的 LoRA 是 Low-Rank "
            "Adaptation，通常冻结基础模型并训练少量低秩 adapter。"
        ),
        "rejected": "LoRA 是 Long Range 通信协议，在本项目里主要训练基础 adapter 的稳定 state。",
        "source_type": "heldout_eval",
    },
    {
        "prompt": "自采集技术数据为什么要保留来源元数据？",
        "chosen": (
            "来源元数据让样本可追溯、可清洗、可去重，也方便复盘哪些网页或文档贡献了 badcase 修复。"
            "后续转换成 instruction-answer 或 Qwen chat JSONL 时仍能定位问题来源。"
        ),
        "rejected": "来源元数据主要用于归一化表格字段，技术问答数据不需要保留网页路径或标题。",
        "source_type": "heldout_eval",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare candidate-derived Stage 5 DPO data.")
    parser.add_argument("--scores_file", default="reports/stage5_structured_behavior_scores.jsonl")
    parser.add_argument("--train_output", default="data/processed/dpo_candidate_train.jsonl")
    parser.add_argument("--eval_output", default="data/processed/dpo_candidate_eval.jsonl")
    parser.add_argument("--report_file", default="reports/stage5e_candidate_preference_data_report.md")
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


def score_lookup(scores: list[dict[str, Any]]) -> dict[tuple[str, str, int], dict[str, Any]]:
    lookup: dict[tuple[str, str, int], dict[str, Any]] = {}
    for row in scores:
        key = (str(row["run_id"]), str(row["variant"]), int(row["prompt_index"]))
        lookup[key] = row
    return lookup


def normalized_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "prompt": str(row["prompt"]).strip(),
        "chosen": str(row["chosen"]).strip(),
        "rejected": str(row["rejected"]).strip(),
        **{key: value for key, value in row.items() if key not in {"prompt", "chosen", "rejected"}},
    }


def add_unique(rows: list[dict[str, Any]], seen: set[tuple[str, str, str]], row: dict[str, Any]) -> None:
    item = normalized_row(row)
    key = (item["prompt"], item["chosen"], item["rejected"])
    if key in seen:
        return
    if not item["prompt"] or not item["chosen"] or not item["rejected"]:
        raise ValueError(f"Empty field in row: {item}")
    if item["chosen"] == item["rejected"]:
        raise ValueError(f"Chosen equals rejected for prompt: {item['prompt']}")
    seen.add(key)
    rows.append(item)


def build_train_rows(scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = score_lookup(scores)
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for run_id, compare_path in COMPARE_FILES.items():
        compare_rows = read_jsonl(compare_path)
        if len(compare_rows) != 8:
            raise ValueError(f"Expected 8 rows in {compare_path}, got {len(compare_rows)}")
        for prompt_index, compare_row in enumerate(compare_rows, start=1):
            dpo_score = lookup[(run_id, "dpo_tiny_answer", prompt_index)]
            if bool(dpo_score["passed"]):
                continue

            custom_score = lookup[(run_id, "custom_sft_v3_answer", prompt_index)]
            if bool(custom_score["passed"]):
                chosen = str(compare_row["custom_sft_v3_answer"]).strip()
                source_type = "failed_candidate_vs_custom_sft"
            else:
                chosen = CURATED_CHOSEN_BY_INDEX[prompt_index]
                source_type = "failed_candidate_vs_curated"

            add_unique(
                rows,
                seen,
                {
                    "prompt": compare_row["prompt"],
                    "chosen": chosen,
                    "rejected": compare_row["dpo_tiny_answer"],
                    "source_type": source_type,
                    "source_run": run_id,
                    "source_prompt_index": prompt_index,
                    "source_score": dpo_score["score"],
                    "source_forbidden": dpo_score["forbidden_hits"],
                },
            )

    # The current recommended SFT adapter also fails the loss-vs-behavior prompt.
    # Keep that single known gap in the preference set without changing the
    # recommended base checkpoint for DPO.
    first_compare = read_jsonl(next(iter(COMPARE_FILES.values())))
    prompt_index = 7
    add_unique(
        rows,
        seen,
        {
            "prompt": first_compare[prompt_index - 1]["prompt"],
            "chosen": CURATED_CHOSEN_BY_INDEX[prompt_index],
            "rejected": first_compare[prompt_index - 1]["custom_sft_v3_answer"],
            "source_type": "custom_sft_known_gap_vs_curated",
            "source_run": "custom_sft_v3",
            "source_prompt_index": prompt_index,
        },
    )

    for pair in GUARDRAIL_PAIRS:
        add_unique(rows, seen, pair)
    return rows


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


def render_report(train_rows: list[dict[str, Any]], eval_rows: list[dict[str, Any]], train_output: Path, eval_output: Path) -> str:
    train_counter = Counter(str(row.get("source_type", "unknown")) for row in train_rows)
    prompt_lengths = [len(str(row["prompt"])) for row in train_rows]
    chosen_lengths = [len(str(row["chosen"])) for row in train_rows]
    rejected_lengths = [len(str(row["rejected"])) for row in train_rows]
    source_lines = ["| Source Type | Rows |", "|---|---:|"]
    for source_type, count in sorted(train_counter.items()):
        source_lines.append(f"| `{source_type}` | {count} |")

    return f"""# Stage 5E Candidate Preference Data Report

Date: 2026-05-16

## Scope

This data step prepares a smaller Stage 5 DPO retry based on actual failed
candidate outputs from:

```text
reports/compare_outputs_four_way_dpo_tiny.jsonl
reports/compare_outputs_four_way_dpo_tiny_v2.jsonl
reports/compare_outputs_four_way_dpo_tiny_v3.jsonl
```

The goal is to teach against concrete failures, while preserving the current
recommended SFT adapter as the DPO starting point:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
```

## Outputs

```text
{train_output.as_posix()}
{eval_output.as_posix()}
```

## Dataset Summary

- Train rows: {len(train_rows)}
- Eval rows: {len(eval_rows)}
- Train unique prompts: {len(set(str(row["prompt"]) for row in train_rows))}
- Train prompt length min/avg/max chars: {stats(prompt_lengths)}
- Train chosen length min/avg/max chars: {stats(chosen_lengths)}
- Train rejected length min/avg/max chars: {stats(rejected_lengths)}

## Train Sources

{chr(10).join(source_lines)}

## Design Notes

- Failed DPO v1/v2/v3 outputs become rejected answers directly.
- Passing custom-SFT v3 answers are used as chosen answers where they already
  pass the structured gate.
- The known custom-SFT v3 loss-vs-behavior gap uses a curated chosen answer.
- Held-out eval pairs cover public-SFT motivation, loss-vs-behavior, DPO smoke
  interpretation, LoRA definition, and data-source metadata.

Next step: run Stage 5B.4 with an eval split and keep it blocked unless the
behavior comparison improves without broad regressions.
"""


def main() -> None:
    args = parse_args()
    scores = read_jsonl(Path(args.scores_file))
    train_rows = build_train_rows(scores)
    eval_rows = [normalized_row(row) for row in EVAL_PAIRS]
    validate(train_rows, "train")
    validate(eval_rows, "eval")
    train_output = Path(args.train_output)
    eval_output = Path(args.eval_output)
    report_file = Path(args.report_file)
    write_jsonl(train_output, train_rows)
    write_jsonl(eval_output, eval_rows)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(render_report(train_rows, eval_rows, train_output, eval_output), encoding="utf-8")
    print(f"Wrote {len(train_rows)} candidate-derived train rows to {train_output}")
    print(f"Wrote {len(eval_rows)} held-out eval rows to {eval_output}")
    print(f"Wrote report to {report_file}")


if __name__ == "__main__":
    main()
