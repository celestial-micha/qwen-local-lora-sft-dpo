"""Compare base, public-SFT, custom-SFT v3, and tiny-DPO outputs.

Stage 5C uses the same fixed prompt suite as Stage 4B. The script loads only
one model variant at a time so it stays friendly to an 8GB GPU.
"""

from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
from typing import Any

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer


DEFAULT_SYSTEM_PROMPT = (
    "你是一个清晰、严谨、适合初学者的大模型微调中文助教。"
    "回答时优先解释 LoRA、SFT、DPO、数据清洗、显存和实验复盘。"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare four model variants on fixed prompts.")
    parser.add_argument("--model_name", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--prompt_file", default="data/samples/custom_technical_prompts.jsonl")
    parser.add_argument("--public_adapter_path", default="outputs/sft_lora_qwen05b_public")
    parser.add_argument("--custom_adapter_path", default="outputs/sft_lora_qwen05b_custom_v3_from_v1_patch")
    parser.add_argument("--dpo_adapter_path", default="outputs/dpo_lora_qwen05b_tiny")
    parser.add_argument("--output_file", default="reports/compare_outputs_four_way_dpo_tiny.jsonl")
    parser.add_argument("--max_new_tokens", type=int, default=128)
    parser.add_argument("--system_prompt", default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument("--dtype", choices=["auto", "fp16", "bf16", "fp32"], default="auto")
    parser.add_argument("--local_files_only", action="store_true", default=True)
    return parser.parse_args()


def read_prompt_rows(path: Path) -> list[dict[str, Any]]:
    prompt_rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            try:
                prompt = str(row["prompt"]).strip()
            except KeyError as exc:
                raise ValueError(f"Missing prompt in {path}:{line_no}") from exc
            if not prompt:
                raise ValueError(f"Empty prompt in {path}:{line_no}")
            prompt_row = dict(row)
            prompt_row["prompt"] = prompt
            prompt_rows.append(prompt_row)
    if not prompt_rows:
        raise ValueError(f"No prompts loaded from {path}")
    return prompt_rows


def select_dtype(name: str) -> torch.dtype:
    if name == "fp16":
        return torch.float16
    if name == "bf16":
        return torch.bfloat16
    if name == "fp32":
        return torch.float32
    if torch.cuda.is_available():
        return torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    return torch.float32


def load_model(
    model_name: str,
    adapter_path: str | None,
    tokenizer: AutoTokenizer,
    dtype_name: str,
    local_files_only: bool,
) -> torch.nn.Module:
    dtype = select_dtype(dtype_name)
    dtype_arg = "dtype" if int(transformers.__version__.split(".", maxsplit=1)[0]) >= 5 else "torch_dtype"
    model_kwargs: dict[str, Any] = {
        dtype_arg: dtype,
        "local_files_only": local_files_only,
    }
    if torch.cuda.is_available():
        model_kwargs["device_map"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
    if adapter_path:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, adapter_path)

    if not torch.cuda.is_available():
        model.to(torch.device("cpu"))
    model.eval()
    tokenizer.padding_side = "left"
    return model


def build_inputs(
    tokenizer: AutoTokenizer,
    prompt: str,
    system_prompt: str,
    device: torch.device,
) -> tuple[dict[str, torch.Tensor], int]:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    try:
        encoded = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
        )
    except TypeError:
        encoded = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        )

    if isinstance(encoded, torch.Tensor):
        model_inputs = {"input_ids": encoded.to(device)}
    elif hasattr(encoded, "to"):
        moved = encoded.to(device)
        model_inputs = {key: value for key, value in moved.items() if isinstance(value, torch.Tensor)}
    else:
        model_inputs = {"input_ids": torch.tensor([encoded], dtype=torch.long, device=device)}

    prompt_len = model_inputs["input_ids"].shape[-1]
    return model_inputs, prompt_len


def generate_one(
    model: torch.nn.Module,
    tokenizer: AutoTokenizer,
    prompt: str,
    system_prompt: str,
    max_new_tokens: int,
    temperature: float,
    top_p: float,
) -> str:
    device = next(model.parameters()).device
    model_inputs, prompt_len = build_inputs(tokenizer, prompt, system_prompt, device)
    do_sample = temperature > 0
    generation_kwargs: dict[str, Any] = {
        **model_inputs,
        "max_new_tokens": max_new_tokens,
        "do_sample": do_sample,
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id,
    }
    if do_sample:
        generation_kwargs["temperature"] = temperature
        generation_kwargs["top_p"] = top_p

    with torch.inference_mode():
        output_ids = model.generate(**generation_kwargs)
    new_tokens = output_ids[0, prompt_len:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def run_variant(
    name: str,
    adapter_path: str | None,
    prompts: list[str],
    args: argparse.Namespace,
    tokenizer: AutoTokenizer,
) -> list[str]:
    print(f"Loading {name}...")
    model = load_model(args.model_name, adapter_path, tokenizer, args.dtype, args.local_files_only)
    answers: list[str] = []
    for index, prompt in enumerate(prompts, start=1):
        answer = generate_one(
            model,
            tokenizer,
            prompt,
            args.system_prompt,
            args.max_new_tokens,
            args.temperature,
            args.top_p,
        )
        answers.append(answer)
        print(f"{name}: generated {index}/{len(prompts)}")

    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return answers


def main() -> None:
    args = parse_args()
    prompt_rows = read_prompt_rows(Path(args.prompt_file))
    prompts = [str(row["prompt"]) for row in prompt_rows]
    tokenizer = AutoTokenizer.from_pretrained(args.model_name, local_files_only=args.local_files_only)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    variants = [
        ("base_answer", None, "base"),
        ("public_sft_answer", args.public_adapter_path, "public-SFT"),
        ("custom_sft_v3_answer", args.custom_adapter_path, "custom-SFT-v3"),
        ("dpo_tiny_answer", args.dpo_adapter_path, "DPO-tiny"),
    ]

    outputs: dict[str, list[str]] = {}
    for key, adapter_path, label in variants:
        outputs[key] = run_variant(label, adapter_path, prompts, args, tokenizer)

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for index, prompt in enumerate(prompts):
            row = dict(prompt_rows[index])
            row["prompt"] = prompt
            for key in outputs:
                row[key] = outputs[key][index]
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print("Saved four-way comparison to:", output_path)


if __name__ == "__main__":
    main()
