# Stage 7 Safety Data

This directory is reserved for the Stage 7 safety-sensitive assistance loop.

The important rule is:

```text
Evaluation first, training second.
```

Before creating files here, study:

```text
project_learning_notebooks_zh/stage7_evaluation_learning/README.md
reports/stage7_safety_eval_design.md
```

Planned files:

```text
eval_safety_prompts.jsonl
  Held-out safety evaluation prompts. These prompts must not be used for SFT or
  DPO training.

sft_safety_train.jsonl
  Safety SFT training data in the existing project `messages` format.

sft_safety_eval.jsonl
  Safety SFT evaluation split. Separate from both train data and held-out
  behavior prompts.

dpo_safety_train.jsonl
  Preference pairs constructed after SFT from remaining badcases.
```

Canonical plan:

```text
reports/stage7_safety_eval_design.md
```

Risk levels:

```text
L0 ordinary safety knowledge
L1 low-risk practical help
L2 active crisis but safe to help
L3 explicit harmful request
```

The intended behavior is not blanket refusal. The model should refuse concrete
harmful details while still giving safe alternatives, support, and help-seeking
routes.
