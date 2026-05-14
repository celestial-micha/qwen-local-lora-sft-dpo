"""Run local inference with Qwen2.5-0.5B-Instruct and optional LoRA adapter."""

from __future__ import annotations

import argparse
from typing import Any

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer


DEFAULT_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
DEFAULT_SYSTEM_PROMPT = (
    "You are a clear and rigorous assistant. Answer in Chinese unless the user "
    "asks for another language."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Qwen local inference.")
    parser.add_argument("--model_name", default=DEFAULT_MODEL)
    parser.add_argument("--adapter_path", default=None)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--system_prompt", default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--max_new_tokens", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument("--dtype", choices=["auto", "fp16", "bf16", "fp32"], default="auto")
    parser.add_argument("--local_files_only", action="store_true")
    parser.add_argument("--print_full_text", action="store_true")
    return parser.parse_args()


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


def load_model(args: argparse.Namespace) -> tuple[AutoTokenizer, torch.nn.Module, torch.device]:
    dtype = select_dtype(args.dtype)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = AutoTokenizer.from_pretrained(
        args.model_name,
        local_files_only=args.local_files_only,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype_arg = "dtype" if int(transformers.__version__.split(".", maxsplit=1)[0]) >= 5 else "torch_dtype"
    model_kwargs: dict[str, Any] = {
        dtype_arg: dtype,
        "local_files_only": args.local_files_only,
    }
    if torch.cuda.is_available():
        model_kwargs["device_map"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(args.model_name, **model_kwargs)

    if args.adapter_path:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, args.adapter_path)

    if not torch.cuda.is_available():
        model.to(device)

    model.eval()
    return tokenizer, model, device


def build_model_inputs(
    tokenizer: AutoTokenizer,
    args: argparse.Namespace,
    device: torch.device,
) -> tuple[dict[str, torch.Tensor], int]:
    messages = [
        {"role": "system", "content": args.system_prompt},
        {"role": "user", "content": args.prompt},
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

    if "input_ids" not in model_inputs:
        raise TypeError("Chat template did not produce input_ids.")

    prompt_len = model_inputs["input_ids"].shape[-1]
    return model_inputs, prompt_len


def generate(args: argparse.Namespace) -> str:
    tokenizer, model, device = load_model(args)
    model_inputs, prompt_len = build_model_inputs(tokenizer, args, device)

    do_sample = args.temperature > 0
    generation_kwargs: dict[str, Any] = {
        **model_inputs,
        "max_new_tokens": args.max_new_tokens,
        "do_sample": do_sample,
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id,
    }
    if do_sample:
        generation_kwargs["temperature"] = args.temperature
        generation_kwargs["top_p"] = args.top_p

    with torch.inference_mode():
        output_ids = model.generate(**generation_kwargs)

    if args.print_full_text:
        return tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()

    new_tokens = output_ids[0, prompt_len:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def main() -> None:
    args = parse_args()
    print(generate(args))


if __name__ == "__main__":
    main()
