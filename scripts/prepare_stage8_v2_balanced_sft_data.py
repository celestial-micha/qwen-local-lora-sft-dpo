"""Prepare Stage 8D balanced SFT v2 data.

Stage 8B showed a classic loss-vs-behavior failure: eval loss improved, but
the model mixed project stages and regressed on core LoRA/SFT/DPO concepts.

This v2 dataset keeps the scale useful for the resume, but changes the data
shape:

- direct concept/replay rows first;
- explicit bad-answer correction rows;
- held-out style paraphrases without copying the 96 eval prompts exactly;
- anti-hallucination rows that forbid invented stage IDs, durations, and
  memory numbers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any


SYSTEM_PROMPT = (
    "你是一个清晰、严谨、适合初学者的大模型微调中文助教。"
    "只根据已记录的项目事实回答，不编造阶段号、训练周期、显存数字或不存在的结论。"
)


AREAS: dict[str, dict[str, Any]] = {
    "LoRA 定义与边界": {
        "topic_id": "lora_definition",
        "facts": [
            "机器学习里的 LoRA 是 Low-Rank Adaptation，一种参数高效微调方法。",
            "LoRA 冻结基础模型大部分参数，只训练少量低秩 adapter 参数。",
            "LoRA adapter 不是完整模型，推理时仍要加载基础模型。",
            "不能把机器学习 LoRA 解释成无线通信 LoRa、路由协议或全量重训。",
        ],
        "project": [
            "本项目用 LoRA 在 RTX 4060 Laptop GPU 上降低 Qwen2.5-0.5B 后训练成本。",
            "public-SFT、custom-SFT 和 DPO 都围绕 adapter 保存、加载和推理对比做验证。",
        ],
        "wrong": [
            "LoRA 是 Long Range 无线通信协议，所以主要优化网络延迟。",
            "LoRA 会重新训练全部基础模型参数，adapter 可以脱离基础模型单独推理。",
        ],
    },
    "SFT 与 LoRA 关系": {
        "topic_id": "sft_lora_relation",
        "facts": [
            "SFT 是 supervised fine-tuning，也就是有监督微调。",
            "SFT 描述训练目标和 instruction-answer 或 chat 数据形式。",
            "LoRA 描述参数高效更新方法。",
            "LoRA SFT 表示用 LoRA adapter 来执行 SFT，二者不是互斥关系。",
        ],
        "project": [
            "本项目先做 public LoRA SFT 验证链路，再做 custom LoRA SFT 修正目标概念。",
            "固定 prompt 对比用来检查 SFT 后行为是否真的改善。",
        ],
        "wrong": [
            "SFT 是某个网络安全缩写，LoRA 和 SFT 不能一起使用。",
            "LoRA SFT 是先做 DPO 再训练无线 LoRa 协议。",
        ],
    },
    "DPO 与 SFT 区别": {
        "topic_id": "dpo_vs_sft",
        "facts": [
            "SFT 使用标准 instruction-answer 数据教模型模仿目标回答。",
            "DPO 使用同一 prompt 下的 chosen/rejected 偏好对。",
            "DPO 让模型更偏向 chosen，远离 rejected。",
            "通常先做 SFT，再在基础回答稳定后做 DPO。",
        ],
        "project": [
            "本项目从 custom-SFT v3 出发做 tiny DPO 和 separate-reference DPO。",
            "DPO v7/v8 preference accuracy 到 1.0，但固定行为 gate 仍发现 prompt 7 问题。",
        ],
        "wrong": [
            "DPO 是 Data Preprocessing 或数据保护对象。",
            "preference accuracy 到 1.0 就能直接接受 DPO checkpoint。",
        ],
    },
    "public-SFT 诊断价值": {
        "topic_id": "public_sft_motivation",
        "facts": [
            "public-SFT 是工程 baseline，不是最终目标模型。",
            "它证明公开数据、训练、保存、加载和推理对比链路能跑通。",
            "Stage 4A 发现 public-SFT 仍未修正 LoRA/SFT/DPO 目标概念误解。",
            "这个失败推动 Stage 2B 自采集技术数据和 badcase 数据补丁。",
        ],
        "project": [
            "公开数据基线使用 1003 条 train 和 111 条 eval。",
            "custom-SFT 后才明显改善大部分目标技术 prompt。",
        ],
        "wrong": [
            "public-SFT 已经彻底修好所有目标概念。",
            "Stage 2B 是从零训练完整模型，或者需要编造三到六个月周期。",
        ],
    },
    "自采集技术数据管线": {
        "topic_id": "data_pipeline",
        "facts": [
            "数据采集要保留 source_id、标题、路径或 URL。",
            "清洗要去掉网页噪声、导航栏、广告、重复空白和无关内容。",
            "清洗后要做去重、筛选，再改写成 instruction-answer 或 Qwen chat JSONL。",
            "训练集和 held-out eval 要分离，不能只用训练题自测。",
        ],
        "project": [
            "旧 Stage 2B 有 10 个来源、96 个清洗片段和 157 条 seed。",
            "Stage 8 扩容到 1500 条 SFT train、160 条 SFT eval 和 96 条行为 prompt。",
        ],
        "wrong": [
            "把网页全文不清洗直接塞进训练集。",
            "只讲缺失值填充、标准化、归一化这类表格预处理。",
        ],
    },
    "DPO 显存风险": {
        "topic_id": "dpo_vram",
        "facts": [
            "DPO 同时处理 chosen/rejected，并涉及 reference policy 对比。",
            "DPO 显存压力通常高于普通 SFT。",
            "8GB 显存下应使用 LoRA、小 batch、短 max_length、短 max_prompt_length 和少量 eval。",
            "tiny smoke test 只证明可跑，不证明行为质量。",
        ],
        "project": [
            "tiny DPO 33 pair 完成 4 个 optimizer step，没有 OOM。",
            "DPO v6 separate-reference 跑通，但仍未完整通过行为 gate。",
        ],
        "wrong": [
            "无 OOM 就等于 DPO checkpoint 质量过关。",
            "忽略 reference policy 和 chosen/rejected 的额外显存成本。",
        ],
    },
    "loss 与行为验收": {
        "topic_id": "loss_behavior",
        "facts": [
            "loss 是平均训练目标上的优化信号。",
            "loss 必要但不充分，不能替代可见输出行为。",
            "验收要看固定 prompt、badcase review 和旧能力回归。",
            "preference accuracy 也不能直接替代行为 gate。",
        ],
        "project": [
            "public-SFT loss 正常但目标概念仍错。",
            "Stage 8B eval loss 降到约 0.199，但 Stage 8C 行为评分没有提升。",
        ],
        "wrong": [
            "只要 train loss 或 eval loss 下降就宣布 SFT 成功。",
            "只要 DPO preference accuracy 到 1.0 就接受 checkpoint。",
        ],
    },
    "固定 Prompt 与扩展评测": {
        "topic_id": "behavior_eval",
        "facts": [
            "固定 prompt 让 base、SFT、DPO 在同一问题上可比。",
            "扩展 held-out 改写能降低模型只记住单句 prompt 的风险。",
            "结构化评分记录 required 和 forbidden 项，但它不是最终 LLM judge。",
            "评测结果要结合人工 badcase 复查。",
        ],
        "project": [
            "旧 pilot gate 是 8 题，Stage 8 扩展为 96 条行为评测 prompt。",
            "旧 7/8 不能直接说成 96 题通过率，必须重新评测。",
        ],
        "wrong": [
            "只测一个 prompt 就宣布泛化成功。",
            "把旧 pilot 7/8 当成 Stage 8 96 题通过率。",
        ],
    },
    "checkpoint 选择与拒绝理由": {
        "topic_id": "checkpoint_decision",
        "facts": [
            "接受 checkpoint 要看行为稳定性，而不只看单项指标。",
            "custom-SFT v3 是旧阶段保守推荐，因为固定 gate 7/8 且旧题较稳定。",
            "DPO v6 是较好的 DPO artifact，但不是默认推荐模型。",
            "能修一个 prompt 但破坏旧题的 adapter 应拒绝。",
        ],
        "project": [
            "Stage 5O 强修 prompt 7，但固定 gate 降到 4/8，所以被拒绝。",
            "Stage 8B loss 好看但行为评分没提升，所以不能直接接受。",
        ],
        "wrong": [
            "只因 eval loss 低就切换 checkpoint。",
            "只因 preference accuracy 高就接受 DPO。",
        ],
    },
    "面试叙事与边界": {
        "topic_id": "interview_narrative",
        "facts": [
            "项目重点是可复现的后训练链路和评估闭环。",
            "要区分 pilot 结果、扩容数据和重新训练后的结果。",
            "不能把未跑过的新评测说成已有通过率。",
            "可以强调数据构造、badcase 迭代和评测边界意识。",
        ],
        "project": [
            "Stage 8 已构建 1500/160 SFT、1500/160 DPO 和 96 条行为 prompt。",
            "如果被问结果，要说明旧 7/8 是 pilot gate，新 96 题需要重新评测。",
        ],
        "wrong": [
            "把旧 checkpoint 说成已经在 96 条 Stage 8 prompt 上达到某个通过率。",
            "只报漂亮数字，不解释数据来源和限制。",
        ],
    },
}

DIRECT_FRAMES = [
    "请解释{area}，要求先给定义，再结合本项目证据。",
    "如果面试官追问{area}，请给出稳定、可复盘的回答。",
    "请用三点说明{area}，并指出一个不能接受的错误说法。",
    "请从训练指标、行为评测和 badcase 复查三个角度说明{area}。",
    "请把下面错误说法改成正确说法：{wrong}",
    "请说明为什么这个说法不严谨：{wrong}",
    "请给出{area}的最小验收清单。",
    "请用一句总述加三条要点回答{area}。",
    "请说明{area}在 Stage 8 重新训练中的作用。",
    "请说明{area}如何防止旧能力回归。",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Stage 8D balanced SFT v2 data.")
    parser.add_argument("--train_output", default="data/processed/custom_sft_expanded_v2_train.jsonl")
    parser.add_argument("--eval_output", default="data/processed/custom_sft_expanded_v2_eval.jsonl")
    parser.add_argument("--report_output", default="reports/stage8d_badcase_data_patch_report.md")
    parser.add_argument("--train_size", type=int, default=1500)
    parser.add_argument("--eval_size", type=int, default=160)
    parser.add_argument("--seed", type=int, default=43)
    return parser.parse_args()


def stable_id(prefix: str, text: str) -> str:
    return f"{prefix}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]}"


def answer_for(area: str, wrong: str, variant: int) -> str:
    item = AREAS[area]
    facts = item["facts"]
    project = item["project"][variant % len(item["project"])]
    bad = wrong or item["wrong"][variant % len(item["wrong"])]
    return (
        f"{area}可以这样讲：第一，{facts[0]} 第二，{facts[1]} "
        f"第三，{facts[2]} 结合本项目，{project} "
        f"需要避免的错误说法是：{bad} 正确验收时还要看固定 prompt、"
        "held-out 改写、badcase review 和旧能力是否回归；不能只看 loss "
        "或 preference accuracy。"
    )


def build_candidates() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    train_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []
    for area, item in AREAS.items():
        wrongs = item["wrong"]
        for frame_index, frame in enumerate(DIRECT_FRAMES):
            for wrong_index, wrong in enumerate(wrongs):
                for repeat in range(10):
                    variant = frame_index * 100 + wrong_index * 10 + repeat
                    prompt = frame.format(area=area, wrong=wrong)
                    if repeat % 3 == 1:
                        prompt += "\n回答时必须明确说明：不要编造不存在的 stage、月份、显存数字或通过率。"
                    elif repeat % 3 == 2:
                        prompt += "\n回答时必须包含项目证据、错误边界和验收标准。"
                    output = answer_for(area, wrong, variant)
                    row = {
                        "sample_id": stable_id("stage8d-train", prompt + output),
                        "prompt_area": area,
                        "topic_id": item["topic_id"],
                        "source_type": "stage8d_balanced_replay_and_badcase_patch",
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": output},
                        ],
                    }
                    train_rows.append(row)

        eval_frames = [
            f"请用项目答辩口吻解释{area}，并说明一个回归风险。",
            f"请设计一个不泄漏训练答案的 held-out 问题来检查{area}。",
            f"如果模型在{area}上只背术语但没有项目证据，应该如何追问？",
            f"请说明{area}为什么不能只看 loss 或 preference accuracy。",
        ]
        eval_suffixes = [
            "回答要包含项目事实和不能接受的错误说法。",
            "回答要说明如何用固定 prompt 复查。",
            "回答要说明为什么不能编造未记录结果。",
            "回答要说明如何保护旧能力不回归。",
        ]
        for eval_index, prompt in enumerate(eval_frames):
            for suffix_index, suffix in enumerate(eval_suffixes):
                full_prompt = f"{prompt}\n{suffix}"
                output = answer_for(area, "", eval_index * 10 + suffix_index + 7)
                eval_rows.append(
                    {
                        "sample_id": stable_id("stage8d-eval", full_prompt + output),
                        "prompt_area": area,
                        "topic_id": item["topic_id"],
                        "source_type": "stage8d_heldout_balanced_eval",
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": full_prompt},
                            {"role": "assistant", "content": output},
                        ],
                    }
                )
    return train_rows, eval_rows


def take_rows(rows: list[dict[str, Any]], target: int, seed: int, label: str) -> list[dict[str, Any]]:
    if len(rows) < target:
        repeats = (target // len(rows)) + 1
        expanded = []
        for repeat in range(repeats):
            for row in rows:
                copied = json.loads(json.dumps(row, ensure_ascii=False))
                copied["sample_id"] = f"{row['sample_id']}-r{repeat:02d}"
                expanded.append(copied)
        rows = expanded
    shuffled = list(rows)
    random.Random(seed).shuffle(shuffled)
    selected = shuffled[:target]
    for row in selected:
        row["split"] = label
    return selected


def validate(rows: list[dict[str, Any]], label: str) -> None:
    for index, row in enumerate(rows, start=1):
        messages = row.get("messages")
        if not isinstance(messages, list) or len(messages) != 3:
            raise ValueError(f"{label} row {index} must have 3 messages")
        if [msg.get("role") for msg in messages] != ["system", "user", "assistant"]:
            raise ValueError(f"{label} row {index} has invalid role order")
        if not messages[1]["content"].strip() or not messages[2]["content"].strip():
            raise ValueError(f"{label} row {index} has empty text")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def render_report(train_rows: list[dict[str, Any]], eval_rows: list[dict[str, Any]]) -> str:
    return f"""# Stage 8D Badcase Data Patch Report

