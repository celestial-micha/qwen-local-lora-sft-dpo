"""Train DPO.

Stage 5 placeholder.

Stage 5 is intentionally split before implementation:

Stage 5A: prepare `data/processed/dpo_tiny_train.jsonl`.
Stage 5B: run a tiny DPO smoke test from
`outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`.
Stage 5C: compare fixed prompts before considering any larger DPO.

Important: the current Windows local environment has shown python.exe native
crashes when importing some heavy training stacks in-process. Keep the first DPO
run tiny and review `reports/stage5_dpo_plan.md` before replacing this
placeholder with executable training code.
"""


def main() -> None:
    raise SystemExit(
        "Stage 5 placeholder: prepare tiny DPO data and review reports/stage5_dpo_plan.md first."
    )


if __name__ == "__main__":
    main()
