"""Generate base vs adapter outputs for fixed prompts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare base and LoRA adapter outputs.")
    parser.add_argument("--prompt_file", default="data/samples/smoke_prompts.jsonl")
    parser.add_argument("--adapter_path", default="outputs/sft_lora_qwen05b")
    parser.add_argument("--output_file", default="reports/compare_outputs.jsonl")
    parser.add_argument("--max_new_tokens", type=int, default=256)
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


def run_infer(prompt: str, adapter_path: str | None, max_new_tokens: int, local_files_only: bool) -> str:
    cmd = [
        sys.executable,
        "scripts/infer.py",
        "--prompt",
        prompt,
        "--max_new_tokens",
        str(max_new_tokens),
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
        for prompt in prompts:
            base_answer = run_infer(prompt, None, args.max_new_tokens, args.local_files_only)
            sft_answer = run_infer(prompt, args.adapter_path, args.max_new_tokens, args.local_files_only)
            row = {
                "prompt": prompt,
                "base_answer": base_answer,
                "sft_answer": sft_answer,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print("Compared:", prompt)

    print("Saved comparison to:", output_path)


if __name__ == "__main__":
    main()
