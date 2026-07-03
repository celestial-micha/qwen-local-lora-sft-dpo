"""Prepare Stage 8F fact-guard SFT v3 data.

Stage 8E improved the expanded behavior score, but manual review still found
project-fact drift: invented stage numbers, invented hardware facts, and some
answers that repeated a bad concept while trying to warn against it.

This dataset is intentionally conservative:

- compact answers with stable wording;
- no made-up stage IDs, dates, durations, pass rates, or memory numbers;
- direct coverage of the 8 behavior-eval areas;
- correction rows for hallucination and old-capability regression.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any


SYSTEM_PROMPT = (
    "你是一个严谨的大模型微调项目中文助教。回答必须基于已记录项目事实；"
    "如果没有记录，不要编造 stage 号、月份、训练周期、显存数字、通过率或新结论。"
)


COMMON_ACCEPTANCE = (
    "验收时要看固定 prompt 同题对比、held-out 改写、required/forbidden 结构化评分、"
    "人工 badcase review 和旧能力回归检查；不能只看 loss 或 preference accuracy。"
)


AREAS: dict[str, dict[str, Any]] = {
    "LoRA 定义与边界": {
        "topic_id": "lora_definition",
        "one_liner": "LoRA 是 Low-Rank Adaptation，是一种参数高效微调方法。",
        "points": [
            "冻结基础模型大部分参数，只训练少量低秩 adapter/适配器参数。",
            "LoRA adapter 不是完整模型，推理时仍要加载基础模型。",
            "这里讨论的是机器学习微调方法，不是无线通信里的 LoRa。",
        ],
        "project": [
            "本项目用 LoRA 在本地单卡上降低 Qwen2.5-0.5B 后训练成本。",
            "public-SFT、custom-SFT 和 DPO 都围绕 adapter 保存、加载和推理验证展开。",
        ],
        "bad": [
            "把 LoRA 当成通信协议或网络路由概念。",
            "说 adapter 可以脱离基础模型单独推理。",
            "说 LoRA 会重新训练基础模型全部参数。",
        ],
    },
    "SFT 与 LoRA 关系": {
        "topic_id": "sft_lora_relation",
        "one_liner": "SFT 是 supervised fine-tuning，LoRA 是参数高效更新方法，二者不是互斥关系。",
        "points": [
            "SFT 描述训练目标和 instruction-answer/chat 数据形式。",
            "LoRA 描述如何用较少可训练参数完成微调。",
            "LoRA SFT 表示用 LoRA adapter 执行 SFT。",
        ],
        "project": [
            "本项目先用 public LoRA SFT 验证链路，再用 custom LoRA SFT 修正目标概念。",
            "固定 prompt 对比用于检查 SFT 后回答行为是否真的改善。",
        ],
        "bad": [
            "把 SFT 解释成网络安全缩写。",
            "说 LoRA 和 SFT 不能一起使用。",
            "把 LoRA SFT 说成先做 DPO 再训练通信协议。",
        ],
    },
    "DPO 与 SFT 区别": {
        "topic_id": "dpo_vs_sft",
        "one_liner": "SFT 学标准答案，DPO 学 chosen/rejected preference pair 中的偏好方向。",
        "points": [
            "SFT 使用 instruction-answer 或 chat 样本，让模型模仿目标回答。",
            "DPO 使用同一 prompt 下的 chosen/rejected 偏好对。",
            "通常先做 SFT，让基础回答稳定后再做 DPO。",
        ],
        "project": [
            "本项目在 custom-SFT 稳定后尝试 tiny DPO 和 separate-reference DPO。",
            "DPO 指标好看仍要回到固定行为 gate 做复查。",
        ],
        "bad": [
            "把 DPO 当成普通数据预处理流程。",
            "把 DPO 当成数据隐私保护对象。",
            "只因 preference accuracy 高就接受 checkpoint。",
        ],
    },
    "public-SFT 诊断价值": {
        "topic_id": "public_sft_motivation",
        "one_liner": "public-SFT 是工程 baseline，不是最终目标模型。",
        "points": [
            "它证明公开数据、训练、保存、加载和推理对比链路能跑通。",
            "它没有自动修正 LoRA/SFT/DPO 目标概念误解。",
            "失败结果推动自采集技术数据和 badcase 数据补充。",
        ],
        "project": [
            "本项目用 public-SFT 先验证训练链路，再进入 custom-SFT。",
            "public-SFT 的诊断价值在于暴露目标领域行为没有被解决。",
        ],
        "bad": [
            "说 public-SFT 已经彻底修好所有目标概念。",
            "说 public-SFT 等于从零训练完整模型。",
            "编造未记录的训练周期或项目工期。",
        ],
    },
    "自采集技术数据管线": {
        "topic_id": "data_pipeline",
        "one_liner": "自采集数据要保留来源、清洗去噪、去重筛选，再转成训练格式并分离评测集。",
        "points": [
            "记录 source_id、标题、路径或 URL 等 source metadata。",
            "清理网页噪声、导航栏、广告、重复空白和无关内容。",
            "清洗后去重筛选，改写成 instruction-answer 或 Qwen chat JSONL。",
            "train 和 held-out eval 必须分离，不能只用训练题自测。",
        ],
        "project": [
            "Stage 8 已扩展为 1500 条 SFT train、160 条 SFT eval 和 96 条行为评测 prompt。",
            "数据扩容后仍要重新训练和重新评测，不能沿用旧 8 题 pilot 结论。",
        ],
        "bad": [
            "把网页全文不清洗直接塞进训练集。",
            "只讲缺失值填充、标准化、归一化这类表格预处理。",
            "不保留来源信息，也不拆分 train/eval。",
        ],
    },
    "DPO 显存风险": {
        "topic_id": "dpo_vram",
        "one_liner": "DPO 的显存压力通常高于普通 SFT，因为它处理 chosen/rejected 并涉及 reference policy。",
        "points": [
            "DPO 同时比较 chosen 和 rejected。",
            "reference policy 对比会增加显存和计算压力。",
            "8GB 显存下应使用 LoRA、batch_size=1、短 max_length、短 max_prompt_length 和少量 eval。",
            "tiny smoke test 只证明可跑，不证明行为质量。",
        ],
        "project": [
            "本项目 tiny DPO 能跑通，但 checkpoint 是否接受仍看行为 gate。",
            "DPO v6 是可用 artifact，但不是默认推荐的最终 checkpoint。",
        ],
        "bad": [
            "说没有 OOM 就代表 DPO 质量过关。",
            "忽略 reference policy 和 chosen/rejected 的额外显存成本。",
            "编造没有记录的显存增长数字。",
        ],
    },
    "loss 与行为验收": {
        "topic_id": "loss_behavior",
        "one_liner": "loss 是优化信号，必要但不充分，不能替代可见输出行为验收。",
        "points": [
            "train/eval loss 反映平均训练目标上的拟合情况。",
            "行为验收要看固定 prompt、badcase review 和旧能力回归。",
            "preference accuracy 也不能直接替代行为 gate。",
        ],
        "project": [
            "public-SFT loss 正常下降，但目标概念仍可能答错。",
            "Stage 8B eval loss 降低后，Stage 8C 行为评分没有提升，因此不能直接接受。",
        ],
        "bad": [
            "只要 eval loss 降低就宣布 SFT 成功。",
            "只要 preference accuracy 到 1.0 就接受 DPO。",
            "把 loss 说成完全没有意义。",
        ],
    },
    "固定 Prompt 与扩展评测": {
        "topic_id": "behavior_eval",
        "one_liner": "固定 prompt 让 base、SFT、DPO 在同题上可比，扩展 held-out 改写降低背题风险。",
        "points": [
            "同一批固定问题用于比较不同阶段输出。",
            "扩展到 96 条行为评测 prompt，覆盖多个概念区。",
            "结构化评分记录 required 和 forbidden，但不是最终 LLM judge。",
            "最终要结合人工 badcase 复查。",
        ],
        "project": [
            "旧 7/8 只是 8 题 pilot gate，不能直接说成 96 题通过率。",
            "Stage 8 重新跑 base、public-SFT、custom-SFT、DPO/SFT 候选对比。",
        ],
        "bad": [
            "只测一条 prompt 就宣称泛化成功。",
            "把旧 7/8 当作 Stage 8 的 96 题结果。",
            "只给分数，不看回归样例和坏例。",
        ],
    },
}


QUESTION_FRAMES = [
    "请面向{audience}解释{area}，要求先给结论，再给项目证据。",
    "如果面试官追问{area}，你会怎样回答得稳定又不夸大？",
    "请用三点说明{area}，并指出一个不能接受的错误说法。",
    "请从训练指标、行为评测和 badcase 复查三个角度说明{area}。",
    "请把{area}改写成适合结构化评分的回答。",
    "请说明{area}为什么不能只看 loss 或单个指标。",
    "请设计一个 held-out 问法来检查模型是否真正理解{area}。",
    "如果模型在{area}上回答得像背术语但没有项目证据，应该如何追问？",
    "请说明{area}如何支撑简历里的项目可信度。",
    "请说明{area}在扩容到 10 倍数据后仍要注意什么。",
]

AUDIENCES = ["初学者", "面试官", "项目复盘读者", "未来接手同学", "简历审阅者"]
TONES = ["简洁", "工程复盘", "面试口径", "实验报告", "风险边界"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Stage 8F fact-guard SFT v3 data.")
    parser.add_argument("--train_output", default="data/processed/custom_sft_expanded_v3_train.jsonl")
    parser.add_argument("--eval_output", default="data/processed/custom_sft_expanded_v3_eval.jsonl")
    parser.add_argument("--report_output", default="reports/stage8f_fact_guard_data_report.md")
    parser.add_argument("--train_size", type=int, default=1500)
    parser.add_argument("--eval_size", type=int, default=160)
    parser.add_argument("--seed", type=int, default=44)
    return parser.parse_args()


def stable_id(prefix: str, text: str) -> str:
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]}"


def answer_for(area: str, variant: int, bad: str | None = None) -> str:
    item = AREAS[area]
    project = item["project"][variant % len(item["project"])]
    bad_item = bad or item["bad"][variant % len(item["bad"])]
    points = " ".join(f"{index}. {point}" for index, point in enumerate(item["points"], start=1))
    return (
        f"结论：{item['one_liner']}\n"
        f"要点：{points}\n"
        f"项目证据：{project}\n"
        f"边界：不能接受的说法是“{bad_item}”。如果没有记录，就不要编造 stage 号、月份、"
        f"训练周期、显存数字或通过率。\n"
        f"{COMMON_ACCEPTANCE}"
    )


def correction_answer(area: str, bad: str, variant: int) -> str:
    item = AREAS[area]
    return (
        f"这个回答不能接受，因为它把{area}说偏了，或者把没有记录的项目事实当成结论。"
        f"正确说法是：{item['one_liner']} {item['points'][0]} {item['points'][1]} "
        f"项目里只能引用已记录证据：{item['project'][variant % len(item['project'])]} "
        f"修正后还要重新跑固定 prompt、held-out 改写和 badcase review，确认旧问题没有回归。"
    )


def build_candidates() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    train_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []
    for area, item in AREAS.items():
        for frame_index, frame in enumerate(QUESTION_FRAMES):
            for audience_index, audience in enumerate(AUDIENCES):
                for tone_index, tone in enumerate(TONES):
                    variant = frame_index * 100 + audience_index * 10 + tone_index
                    prompt = frame.format(area=area, audience=audience)
                    prompt += f"\n回答风格：{tone}；不要编造未记录事实。"
                    output = answer_for(area, variant)
                    train_rows.append(
                        {
                            "sample_id": stable_id("stage8f-train", prompt + output),
                            "prompt_area": area,
                            "topic_id": item["topic_id"],
                            "source_type": "stage8f_fact_guard_replay",
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": prompt},
                                {"role": "assistant", "content": output},
                            ],
                        }
                    )

        for bad_index, bad in enumerate(item["bad"]):
            for repeat in range(24):
                prompt = (
                    f"下面是一个关于{area}的坏回答，请指出问题并改成可接受答案：{bad}\n"
                    "要求：不要把坏回答复述成事实；必须说明如何重新评测。"
                )
                output = correction_answer(area, bad, bad_index + repeat)
                train_rows.append(
                    {
                        "sample_id": stable_id("stage8f-correction", prompt + output + str(repeat)),
                        "prompt_area": area,
                        "topic_id": item["topic_id"],
                        "source_type": "stage8f_badcase_correction",
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": output},
                        ],
                    }
                )

        for repeat in range(36):
            prompt = (
                f"如果模型回答{area}时出现未记录的 stage 号、硬件数字、训练周期或通过率，"
                "应该如何处理？"
            )
            output = (
                f"应当把它记为 badcase，而不是当作项目事实。可接受回答必须回到已记录事实："
                f"{item['one_liner']} {item['project'][repeat % len(item['project'])]} "
                f"随后重新跑固定 prompt、held-out 改写、结构化评分和人工复查；如果旧能力回归，"
                "就拒绝该 checkpoint。"
            )
            train_rows.append(
                {
                    "sample_id": stable_id("stage8f-guard", prompt + output + str(repeat)),
                    "prompt_area": area,
                    "topic_id": item["topic_id"],
                    "source_type": "stage8f_fact_guard",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": output},
                    ],
                }
            )

        eval_frames = [
            f"请用项目复盘口吻解释{area}的验收标准。",
            f"请给出一个{area}的反例，并说明为什么不能接受。",
            f"请说明{area}如何防止旧问题回归。",
            f"请从 source metadata、held-out 或 badcase 角度说明{area}。",
        ]
        suffixes = [
            "回答要包含结论、项目证据、边界和复查方法。",
            "回答不要编造未记录的 stage、显存、周期或通过率。",
            "回答要说明为什么旧 8 题 pilot 不能直接替代 96 题评测。",
            "回答要区分训练指标和可见输出行为。",
            "回答要适合面试时追问。",
        ]
        for eval_index, eval_prompt in enumerate(eval_frames):
            for suffix_index, suffix in enumerate(suffixes):
                prompt = f"{eval_prompt}\n{suffix}"
                output = answer_for(area, eval_index * 10 + suffix_index)
                eval_rows.append(
                    {
                        "sample_id": stable_id("stage8f-eval", prompt + output),
                        "prompt_area": area,
                        "topic_id": item["topic_id"],
                        "source_type": "stage8f_heldout_fact_guard_eval",
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": output},
                        ],
                    }
                )
    return train_rows, eval_rows


def take_rows(rows: list[dict[str, Any]], target: int, seed: int, split: str) -> list[dict[str, Any]]:
    shuffled = list(rows)
    random.Random(seed).shuffle(shuffled)
    if len(shuffled) < target:
        raise ValueError(f"Only {len(shuffled)} {split} rows, need {target}")
    selected = shuffled[:target]
    for row in selected:
        row["split"] = split
    return selected


def validate(rows: list[dict[str, Any]], label: str) -> None:
    prompts: set[str] = set()
    for index, row in enumerate(rows, start=1):
        messages = row.get("messages")
        if not isinstance(messages, list) or len(messages) != 3:
            raise ValueError(f"{label} row {index} must have 3 messages")
        if [message.get("role") for message in messages] != ["system", "user", "assistant"]:
            raise ValueError(f"{label} row {index} has invalid role order")
        prompt = str(messages[1]["content"]).strip()
        answer = str(messages[2]["content"]).strip()
        if not prompt or not answer:
            raise ValueError(f"{label} row {index} has empty text")
        prompts.add(prompt)
    if label == "eval" and len(prompts) != len(rows):
        raise ValueError("Eval prompts must be unique")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def render_report(train_rows: list[dict[str, Any]], eval_rows: list[dict[str, Any]]) -> str:
    train_prompts = {row["messages"][1]["content"] for row in train_rows}
    eval_prompts = {row["messages"][1]["content"] for row in eval_rows}
    area_lines = []
    for area in AREAS:
        area_lines.append(
            f"- {area}: train {sum(row['prompt_area'] == area for row in train_rows)}, "
            f"eval {sum(row['prompt_area'] == area for row in eval_rows)}"
        )
    return f"""# Stage 8F Fact-Guard SFT Data Report

Date: 2026-07-03

## Purpose

Stage 8E SFT v2 improved the expanded behavior score, but manual review still
found project-fact drift. This v3 data patch keeps the expanded scale while
making answers shorter, more factual, and less likely to repeat bad concepts as
if they were true.

## Outputs

```text
data/processed/custom_sft_expanded_v3_train.jsonl
data/processed/custom_sft_expanded_v3_eval.jsonl
```

## Size

- Train rows: {len(train_rows)}
- Train unique prompts: {len(train_prompts)}
- Eval rows: {len(eval_rows)}
- Eval unique prompts: {len(eval_prompts)}

## Area Balance

{chr(10).join(area_lines)}

## Intended Training

Continue from the Stage 8E v2 SFT adapter with a lower learning rate:

```text
outputs/sft_lora_qwen05b_stage8_expanded_v2
  -> outputs/sft_lora_qwen05b_stage8_expanded_v3
```
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
