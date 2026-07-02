"""Prepare Stage 8 expanded technical SFT/DPO data.

This stage is a data-scale upgrade. It does not claim that the old accepted
adapter was trained on the new rows. Instead, it creates a reproducible
training-ready dataset large enough for a follow-up run and a larger held-out
behavior suite.

The data is deliberately synthetic/curated Chinese QA grounded in:

- this repository's previous experiment reports;
- public reference metadata for LoRA, DPO, PEFT, TRL, and Qwen;
- the actual badcases found in the Stage 2B to Stage 6 loop.

No long web passages are copied into the dataset.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


DEFAULT_SYSTEM_PROMPT = (
    "你是一个清晰、严谨、适合初学者的大模型微调中文助教。"
    "回答时优先解释 LoRA、SFT、DPO、数据清洗、显存、评估和实验复盘。"
)

SOURCE_REGISTRY: list[dict[str, str]] = [
    {
        "source_id": "local_final_summary",
        "source_type": "local_project_report",
        "title": "项目最终总结：Qwen 本地 LoRA SFT / DPO 学习链路",
        "path_or_url": "reports/final_project_summary_zh.md",
        "usage": "project timeline, accepted checkpoint decision, fixed-gate results",
    },
    {
        "source_id": "local_stage6_interview",
        "source_type": "local_project_report",
        "title": "Stage 6 Final Interview Package",
        "path_or_url": "reports/stage6_final_interview_package.md",
        "usage": "interview narrative, before/after examples, failure review",
    },
    {
        "source_id": "local_stage2b_data",
        "source_type": "local_project_report",
        "title": "Stage 2B Custom Technical Data Report",
        "path_or_url": "reports/stage2b_custom_technical_data_report.md",
        "usage": "custom data pipeline, source metadata, cleaning and split policy",
    },
    {
        "source_id": "local_stage5_scores",
        "source_type": "local_project_report",
        "title": "Stage 5 Structured Behavior Score Report",
        "path_or_url": "reports/stage5_structured_behavior_score_report.md",
        "usage": "rubric areas, old prompt failures, DPO gate decisions",
    },
    {
        "source_id": "web_lora_paper",
        "source_type": "public_reference_metadata",
        "title": "LoRA: Low-Rank Adaptation of Large Language Models",
        "path_or_url": "https://arxiv.org/abs/2106.09685",
        "usage": "LoRA concept grounding: low-rank adaptation and parameter efficiency",
    },
    {
        "source_id": "web_dpo_paper",
        "source_type": "public_reference_metadata",
        "title": "Direct Preference Optimization: Your Language Model is Secretly a Reward Model",
        "path_or_url": "https://arxiv.org/abs/2305.18290",
        "usage": "DPO concept grounding: chosen/rejected preference optimization",
    },
    {
        "source_id": "web_peft_lora_docs",
        "source_type": "public_reference_metadata",
        "title": "Hugging Face PEFT LoRA conceptual guide",
        "path_or_url": "https://huggingface.co/docs/peft/en/conceptual_guides/lora",
        "usage": "PEFT/LoRA implementation framing",
    },
    {
        "source_id": "web_trl_dpo_docs",
        "source_type": "public_reference_metadata",
        "title": "Hugging Face TRL DPOTrainer documentation",
        "path_or_url": "https://huggingface.co/docs/trl/en/dpo_trainer",
        "usage": "TRL DPO training schema and preference-data framing",
    },
    {
        "source_id": "web_qwen_model_card",
        "source_type": "public_reference_metadata",
        "title": "Qwen2.5-0.5B-Instruct model card",
        "path_or_url": "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct",
        "usage": "base model identity and model-card reference",
    },
]


@dataclass(frozen=True)
class Topic:
    topic_id: str
    label: str
    source_refs: tuple[str, ...]
    must_points: tuple[str, ...]
    project_points: tuple[str, ...]
    bad_points: tuple[str, ...]
    regression_checks: tuple[str, ...]


TOPICS: tuple[Topic, ...] = (
    Topic(
        topic_id="lora_definition",
        label="LoRA 定义与边界",
        source_refs=("web_lora_paper", "web_peft_lora_docs", "local_stage6_interview"),
        must_points=(
            "LoRA 是 Low-Rank Adaptation，一种参数高效微调方法",
            "基础模型大部分参数冻结，只训练少量低秩 adapter",
            "LoRA adapter 不是完整模型，推理时仍依赖基础模型",
            "机器学习里的 LoRA 不应和无线通信 LoRa 混淆",
        ),
        project_points=(
            "本项目用 LoRA 在 RTX 4060 Laptop GPU 上降低 Qwen2.5-0.5B 后训练成本",
            "public-SFT 和 custom-SFT 都通过 adapter 保存、加载和推理对比验证链路",
            "LoRA 可训练参数约 4.40M，占总参数约 0.88%",
        ),
        bad_points=(
            "把 LoRA 解释成 Long Range 无线通信协议",
            "把 LoRA 说成全量重训完整基础模型",
            "把 adapter 当成不用基础模型就能独立推理的模型",
        ),
        regression_checks=(
            "回答中必须出现参数高效、低秩、冻结基础模型或 adapter",
            "不能出现无线通信、路由协议或完整重训的错误解释",
        ),
    ),
    Topic(
        topic_id="sft_lora_relation",
        label="SFT 与 LoRA 关系",
        source_refs=("local_stage2b_data", "web_peft_lora_docs", "local_stage6_interview"),
        must_points=(
            "SFT 是 supervised fine-tuning，即有监督微调",
            "SFT 描述训练目标和 instruction-answer/chat 数据形式",
            "LoRA 描述参数高效更新方法",
            "LoRA SFT 表示用 LoRA adapter 来执行 SFT",
        ),
        project_points=(
            "本项目先用公开中文 instruction 数据做 public LoRA SFT",
            "随后用自采集技术数据做 custom LoRA SFT",
            "同一批固定 prompt 比较 base、public-SFT 和 custom-SFT",
        ),
        bad_points=(
            "把 SFT 展开成网络安全或路由术语",
            "把 LoRA 和 SFT 说成互斥关系",
            "只讲模型结构，不讲训练目标和数据格式",
        ),
        regression_checks=(
            "需要区分目标和方法",
            "需要说明 instruction-answer 或 chat messages",
        ),
    ),
    Topic(
        topic_id="dpo_vs_sft",
        label="DPO 与 SFT 区别",
        source_refs=("web_dpo_paper", "web_trl_dpo_docs", "local_stage5_scores"),
        must_points=(
            "SFT 用标准答案教模型模仿目标回答",
            "DPO 使用 prompt、chosen、rejected 偏好对",
            "DPO 让模型更偏向 chosen、远离 rejected",
            "通常先做 SFT，再在稳定回答基础上做 DPO",
        ),
        project_points=(
            "本项目先保留 custom-SFT v3 作为 DPO 起点",
            "tiny DPO 先验证显存、训练、保存和加载链路",
            "v6/v7/v8 偏好指标好看但仍未完全通过行为 gate",
        ),
        bad_points=(
            "把 DPO 解释成 Data Preprocessing 或数据保护对象",
            "认为 DPO 可以完全替代 SFT",
            "只看 preference accuracy，不看固定 prompt 行为",
        ),
        regression_checks=(
            "需要同时提到 chosen/rejected 和 SFT 基础能力",
            "不能把 DPO 说成普通分类指标或数据清洗流程",
        ),
    ),
    Topic(
        topic_id="public_sft_motivation",
        label="public-SFT 诊断价值",
        source_refs=("local_stage2b_data", "local_stage6_interview", "local_final_summary"),
        must_points=(
            "public-SFT 是工程 baseline，不是最终目标模型",
            "它证明训练、保存、加载和推理对比链路可跑",
            "它没有修正 LoRA/SFT/DPO 目标概念误解",
            "这个失败直接推动 Stage 2B 自采集技术数据",
        ),
        project_points=(
            "公开数据基线使用 1003 条训练和 111 条验证样本",
            "Stage 4A 固定 prompt 发现 public-SFT 仍答错目标概念",
            "custom-SFT 后才把大部分目标概念行为修正到可展示水平",
        ),
        bad_points=(
            "说 public-SFT 已经证明目标概念全部修好",
            "说 Stage 2B 是从零重训完整模型",
            "编造三到六个月训练周期来显得更大",
        ),
        regression_checks=(
            "必须把 public-SFT 的价值定位为链路证明和 badcase 发现",
            "不能把失败包装成已经成功",
        ),
    ),
    Topic(
        topic_id="data_pipeline",
        label="自采集技术数据管线",
        source_refs=("local_stage2b_data", "local_final_summary", "local_stage6_interview"),
        must_points=(
            "采集时保留 source_id、标题、路径或 URL",
            "清洗网页噪声、导航栏、广告、重复空白和无关内容",
            "去重和筛选后改写成 instruction-answer 或 chat JSONL",
            "训练集和评测集需要分离，不能用同一批问题自测",
        ),
        project_points=(
            "旧 Stage 2B 有 10 个来源、96 个清洗片段和 157 条 seed",
            "Stage 8 扩容后生成 1500 条 SFT train 和 160 条 SFT eval",
            "数据来源由本地项目报告和公开参考元数据共同支撑",
        ),
        bad_points=(
            "把网页全文直接塞进训练集",
            "只讲缺失值填充、标准化和归一化等表格预处理",
            "不保留来源，导致后续无法复盘",
        ),
        regression_checks=(
            "需要讲清采集、清洗、去重、筛选、改写和拆分",
            "需要强调来源追踪和 held-out eval",
        ),
    ),
    Topic(
        topic_id="loss_behavior",
        label="loss 与行为验收",
        source_refs=("local_stage5_scores", "local_stage6_interview", "local_final_summary"),
        must_points=(
            "loss 是平均训练目标上的优化信号",
            "loss 必要但不充分，不能替代可见输出行为",
            "固定 prompt、badcase review 和旧能力回归要一起看",
            "preference accuracy 也不能直接替代行为验收",
        ),
        project_points=(
            "public-SFT loss 正常但目标概念仍错",
            "DPO v7/v8 preference accuracy 到 1.0 但 prompt 7 仍失败",
            "Stage 5O 能强修 prompt 7，却让旧题回到 4/8",
        ),
        bad_points=(
            "只要 train loss 降低就宣布成功",
            "只要 DPO preference accuracy 到 1.0 就接受 checkpoint",
            "修好一个新问题时忽略旧问题回归",
        ),
        regression_checks=(
            "需要同时包含平均信号、不充分、固定 prompt、badcase 和回归",
            "不能把 loss 当成最终验收",
        ),
    ),
    Topic(
        topic_id="behavior_eval",
        label="固定 Prompt 与扩展评测",
        source_refs=("local_stage5_scores", "local_stage6_interview", "local_final_summary"),
        must_points=(
            "固定 prompt 用来保证不同模型阶段在同题上可比",
            "扩展评测用 held-out 改写降低记忆单句的风险",
            "结构化评分脚本记录 required 和 forbidden 项",
            "人工复查仍然必要，脚本只是可复现 gate helper",
        ),
        project_points=(
            "旧固定 gate 只有 8 题，适合 pilot 但不适合作为大规模结论",
            "Stage 8 扩展为 96 条行为评测 prompt",
            "未来训练必须重新跑 expanded suite，不能沿用旧 7/8 直接宣传",
        ),
        bad_points=(
            "只测一条原始 prompt 就宣布泛化成功",
            "把评分脚本当成完全可靠的 LLM judge",
            "把 pilot 的 7/8 说成大评测集结果",
        ),
        regression_checks=(
            "需要提到同题可比、held-out 改写和 regression check",
            "需要承认小评测的边界",
        ),
    ),
    Topic(
        topic_id="dpo_vram",
        label="DPO 显存风险",
        source_refs=("web_trl_dpo_docs", "local_final_summary", "local_stage5_scores"),
        must_points=(
            "DPO 同时处理 chosen/rejected，并涉及 reference policy 对比",
            "显存压力通常高于普通 SFT",
            "8GB 下先用 LoRA、小 batch、短 max_length 和少量 eval",
            "tiny smoke test 只证明可跑，不证明行为质量",
        ),
        project_points=(
            "tiny DPO 33 pair 完成 4 个 optimizer steps 且无 OOM",
            "DPO v6 separate reference 跑通并达到固定 gate 7/8",
            "硬件可跑不是接受 DPO checkpoint 的充分条件",
        ),
        bad_points=(
            "把无 OOM 等同于模型质量过关",
            "编造显存数字或 batch_size=4GB 这类错误说法",
            "忽略 reference policy 和 chosen/rejected 的额外成本",
        ),
        regression_checks=(
            "需要提到 chosen/rejected、reference、8GB 风险和小 batch",
            "需要区分 smoke test 与质量验收",
        ),
    ),
    Topic(
        topic_id="checkpoint_decision",
        label="checkpoint 选择与拒绝理由",
        source_refs=("local_final_summary", "local_stage6_interview", "local_stage5_scores"),
        must_points=(
            "接受 checkpoint 要看行为稳定性，而不只看单项指标",
            "custom-SFT v3 是保守推荐，因为保住 7/8 且旧题不明显回归",
            "DPO v6 是最好 DPO artifact，但不是默认模型",
            "能修一个 prompt 但破坏旧题的 adapter 应拒绝",
        ),
        project_points=(
            "最终保留 outputs/sft_lora_qwen05b_custom_v3_from_v1_patch",
            "DPO v6/v7/v8 固定 gate 最高 7/8，但 prompt 7 仍失败",
            "Stage 5O prompt 7 通过但固定 gate 降到 4/8",
        ),
        bad_points=(
            "只因 eval loss 低就切换 checkpoint",
            "只因 preference accuracy 高就接受 DPO",
            "只讲成功，不解释拒绝坏 checkpoint 的依据",
        ),
        regression_checks=(
            "需要说明接受、拒绝和保守选择的证据",
            "需要把旧能力回归作为核心风险",
        ),
    ),
    Topic(
        topic_id="interview_narrative",
        label="面试叙事与边界",
        source_refs=("local_stage6_interview", "local_final_summary", "local_stage2b_data"),
        must_points=(
            "项目重点是可复现的后训练链路和评估闭环",
            "要区分 pilot 结果、扩容数据和未来训练计划",
            "不要把未训练的新数据说成已有 checkpoint 的训练结果",
            "可以强调数据构造、badcase 迭代和评测边界意识",
        ),
        project_points=(
            "旧版本适合讲方法闭环，但数据量偏小",
            "Stage 8 把训练数据、preference 数据和评测 prompt 扩到面试更稳的规模",
            "如果被问结果，应说明旧 7/8 是 pilot gate，新 96 prompt 需要重新跑模型",
        ),
        bad_points=(
            "为了好听而混淆旧结果和新数据规模",
            "把 8 条固定 prompt 说成完整 benchmark",
            "只报漂亮数字，不讲数据来源和限制",
        ),
        regression_checks=(
            "需要诚实区分已跑结果和已构建数据",
            "需要用工程语言说明下一步训练和评估",
        ),
    ),
)

PROMPT_FRAMES = (
    "请用三点解释{label}，要求结合本项目而不是只给教科书定义。",
    "如果面试官追问{label}，你会怎样用项目经验回答？",
    "请把{label}讲给第一次接触大模型微调的同学。",
    "请从数据、训练和评估三个角度说明{label}。",
    "请说明{label}里最容易被误解的地方，并给出正确说法。",
    "请用“问题 -> 做法 -> 验收”的结构复盘{label}。",
    "请写一个适合放进实验报告的{label}说明。",
    "请从 badcase 分析角度解释{label}。",
    "请从 checkpoint 选择角度解释{label}。",
    "请从本地 8GB 显存实验约束角度说明{label}。",
    "请给出{label}的最小验收清单。",
    "请说明{label}在 base、public-SFT、custom-SFT、DPO 对比中的作用。",
    "请用一句总述加三条要点回答{label}。",
    "请指出一个关于{label}的错误回答，并改写成正确回答。",
    "请从“不能只看指标”的角度解释{label}。",
    "请用简历项目答辩的口吻说明{label}。",
)

AUDIENCES = (
    "初学者",
    "面试官",
    "项目复盘读者",
    "未来接手同学",
    "简历审阅者",
    "实验报告读者",
)

ANGLE_HINTS = (
    "先给定义，再讲项目里的证据，最后讲不能怎么误解。",
    "要体现数据来源、训练链路和评测边界。",
    "要突出这不是单纯堆数据，而是 badcase 驱动的数据迭代。",
    "要把 old prompt regression 作为验收风险之一。",
    "要区分工程链路跑通和模型行为真正变好。",
    "要避免编造训练周期、显存数字或 benchmark 结论。",
)

DPO_REJECT_STYLES = (
    "wrong_acronym",
    "metric_only",
    "overclaim",
    "generic_pipeline",
    "missing_regression",
    "fabricated_scale",
)

EVAL_FRAMES = (
    "如果模型在{label}上只说了表面结论，应该追问什么？",
    "请设计一个 held-out prompt 来检查模型是否真正理解{label}。",
    "为什么{label}不能只用训练 loss 来验收？",
    "如何判断{label}相关回答有没有旧能力回归？",
    "请给出一个{label}的反例，说明什么回答不能接受。",
    "请用项目复盘口吻解释{label}的评测标准。",
    "如果 DPO 指标很好但{label}仍答错，你会怎么处理？",
    "请说明{label}里哪些内容必须出现在正确答案中。",
    "请把{label}改写成一个适合结构化评分的 prompt。",
    "请从 source metadata 和数据拆分角度说明{label}。",
    "请解释{label}如何支撑简历中的项目可信度。",
    "请说明{label}在扩容到 10 倍数据后仍需要注意什么。",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Stage 8 expanded technical SFT/DPO data.")
    parser.add_argument("--sft_train_output", default="data/processed/custom_sft_expanded_train.jsonl")
    parser.add_argument("--sft_eval_output", default="data/processed/custom_sft_expanded_eval.jsonl")
    parser.add_argument("--dpo_train_output", default="data/processed/dpo_expanded_train.jsonl")
    parser.add_argument("--dpo_eval_output", default="data/processed/dpo_expanded_eval.jsonl")
    parser.add_argument(
        "--behavior_prompt_output",
        default="data/samples/custom_technical_prompts_stage8_expanded.jsonl",
    )
    parser.add_argument(
        "--source_registry_output",
        default="data/references/stage8_expanded_source_registry.jsonl",
    )
    parser.add_argument("--report_output", default="reports/stage8_expanded_data_report.md")
    parser.add_argument("--sft_train_size", type=int, default=1500)
    parser.add_argument("--sft_eval_size", type=int, default=160)
    parser.add_argument("--dpo_train_size", type=int, default=1500)
    parser.add_argument("--dpo_eval_size", type=int, default=160)
    parser.add_argument("--behavior_prompt_size", type=int, default=96)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--system_prompt", default=DEFAULT_SYSTEM_PROMPT)
    return parser.parse_args()


def stable_id(prefix: str, text: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_key(text: str) -> str:
    return "".join(ch.lower() for ch in text if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def select_point(points: tuple[str, ...], index: int, offset: int = 0) -> str:
    return points[(index + offset) % len(points)]


def render_chosen_answer(topic: Topic, frame_index: int, audience: str, hint: str, variant: int) -> str:
    must_a = select_point(topic.must_points, frame_index, 0)
    must_b = select_point(topic.must_points, frame_index, 1)
    project = select_point(topic.project_points, variant, 0)
    bad = select_point(topic.bad_points, variant, 0)
    check = select_point(topic.regression_checks, frame_index + variant, 0)
    transition = (
        "因此这部分不能只写成流水账，而要写成可验证的实验闭环。"
        if variant % 3 == 0
        else "面试时最好把定义、项目证据和验收标准放在一起讲。"
    )
    return (
        f"可以这样回答给{audience}：{topic.label}的核心不是一个孤立名词。"
        f"第一，{must_a}；第二，{must_b}；第三，结合本项目，{project}。"
        f"{transition} 需要特别避免的错误是：{bad}。"
        f"验收时，{check}。{hint}"
    )


def render_instruction(topic: Topic, frame: str, audience: str, hint: str, variant: int) -> str:
    focus = select_point(topic.must_points + topic.project_points + topic.regression_checks, variant)
    suffix = (
        f"\n回答对象：{audience}。补充要求：{hint} 关注点：{focus}"
        if variant % 2 == 0
        else f"\n请同时说明项目证据和常见误区。回答对象：{audience}。补充要求：{hint} 关注点：{focus}"
    )
    return frame.format(label=topic.label) + suffix


def to_chat_row(
    sample_id: str,
    topic: Topic,
    instruction: str,
    output: str,
    system_prompt: str,
    split: str,
    source_type: str,
) -> dict[str, Any]:
    return {
        "sample_id": sample_id,
        "prompt_area": topic.label,
        "topic_id": topic.topic_id,
        "source_type": source_type,
        "source_refs": list(topic.source_refs),
        "split": split,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction},
            {"role": "assistant", "content": output},
        ],
    }


def build_sft_candidates(system_prompt: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    train_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []
    seen_train: set[str] = set()
    seen_eval: set[str] = set()

    for topic_index, topic in enumerate(TOPICS):
        for frame_index, frame in enumerate(PROMPT_FRAMES):
            for audience_index, audience in enumerate(AUDIENCES):
                for hint_index, hint in enumerate(ANGLE_HINTS):
                    variant = topic_index * 1000 + frame_index * 100 + audience_index * 10 + hint_index
                    instruction = render_instruction(topic, frame, audience, hint, variant)
                    answer = render_chosen_answer(topic, frame_index, audience, hint, variant)
                    key = normalize_key(instruction + answer)
                    if key in seen_train:
                        continue
                    seen_train.add(key)
                    sample_id = stable_id("stage8-sft-train", instruction + answer)
                    train_rows.append(
                        to_chat_row(
                            sample_id,
                            topic,
                            instruction,
                            answer,
                            system_prompt,
                            "train_candidate",
                            "stage8_synthetic_curated",
                        )
                    )

        for eval_index, frame in enumerate(EVAL_FRAMES):
            for audience_index, audience in enumerate(AUDIENCES[:4]):
                hint = ANGLE_HINTS[(eval_index + audience_index) % len(ANGLE_HINTS)]
                variant = topic_index * 1000 + eval_index * 10 + audience_index
                instruction = render_instruction(topic, frame, audience, hint, variant)
                answer = render_chosen_answer(topic, eval_index, audience, hint, variant + 17)
                key = normalize_key(instruction + answer)
                if key in seen_eval:
                    continue
                seen_eval.add(key)
                sample_id = stable_id("stage8-sft-eval", instruction + answer)
                eval_rows.append(
                    to_chat_row(
                        sample_id,
                        topic,
                        instruction,
                        answer,
                        system_prompt,
                        "eval_candidate",
                        "stage8_heldout_synthetic_curated",
                    )
                )

    return train_rows, eval_rows


def rejected_answer(topic: Topic, style: str, variant: int) -> str:
    bad = select_point(topic.bad_points, variant)
    if style == "wrong_acronym":
        return f"{topic.label}主要是一个缩写问题，可以按字面猜测理解。比如：{bad}。不需要结合项目里的训练和评测。"
    if style == "metric_only":
        return f"只要 train loss 或 preference accuracy 好看，就说明{topic.label}已经成功，固定 prompt 和 badcase review 只是展示材料。"
    if style == "overclaim":
        return f"本项目已经通过 public-SFT 彻底解决了{topic.label}，后续 Stage 2B、DPO 和扩展评测都只是锦上添花。"
    if style == "generic_pipeline":
        return f"{topic.label}可以按普通表格数据流程处理：缺失值填充、标准化、归一化，然后直接训练即可，不需要 source metadata。"
    if style == "missing_regression":
        return f"只要新问题答对，就不用看旧能力是否回归；{topic.label}相关旧 prompt 变差也不影响最终验收。"
    return f"为了让项目显得更大，可以直接说{topic.label}做了很多个月训练和海量 benchmark，不必解释数据来源。"


def build_dpo_candidates() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    train_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []
    seen_train: set[tuple[str, str, str]] = set()
    seen_eval: set[tuple[str, str, str]] = set()

    for topic_index, topic in enumerate(TOPICS):
        for frame_index, frame in enumerate(PROMPT_FRAMES):
            for style_index, style in enumerate(DPO_REJECT_STYLES):
                for audience_index, audience in enumerate(AUDIENCES):
                    hint = ANGLE_HINTS[(style_index + audience_index) % len(ANGLE_HINTS)]
                    variant = topic_index * 1000 + frame_index * 100 + style_index * 10 + audience_index
                    prompt = render_instruction(topic, frame, audience, hint, variant)
                    chosen = render_chosen_answer(topic, frame_index, audience, hint, variant)
                    rejected = rejected_answer(topic, style, variant)
                    key = (prompt, chosen, rejected)
                    if key in seen_train:
                        continue
                    seen_train.add(key)
                    train_rows.append(
                        {
                            "pair_id": stable_id("stage8-dpo-train", prompt + chosen + rejected),
                            "prompt": prompt,
                            "chosen": chosen,
                            "rejected": rejected,
                            "prompt_area": topic.label,
                            "topic_id": topic.topic_id,
                            "source_type": f"stage8_preference_{style}",
                            "source_refs": list(topic.source_refs),
                            "split": "train_candidate",
                        }
                    )

        for eval_index, frame in enumerate(EVAL_FRAMES):
            for style_index, style in enumerate(DPO_REJECT_STYLES[:4]):
                audience = AUDIENCES[(eval_index + style_index) % len(AUDIENCES)]
                hint = ANGLE_HINTS[(eval_index + style_index) % len(ANGLE_HINTS)]
                variant = topic_index * 1000 + eval_index * 10 + style_index
                prompt = render_instruction(topic, frame, audience, hint, variant)
                chosen = render_chosen_answer(topic, eval_index, audience, hint, variant + 23)
                rejected = rejected_answer(topic, style, variant + 5)
                key = (prompt, chosen, rejected)
                if key in seen_eval:
                    continue
                seen_eval.add(key)
                eval_rows.append(
                    {
                        "pair_id": stable_id("stage8-dpo-eval", prompt + chosen + rejected),
                        "prompt": prompt,
                        "chosen": chosen,
                        "rejected": rejected,
                        "prompt_area": topic.label,
                        "topic_id": topic.topic_id,
                        "source_type": f"stage8_heldout_preference_{style}",
                        "source_refs": list(topic.source_refs),
                        "split": "eval_candidate",
                    }
                )

    return train_rows, eval_rows


def build_behavior_prompts(target_size: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    core_topics = TOPICS[:8]
    per_topic = target_size // len(core_topics)
    remainder = target_size % len(core_topics)
    for topic_index, topic in enumerate(core_topics):
        count = per_topic + (1 if topic_index < remainder else 0)
        for item_index in range(count):
            frame = EVAL_FRAMES[item_index % len(EVAL_FRAMES)]
            audience = AUDIENCES[item_index % len(AUDIENCES)]
            prompt = frame.format(label=topic.label)
            rows.append(
                {
                    "prompt_id": f"stage8_{topic.topic_id}_{item_index + 1:03d}",
                    "prompt_area": topic.label,
                    "topic_id": topic.topic_id,
                    "source": "stage8_expanded_behavior_holdout",
                    "source_refs": list(topic.source_refs),
                    "prompt": f"{prompt}\n请面向{audience}回答，并给出项目里的证据或边界。",
                    "must_cover": list(topic.must_points[:3]) + [select_point(topic.regression_checks, item_index)],
                    "forbidden_behavior": list(topic.bad_points),
                    "notes": "Stage 8 expanded held-out prompt. Do not use old 7/8 pilot result as its score.",
                }
            )
    return rows


def take_exact(rows: list[dict[str, Any]], size: int, seed: int, label: str) -> list[dict[str, Any]]:
    if len(rows) < size:
        raise ValueError(f"Not enough {label} rows: requested {size}, got {len(rows)}")
    shuffled = list(rows)
    random.Random(seed).shuffle(shuffled)
    selected = shuffled[:size]
    for row in selected:
        row["split"] = label
    return selected


def validate_chat_rows(rows: list[dict[str, Any]], label: str) -> None:
    seen_prompts: set[str] = set()
    for index, row in enumerate(rows, start=1):
        messages = row.get("messages")
        if not isinstance(messages, list) or len(messages) != 3:
            raise ValueError(f"{label} row {index} must contain 3 messages")
        roles = [message.get("role") for message in messages]
        if roles != ["system", "user", "assistant"]:
            raise ValueError(f"{label} row {index} has invalid roles: {roles}")
        prompt = str(messages[1].get("content", "")).strip()
        answer = str(messages[2].get("content", "")).strip()
        if not prompt or not answer:
            raise ValueError(f"{label} row {index} has empty prompt/answer")
        seen_prompts.add(normalize_key(prompt))
    if len(seen_prompts) < int(len(rows) * 0.98):
        raise ValueError(f"{label} has too many duplicate prompts")


def validate_dpo_rows(rows: list[dict[str, Any]], label: str) -> None:
    for index, row in enumerate(rows, start=1):
        prompt = str(row.get("prompt", "")).strip()
        chosen = str(row.get("chosen", "")).strip()
        rejected = str(row.get("rejected", "")).strip()
        if not prompt or not chosen or not rejected:
            raise ValueError(f"{label} row {index} has empty prompt/chosen/rejected")
        if chosen == rejected:
            raise ValueError(f"{label} row {index} chosen equals rejected")


def char_stats(values: list[int]) -> str:
    return f"{min(values)} / {round(mean(values), 1)} / {max(values)}"


def area_table(rows: list[dict[str, Any]]) -> str:
    counter = Counter(str(row.get("prompt_area", "unknown")) for row in rows)
    lines = ["| Area | Rows |", "|---|---:|"]
    for area, count in sorted(counter.items()):
        lines.append(f"| {area} | {count} |")
    return "\n".join(lines)


def render_report(
    args: argparse.Namespace,
    sft_train_rows: list[dict[str, Any]],
    sft_eval_rows: list[dict[str, Any]],
    dpo_train_rows: list[dict[str, Any]],
    dpo_eval_rows: list[dict[str, Any]],
    behavior_rows: list[dict[str, Any]],
) -> str:
    train_prompt_chars = [len(row["messages"][1]["content"]) for row in sft_train_rows]
    train_answer_chars = [len(row["messages"][2]["content"]) for row in sft_train_rows]
    eval_prompt_chars = [len(row["messages"][1]["content"]) for row in sft_eval_rows]
    dpo_prompt_chars = [len(row["prompt"]) for row in dpo_train_rows]
    dpo_chosen_chars = [len(row["chosen"]) for row in dpo_train_rows]
    dpo_rejected_chars = [len(row["rejected"]) for row in dpo_train_rows]
    source_lines = ["| Source ID | Type | Use |", "|---|---|---|"]
    for source in SOURCE_REGISTRY:
        source_lines.append(f"| `{source['source_id']}` | {source['source_type']} | {source['usage']} |")

    return f"""# Stage 8 Expanded Technical Data Report

