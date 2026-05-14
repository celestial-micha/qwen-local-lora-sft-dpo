"""Download a small real SFT dataset from Hugging Face.

This script intentionally saves a local raw JSONL snapshot first. Keeping the
raw file makes Stage 2 reproducible even if later conversion settings change.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

from datasets import DownloadConfig, load_dataset


DEFAULT_DATASET = "llm-wizard/alpaca-gpt4-data-zh"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download a real Alpaca-style Chinese SFT dataset.")
    parser.add_argument("--dataset_name", default=DEFAULT_DATASET)
    parser.add_argument("--split", default="train")
    parser.add_argument("--output_file", default="data/raw/alpaca_gpt4_data_zh_1200.jsonl")
    parser.add_argument("--max_samples", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--local_files_only", action="store_true")
    return parser.parse_args()


def row_to_plain_dict(row: dict[str, Any]) -> dict[str, Any]:
    """Convert dataset rows to JSON-serializable plain dictionaries."""
    plain: dict[str, Any] = {}
    for key, value in row.items():
        if value is None or isinstance(value, (str, int, float, bool, list, dict)):
            plain[key] = value
        else:
            plain[key] = str(value)
    return plain


def main() -> None:
    args = parse_args()
    dataset = load_dataset(
        args.dataset_name,
        split=args.split,
        download_mode="reuse_dataset_if_exists",
        download_config=DownloadConfig(local_files_only=args.local_files_only),
        verification_mode="no_checks",
    )

    total = len(dataset)
    indices = list(range(total))
    random.Random(args.seed).shuffle(indices)
    selected = indices[: min(args.max_samples, total)]

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for index in selected:
            f.write(json.dumps(row_to_plain_dict(dataset[index]), ensure_ascii=False) + "\n")

    print("Dataset:", args.dataset_name)
    print("Split:", args.split)
    print("Total samples:", total)
    print("Saved samples:", len(selected))
    print("Output file:", output_path)


if __name__ == "__main__":
    main()
