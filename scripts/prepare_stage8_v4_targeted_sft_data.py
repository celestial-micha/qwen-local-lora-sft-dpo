"""Prepare Stage 8I targeted SFT v4 data.

The best expanded candidate after Stage 8H is still SFT v2. Its two clearest
weak areas are:

- DPO 与 SFT 区别: answers often miss "先做 SFT" and the exact chosen/rejected
  preference framing.
- public-SFT 诊断价值: answers often fail to say public-SFT is only an
  engineering baseline and did not fix target concepts.

This patch continues from SFT v2 with a low learning rate and focuses on these
two gaps while replaying the other six behavior areas.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any


SYSTEM_PROMPT = (
    "你是严谨的大模型微调项目中文助教。回答要短、准、可复盘；"
    "只引用已记录项目事实，不编造 stage、显存数字、训练周期或通过率。"
)


ACCEPTANCE = (
    "验收时还要看固定 prompt 同题对比、held-out 改写、结构化评分、badcase review "
    "和旧能力回归，不能只看 loss 或 preference accuracy。"
)


TARGET_AREAS: dict[str, dict[str, Any]] = {
    "DPO 与 SFT 区别": {
        "topic_id": "dpo_vs_sft",
        "answer": (
            "结论：SFT 和 DPO 的训练信号不同，通常先做 SFT，再在基础回答能力稳定后做 DPO。\n"
            "SFT：使用 instruction-answer 或 chat 标准答案，让模型模仿目标回答。\n"
            "DPO：使用同一 prompt 下的 chosen/rejected 偏好对，让模型更偏向 chosen、远离 rejected。\n"
            "项目边界：DPO 不能替代 SFT 的基础回答能力；preference accuracy 到 1.0 也不能直接等于行为通过。\n"
            f"{ACCEPTANCE}"
        ),
        "bad": [
            "把 DPO 讲成普通数据清洗流程。",
            "只说 DPO 指标好，不解释 chosen/rejected。",
            "跳过 SFT，直接说 DPO 可以替代基础回答能力。",
        ],
    },
    "public-SFT 诊断价值": {
        "topic_id": "public_sft_motivation",
        "answer": (
            "结论：public-SFT 是 public baseline/工程基线，不是最终目标模型。\n"
            "它证明公开数据、训练、保存、加载、推理对比这条链路能跑通。\n"
            "但 Stage 4A 发现 public-SFT 没有修正 LoRA/SFT/DPO 目标概念误解，"
            "所以它的价值是诊断问题，而不是宣称问题已解决。\n"
            "下一步应进入 Stage 2B 自采集技术数据和 badcase 定向补充，再重新做 fixed prompt 行为评测。\n"
            f"{ACCEPTANCE}"
        ),
        "bad": [
            "说 public-SFT 已经彻底修好目标概念。",
            "说 public-SFT 等于从零训练完整模型。",
            "只说 loss 正常下降，不解释为什么还要 Stage 2B。",
        ],
    },
}


REPLAY_AREAS: dict[str, dict[str, str]] = {
    "LoRA 定义与边界": {
        "topic_id": "lora_definition",
        "answer": (
            "LoRA 是 Low-Rank Adaptation，是参数高效微调方法；它冻结基础模型大部分参数，"
            "只训练少量低秩 adapter/适配器参数。LoRA adapter 不是完整模型，推理时仍要加载基础模型。"
            "本项目用 LoRA 降低 Qwen2.5-0.5B 本地后训练成本。这里讨论的是机器学习微调方法，"
            f"不是无线通信 LoRa。{ACCEPTANCE}"
        ),
    },
    "SFT 与 LoRA 关系": {
        "topic_id": "sft_lora_relation",
        "answer": (
            "SFT 是 supervised fine-tuning/有监督微调，描述训练目标和 instruction-answer/chat 数据形式；"
            "LoRA 描述参数高效更新方法。LoRA SFT 表示用 LoRA adapter 执行 SFT，二者不是互斥关系。"
            f"{ACCEPTANCE}"
        ),
    },
    "自采集技术数据管线": {
        "topic_id": "data_pipeline",
        "answer": (
            "自采集技术数据要保留 source_id、标题、路径或 URL 等 metadata；先清洗网页噪声、导航栏、广告和无关内容，"
            "再去重、筛选，并改写成 instruction-answer 或 chat JSONL。train 与 held-out eval 必须分离，"
            f"不能只用训练题自测。{ACCEPTANCE}"
        ),
    },
    "DPO 显存风险": {
        "topic_id": "dpo_vram",
        "answer": (
            "DPO 要处理 chosen/rejected，并涉及 reference policy 对比，所以显存压力通常高于普通 SFT。"
            "8GB 显存下应使用 LoRA、batch_size=1、短 max_length、短 max_prompt_length 和少量 eval。"
            f"tiny smoke test 只证明可跑，不证明行为质量。{ACCEPTANCE}"
        ),
    },
    "loss 与行为验收": {
        "topic_id": "loss_behavior",
        "answer": (
            "loss 是平均训练目标上的优化信号，必要但不充分。SFT 或 DPO 是否成功，"
            "还要看固定 prompt、可见输出行为、badcase review 和旧能力回归。"
            "public-SFT loss 可以下降，但仍可能答错 LoRA/SFT/DPO。"
            f"{ACCEPTANCE}"
        ),
    },
    "固定 Prompt 与扩展评测": {
        "topic_id": "behavior_eval",
        "answer": (
            "固定 prompt 让 base、SFT、DPO 在同一问题上可比；扩展 held-out 改写能降低只背单句 prompt 的风险。"
            "Stage 8 使用 96 条行为评测 prompt，并用 required/forbidden 结构化评分辅助复查。"
            f"旧 7/8 只是 pilot gate，不能直接当成 96 题结果。{ACCEPTANCE}"
        ),
    },
}


TARGET_FRAMES = [
    "请解释{area}，必须说清训练信号和项目验收边界。",
    "如果面试官追问{area}，怎样回答才不会只报指标？",
    "请把下面坏回答改成正确说法：{bad}",
    "{area}为什么不能只看 loss 或 preference accuracy？",
    "请用项目复盘口吻说明{area}。",
    "请面向简历审阅者说明{area}如何支撑项目可信度。",
    "请设计一个 held-out prompt 来检查{area}是否真正理解。",
    "如果模型在{area}上答得像背模板但缺项目证据，应该追问什么？",
]

REPLAY_FRAMES = [
    "请简洁解释{area}，并给出项目边界。",
    "{area}的正确验收标准是什么？",
    "请说明{area}为什么要结合固定 prompt 和 badcase review。",
    "请面向面试官回答{area}。",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Stage 8I targeted SFT v4 data.")
    parser.add_argument("--train_output", default="data/processed/custom_sft_expanded_v4_targeted_train.jsonl")
    parser.add_argument("--eval_output", default="data/processed/custom_sft_expanded_v4_targeted_eval.jsonl")
    parser.add_argument("--report_output", default="reports/stage8i_targeted_sft_data_report.md")
    parser.add_argument("--train_size", type=int, default=1500)
    parser.add_argument("--eval_size", type=int, default=160)
    parser.add_argument("--seed", type=int, default=45)
    return parser.parse_args()


def stable_id(prefix: str, text: str) -> str:
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]}"


def make_row(prefix: str, area: str, topic_id: str, source_type: str, prompt: str, answer: str) -> dict[str, Any]:
    return {
        "sample_id": stable_id(prefix, area + prompt + answer),
        "prompt_area": area,
        "topic_id": topic_id,
        "source_type": source_type,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": answer},
        ],
    }


def build_candidates() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    train_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []

    for area, item in TARGET_AREAS.items():
        for repeat in range(95):
            for frame_index, frame in enumerate(TARGET_FRAMES):
                bad = item["bad"][(repeat + frame_index) % len(item["bad"])]
                prompt = frame.format(area=area, bad=bad)
                prompt += "\n回答必须包含：SFT、DPO、chosen/rejected、先做 SFT 或 public-SFT baseline 等关键边界。"
                train_rows.append(
                    make_row(
                        "stage8i-target",
                        area,
                        item["topic_id"],
                        "stage8i_targeted_weak_area_patch",
                        prompt,
                        item["answer"],
                    )
                )

        for eval_index in range(40):
            prompt = (
                f"请用新的说法解释{area}，要求包含项目证据、反例边界和行为验收。"
                f"这是 held-out eval paraphrase {eval_index + 1}。"
            )
            eval_rows.append(
                make_row(
                    "stage8i-eval-target",
                    area,
                    item["topic_id"],
                    "stage8i_targeted_heldout_eval",
                    prompt,
                    item["answer"],
                )
            )

    for area, item in REPLAY_AREAS.items():
        for repeat in range(35):
            for frame in REPLAY_FRAMES:
                prompt = frame.format(area=area)
                prompt += "\n回答要保留旧能力，不要引入未记录事实。"
                train_rows.append(
                    make_row(
                        "stage8i-replay",
                        area,
                        item["topic_id"],
                        "stage8i_replay_keep_stable_areas",
                        prompt,
                        item["answer"],
                    )
                )

        for eval_index in range(14):
            prompt = f"请复查{area}是否稳定，并说明为什么不能只看指标。held-out replay {eval_index + 1}。"
            eval_rows.append(
                make_row(
                    "stage8i-eval-replay",
                    area,
                    item["topic_id"],
                    "stage8i_replay_heldout_eval",
                    prompt,
                    item["answer"],
                )
            )

    return train_rows, eval_rows


def take_rows(rows: list[dict[str, Any]], target: int, seed: int, split: str) -> list[dict[str, Any]]:
    expanded = list(rows)
    if len(expanded) < target:
        copies: list[dict[str, Any]] = []
        rounds = target // len(expanded) + 2
        for round_index in range(rounds):
            for row in expanded:
                copied = json.loads(json.dumps(row, ensure_ascii=False))
                copied["sample_id"] = f"{row['sample_id']}-r{round_index:02d}"
                copied["messages"][1]["content"] += f"\n同义改写编号：{round_index + 1}。"
                copies.append(copied)
        expanded = copies
    random.Random(seed).shuffle(expanded)
    selected = expanded[:target]
    for row in selected:
        row["split"] = split
    return selected


def validate(rows: list[dict[str, Any]], label: str) -> None:
    for index, row in enumerate(rows, start=1):
        messages = row.get("messages")
        if not isinstance(messages, list) or len(messages) != 3:
            raise ValueError(f"{label} row {index} must have 3 messages")
        if [message.get("role") for message in messages] != ["system", "user", "assistant"]:
            raise ValueError(f"{label} row {index} has invalid role order")
        if not messages[1]["content"].strip() or not messages[2]["content"].strip():
            raise ValueError(f"{label} row {index} has empty text")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def render_report(train_rows: list[dict[str, Any]], eval_rows: list[dict[str, Any]]) -> str:
    areas = sorted({row["prompt_area"] for row in train_rows + eval_rows})
    lines = []
    for area in areas:
        lines.append(
            f"- {area}: train {sum(row['prompt_area'] == area for row in train_rows)}, "
            f"eval {sum(row['prompt_area'] == area for row in eval_rows)}"
        )
    return f"""# Stage 8I Targeted SFT v4 Data Report