Date: 2026-07-02

## Scope

Stage 8 upgrades the project data scale so the resume story no longer depends
only on the earlier 142 / 15 custom SFT split and 8-prompt pilot gate.

This stage generates training-ready data and a larger held-out behavior suite.
It does **not** claim that the existing accepted checkpoint was retrained on
the new data. The old 7 / 8 result remains a pilot fixed-gate result until a
new training and evaluation run is executed.

## Outputs

```text
{args.sft_train_output}
{args.sft_eval_output}
{args.dpo_train_output}
{args.dpo_eval_output}
{args.behavior_prompt_output}
{args.source_registry_output}
```

## Scale Upgrade

| Asset | Previous Main Size | Stage 8 Size | Notes |
|---|---:|---:|---|
| Custom SFT train | 142 | {len(sft_train_rows)} | more than 10x |
| Custom SFT eval | 15 | {len(sft_eval_rows)} | independent held-out chat rows |
| Fixed behavior prompts | 8 | {len(behavior_rows)} | 12x expanded behavior suite |
| DPO preference train | 278 Stage 5H rows | {len(dpo_train_rows)} | expanded chosen/rejected pairs |
| DPO preference eval | 55 Stage 5H rows | {len(dpo_eval_rows)} | held-out preference pairs |

## Source Policy

