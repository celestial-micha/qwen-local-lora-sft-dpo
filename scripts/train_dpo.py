"""Run a tiny Stage 5B DPO smoke test.

This script is intentionally conservative. It is designed for the first local
8GB VRAM probe, not for full DPO training.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import torch
import transformers
from datasets import Dataset
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import DPOConfig, DPOTrainer


DEFAULT_SYSTEM_PROMPT = (
    "你是一个清晰、严谨、适合初学者的大模型微调中文助教。"
    "回答时优先解释 LoRA、SFT、DPO、数据清洗、显存和实验复盘。"
)


def parse_scalar(value: str) -> Any:
    text = value.strip()
    lowered = text.lower()
    if lowered in {"none", "null"}:
        return "none"
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if any(ch in lowered for ch in [".", "e"]):
            return float(text)
        return int(text)
    except ValueError:
        return text.strip("\"'")


def read_simple_yaml(path: str | None) -> dict[str, Any]:
    if not path:
        return {}

    config: dict[str, Any] = {}
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "#" in stripped:
            stripped = stripped.split("#", maxsplit=1)[0].strip()
        if not stripped:
            continue
        if ":" not in stripped:
            raise ValueError(f"Unsupported config line {path}:{line_no}: {line}")
        key, value = stripped.split(":", maxsplit=1)
        config[key.strip()] = parse_scalar(value)
    return config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Stage 5B tiny DPO.")
    parser.add_argument("--config", default="configs/dpo_qwen05b.yaml")
    parser.add_argument("--model_name", default=None)
    parser.add_argument("--sft_adapter_path", default=None)
    parser.add_argument("--dpo_file", default=None)
    parser.add_argument("--output_dir", default=None)
    parser.add_argument("--max_length", type=int, default=None)
    parser.add_argument("--max_prompt_length", type=int, default=None)
    parser.add_argument("--per_device_train_batch_size", type=int, default=None)
    parser.add_argument("--gradient_accumulation_steps", type=int, default=None)
    parser.add_argument("--learning_rate", type=float, default=None)
    parser.add_argument("--num_train_epochs", type=float, default=None)
    parser.add_argument("--beta", type=float, default=None)
    parser.add_argument("--logging_steps", type=int, default=None)
    parser.add_argument("--save_steps", type=int, default=None)
    parser.add_argument("--report_to", default=None)
    parser.add_argument("--local_files_only", action="store_true")
    parser.add_argument("--gradient_checkpointing", action="store_true")
    parser.add_argument(
        "--no_chat_template",
        action="store_true",
        help="Use raw prompt strings instead of Qwen chat-template prompts.",
    )
    parser.add_argument("--system_prompt", default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def merged_config(args: argparse.Namespace) -> dict[str, Any]:
    config = read_simple_yaml(args.config)
    defaults: dict[str, Any] = {
        "model_name": "Qwen/Qwen2.5-0.5B-Instruct",
        "sft_adapter_path": "outputs/sft_lora_qwen05b_custom_v3_from_v1_patch",
        "dpo_file": "data/processed/dpo_tiny_train.jsonl",
        "output_dir": "outputs/dpo_lora_qwen05b_tiny",
        "max_length": 256,
        "max_prompt_length": 128,
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 8,
        "learning_rate": 5e-5,
        "num_train_epochs": 1,
        "beta": 0.1,
        "logging_steps": 10,
        "save_steps": 200,
        "report_to": "none",
    }
    defaults.update(config)

    for key in defaults:
        value = getattr(args, key, None)
        if value is not None:
            defaults[key] = value
    return defaults


def load_tokenizer(model_name: str, local_files_only: bool) -> AutoTokenizer:
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=local_files_only)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def load_policy_model(config: dict[str, Any], local_files_only: bool) -> torch.nn.Module:
    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
    dtype_arg = "dtype" if int(transformers.__version__.split(".", maxsplit=1)[0]) >= 5 else "torch_dtype"
    base_model = AutoModelForCausalLM.from_pretrained(
        str(config["model_name"]),
        **{dtype_arg: dtype if torch.cuda.is_available() else torch.float32},
        device_map="auto" if torch.cuda.is_available() else None,
        local_files_only=local_files_only,
    )
    base_model.config.use_cache = False
    model = PeftModel.from_pretrained(
        base_model,
        str(config["sft_adapter_path"]),
        is_trainable=True,
    )
    return model


def read_dpo_rows(path: str, tokenizer: AutoTokenizer, system_prompt: str, use_chat_template: bool) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            try:
                prompt = str(row["prompt"]).strip()
                chosen = str(row["chosen"]).strip()
                rejected = str(row["rejected"]).strip()
            except KeyError as exc:
                raise ValueError(f"Missing key in {path}:{line_no}: {exc}") from exc
            if not prompt or not chosen or not rejected:
                raise ValueError(f"Empty prompt/chosen/rejected in {path}:{line_no}")

            if use_chat_template:
                prompt = tokenizer.apply_chat_template(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    add_generation_prompt=True,
                    tokenize=False,
                )
            rows.append({"prompt": prompt, "chosen": chosen, "rejected": rejected})

    if not rows:
        raise ValueError(f"No DPO rows loaded from {path}")
    return rows


def gpu_snapshot() -> dict[str, Any]:
    if not torch.cuda.is_available():
        return {"cuda": False}
    return {
        "cuda": True,
        "device": torch.cuda.get_device_name(0),
        "allocated_gb": round(torch.cuda.memory_allocated(0) / 1024**3, 3),
        "reserved_gb": round(torch.cuda.memory_reserved(0) / 1024**3, 3),
        "max_allocated_gb": round(torch.cuda.max_memory_allocated(0) / 1024**3, 3),
        "max_reserved_gb": round(torch.cuda.max_memory_reserved(0) / 1024**3, 3),
    }


def main() -> None:
    args = parse_args()
    config = merged_config(args)
    local_files_only = bool(args.local_files_only)

    tokenizer = load_tokenizer(str(config["model_name"]), local_files_only=local_files_only)
    rows = read_dpo_rows(
        str(config["dpo_file"]),
        tokenizer,
        system_prompt=args.system_prompt,
        use_chat_template=not args.no_chat_template,
    )
    train_dataset = Dataset.from_list(rows)
    model = load_policy_model(config, local_files_only=local_files_only)
    model.print_trainable_parameters()

    if args.gradient_checkpointing and hasattr(model, "enable_input_require_grads"):
        model.enable_input_require_grads()

    report_to = [] if str(config["report_to"]).lower() == "none" else [str(config["report_to"])]
    training_args = DPOConfig(
        output_dir=str(config["output_dir"]),
        per_device_train_batch_size=int(config["per_device_train_batch_size"]),
        gradient_accumulation_steps=int(config["gradient_accumulation_steps"]),
        learning_rate=float(config["learning_rate"]),
        num_train_epochs=float(config["num_train_epochs"]),
        beta=float(config["beta"]),
        max_length=int(config["max_length"]),
        max_prompt_length=int(config["max_prompt_length"]),
        logging_steps=int(config["logging_steps"]),
        save_steps=int(config["save_steps"]),
        save_strategy="steps",
        save_total_limit=1,
        eval_strategy="no",
        bf16=torch.cuda.is_available() and torch.cuda.is_bf16_supported(),
        fp16=torch.cuda.is_available() and not torch.cuda.is_bf16_supported(),
        report_to=report_to,
        remove_unused_columns=False,
        gradient_checkpointing=bool(args.gradient_checkpointing),
        seed=int(args.seed),
    )

    trainer = DPOTrainer(
        model=model,
        ref_model=None,
        args=training_args,
        train_dataset=train_dataset,
        processing_class=tokenizer,
    )

    print("Stage 5B tiny DPO config:")
    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("Rows:", len(rows))
    print("GPU before train:", json.dumps(gpu_snapshot(), ensure_ascii=False))
    start = time.perf_counter()
    trainer.train()
    elapsed = time.perf_counter() - start
    trainer.save_model(str(config["output_dir"]))
    tokenizer.save_pretrained(str(config["output_dir"]))
    print("GPU after train:", json.dumps(gpu_snapshot(), ensure_ascii=False))
    print(f"Runtime seconds: {elapsed:.1f}")
    print("Saved DPO LoRA adapter to:", config["output_dir"])


if __name__ == "__main__":
    main()
