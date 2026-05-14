"""Compare base, public-SFT, and custom-SFT outputs for fixed prompts.

This script favors reproducibility and low memory use over speed. It launches
the existing inference script separately for each model variant so we do not
keep multiple adapters or model copies in GPU memory at the same time.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare base, public-SFT, and custom-SFT outputs.")
    parser.add_argument("--prompt_file", default="data/samples/custom_technical_prompts.jsonl")
    parser.add_argument("--public_adapter_path", default="outputs/sft_lora_qwen05b_public")
    parser.add_argument("--custom_adapter_path", default="outputs/sft_lora_qwen05b_custom")
    parser.add_argument("--output_file", default="reports/compare_outputs_three_way_custom.jsonl")
    parser.add_argument("--max_new_tokens", type=int, default=128)
    parser.add_argument(
        "--system_prompt",
        default=(
            "你是一个清晰、严谨、适合初学者的大模型微调中文助教。"
            "回答时优先解释 LoRA、SFT、DPO、数据清洗、显存和实验复盘。"
        ),
    )
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument("--local_files_only", action="store_true", default=True)
    return parser.parse_args()


def read_prompts(path: Path) -> list[str]:
    prompts = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            prompts.append(row["prompt"])
    return prompts


def run_infer(
    prompt: str,
    adapter_path: str | None,
    max_new_tokens: int,
    system_prompt: str,
    temperature: float,
    top_p: float,
    local_files_only: bool,
) -> str:
    cmd = [
        sys.executable,
        "scripts/infer.py",
        "--prompt",
        prompt,
        "--system_prompt",
        system_prompt,
        "--max_new_tokens",
        str(max_new_tokens),
        "--temperature",
        str(temperature),
        "--top_p",
        str(top_p),
    ]
    if local_files_only:
        cmd.append("--local_files_only")
    if adapter_path:
        cmd.extend(["--adapter_path", adapter_path])

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    return result.stdout.strip()


def main() -> None:
    args = parse_args()
    prompts = read_prompts(Path(args.prompt_file))
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for index, prompt in enumerate(prompts, start=1):
            base_answer = run_infer(
                prompt,
                None,
                args.max_new_tokens,
                args.system_prompt,
                args.temperature,
                args.top_p,
                args.local_files_only,
            )
            public_answer = run_infer(
                prompt,
                args.public_adapter_path,
                args.max_new_tokens,
                args.system_prompt,
                args.temperature,
                args.top_p,
                args.local_files_only,
            )
            custom_answer = run_infer(
                prompt,
                args.custom_adapter_path,
                args.max_new_tokens,
                args.system_prompt,
                args.temperature,
                args.top_p,
                args.local_files_only,
            )
            row = {
                "prompt": prompt,
                "base_answer": base_answer,
                "public_sft_answer": public_answer,
                "custom_sft_answer": custom_answer,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"Compared {index}/{len(prompts)}:", prompt)

    print("Saved three-way comparison to:", output_path)


if __name__ == "__main__":
    main()