Stage 8 uses local project reports and public reference metadata. It does not
copy long web text into the training set. The generated Chinese QA rows are
synthetic/curated around project badcases, definitions, near-miss rejected
answers, and evaluation rubrics.

{chr(10).join(source_lines)}

## SFT Data Stats

- Train prompt chars min/avg/max: {char_stats(train_prompt_chars)}
- Train answer chars min/avg/max: {char_stats(train_answer_chars)}
- Eval prompt chars min/avg/max: {char_stats(eval_prompt_chars)}
- Schema: Qwen chat JSONL with `system`, `user`, `assistant`

Train area distribution:

{area_table(sft_train_rows)}

Eval area distribution:

{area_table(sft_eval_rows)}

## DPO Data Stats

- Train prompt chars min/avg/max: {char_stats(dpo_prompt_chars)}
- Train chosen chars min/avg/max: {char_stats(dpo_chosen_chars)}
- Train rejected chars min/avg/max: {char_stats(dpo_rejected_chars)}
- Schema: `prompt`, `chosen`, `rejected`, plus metadata

Train area distribution:

{area_table(dpo_train_rows)}

Eval area distribution:

{area_table(dpo_eval_rows)}

## Behavior Suite

The expanded behavior suite contains {len(behavior_rows)} held-out prompts
across the original core areas:

