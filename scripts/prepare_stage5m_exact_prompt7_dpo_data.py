"""Prepare exact-failure DPO data for a Stage 5M prompt-7 repair probe.

Stage 5H gave a broad prompt-7 preference distribution, but DPO v7 still
generated the same style of visible failure. Stage 5M uses actual failed
outputs from v6/v7/Stage5K as rejected answers and keeps compact replay pairs
for the previously stable prompts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROMPT7_CHOSEN = [
    "不能只看 loss。loss 是训练目标上的平均拟合信号，能说明模型在训练/验证样本上平均更贴近标签，但它是必要不充分的指标。一次 SFT 是否成功，还要看固定 prompt 的真实输出、目标 badcase 是否修好、旧能力是否回归。这个项目里 public-SFT 能跑通训练却仍误解 LoRA/SFT/DPO，DPO v6 也能拿到很好的 preference eval 但 prompt 7 仍失败，所以最终要用 behavior gate 验收。",
    "loss 下降不等于目标行为正确。它只是优化目标的平均信号，不能保证固定问题答对，也不能发现某个 badcase 是否仍在，或者旧的 LoRA/SFT/DPO、数据管线、显存解释能力是否回归。正确验收应同时看 train/eval loss、固定 prompt 对比、badcase review、regression check，以及 public-SFT 或 DPO v6 这类指标好看但行为未过的例子。",
    "我会把它分成三层：第一，loss 是训练目标上的平均指标，只能说明优化方向；第二，固定 prompt 和 held-out 改写检查用户真正看到的行为；第三，badcase 和旧能力回归检查是否修了一个问题又破坏其他问题。public-SFT 和 DPO v6 的结果都说明，指标好看仍可能不过行为 gate。",
]

PROMPT7_PROMPTS = [
    "为什么不能只看 loss 判断一次 SFT 是否成功？",
    "train loss 降了，为什么还不能说 SFT 成功？",
    "eval loss 看起来不错，为什么还要做固定 prompt 对比？",
    "为什么 DPO v6 preference eval 很好看，仍然不能说行为通过？",
    "面试官问 loss 和真实输出行为的关系，你怎么回答？",
    "为什么要同时看 loss、badcase review 和旧能力回归？",
    "如果 public-SFT 训练成功但仍误解 LoRA/SFT/DPO，这说明了什么？",
    "为什么 held-out prompt 改写能补充 train/eval loss？",
]

GENERIC_REJECTED = [
    "只要 loss 降低，就说明 SFT 已经成功。固定 prompt 只是展示用，不需要作为验收标准。",
    "eval loss 比 train loss 更客观，所以 eval loss 好看就可以不用再看具体输出。",
    "DPO preference accuracy 到 1.0 就说明模型行为已经通过，prompt 失败只是偶然。",
    "只要新的 loss-vs-behavior prompt 答对，旧的 LoRA/SFT/DPO prompt 回归也可以忽略。",
    "loss 完全没有意义，只能凭人工感觉判断训练是否成功。",
]

REPLAY_ROWS = [
    {
        "prompt": "请用三点解释机器学习里的 LoRA 微调，不要解释成无线通信 LoRa。",
        "chosen": "第一，机器学习里的 LoRA 是 Low-Rank Adaptation，是参数高效微调方法，不是无线通信 LoRa。第二，它通常冻结基础模型大部分权重，只训练少量低秩 adapter。第三，它能降低显存和训练成本，适合本地 GPU 做 LoRA SFT 学习。",
        "rejected": "LoRA 是 Long Range 无线通信协议，本项目主要训练远距离通信知识。",
        "source_type": "stage5m_replay_lora_definition",
    },
    {
        "prompt": "SFT 是什么？它和 LoRA 是什么关系？",
        "chosen": "SFT 是 supervised fine-tuning，描述训练目标和 instruction-answer 数据形式。LoRA 是参数高效微调方法，描述怎样少量更新模型参数。LoRA SFT 就是用 LoRA adapter 来执行 SFT，二者不是互斥关系。",
        "rejected": "SFT 是安全指标，LoRA 是 DPO 后自动生成的数据保护对象。",
        "source_type": "stage5m_replay_sft_lora",
    },
    {
        "prompt": "DPO 和 SFT 的区别是什么？为什么通常先做 SFT 再做 DPO？",
        "chosen": "SFT 用 instruction-answer 样本教模型模仿标准答案；DPO 用 chosen/rejected 偏好对，让模型更偏向 chosen、远离 rejected。通常先 SFT 建立基础回答能力，再用 DPO 做偏好优化。",
        "rejected": "DPO 可以在基础模型不会回答时直接替代 SFT，只要 DPO loss 低就成功。",
        "source_type": "stage5m_replay_dpo_sft",
    },
    {
        "prompt": "为什么 public-SFT adapter 没修正 LoRA/SFT/DPO 概念误解，反而说明 Stage 2B 有必要？",
        "chosen": "public-SFT 是公开数据基线，用来证明训练、保存、加载和对比链路能跑通。它没有修正 LoRA/SFT/DPO 概念误解，说明公开通用 instruction 数据没有覆盖目标 badcase，所以 Stage 2B 需要自采集技术数据做定向修复。",
        "rejected": "public-SFT adapter 已经补足概念，所以 Stage 2B 是从零重新建模型。",
        "source_type": "stage5m_replay_public_sft",
    },
    {
        "prompt": "请解释自采集技术数据从采集、清洗、去重、筛选到 instruction-answer 转换的流程。",
        "chosen": "先保留 source_id、标题、路径或 URL 等来源元数据，再清洗网页噪声、导航栏和广告，之后去重、筛选，最后改写为 instruction-answer 或 Qwen chat JSONL，并用固定 prompt 做回归检查。",
        "rejected": "主要做缺失值填充、归一化和标准化，像处理表格传感器数据一样即可。",
        "source_type": "stage5m_replay_data_pipeline",
    },
    {
        "prompt": "8GB 显存下做 DPO 有什么风险？应该怎样降低显存压力？",
        "chosen": "DPO 要比较 chosen/rejected，并且通常需要 reference policy 评分，所以比普通 SFT 更吃显存。8GB 下应使用 LoRA、batch_size=1、短 max_length/max_prompt_length、少量 pair 和少量 eval 做 smoke test。",
        "rejected": "DPO 每个 epoch 只增加 0.1GB 显存，batch_size=4GB 就够了。",
        "source_type": "stage5m_replay_dpo_vram",
    },
    {
        "prompt": "如果面试官问你这个项目的数据管线，你会怎么讲？",
        "chosen": "我会说先用公开数据跑通可复现基线，证明训练、保存、加载和对比链路；Stage 4A 发现 public-SFT 没修正目标概念 badcase；于是 Stage 2B 自采集、清洗、去重并转换技术 instruction-answer 数据，再训练 custom-SFT 并做三方对比。",
        "rejected": "这个项目主要是下载公开数据后直接训练，public-SFT 已经解决所有概念问题。",
        "source_type": "stage5m_replay_interview",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Stage 5M exact prompt-7 DPO data.")
    parser.add_argument("--v6_compare", default="reports/compare_outputs_four_way_dpo_naive_v6.jsonl")
    parser.add_argument("--v7_compare", default="reports/compare_outputs_four_way_dpo_v7_stage5h.jsonl")
    parser.add_argument("--stage5k_compare", default="reports/compare_outputs_four_way_stage5k_sft_repair.jsonl")
    parser.add_argument("--train_output", default="data/processed/dpo_stage5m_exact_prompt7_train.jsonl")
    parser.add_argument("--eval_output", default="data/processed/dpo_stage5m_exact_prompt7_eval.jsonl")
    parser.add_argument("--report_file", default="reports/stage5m_exact_prompt7_dpo_data_report.md")
    return parser.parse_args()


def read_prompt7_failure(path: Path, key: str) -> str:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) < 7:
        raise ValueError(f"Expected at least 7 rows in {path}")
    return str(rows[6][key]).strip()


def add_unique(rows: list[dict[str, Any]], seen: set[tuple[str, str, str]], row: dict[str, Any]) -> None:
    item = {
        "prompt": str(row["prompt"]).strip(),
        "chosen": str(row["chosen"]).strip(),
        "rejected": str(row["rejected"]).strip(),
        "source_type": str(row.get("source_type", "stage5m")),
    }
    key = (item["prompt"], item["chosen"], item["rejected"])
    if key in seen:
        return
    seen.add(key)
    rows.append(item)


def build_rows(args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    failures = [
        ("actual_v6_failure", read_prompt7_failure(Path(args.v6_compare), "dpo_tiny_answer")),
        ("actual_v7_failure", read_prompt7_failure(Path(args.v7_compare), "dpo_tiny_answer")),
        ("actual_stage5k_failure", read_prompt7_failure(Path(args.stage5k_compare), "custom_sft_v3_answer")),
    ]
    rejected_pool = failures + [(f"generic_{i}", text) for i, text in enumerate(GENERIC_REJECTED, start=1)]
    train_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []
    seen_train: set[tuple[str, str, str]] = set()
    seen_eval: set[tuple[str, str, str]] = set()

    for prompt_index, prompt in enumerate(PROMPT7_PROMPTS):
        for chosen_index, chosen in enumerate(PROMPT7_CHOSEN):
            for rejected_index, (source, rejected) in enumerate(rejected_pool):
                row = {
                    "prompt": prompt,
                    "chosen": chosen,
                    "rejected": rejected,
                    "source_type": f"stage5m_prompt7_{source}",
                }
                if (prompt_index + chosen_index + rejected_index) % 5 == 0:
                    add_unique(eval_rows, seen_eval, row)
                else:
                    add_unique(train_rows, seen_train, row)

    for index, row in enumerate(REPLAY_ROWS):
        for repeat in range(4):
            target = eval_rows if repeat == 0 and index % 2 == 0 else train_rows
            seen = seen_eval if target is eval_rows else seen_train
            add_unique(target, seen, row)

    return train_rows, eval_rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def render_report(train_rows: list[dict[str, Any]], eval_rows: list[dict[str, Any]], train_output: Path, eval_output: Path) -> str:
    return f"""# Stage 5M Exact Prompt-7 DPO Data Report

