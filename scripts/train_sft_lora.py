"""Train a LoRA SFT adapter for Qwen2.5-0.5B-Instruct.

This first version intentionally uses Transformers Trainer + PEFT instead of a
high-level TRL trainer. It keeps the training path explicit and easier to debug
on Windows.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
import transformers
from torch.utils.data import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments

from peft import LoraConfig, TaskType, get_peft_model


IGNORE_INDEX = -100


@dataclass
class ChatExample:
    input_ids: list[int]
    attention_mask: list[int]
    labels: list[int]


class ChatSFTDataset(Dataset[ChatExample]):
    def __init__(self, path: str, tokenizer: AutoTokenizer, max_length: int) -> None:
        self.examples: list[ChatExample] = []
        self.tokenizer = tokenizer
        self.max_length = max_length

        with Path(path).open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                try:
                    self.examples.append(self.encode(row["messages"]))
                except Exception as exc:
                    raise ValueError(f"Failed to encode {path}:{line_no}: {exc}") from exc

        if not self.examples:
            raise ValueError(f"No examples loaded from {path}")

    def encode(self, messages: list[dict[str, str]]) -> ChatExample:
        prompt_messages = messages[:-1]
        assistant_message = messages[-1]
        if assistant_message.get("role") != "assistant":
            raise ValueError("Last message must be assistant.")

        prompt_ids = self.tokenizer.apply_chat_template(
            prompt_messages,
            add_generation_prompt=True,
            return_tensors=None,
        )
        full_ids = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=False,
            return_tensors=None,
        )

        if len(full_ids) > self.max_length:
            full_ids = full_ids[: self.max_length]
        prompt_len = min(len(prompt_ids), len(full_ids))
        labels = [IGNORE_INDEX] * prompt_len + full_ids[prompt_len:]
        labels = labels[: len(full_ids)]
        attention_mask = [1] * len(full_ids)
        return ChatExample(input_ids=full_ids, attention_mask=attention_mask, labels=labels)

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> ChatExample:
        return self.examples[index]


class DataCollatorForChatSFT:
    def __init__(self, tokenizer: AutoTokenizer) -> None:
        self.tokenizer = tokenizer

    def __call__(self, features: list[ChatExample]) -> dict[str, torch.Tensor]:
        max_len = max(len(x.input_ids) for x in features)
        pad_id = self.tokenizer.pad_token_id

        input_ids = []
        attention_mask = []
        labels = []

        for feature in features:
            pad_len = max_len - len(feature.input_ids)
            input_ids.append(feature.input_ids + [pad_id] * pad_len)
            attention_mask.append(feature.attention_mask + [0] * pad_len)
            labels.append(feature.labels + [IGNORE_INDEX] * pad_len)

        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Qwen LoRA SFT locally.")
    parser.add_argument("--model_name", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--train_file", default="data/processed/sft_train.jsonl")
    parser.add_argument("--eval_file", default="data/processed/sft_eval.jsonl")
    parser.add_argument("--output_dir", default="outputs/sft_lora_qwen05b")
    parser.add_argument("--max_length", type=int, default=512)
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--grad_accum", type=int, default=8)
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--lora_r", type=int, default=8)
    parser.add_argument("--lora_alpha", type=int, default=16)
    parser.add_argument("--lora_dropout", type=float, default=0.05)
    parser.add_argument("--logging_steps", type=int, default=10)
    parser.add_argument("--eval_steps", type=int, default=100)
    parser.add_argument("--save_steps", type=int, default=100)
    parser.add_argument("--report_to", default="tensorboard")
    parser.add_argument("--local_files_only", action="store_true")
    parser.add_argument("--gradient_checkpointing", action="store_true")
    return parser.parse_args()


def load_tokenizer(model_name: str, local_files_only: bool) -> AutoTokenizer:
    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=local_files_only)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def load_model(args: argparse.Namespace) -> torch.nn.Module:
    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
    dtype_arg = "dtype" if int(transformers.__version__.split(".", maxsplit=1)[0]) >= 5 else "torch_dtype"
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        **{dtype_arg: dtype if torch.cuda.is_available() else torch.float32},
        device_map="auto" if torch.cuda.is_available() else None,
        local_files_only=args.local_files_only,
    )
    model.config.use_cache = False

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, lora_config)
    if args.gradient_checkpointing and hasattr(model, "enable_input_require_grads"):
        model.enable_input_require_grads()
    return model


def main() -> None:
    args = parse_args()
    tokenizer = load_tokenizer(args.model_name, args.local_files_only)
    train_dataset = ChatSFTDataset(args.train_file, tokenizer, args.max_length)
    eval_dataset = ChatSFTDataset(args.eval_file, tokenizer, args.max_length)
    model = load_model(args)
    model.print_trainable_parameters()

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=args.grad_accum,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        logging_steps=args.logging_steps,
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        save_steps=args.save_steps,
        save_total_limit=2,
        bf16=torch.cuda.is_available() and torch.cuda.is_bf16_supported(),
        fp16=torch.cuda.is_available() and not torch.cuda.is_bf16_supported(),
        report_to=[] if args.report_to.lower() == "none" else [args.report_to],
        remove_unused_columns=False,
        gradient_checkpointing=args.gradient_checkpointing,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=DataCollatorForChatSFT(tokenizer),
    )
    trainer.train()
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print("Saved LoRA adapter to:", args.output_dir)


if __name__ == "__main__":
    main()