{area_table(behavior_rows)}

Each prompt includes `must_cover` and `forbidden_behavior` metadata so future
scoring can be extended beyond the original 8-prompt pilot gate.

## Resume-Safe Interpretation

Recommended phrasing:

```text
在原 8 题 pilot gate 基础上，将项目数据扩展为 1500 条 SFT 训练样本、
160 条 SFT held-out 样本、1500 条 DPO preference pair、160 条 DPO eval
pair，并构建 96 条扩展行为评测 prompt；扩容数据由项目 badcase、公开
LoRA/DPO/PEFT/TRL/Qwen 参考元数据和自构造中文技术问答组成。
```

Boundary:

```text
旧 checkpoint 的 7 / 8 结果仍然对应 pilot gate。若要汇报扩展评测通过率，
必须先用 Stage 8 数据重新训练或至少重新跑 96 条行为评测。
```

## Next Training Command Sketch

SFT:

```powershell
python scripts\\train_sft_lora.py `
  --init_adapter_path outputs\\sft_lora_qwen05b_custom_v3_from_v1_patch `
  --train_file {args.sft_train_output.replace('/', '\\')} `
  --eval_file {args.sft_eval_output.replace('/', '\\')} `
  --output_dir outputs\\sft_lora_qwen05b_stage8_expanded `
  --max_length 512 `
  --batch_size 1 `
  --grad_accum 4 `
  --epochs 1 `
  --lr 3e-5 `
  --logging_steps 20 `
  --eval_steps 100 `
  --save_steps 200 `
  --report_to none `
  --local_files_only
```

