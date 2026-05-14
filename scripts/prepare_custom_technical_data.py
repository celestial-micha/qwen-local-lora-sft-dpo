"""Prepare Stage 2B custom technical SFT data.

The first custom-data pass deliberately uses project-owned technical notes and
curated concept seeds. This keeps the data legally clean and reproducible while
still exercising the real data pipeline:

collect -> clean -> filter -> deduplicate -> rewrite into instruction samples
        -> convert into Qwen chat JSONL

The script also supports optional URL collection for later iterations, but the
default run does not depend on external network access.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


DEFAULT_SYSTEM_PROMPT = (
    "你是一个清晰、严谨、适合初学者的大模型微调中文助教。"
    "回答时优先解释 LoRA、SFT、DPO、数据清洗、显存和实验复盘。"
)

DEFAULT_LOCAL_SOURCES = [
    "README.zh-CN.md",
    "PROJECT_RUNBOOK.md",
    "reports/beginner_learning_report_zh.md",
    "reports/data_pipeline_plan.md",
    "reports/stage2_sft_data_report.md",
    "reports/stage3a_public_lora_sft_report.md",
    "reports/stage4a_public_sft_comparison_report.md",
    "reports/vram_and_dpo_plan.md",
    "reports/windows_debug_report.md",
    "reports/project_context_for_next_chat.md",
]

TECH_KEYWORDS = [
    "LoRA",
    "SFT",
    "DPO",
    "adapter",
    "Qwen",
    "CUDA",
    "显存",
    "训练",
    "微调",
    "数据",
    "清洗",
    "去重",
    "instruction",
    "Hugging Face",
    "PEFT",
    "loss",
    "batch",
    "gradient",
    "Windows",
    "推理",
    "对比",
]


@dataclass
class SourceRecord:
    source_id: str
    source_type: str
    title: str
    path_or_url: str
    raw_text: str


class TextOnlyHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "nav", "footer", "header", "noscript"}:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "nav", "footer", "header", "noscript"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            text = data.strip()
            if text:
                self.parts.append(text)

    def text(self) -> str:
        return "\n".join(self.parts)


CURATED_CONCEPTS: list[dict[str, str]] = [
    {
        "name": "LoRA",
        "definition": "LoRA 是一种参数高效微调方法。它冻结基础模型大部分参数，只训练插入到线性层旁边的低秩 adapter 矩阵。",
        "project_use": "本项目用 LoRA 在 8GB RTX 4060 上训练 Qwen2.5-0.5B-Instruct，避免全量微调带来的显存压力。",
        "mistake": "不要把机器学习里的 LoRA 和无线通信里的 LoRa 混为一谈。",
    },
    {
        "name": "SFT",
        "definition": "SFT 是 supervised fine-tuning，有监督微调。它用 instruction-answer 或 chat messages 数据教模型模仿目标回答。",
        "project_use": "本项目的训练目标是 SFT，数据格式是 system、user、assistant 三段式 Qwen chat JSONL。",
        "mistake": "SFT 不是某个网络安全缩写，也不是某种模型结构；它描述的是训练目标。",
    },
    {
        "name": "LoRA SFT",
        "definition": "LoRA SFT 指用 LoRA adapter 来执行 SFT。SFT 是目标，LoRA 是实现这个目标的参数高效方法。",
        "project_use": "本项目先用公开数据训练 public LoRA SFT adapter，再计划用自采集技术数据训练 custom 或 mixed adapter。",
        "mistake": "不要把 LoRA 和 SFT 当成互斥选项；它们在本项目里是方法和目标的关系。",
    },
    {
        "name": "DPO",
        "definition": "DPO 是 direct preference optimization，直接偏好优化。它用 chosen/rejected 成对回答让模型更偏向好的回答。",
        "project_use": "本项目把 DPO 放在 SFT 稳定之后，因为 DPO 依赖较好的基础回答能力和偏好样本质量。",
        "mistake": "DPO 不是数据保护对象，也不是灾备计划；在大模型训练里它是一种偏好优化方法。",
    },
    {
        "name": "public-SFT baseline",
        "definition": "public-SFT baseline 是用公开通用 instruction 数据训练出的基线 adapter。",
        "project_use": "它证明训练链路能跑通，但 Stage 4A 发现它没有修正 LoRA/SFT/DPO 的技术概念误解。",
        "mistake": "公开数据跑通不等于目标领域行为已经解决。",
    },
    {
        "name": "Stage 2B",
        "definition": "Stage 2B 是自采集技术数据阶段，包含采集、清洗、去重、筛选和 instruction-answer 转换。",
        "project_use": "它的目标是补足公开通用数据没有覆盖的 LoRA、SFT、DPO、显存和实验复盘知识。",
        "mistake": "Stage 2B 不是盲目堆数据，而是围绕固定 badcase 做有目标的数据改进。",
    },
    {
        "name": "Qwen chat JSONL",
        "definition": "Qwen chat JSONL 是每行一个 JSON，对话消息包含 system、user、assistant。",
        "project_use": "本项目的 train_sft_lora.py 会读取 messages 字段，并只对 assistant 部分计算训练标签。",
        "mistake": "不要把原始网页文本直接丢给 SFT；应先转成明确的问答或对话样本。",
    },
    {
        "name": "data cleaning",
        "definition": "数据清洗是去掉网页噪声、广告、导航栏、重复内容、过短内容和无关内容。",
        "project_use": "Stage 2B 要把自采集文本变成可解释、可复现、质量可控的训练数据。",
        "mistake": "脏数据会让模型学习到无关模板，甚至放大原有概念误解。",
    },
    {
        "name": "deduplication",
        "definition": "去重包括精确去重和近似去重，目的是避免同一段内容重复影响训练分布。",
        "project_use": "本项目先用规范化文本 hash 做精确去重，并保留来源信息方便追踪。",
        "mistake": "重复数据可能让模型过度记忆某种表达，而不是学会稳健概念。",
    },
    {
        "name": "fixed-prompt comparison",
        "definition": "固定 prompt 对比是用同一批问题比较 base、public-SFT 和 custom-SFT 的回答。",
        "project_use": "Stage 4A 用它发现 public-SFT 没修正技术概念；Stage 4B 会继续做三方对比。",
        "mistake": "只看 loss 不够，必须看目标 prompt 的行为变化。",
    },
    {
        "name": "VRAM",
        "definition": "显存决定了模型、激活、优化器状态和 batch 能否放在 GPU 上。",
        "project_use": "本项目 public LoRA SFT 约占 5.5GB/8GB，adapter 推理约占 1.2GB/8GB。",
        "mistake": "推理显存低不代表 DPO 一定够，因为 DPO 通常比 SFT 更吃显存。",
    },
    {
        "name": "DPO memory risk",
        "definition": "DPO 需要比较 chosen/rejected，并通常需要 reference policy 评分，因此显存压力高于普通 SFT。",
        "project_use": "8GB 上第一版 DPO 应只做 20-50 pair 的 tiny smoke test。",
        "mistake": "不要一开始就用长序列、大 batch 或两份完整模型做 DPO。",
    },
    {
        "name": "gradient accumulation",
        "definition": "梯度累积是在多个小 batch 上累计梯度，再执行一次参数更新。",
        "project_use": "它让 8GB 显存也能模拟较大的有效 batch，而不增加单步显存太多。",
        "mistake": "梯度累积不能减少总训练时间，但能降低单步显存压力。",
    },
    {
        "name": "max_length",
        "definition": "max_length 控制训练样本 token 上限，直接影响显存和速度。",
        "project_use": "public-SFT 使用 512；DPO smoke test 建议先降到 256。",
        "mistake": "盲目增大 max_length 会快速增加显存占用。",
    },
    {
        "name": "adapter inference",
        "definition": "adapter 推理是在基础模型上加载 LoRA adapter 权重，然后生成回答。",
        "project_use": "本项目验证了 demo adapter 和 public adapter 都能保存并加载。",
        "mistake": "adapter 文件不是完整模型，推理时仍需要基础模型。",
    },
    {
        "name": "loss vs behavior",
        "definition": "loss 是训练优化指标，behavior 是模型在目标问题上的实际回答质量。",
        "project_use": "public-SFT loss 能正常下降，但固定 prompt 仍显示目标概念错误。",
        "mistake": "不能只凭 loss 判断项目成功。",
    },
    {
        "name": "badcase",
        "definition": "badcase 是模型失败样例，用来指导下一轮数据和训练设计。",
        "project_use": "LoRA/SFT/DPO 概念误解就是 Stage 2B 的核心 badcase。",
        "mistake": "badcase 不是丢脸的结果，而是下一阶段数据建设的方向。",
    },
    {
        "name": "mixed data",
        "definition": "mixed data 是把公开通用数据和自采集技术数据按比例混合。",
        "project_use": "Stage 3B 可比较 custom-only 和 mixed adapter，观察通用能力与目标概念的平衡。",
        "mistake": "只用极少 custom 数据可能过拟合风格，只用 public 数据又可能不解决目标概念。",
    },
    {
        "name": "source metadata",
        "definition": "source metadata 是样本来源、标题、路径或 URL 等追踪信息。",
        "project_use": "Stage 2B 保留 source_id，便于解释数据从哪里来、为什么可信。",
        "mistake": "没有来源追踪的数据很难复盘和改进。",
    },
    {
        "name": "interview narrative",
        "definition": "面试叙事不是夸模型多强，而是清楚说明问题、实验、结果和下一步。",
        "project_use": "本项目可以讲：公开数据跑通但没修正概念，所以用自采集技术数据定向改进。",
        "mistake": "只说训练过模型，不如说清楚为什么这样设计数据闭环。",
    },
    {
        "name": "Windows stability",
        "definition": "Windows 原生训练可能受到二进制包版本、CUDA、tokenizers 和 safetensors 等影响。",
        "project_use": "本项目固定 transformers、peft、trl 等稳定版本，避免高版本导致进程级崩溃。",
        "mistake": "遇到 python.exe 进程崩溃时，不要只当普通 Python traceback 排查。",
    },
    {
        "name": "HF_HOME",
        "definition": "HF_HOME 控制 Hugging Face 缓存位置。",
        "project_use": "本项目把 HF_HOME 设置到项目内 .hf_cache，避免系统目录权限问题。",
        "mistake": "缓存目录不可写会导致模型或数据下载失败。",
    },
    {
        "name": "local_files_only",
        "definition": "local_files_only 让 Hugging Face 只使用本地缓存，不再访问网络。",
        "project_use": "本项目在模型已下载后默认使用它，避免无效代理和网络不稳定。",
        "mistake": "首次下载前使用 local_files_only 会找不到模型。",
    },
    {
        "name": "instruction-answer conversion",
        "definition": "instruction-answer conversion 是把资料改写成明确任务和标准回答。",
        "project_use": "Stage 2B 不直接训练原始文本，而是训练概念解释、纠错、复盘和面试讲述样本。",
        "mistake": "原始资料不是天然的 SFT 数据。",
    },
    {
        "name": "manual review",
        "definition": "人工复查是抽查 accepted/rejected 样本，确认数据质量和任务方向。",
        "project_use": "Stage 2B 首批 100-300 条样本应该优先质量而不是数量。",
        "mistake": "完全自动生成的数据如果不检查，可能把错误概念写进训练集。",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare custom technical SFT data for Stage 2B.")
    parser.add_argument("--source_file", action="append", default=None, help="Local markdown/text source file.")
    parser.add_argument("--url_file", default=None, help="Optional text file with one URL per line.")
    parser.add_argument("--raw_sources_file", default="data/raw/custom_sources.jsonl")
    parser.add_argument("--cleaned_chunks_file", default="data/raw/custom_cleaned_chunks.jsonl")
    parser.add_argument("--instruction_seed_file", default="data/raw/custom_instruction_seed.jsonl")
    parser.add_argument("--train_file", default="data/processed/custom_sft_train.jsonl")
    parser.add_argument("--eval_file", default="data/processed/custom_sft_eval.jsonl")
    parser.add_argument("--eval_ratio", type=float, default=0.1)
    parser.add_argument("--max_doc_samples", type=int, default=20)
    parser.add_argument("--system_prompt", default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def normalize_space(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalized_key(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "", text)
    return text


def stable_id(prefix: str, text: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def read_local_sources(paths: list[str]) -> list[SourceRecord]:
    sources = []
    for path_text in paths:
        path = Path(path_text)
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        sources.append(
            SourceRecord(
                source_id=stable_id("local", str(path)),
                source_type="local_markdown",
                title=path.name,
                path_or_url=str(path),
                raw_text=raw,
            )
        )
    return sources


def fetch_url(url: str, timeout: int = 20) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "qwen-local-lora-sft-dpo/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        html = response.read().decode("utf-8", errors="replace")
    parser = TextOnlyHTMLParser()
    parser.feed(html)
    return parser.text()


def read_url_sources(url_file: str | None) -> list[SourceRecord]:
    if not url_file:
        return []
    path = Path(url_file)
    if not path.exists():
        return []
    sources = []
    for line in path.read_text(encoding="utf-8").splitlines():
        url = line.strip()
        if not url or url.startswith("#"):
            continue
        try:
            raw = fetch_url(url)
        except Exception as exc:
            raw = f"FETCH_FAILED: {exc}"
        sources.append(
            SourceRecord(
                source_id=stable_id("url", url),
                source_type="url",
                title=url,
                path_or_url=url,
                raw_text=raw,
            )
        )
    return sources


def split_into_chunks(text: str, min_chars: int = 120, max_chars: int = 400) -> list[str]:
    text = normalize_space(text)
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    chunks: list[str] = []
    current = ""
    for block in blocks:
        if len(block) > max_chars:
            sentences = re.split(r"(?<=[。！？.!?])\s*", block)
            for sentence in sentences:
                sentence = sentence.strip()
                if min_chars <= len(sentence) <= max_chars:
                    chunks.append(sentence)
            continue
        candidate = block if not current else f"{current}\n{block}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if len(current) >= min_chars:
                chunks.append(current)
            current = block
    if len(current) >= min_chars:
        chunks.append(current)
    return chunks


def is_relevant(text: str) -> bool:
    if len(text) < 80:
        return False
    if text.count("|") > 12:
        return False
    return any(keyword.lower() in text.lower() for keyword in TECH_KEYWORDS)


def compact_for_answer(text: str, limit: int = 220) -> str:
    text = normalize_space(text).replace("\n", " ")
    text = re.sub(r"\s*>\s*", " ", text)
    text = re.sub(r"\s*#{1,6}\s+", " ", text)
    text = re.sub(r"\s+[-*]\s+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip("，。；,. ") + "..."


def collect_chunks(sources: list[SourceRecord]) -> tuple[list[dict[str, Any]], int]:
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    rejected = 0
    for source in sources:
        for chunk in split_into_chunks(source.raw_text):
            clean = normalize_space(chunk)
            if not is_relevant(clean):
                rejected += 1
                continue
            key = normalized_key(clean)
            if key in seen:
                rejected += 1
                continue
            seen.add(key)
            rows.append(
                {
                    "chunk_id": stable_id("chunk", source.source_id + clean),
                    "source_id": source.source_id,
                    "source_type": source.source_type,
                    "title": source.title,
                    "path_or_url": source.path_or_url,
                    "cleaned_text": clean,
                    "char_len": len(clean),
                    "status": "accepted",
                }
            )
    return rows, rejected


def concept_samples() -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for concept in CURATED_CONCEPTS:
        name = concept["name"]
        definition = concept["definition"]
        project_use = concept["project_use"]
        mistake = concept["mistake"]
        source_id = f"curated::{name}"
        samples.extend(
            [
                {
                    "instruction": f"用三点解释{name}在本项目里的含义。",
                    "input": "",
                    "output": f"第一，{definition} 第二，{project_use} 第三，{mistake}",
                    "source_id": source_id,
                    "sample_type": "concept_explanation",
                },
                {
                    "instruction": f"请纠正一个关于{name}的常见误解。",
                    "input": "",
                    "output": f"常见误解是：{mistake} 正确理解是：{definition} 在本项目中，{project_use}",
                    "source_id": source_id,
                    "sample_type": "misconception_fix",
                },
                {
                    "instruction": f"如果面试官问{name}和这个项目有什么关系，应该怎么回答？",
                    "input": "",
                    "output": f"可以这样回答：{definition} {project_use} 我们还专门记录了相关误区：{mistake}",
                    "source_id": source_id,
                    "sample_type": "interview_answer",
                },
                {
                    "instruction": f"把{name}解释给刚开始学大模型微调的人听。",
                    "input": "",
                    "output": f"可以先记住一句话：{definition} 结合这个项目看，{project_use} 需要避免的坑是：{mistake}",
                    "source_id": source_id,
                    "sample_type": "beginner_friendly",
                },
            ]
        )
    return samples


def targeted_qa_samples() -> list[dict[str, Any]]:
    rows = [
        {
            "instruction": "请用三点解释机器学习里的 LoRA 微调，不要解释成无线通信 LoRa。",
            "output": (
                "第一，机器学习里的 LoRA 是参数高效微调方法，全称常解释为低秩适配，"
                "不是无线通信 LoRa。第二，它冻结基础模型大部分参数，只在部分线性层旁边训练低秩 adapter 矩阵。"
                "第三，它适合个人 GPU 学习，因为训练参数少、显存压力低、adapter 文件也更小。"
            ),
        },
        {
            "instruction": "SFT 是什么？它和 LoRA 是什么关系？",
            "output": (
                "SFT 是 supervised fine-tuning，也就是有监督微调，描述的是训练目标和数据形式。"
                "LoRA 是参数高效微调方法，描述的是怎样少量更新模型参数。"
                "所以 LoRA SFT 的意思是：用 LoRA adapter 来执行 SFT，二者不是互斥关系。"
            ),
        },
        {
            "instruction": "DPO 和 SFT 的区别是什么？为什么通常先做 SFT 再做 DPO？",
            "output": (
                "SFT 使用 instruction-answer 数据教模型模仿目标回答，是打基础。"
                "DPO 使用 chosen/rejected 偏好对，让模型更偏向人类更喜欢的回答。"
                "通常先做 SFT，因为如果模型基础回答能力还不稳定，DPO 会放大混乱而不是稳定改进。"
            ),
        },
        {
            "instruction": "为什么 public-SFT adapter 没修正 LoRA/SFT/DPO 概念误解，反而说明 Stage 2B 有必要？",
            "output": (
                "public-SFT 证明了训练、保存和加载链路能跑通，但公开通用数据不一定覆盖本项目关心的技术概念。"
                "固定 prompt 显示它仍会把 LoRA、SFT、DPO 解释成无关缩写或通信概念。"
                "因此 Stage 2B 要围绕这些 badcase 自采集并清洗技术数据，做有目标的数据改进。"
            ),
        },
        {
            "instruction": "请解释自采集技术数据从采集、清洗、去重、筛选到 instruction-answer 转换的流程。",
            "output": (
                "第一步采集来源，保留 source_id、标题、路径或 URL。第二步清洗网页噪声、导航栏、广告、重复空白和无关内容。"
                "第三步去重和筛选，只保留和 LoRA/SFT/DPO、显存、实验复盘相关的高质量文本。"
                "最后把资料改写成 instruction-answer 样本，再转换成 Qwen chat JSONL。"
            ),
        },
        {
            "instruction": "8GB 显存下做 DPO 有什么风险？应该怎样降低显存压力？",
            "output": (
                "DPO 比 SFT 更吃显存，因为它要比较 chosen/rejected，并通常需要 reference policy 评分。"
                "8GB 下朴素双模型 DPO 可能爆显存或落到共享内存导致很慢。"
                "降低压力的方法是小模型、LoRA、batch_size=1、短 max_length、短 max_prompt_length、少量 pair、少 eval，并尽量共享 reference。"
            ),
        },
        {
            "instruction": "为什么不能只看 loss 判断一次 SFT 是否成功？",
            "output": (
                "loss 只说明训练目标上的优化情况，不直接等于目标问题回答正确。"
                "Stage 3A 的 public-SFT loss 能正常下降，但 Stage 4A 固定 prompt 仍显示 LoRA/SFT/DPO 概念错误。"
                "所以要同时看 loss、固定 prompt 对比、badcase、过拟合迹象和输出是否符合项目目标。"
            ),
        },
        {
            "instruction": "如果面试官问你这个项目的数据管线，你会怎么讲？",
            "output": (
                "我会先说公开数据集用来建立可复现基线，证明 LoRA SFT 链路能训练、保存和加载。"
                "然后说 Stage 4A 发现 public-SFT 没修正 LoRA/SFT/DPO 概念误解，所以进入 Stage 2B。"
                "Stage 2B 做自采集技术数据：采集、清洗、去重、筛选、转 instruction-answer，再训练 custom-SFT 并做三方对比。"
            ),
        },
        {
            "instruction": "请用一句话区分 LoRA、SFT、DPO。",
            "output": "LoRA 是省显存训练 adapter 的方法，SFT 是用标准答案做有监督微调的目标，DPO 是用 chosen/rejected 偏好对继续优化模型偏好的方法。",
        },
        {
            "instruction": "public-SFT 和 custom-SFT 在这个项目里分别解决什么问题？",
            "output": (
                "public-SFT 解决工程闭环问题：确认公开数据、训练脚本、LoRA adapter、保存加载都能工作。"
                "custom-SFT 解决目标行为问题：针对 LoRA/SFT/DPO 概念误解、显存解释和数据管线讲述做定向训练。"
            ),
        },
        {
            "instruction": "请解释为什么 Stage 2B 不应该盲目爬很多网页。",
            "output": (
                "Stage 2B 的目标不是堆数量，而是围绕 Stage 4A 暴露的 badcase 做数据改进。"
                "盲目爬很多网页会带来版权、噪声、重复和主题漂移问题。"
                "第一版应该小而干净，保留来源，人工抽查，并把资料改写成明确的 instruction-answer 样本。"
            ),
        },
        {
            "instruction": "请说明 adapter 文件和完整模型有什么区别。",
            "output": (
                "adapter 文件只保存 LoRA 训练得到的小矩阵参数，不包含完整基础模型。"
                "推理时仍然需要先加载 Qwen2.5-0.5B-Instruct，再加载对应 adapter。"
                "这样文件更小、训练更省显存，也方便比较 demo、public 和 custom adapter。"
            ),
        },
    ]
    samples = []
    for index, row in enumerate(rows, start=1):
        samples.append(
            {
                "instruction": row["instruction"],
                "input": "",
                "output": row["output"],
                "source_id": f"targeted::{index:03d}",
                "sample_type": "targeted_technical_qa",
            }
        )
    return samples


def badcase_patch_samples() -> list[dict[str, Any]]:
    """Stage 2B.2 samples for the two remaining Stage 4B badcases."""
    rows = [
        {
            "instruction": "为什么 public-SFT 没有修正 LoRA/SFT/DPO 概念误解，反而说明 Stage 2B 有必要？",
            "output": (
                "因为 public-SFT 的主要价值是验证工程链路：数据转换、LoRA 训练、adapter 保存和加载都能跑通。"
                "但公开通用 instruction 数据不一定覆盖本项目关心的 LoRA、SFT、DPO 技术概念。"
                "所以当固定 prompt 仍然答错时，结论不是项目失败，而是需要 Stage 2B 用自采集技术数据做定向补强。"
            ),
        },
        {
            "instruction": "请把 public-SFT 失败和 Stage 2B 数据补丁之间的关系讲清楚。",
            "output": (
                "public-SFT 失败指的是目标行为失败，不是训练流程失败。它已经证明训练流程可复现，"
                "但没有学会本项目需要的技术解释。Stage 2B 的作用就是把这些 badcase 变成数据需求，"
                "围绕错误概念补充更干净、更直接的 instruction-answer 样本。"
            ),
        },
        {
            "instruction": "面试时怎样解释：公开数据集跑通了，但模型还是误解 LoRA/SFT/DPO？",
            "output": (
                "我会说公开数据集先用于建立 baseline，证明本地 LoRA SFT 链路稳定。"
                "后来固定 prompt 评测发现模型仍误解 LoRA/SFT/DPO，说明通用数据没有覆盖目标知识。"
                "于是我进入自采集数据阶段，清洗项目技术资料并写 targeted QA，再训练 custom-SFT 做三方对比。"
            ),
        },
        {
            "instruction": "public-SFT、Stage 4A、Stage 2B 三者在项目闭环中分别是什么角色？",
            "output": (
                "public-SFT 是工程 baseline，用来证明训练、保存、加载 adapter 可行。"
                "Stage 4A 是行为评测，用固定 prompt 暴露 public-SFT 仍然答错的 badcase。"
                "Stage 2B 是数据改进阶段，把 badcase 转成自采集、清洗、去重和 instruction-answer 样本。"
            ),
        },
        {
            "instruction": "为什么不能只凭训练 loss 说一次 SFT 已经成功？",
            "output": (
                "loss 只衡量模型在训练目标上的拟合程度，不等于目标 prompt 一定回答正确。"
                "例如 public-SFT 的 loss 可以正常下降，但 Stage 4A 仍显示它误解 LoRA/SFT/DPO。"
                "因此 SFT 是否成功要同时看训练 loss、eval loss、固定 prompt 对比、badcase 和是否出现过拟合。"
            ),
        },
        {
            "instruction": "训练 loss 下降了，但固定 prompt 仍然答错，应该怎么理解？",
            "output": (
                "这说明模型学会了部分训练分布，但没有学会项目真正关心的目标行为。"
                "下一步不应该只继续堆 epoch，而应该回到数据侧检查样本是否覆盖 badcase、是否有噪声、是否过于模板化。"
                "本项目就是这样从 Stage 4A 的错误进入 Stage 2B 和 Stage 2B.2 数据补丁的。"
            ),
        },
        {
            "instruction": "请区分 train loss、eval loss、固定 prompt 对比和 badcase review。",
            "output": (
                "train loss 看训练集拟合情况，eval loss 看留出集上的平均泛化趋势。"
                "固定 prompt 对比看模型在项目目标问题上的实际回答质量。"
                "badcase review 则把答错的例子整理成下一轮数据清洗、补样本和训练设置调整的依据。"
            ),
        },
        {
            "instruction": "为什么 Stage 3B 训练后还要做 Stage 4B 三方对比，而不是只汇报 loss？",
            "output": (
                "因为这个项目的目标是修正 LoRA/SFT/DPO 技术概念误解，而不是只让平均 loss 变低。"
                "Stage 4B 用同一组 prompt 比较 base、public-SFT 和 custom-SFT，能看出哪些行为真的改善、哪些仍然失败。"
                "这种对比能直接指导下一轮 Stage 2B.2 数据补丁。"
            ),
        },
    ]
    samples = []
    for index, row in enumerate(rows, start=1):
        samples.append(
            {
                "instruction": row["instruction"],
                "input": "",
                "output": row["output"],
                "source_id": f"stage2b2_badcase::{index:03d}",
                "sample_type": "badcase_patch_stage2b2",
            }
        )
    return samples


def doc_chunk_samples(chunks: list[dict[str, Any]], max_samples: int) -> list[dict[str, Any]]:
    samples = []
    for chunk in chunks[:max_samples]:
        text = compact_for_answer(chunk["cleaned_text"])
        title = chunk["title"]
        source_id = chunk["chunk_id"]
        samples.append(
            {
                "instruction": "请把下面的项目记录整理成适合面试讲述的三点总结。",
                "input": chunk["cleaned_text"],
                "output": (
                    f"可以从三点讲：第一，这段记录来自 {title}，说明项目不是只跑 demo，"
                    f"而是在持续记录过程。第二，核心内容是：{text} 第三，面试中要强调"
                    "实验结论、问题定位和下一步改进，而不是只报一个训练命令。"
                ),
                "source_id": source_id,
                "sample_type": "project_record_summary",
            }
        )
    return samples


def dedupe_samples(samples: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    seen: set[str] = set()
    deduped = []
    duplicates = 0
    for sample in samples:
        key = normalized_key(sample["instruction"] + sample.get("input", "") + sample["output"])
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        deduped.append(sample)
    return deduped, duplicates


def to_chat_row(sample: dict[str, Any], system_prompt: str) -> dict[str, Any]:
    user = sample["instruction"]
    input_text = sample.get("input", "").strip()
    if input_text:
        user = f"{user}\n\n补充材料：\n{input_text}"
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user},
            {"role": "assistant", "content": sample["output"]},
        ]
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    source_paths = args.source_file or DEFAULT_LOCAL_SOURCES
    sources = read_local_sources(source_paths) + read_url_sources(args.url_file)

    source_rows = [
        {
            "source_id": source.source_id,
            "source_type": source.source_type,
            "title": source.title,
            "path_or_url": source.path_or_url,
            "raw_text": source.raw_text,
            "char_len": len(source.raw_text),
        }
        for source in sources
    ]
    write_jsonl(Path(args.raw_sources_file), source_rows)

    chunks, rejected_chunks = collect_chunks(sources)
    chunks.sort(key=lambda row: (row["title"], row["chunk_id"]))
    write_jsonl(Path(args.cleaned_chunks_file), chunks)

    samples = (
        concept_samples()
        + targeted_qa_samples()
        + badcase_patch_samples()
        + doc_chunk_samples(chunks, args.max_doc_samples)
    )
    samples, duplicate_samples = dedupe_samples(samples)
    random.Random(args.seed).shuffle(samples)
    write_jsonl(Path(args.instruction_seed_file), samples)

    eval_size = max(1, int(len(samples) * args.eval_ratio))
    eval_samples = samples[:eval_size]
    train_samples = samples[eval_size:]

    train_rows = [to_chat_row(sample, args.system_prompt) for sample in train_samples]
    eval_rows = [to_chat_row(sample, args.system_prompt) for sample in eval_samples]
    write_jsonl(Path(args.train_file), train_rows)
    write_jsonl(Path(args.eval_file), eval_rows)

    print("Sources:", len(source_rows))
    print("Accepted chunks:", len(chunks))
    print("Rejected chunks:", rejected_chunks)
    print("Instruction samples:", len(samples))
    print("Train samples:", len(train_rows))
    print("Eval samples:", len(eval_rows))
    print("Duplicate instruction samples:", duplicate_samples)
    print("Raw sources file:", args.raw_sources_file)
    print("Cleaned chunks file:", args.cleaned_chunks_file)
    print("Instruction seed file:", args.instruction_seed_file)
    print("Train file:", args.train_file)
    print("Eval file:", args.eval_file)


if __name__ == "__main__":
    main()
