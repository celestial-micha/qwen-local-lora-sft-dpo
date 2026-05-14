"""Prepare small SFT datasets for Qwen LoRA training.

The first workflow uses either:

1. A local Alpaca-style JSON/JSONL file with `instruction`, optional `input`,
   and `output` fields.
2. A tiny built-in demo dataset for smoke testing.

Output format is Qwen chat JSONL:

{"messages":[{"role":"system","content":"..."},{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any


DEFAULT_SYSTEM_PROMPT = "你是一个清晰、严谨、擅长解释机器学习概念的中文助手。"

DEMO_SAMPLES = [
    {
        "instruction": "请解释什么是LoRA微调。",
        "output": "LoRA是一种参数高效微调方法。它冻结原始大模型参数，只在部分线性层旁边加入低秩矩阵进行训练，从而显著降低显存和训练成本。对个人学习者来说，LoRA的价值在于能用较小GPU完成可复现的微调实验。",
    },
    {
        "instruction": "SFT和DPO有什么区别？",
        "output": "SFT是有监督微调，使用高质量问题和标准答案教模型模仿目标回答风格。DPO是偏好优化，使用chosen和rejected成对样本，让模型更偏向人类更喜欢的回答。通常先做SFT获得基础能力，再用DPO调整偏好和边界。",
    },
    {
        "instruction": "为什么第一次学习大模型微调适合用0.5B小模型？",
        "output": "0.5B模型显存压力小、下载快、训练迭代快，适合把环境、数据格式、LoRA配置、训练日志和推理验证完整跑通。第一次项目的重点是理解链路，而不是追求模型规模。",
    },
    {
        "instruction": "LoRA训练中lora_r和lora_alpha分别是什么意思？",
        "output": "lora_r表示低秩矩阵的秩，越大可训练容量越强但显存和计算开销也更高。lora_alpha是缩放系数，用来调节LoRA更新对原模型的影响强度。小模型入门可以先用r=8、alpha=16这样的保守配置。",
    },
    {
        "instruction": "如何判断一次SFT实验是否值得记录？",
        "output": "至少记录模型名、数据量、最大长度、batch size、梯度累积、学习率、epoch、训练时间、显存占用、loss变化和推理样例。即使效果不好，只要能解释原因和下一步改进，也值得写进实验日志。",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare SFT train/eval JSONL files.")
    parser.add_argument("--input_file", default=None, help="Optional local JSON/JSONL Alpaca-style file.")
    parser.add_argument("--train_file", default="data/processed/sft_train.jsonl")
    parser.add_argument("--eval_file", default="data/processed/sft_eval.jsonl")
    parser.add_argument("--eval_ratio", type=float, default=0.2)
    parser.add_argument("--max_samples", type=int, default=1000)
    parser.add_argument("--min_answer_chars", type=int, default=10)
    parser.add_argument("--system_prompt", default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--demo", action="store_true", help="Use built-in demo samples.")
    return parser.parse_args()


def read_json_or_jsonl(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        if isinstance(data, dict):
            for key in ("data", "train", "examples"):
                if isinstance(data.get(key), list):
                    return data[key]
            raise ValueError("JSON dict input must contain a list under data/train/examples.")
        if isinstance(data, list):
            return data
        raise ValueError("JSON input must be a list or supported dict.")

    rows = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc
    return rows


def normalize_prompt(sample: dict[str, Any]) -> tuple[str, str] | None:
    if "messages" in sample and isinstance(sample["messages"], list):
        user = ""
        assistant = ""
        for msg in sample["messages"]:
            if msg.get("role") == "user":
                user = str(msg.get("content", "")).strip()
            elif msg.get("role") == "assistant":
                assistant = str(msg.get("content", "")).strip()
        return (user, assistant) if user and assistant else None

    instruction = str(sample.get("instruction", "")).strip()
    input_text = str(sample.get("input", "")).strip()
    output = str(sample.get("output", sample.get("answer", ""))).strip()
    if not instruction or not output:
        return None

    prompt = instruction if not input_text else f"{instruction}\n\n补充信息：{input_text}"
    return prompt, output


def convert_sample(sample: dict[str, Any], system_prompt: str, min_answer_chars: int) -> dict[str, Any] | None:
    normalized = normalize_prompt(sample)
    if normalized is None:
        return None
    user, assistant = normalized
    if len(assistant) < min_answer_chars:
        return None
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ]
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    if args.demo:
        raw_samples = DEMO_SAMPLES
    elif args.input_file:
        raw_samples = read_json_or_jsonl(Path(args.input_file))
    else:
        raise SystemExit("Use --demo or provide --input_file.")

    random.seed(args.seed)
    random.shuffle(raw_samples)
    raw_samples = raw_samples[: args.max_samples]

    seen_prompts: set[str] = set()
    converted: list[dict[str, Any]] = []
    dropped = 0
    duplicates = 0

    for sample in raw_samples:
        row = convert_sample(sample, args.system_prompt, args.min_answer_chars)
        if row is None:
            dropped += 1
            continue
        prompt = row["messages"][1]["content"]
        if prompt in seen_prompts:
            duplicates += 1
            continue
        seen_prompts.add(prompt)
        converted.append(row)

    if len(converted) < 2:
        raise SystemExit("Need at least 2 valid samples to split train/eval.")

    eval_size = max(1, int(len(converted) * args.eval_ratio))
    eval_rows = converted[:eval_size]
    train_rows = converted[eval_size:]

    write_jsonl(Path(args.train_file), train_rows)
    write_jsonl(Path(args.eval_file), eval_rows)

    print("Raw samples:", len(raw_samples))
    print("Valid samples:", len(converted))
    print("Train samples:", len(train_rows))
    print("Eval samples:", len(eval_rows))
    print("Dropped samples:", dropped)
    print("Duplicate prompts:", duplicates)
    print("Train file:", args.train_file)
    print("Eval file:", args.eval_file)


if __name__ == "__main__":
    main()
