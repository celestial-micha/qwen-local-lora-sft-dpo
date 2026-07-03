"""Compare arbitrary model/adapters on the Stage 8 behavior prompt suite.

The older comparison helpers were tied to fixed Stage 4/5 variants. Stage 8
needs repeated comparisons across old SFT, new SFT, and DPO candidates, so this
script accepts explicit variant specs and runs them one at a time to stay
friendly to an 8GB GPU.
"""

from __future__ import annotations

import argparse
import gc
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer


DEFAULT_SYSTEM_PROMPT = (
    "你是一个清晰、严谨、适合初学者的大模型微调中文助教。"
    "回答时优先解释 LoRA、SFT、DPO、数据清洗、显存、评估和实验复盘。"
)


@dataclass(frozen=True)
class Variant:
    key: str
    label: str
    adapter_path: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare Stage 8 model variants.")
    parser.add_argument("--model_name", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument(
        "--prompt_file",
        default="data/samples/custom_technical_prompts_stage8_expanded.jsonl",
    )
    parser.add_argument("--output_file", required=True)
    parser.add_argument(
        "--variant",
        action="append",
        required=True,
        help="Variant spec: answer_key=label=adapter_path. Use none for base model.",
    )
    parser.add_argument("--max_new_tokens", type=int, default=160)
    parser.add_argument("--system_prompt", default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument("--dtype", choices=["auto", "fp16", "bf16", "fp32"], default="auto")
    parser.add_argument("--local_files_only", action="store_true", default=True)
    return parser.parse_args()


def parse_variant(text: str) -> Variant:
    parts = text.split("=", maxsplit=2)
    if len(parts) != 3:
        raise ValueError(f"Invalid variant spec {text!r}; expected key=label=adapter_path")
    key, label, adapter_path = [part.strip() for part in parts]
    if not key.endswith("_answer"):
        raise ValueError(f"Variant key must end with _answer: {key}")
    if not key or not label:
        raise ValueError(f"Variant key and label must be non-empty: {text!r}")
    adapter = None if adapter_path.lower() in {"", "none", "base"} else adapter_path
    return Variant(key=key, label=label, adapter_path=adapter)


def read_prompt_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            prompt = str(row.get("prompt", "")).strip()
            if not prompt:
                raise ValueError(f"Missing/empty prompt in {path}:{line_no}")
            row["prompt"] = prompt
            rows.append(row)
    if not rows:
        raise ValueError(f"No prompts loaded from {path}")
    return rows


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
    dtype_name: str,
    local_files_only: bool,
) -> torch.nn.Module:
    dtype = select_dtype(dtype_name)
    dtype_arg = "dtype" if int(transformers.__version__.split(".", maxsplit=1)[0]) >= 5 else "torch_dtype"
    kwargs: dict[str, Any] = {
        dtype_arg: dtype,
        "local_files_only": local_files_only,
    }
    if torch.cuda.is_available():
        kwargs["device_map"] = "auto"
    model = AutoModelForCausalLM.from_pretrained(model_name, **kwargs)
    if adapter_path:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, adapter_path)
    if not torch.cuda.is_available():
        model.to(torch.device("cpu"))
    model.eval()
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
    return model_inputs, model_inputs["input_ids"].shape[-1]


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
    kwargs: dict[str, Any] = {
        **model_inputs,
        "max_new_tokens": max_new_tokens,
        "do_sample": do_sample,
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id,
    }
    if do_sample:
        kwargs["temperature"] = temperature
        kwargs["top_p"] = top_p
    with torch.inference_mode():
        output_ids = model.generate(**kwargs)
    return tokenizer.decode(output_ids[0, prompt_len:], skip_special_tokens=True).strip()


def run_variant(
    variant: Variant,
    prompts: list[str],
    args: argparse.Namespace,
    tokenizer: AutoTokenizer,
) -> list[str]:
    print(f"Loading {variant.label} ({variant.key})...")
    model = load_model(args.model_name, variant.adapter_path, args.dtype, args.local_files_only)
    answers: list[str] = []
    for index, prompt in enumerate(prompts, start=1):
        answers.append(
            generate_one(
                model,
                tokenizer,
                prompt,
                args.system_prompt,
                args.max_new_tokens,
                args.temperature,
                args.top_p,
            )
        )
        print(f"{variant.label}: generated {index}/{len(prompts)}")
    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return answers


def main() -> None:
    args = parse_args()
    variants = [parse_variant(text) for text in args.variant]
    prompt_rows = read_prompt_rows(Path(args.prompt_file))
    prompts = [str(row["prompt"]) for row in prompt_rows]

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, local_files_only=args.local_files_only)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    outputs: dict[str, list[str]] = {}
    variant_meta = {
        variant.key: {"label": variant.label, "adapter_path": variant.adapter_path or "base"}
        for variant in variants
    }
    for variant in variants:
        outputs[variant.key] = run_variant(variant, prompts, args, tokenizer)

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as f:
        for index, prompt in enumerate(prompts):
            row = dict(prompt_rows[index])
            row["prompt"] = prompt
            row["variant_meta"] = variant_meta
            for variant in variants:
                row[variant.key] = outputs[variant.key][index]
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("Saved comparison to:", output_path)


if __name__ == "__main__":
    main()
