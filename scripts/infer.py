# 运行本地推理，默认模型是 Qwen2.5-0.5B-Instruct，也可以额外加载 LoRA 微调权重。
"""Run local inference with Qwen2.5-0.5B-Instruct and optional LoRA adapter."""

# 便于添加注释，注释更灵活：
from __future__ import annotations

# 导入了几个核心库
import argparse
from typing import Any

import torch
import transformers

# AutoModelForCausalLM：加载因果语言模型，也就是生成式大语言模型。 AutoTokenizer：加载对应 tokenizer。
from transformers import AutoModelForCausalLM, AutoTokenizer

# 默认使用的是 Hugging Face 上的qwen模型：
DEFAULT_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
# 默认的系统提示词，这会作为聊天消息里的 system 角色传给模型。
DEFAULT_SYSTEM_PROMPT = (
    "You are a clear and rigorous assistant. Answer in Chinese unless the user "
    "asks for another language."
)

'''
这个函数负责解析用户在命令行里传入的参数。
比如你可以这样运行：
python infer.py --prompt "请解释一下 LoRA 是什么"

adapter是LoRA adapter 路径，如果不传，就只用原始模型。

parser.add_argument("--prompt", required=True)指的用户输入的问题。

parser.add_argument("--top_p", type=float, default=0.9)表示从累计概率最高的前 p 部分词里采样。

parser.add_argument("--local_files_only", action="store_true")如果加上这个参数，就只从本地缓存加载模型，不联网下载。
'''
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


# select_dtype()：选择模型精度
# 分别是fp16,bf16,fb32
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


# load_model()：加载 tokenizer模型和 LoRA
# 它返回三个东西：tokenizer, model, device
def load_model(args: argparse.Namespace) -> tuple[AutoTokenizer, torch.nn.Module, torch.device]:
    # 选择 dtype 和设备：如果有 CUDA，就用 GPU；否则用 CPU。 （dtype应该就是精度）
    dtype = select_dtype(args.dtype)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 加载 tokenizer。从 Hugging Face 或本地缓存加载 tokenizer。
    tokenizer = AutoTokenizer.from_pretrained(
        args.model_name,
        local_files_only=args.local_files_only,
    )

    # 有些生成模型没有单独的 pad_token。为了避免生成时报错，就把 padding token 设置成 eos toke
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 兼容 Transformers v4 和 v5。
    # Transformers v4 通常使用torch_dtype=... ;
    # Transformers v5 以后可能改成： dtype=...
    dtype_arg = "dtype" if int(transformers.__version__.split(".", maxsplit=1)[0]) >= 5 else "torch_dtype"
    
    # 构造模型时加载参数：
    model_kwargs: dict[str, Any] = {
        dtype_arg: dtype,
        "local_files_only": args.local_files_only,
    }

    # 如果有 GPU：这表示让 Transformers 自动把模型放到合适设备上。
    if torch.cuda.is_available():
        model_kwargs["device_map"] = "auto"

    # 真正加载大语言模型
    model = AutoModelForCausalLM.from_pretrained(args.model_name, **model_kwargs)

    # 可选加载 LoRA adapter
    # 如果用户传了：--adapter_path 那么就会在基础模型上加载 LoRA 微调权重。
    # 注意：这要求安装 peft：
    if args.adapter_path:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, args.adapter_path)

    # 如果没有 GPU，就把模型放到 CPU 上。
    if not torch.cuda.is_available():
        model.to(device)

    # 评估模式
    model.eval()
    return tokenizer, model, device


# 构造模型输入
# 负责把用户 prompt 转成模型能理解的 tensor。
def build_model_inputs(
    tokenizer: AutoTokenizer,
    args: argparse.Namespace,
    device: torch.device,
) -> tuple[dict[str, torch.Tensor], int]:
    
    # 这里构造了聊天格式：
    # system: 你是一个清晰严谨的助手……
    # user: 用户的问题
    messages = [
        {"role": "system", "content": args.system_prompt},
        {"role": "user", "content": args.prompt},
    ]

    try:
        # 调用apply_chat_template() ，函数会根据 Qwen 的聊天模板，把 messages 转成模型训练时熟悉的格式。
        '''
        比如内部可能会变成类似：
        <|im_start|>system
        ...
        <|im_end|>
        <|im_start|>user
        ...
        <|im_end|>
        <|im_start|>assistant

        add_generation_prompt=True表示在最后加上 assistant 开始回答的标记，让模型知道该继续生成回答了。

        为什么有 try except TypeError？
        因为不同版本的 Transformers 对 apply_chat_template() 支持不完全一样。
        有些旧版本可能不支持 return_dict=True，所以这里做了兼容。
        '''
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

    # 后面这段是在处理 encoded 的不同可能返回形式：
    # 可能出现三种情况：
    #   1. 返回的是一个 torch.Tensor
    #   2. 返回的是类似字典的 BatchEncoding
    #   3. 返回的是普通 token id 列表

    # 最终统一成：
    # model_inputs = {
    #    "input_ids": ...
    # }
    if isinstance(encoded, torch.Tensor):
        model_inputs = {"input_ids": encoded.to(device)}
    elif hasattr(encoded, "to"):
        moved = encoded.to(device)
        model_inputs = {key: value for key, value in moved.items() if isinstance(value, torch.Tensor)}
    else:
        model_inputs = {"input_ids": torch.tensor([encoded], dtype=torch.long, device=device)}

    # 如果没有 input_ids，就报错：
    if "input_ids" not in model_inputs:
        raise TypeError("Chat template did not produce input_ids.")

    # 最后记录 prompt 长度：
    # 这个长度后面用来区分：
    #   哪些 token 是输入 prompt
    #   哪些 token 是模型新生成的回答
    prompt_len = model_inputs["input_ids"].shape[-1]
    return model_inputs, prompt_len

# generate()：真正生成回答
def generate(args: argparse.Namespace) -> str:
    # 第一步，加载模型
    tokenizer, model, device = load_model(args)
    # 第二部，构造输入
    model_inputs, prompt_len = build_model_inputs(tokenizer, args, device)

    # 第三步：判断是否采样。
    # 如果 temperature > 0，就启用采样。
    # 如果 temperature = 0，就不采样，生成更确定。
    do_sample = args.temperature > 0
    generation_kwargs: dict[str, Any] = {
        **model_inputs,
        "max_new_tokens": args.max_new_tokens,
        "do_sample": do_sample,
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id,
    }

    # 如果启用采样：
    if do_sample:
        generation_kwargs["temperature"] = args.temperature
        generation_kwargs["top_p"] = args.top_p

    # 真正调用生成：
    # torch.inference_mode() 会关闭梯度计算，比 no_grad() 更适合纯推理。
    with torch.inference_mode():
        output_ids = model.generate(**generation_kwargs)

    # 如果用户加了：--print_full_text，就输出完整文本：
    # (输入 prompt + 新生成回答)
    if args.print_full_text:
        return tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()

    # 否则只输出新生成的部分：
    # 用：output_ids[0, prompt_len:]把前面的输入切掉，只保留回答。
    new_tokens = output_ids[0, prompt_len:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def main() -> None:
    args = parse_args()
    print(generate(args))


if __name__ == "__main__":
    main()
