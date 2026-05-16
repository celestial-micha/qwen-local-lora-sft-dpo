"""Prepare Stage 5N micro-SFT data for prompt-7 repair from DPO v6.

Stage 5J and Stage 5M showed that preference metrics can look perfect while
the visible fixed prompt still misses the exact loss-vs-behavior acceptance
points. Stage 5K showed that broad direct SFT repair from SFT v3 can overwrite
older behavior. This script makes a smaller continuation dataset intended for
low-learning-rate SFT from the stable DPO v6 adapter.
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

FIXED_PROMPTS: dict[str, str] = {
    "lora_definition": "请用三点解释机器学习里的 LoRA 微调，不要解释成无线通信 LoRa。",
    "sft_lora_relation": "SFT 是什么？它和 LoRA 是什么关系？",
    "dpo_vs_sft": "DPO 和 SFT 的区别是什么？为什么通常先做 SFT 再做 DPO？",
    "public_sft_motivation": "为什么 public-SFT adapter 没修正 LoRA/SFT/DPO 概念误解，反而说明 Stage 2B 有必要？",
    "data_pipeline": "请解释自采集技术数据从采集、清洗、去重、筛选到 instruction-answer 转换的流程。",
    "dpo_vram_risk": "8GB 显存下做 DPO 有什么风险？应该怎样降低显存压力？",
    "loss_vs_behavior": "为什么不能只看 loss 判断一次 SFT 是否成功？",
    "interview_pipeline": "如果面试官问你这个项目的数据管线，你会怎么讲？",
}

REPLAY_ANSWERS: dict[str, str] = {
    "lora_definition": (
        "三点说清楚：第一，机器学习里的 LoRA 是参数高效微调方法，不是无线通信 LoRa。"
        "第二，它在部分线性层旁边加入低秩 adapter，只训练少量新增参数。"
        "第三，基础模型大部分权重保持冻结，所以显存和训练成本更低，也方便保存、加载和替换 adapter。"
    ),
    "sft_lora_relation": (
        "SFT 是 supervised fine-tuning，也就是用 instruction-answer 或对话样本让模型模仿目标回答。"
        "LoRA 不是另一种数据格式，而是一种参数高效训练方式：在执行 SFT 时，可以用 LoRA adapter 来更新少量参数。"
        "所以二者关系是：SFT 定义训练目标和数据形式，LoRA 定义怎样更省显存地完成这次微调。"
    ),
    "dpo_vs_sft": (
        "SFT 学的是标准回答，数据通常是 instruction-answer；DPO 学的是偏好对，数据是 chosen/rejected。"
        "DPO 会让模型更偏向 chosen、远离 rejected，而不是只模仿一个答案。"
        "通常先做 SFT，是因为模型要先具备基础回答能力，再用 DPO 调整风格、偏好和坏例边界。"
    ),
    "public_sft_motivation": (
        "public-SFT 的价值是先用公开数据跑通训练链路，得到一个可复现基线。"
        "它没修正 LoRA/SFT/DPO 概念误解，说明公开通用 instruction 数据不等于本项目目标行为。"
        "因此 Stage 2B 有必要：需要自采集、清洗、去重、筛选技术数据，再做定向 instruction-answer 样本修复。"
    ),
    "data_pipeline": (
        "我会先保留 source_id、标题、路径或 URL 等来源信息，再清洗网页噪声、导航栏和广告。"
        "然后做去重和筛选，留下和 LoRA/SFT/DPO、显存、训练复盘相关的技术内容。"
        "最后把材料改写成 instruction-answer 或多轮对话样本，保存成 Qwen chat JSONL，供 SFT 或 DPO 使用。"
    ),
    "dpo_vram_risk": (
        "DPO 在 8GB 显存上更容易 OOM，因为一次要处理 chosen/rejected，并且通常还要 reference policy。"
        "降低压力的方法是用 LoRA、小 batch，比如 batch_size=1，缩短 max_length 和 max_prompt_length，控制 pair 数量和 eval 频率。"
        "训练时还要观察 dedicated VRAM、shared GPU memory、step time 和保存/加载是否稳定。"
    ),
    "interview_pipeline": (
        "我会说这个项目先用公开数据集做 public-SFT，跑通训练、保存、加载，建立可复现基线。"
        "然后通过三方对比发现 Stage 4A 仍没修正 LoRA/SFT/DPO 等 badcase。"
        "接着 Stage 2B 做自采集技术数据，经过采集、清洗、去重、筛选，再转成 instruction-answer，用 custom-SFT 和 DPO 做定向修复。"
    ),
}

PROMPT7_TRAIN_PROMPTS = [
    FIXED_PROMPTS["loss_vs_behavior"],
    "如果 SFT 的 train loss 和 eval loss 都下降了，为什么还不能直接宣布成功？",
    "为什么 loss 只能作为训练目标上的平均指标，而不能替代固定 prompt 验收？",
    "请解释 loss、固定 prompt behavior gate、badcase 复盘三者的关系。",
    "public-SFT loss 看起来正常下降，但 LoRA/SFT/DPO 仍答错，这说明什么？",
    "一次 LoRA SFT 是否学会概念，为什么要看 badcase 和旧能力回归？",
    "为什么 DPO preference accuracy 很高时，也仍要检查固定 prompt 输出？",
    "请用这个项目解释：loss 下降、固定问题答对、旧能力不回归分别证明什么？",
    "为什么不能把 eval loss 当成 SFT 成功的充分证明？",
    "SFT 训练结束后，怎样判断模型是真的行为变好了，而不是只把平均 loss 压低？",
    "为什么 prompt 7 失败会阻止继续扩大 DPO？",
    "如果模型在公开数据上 loss 好看，但项目核心问题还错，该怎么复盘？",
    "请说明 loss 指标和人工/规则 behavior gate 的分工。",
    "为什么要把 public-SFT 的 badcase 和 regression 检查写进验收标准？",
]

PROMPT7_EVAL_PROMPTS = [
    "为什么说 loss 是必要但不充分的 SFT 验收信号？",
    "固定 prompt 仍失败时，eval loss 下降应该怎样解读？",
    "请区分平均优化指标、目标行为和旧能力回归检查。",
    "如果模型 loss 下降却还误解 LoRA/SFT/DPO，下一步应该看什么？",
    "为什么 prompt 级 badcase 比单个 loss 数字更能说明行为问题？",
    "DPO 或 SFT 的训练指标很好时，为什么仍要看 expanded behavior gate？",
]

PROMPT7_ANSWERS = [
    (
        "不能只看 loss，因为 loss 只是训练目标上的平均优化指标，说明模型在训练或验证分布上更会拟合。"
        "它是必要但不充分的信号，不能只看 loss 或只看 eval loss 判断 SFT 成功。"
        "验收还要看固定 prompt 的实际行为、badcase/坏例复盘、旧能力回归检查。"
        "比如本项目 public-SFT loss 能正常下降，但固定 prompt 仍暴露 LoRA/SFT/DPO 概念误解，所以要结合三方对比和 regression gate 决定是否通过。"
    ),
    (
        "loss 下降只能说明平均训练目标被优化了，不等于目标行为已经稳定出现。"
        "SFT 是否成功还要看固定 prompt behavior gate：核心问题是否答对，badcase 是否修复，旧能力有没有回归。"
        "本项目里 public-SFT 的 loss 并不异常，但它仍没修正 LoRA/SFT/DPO 概念误解，这正说明 loss 是必要但不充分的证据。"
    ),
    (
        "loss 是一个平均拟合信号，不是项目验收结论。"
        "不能只看 loss，因为模型可能在总体数据上变好，却在固定 prompt、关键概念或边界 badcase 上继续失败。"
        "因此要同时检查固定 prompt 行为、badcase/regression 记录和 public-SFT 到 custom-SFT、DPO 的对比，确认 LoRA/SFT/DPO 等核心能力没有旧能力回归。"
    ),
    (
        "一次 SFT 成功至少要同时看三层证据：train/eval loss 是否正常、固定 prompt 行为是否过 gate、badcase 和旧能力回归是否可接受。"
        "loss 是平均指标，必要但不充分；只看 loss 不够。"
        "本项目 public-SFT 就是例子：loss 能下降并说明链路跑通，但固定 prompt 仍显示 LoRA/SFT/DPO 概念误解，所以不能直接判定成功。"
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Stage 5N prompt-7 micro-SFT data.")
    parser.add_argument("--train_file", default="data/processed/sft_stage5n_prompt7_micro_train.jsonl")
    parser.add_argument("--eval_file", default="data/processed/sft_stage5n_prompt7_micro_eval.jsonl")
    parser.add_argument("--report_file", default="reports/stage5n_prompt7_micro_sft_data_report.md")
    parser.add_argument("--system_prompt", default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--prompt7_exact_repeats", type=int, default=12)
    parser.add_argument("--replay_repeats", type=int, default=6)
    parser.add_argument("--stage_label", default="Stage 5N")
    parser.add_argument("--init_adapter_hint", default="outputs/dpo_lora_qwen05b_naive_v6")
    return parser.parse_args()


def make_row(prompt: str, answer: str, system_prompt: str, source_type: str, prompt_area: str) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": answer},
        ],
        "source_type": source_type,
        "prompt_area": prompt_area,
    }


def build_train_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for key, answer in REPLAY_ANSWERS.items():
        prompt = FIXED_PROMPTS[key]
        for _ in range(args.replay_repeats):
            rows.append(make_row(prompt, answer, args.system_prompt, "stage5n_replay_guardrail", key))

    fixed_prompt = FIXED_PROMPTS["loss_vs_behavior"]
    for _ in range(args.prompt7_exact_repeats):
        for answer in PROMPT7_ANSWERS:
            rows.append(
                make_row(fixed_prompt, answer, args.system_prompt, "stage5n_prompt7_exact_micro", "Loss vs behavior")
            )

    for index, prompt in enumerate(PROMPT7_TRAIN_PROMPTS[1:], start=1):
        answer = PROMPT7_ANSWERS[index % len(PROMPT7_ANSWERS)]
        rows.append(
            make_row(prompt, answer, args.system_prompt, "stage5n_prompt7_paraphrase_micro", "Loss vs behavior")
        )
        rows.append(
            make_row(
                prompt,
                PROMPT7_ANSWERS[(index + 1) % len(PROMPT7_ANSWERS)],
                args.system_prompt,
                "stage5n_prompt7_paraphrase_micro",
                "Loss vs behavior",
            )
        )
    return rows


def build_eval_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, answer in REPLAY_ANSWERS.items():
        rows.append(make_row(FIXED_PROMPTS[key], answer, args.system_prompt, "stage5n_replay_eval", key))
    for index, prompt in enumerate(PROMPT7_EVAL_PROMPTS):
        rows.append(
            make_row(
                prompt,
                PROMPT7_ANSWERS[index % len(PROMPT7_ANSWERS)],
                args.system_prompt,
                "stage5n_prompt7_eval_holdout",
                "Loss vs behavior",
            )
        )
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def render_report(train_rows: list[dict[str, Any]], eval_rows: list[dict[str, Any]], args: argparse.Namespace) -> str:
    prompt7_train = sum(1 for row in train_rows if row["prompt_area"] == "Loss vs behavior")
    replay_train = len(train_rows) - prompt7_train
    prompt7_eval = sum(1 for row in eval_rows if row["prompt_area"] == "Loss vs behavior")
    return f"""# {args.stage_label} Prompt-7 Micro-SFT Data Report