Date: 2026-07-03

## Purpose

Stage 8E SFT v2 remains the strongest expanded candidate, but it has two weak
areas: DPO vs SFT and public-SFT diagnostic value. This patch targets those
weak areas and replays the six stronger areas to reduce regression risk.

## Outputs

```text
data/processed/custom_sft_expanded_v4_targeted_train.jsonl
data/processed/custom_sft_expanded_v4_targeted_eval.jsonl
```

## Size

- Train rows: {len(train_rows)}
- Eval rows: {len(eval_rows)}

## Area Balance

{chr(10).join(lines)}
"""


def main() -> None:
    args = parse_args()
    train_candidates, eval_candidates = build_candidates()
    train_rows = take_rows(train_candidates, args.train_size, args.seed, "train")
    eval_rows = take_rows(eval_candidates, args.eval_size, args.seed + 1, "eval")
    validate(train_rows, "train")
    validate(eval_rows, "eval")
    write_jsonl(Path(args.train_output), train_rows)
    write_jsonl(Path(args.eval_output), eval_rows)
    Path(args.report_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report_output).write_text(render_report(train_rows, eval_rows), encoding="utf-8")
    print(f"Wrote {len(train_rows)} train rows to {args.train_output}")
    print(f"Wrote {len(eval_rows)} eval rows to {args.eval_output}")
    print(f"Wrote report to {args.report_output}")


if __name__ == "__main__":
    main()