DPO:

```powershell
python scripts\\train_dpo.py `
  --config configs\\dpo_qwen05b_v6_naive.yaml `
  --dpo_file {args.dpo_train_output.replace('/', '\\')} `
  --eval_file {args.dpo_eval_output.replace('/', '\\')} `
  --output_dir outputs\\dpo_lora_qwen05b_stage8_expanded `
  --local_files_only
```
"""


def main() -> None:
    args = parse_args()
    sft_train_candidates, sft_eval_candidates = build_sft_candidates(args.system_prompt)
    dpo_train_candidates, dpo_eval_candidates = build_dpo_candidates()

    sft_train_rows = take_exact(sft_train_candidates, args.sft_train_size, args.seed, "train")
    sft_eval_rows = take_exact(sft_eval_candidates, args.sft_eval_size, args.seed + 1, "eval")
    dpo_train_rows = take_exact(dpo_train_candidates, args.dpo_train_size, args.seed + 2, "train")
    dpo_eval_rows = take_exact(dpo_eval_candidates, args.dpo_eval_size, args.seed + 3, "eval")
    behavior_rows = build_behavior_prompts(args.behavior_prompt_size)

    validate_chat_rows(sft_train_rows, "sft_train")
    validate_chat_rows(sft_eval_rows, "sft_eval")
    validate_dpo_rows(dpo_train_rows, "dpo_train")
    validate_dpo_rows(dpo_eval_rows, "dpo_eval")

    write_jsonl(Path(args.sft_train_output), sft_train_rows)
    write_jsonl(Path(args.sft_eval_output), sft_eval_rows)
    write_jsonl(Path(args.dpo_train_output), dpo_train_rows)
    write_jsonl(Path(args.dpo_eval_output), dpo_eval_rows)
    write_jsonl(Path(args.behavior_prompt_output), behavior_rows)
    write_jsonl(Path(args.source_registry_output), SOURCE_REGISTRY)

    report = render_report(args, sft_train_rows, sft_eval_rows, dpo_train_rows, dpo_eval_rows, behavior_rows)
    report_path = Path(args.report_output)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"Wrote {len(sft_train_rows)} SFT train rows to {args.sft_train_output}")
    print(f"Wrote {len(sft_eval_rows)} SFT eval rows to {args.sft_eval_output}")
    print(f"Wrote {len(dpo_train_rows)} DPO train rows to {args.dpo_train_output}")
    print(f"Wrote {len(dpo_eval_rows)} DPO eval rows to {args.dpo_eval_output}")
    print(f"Wrote {len(behavior_rows)} behavior prompts to {args.behavior_prompt_output}")
    print(f"Wrote source registry to {args.source_registry_output}")
    print(f"Wrote report to {args.report_output}")


if __name__ == "__main__":
    main()