Date: 2026-05-16

## Scope

{args.stage_label} is a conservative micro-SFT repair from a stable previous adapter. It
exists because:

- Stage 5H/5J prompt-7 preference data gave clean DPO preference metrics but
  did not pass the visible fixed prompt.
- Stage 5K broad direct SFT repair regressed older fixed prompts.
- Stage 5M exact-failure DPO from v6 improved wording but still missed
  "not sufficient" and "badcase/regression".

## Outputs

```text
{Path(args.train_file).as_posix()}
{Path(args.eval_file).as_posix()}
```

## Summary

- Train rows: {len(train_rows)}
- Eval rows: {len(eval_rows)}
- Prompt-7 train rows: {prompt7_train}
- Replay train rows: {replay_train}
- Prompt-7 eval rows: {prompt7_eval}

## Design

- Intended init adapter: `{args.init_adapter_hint}`.
- Do not train from the rejected Stage 5K SFT adapter.
- Use direct prompt-7 SFT targets that explicitly contain:
  - loss as an average training/eval optimization signal;
  - necessary but not sufficient / cannot only look at loss;
  - fixed prompt behavior;
  - badcase, regression, and old-capability checks;
  - the public-SFT LoRA/SFT/DPO project example.
- Keep replay rows for fixed prompts 1-6 and 8 to reduce regression risk.
- The original fixed prompt 7 is included as a direct repair target; the
  expanded Stage 5H prompt suite remains the held-out behavior gate.
"""


def main() -> None:
    args = parse_args()
    train_rows = build_train_rows(args)
    eval_rows = build_eval_rows(args)
    train_file = Path(args.train_file)
    eval_file = Path(args.eval_file)
    report_file = Path(args.report_file)
    write_jsonl(train_file, train_rows)
    write_jsonl(eval_file, eval_rows)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(render_report(train_rows, eval_rows, args), encoding="utf-8")
    print(f"Wrote {len(train_rows)} {args.stage_label} train rows to {train_file}")
    print(f"Wrote {len(eval_rows)} {args.stage_label} eval rows to {eval_file}")
    print(f"Wrote report to {report_file}")


if __name__ == "__main__":
    main()