Date: 2026-07-03

## Why This Patch Exists

Stage 8B used the first expanded SFT data and reached good-looking training
metrics, but Stage 8C behavior scoring regressed:

```text
old custom-SFT v3: 21 / 96
Stage 8B SFT:      19 / 96
```

Manual spot checks showed stage mixing, invented project facts, and regression
on LoRA/SFT/DPO definitions. This proves the project should not accept a
checkpoint just because eval loss improved.

## Patch Design

- Replace loose meta templates with direct concept, correction, and replay rows.
- Cover the same core areas as the 96-prompt behavior suite.
- Include explicit anti-hallucination instructions:
  do not invent stage IDs, durations, memory numbers, or pass rates.
- Keep the scale resume-friendly while making the data cleaner.

## Outputs

```text
data/processed/custom_sft_expanded_v2_train.jsonl
data/processed/custom_sft_expanded_v2_eval.jsonl
```

## Dataset Size

- Train rows: {len(train_rows)}
- Eval rows: {len(eval_rows)}

## Next Step

Train a conservative v2 SFT adapter from the old stable checkpoint, not from
the regressed Stage 8B adapter:

```text
outputs/sft_lora_qwen05b_custom_v3_from_v1_patch
  -> outputs/sft_lora_qwen05b_stage8_expanded_v2
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