Date: 2026-05-16

## Scope

Stage 5M prepares a deliberate exact-failure DPO repair set. It uses actual
failed prompt-7 outputs from DPO v6, DPO v7, and Stage 5K SFT repair as
rejected answers, then mixes compact replay pairs for the seven stable areas.

## Outputs

```text
{train_output.as_posix()}
{eval_output.as_posix()}
```

## Summary

- Train rows: {len(train_rows)}
- Eval rows: {len(eval_rows)}
- Start adapter for the intended probe: `outputs/dpo_lora_qwen05b_naive_v6`
- This is a deliberate DPO-on-DPO repair probe, not the conservative default
  recommendation.
"""


def main() -> None:
    args = parse_args()
    train_rows, eval_rows = build_rows(args)
    train_output = Path(args.train_output)
    eval_output = Path(args.eval_output)
    report_file = Path(args.report_file)
    write_jsonl(train_output, train_rows)
    write_jsonl(eval_output, eval_rows)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(render_report(train_rows, eval_rows, train_output, eval_output), encoding="utf-8")
    print(f"Wrote {len(train_rows)} Stage 5M train rows to {train_output}")
    print(f"Wrote {len(eval_rows)} Stage 5M eval rows to {eval_output}")
    print(f"Wrote report to {report_file}")


if __name__ == "__main__":
    main()
