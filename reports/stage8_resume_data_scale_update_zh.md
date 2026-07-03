# Stage 8 简历数据规模更新建议

Date: 2026-07-02

## 可写进简历的安全版本

```text
基于 Qwen2.5-0.5B-Instruct 搭建本地 LoRA SFT / DPO 后训练实验链路，
完成数据构造、adapter 训练保存加载、固定 prompt 回归测试、Badcase
分析和结构化行为评分；在原 8 题 pilot gate 基础上，将技术问答数据扩展为
1500 条 SFT train / 160 条 held-out eval、1500 条 DPO preference train /
160 条 DPO eval，并构建 96 条扩展行为评测 prompt，覆盖 LoRA 定义、
SFT/LoRA 关系、DPO/SFT 区别、数据管线、DPO 显存风险、loss-vs-behavior
和 checkpoint 选择等维度。
```

## 推荐项目 bullet

- 搭建 Qwen2.5-0.5B 本地 LoRA SFT / DPO 后训练链路，覆盖公开数据
  public-SFT、自采集技术数据 custom-SFT、tiny / separate-reference DPO、
  adapter 保存加载、推理对比和固定 prompt 行为回归测试。
- 围绕 LoRA、SFT、DPO、数据清洗、显存风险和实验复盘等主题，构建
  1500 条 SFT 训练样本、160 条 held-out eval 样本、1500 条 DPO
  preference pair、160 条 DPO eval pair，并维护 96 条扩展行为评测
  prompt；数据由项目 badcase、公开 LoRA/DPO/PEFT/TRL/Qwen 参考元数据
  和自构造中文技术问答组成。
- 使用固定 prompt 与扩展行为评测区分训练指标和真实输出质量：旧版
  pilot gate 中 custom-SFT v3 达到 7/8，后续 DPO 虽出现 preference
  accuracy 1.0，但仍因 loss-vs-behavior 和旧题回归问题未被接受为默认
  checkpoint，最终保留更稳定的 SFT checkpoint。

## 面试被追问时的说法

如果被问“你的数据量到底有多少”，建议这样答：

```text
最早的 custom-SFT 是小规模 pilot，只有 142 条 train 和 15 条 eval，
主要用来验证链路和发现 badcase，所以我没有把它当成完整 benchmark。
后面我专门做了 Stage 8 数据扩容，把技术问答 SFT 扩到 1500/160，
DPO preference 扩到 1500/160，并把行为评测从 8 条固定 prompt 扩到
96 条 held-out prompt。旧的 7/8 是 pilot gate 的结果；如果继续推进，
需要用 Stage 8 数据重新训练并重新跑 96 条评测。
```

## 不能混淆的边界

- 可以说：已经构建 Stage 8 扩容数据和 96 条评测 prompt。
- 可以说：旧 pilot gate 中 custom-SFT v3 是 7 / 8。
- 不要说：旧 checkpoint 已经在 96 条 Stage 8 prompt 上达到某个通过率。
- 不要说：Stage 8 数据已经训练出新的最佳 checkpoint，除非以后真的跑完训练和评测。

## 对应文件

```text
scripts/prepare_stage8_expanded_data.py
data/processed/custom_sft_expanded_train.jsonl
data/processed/custom_sft_expanded_eval.jsonl
data/processed/dpo_expanded_train.jsonl
data/processed/dpo_expanded_eval.jsonl
data/samples/custom_technical_prompts_stage8_expanded.jsonl
data/references/stage8_expanded_source_registry.jsonl
reports/stage8_expanded_data_report.md
```

## 2026-07-04 重训后更新

Stage 8 已经完成扩容后的重新训练与 96 题行为评测。现在简历口径应更新为：

```text
扩容后重新跑通 SFT / DPO 训练与 96 条行为评测。old custom-SFT v3 在
expanded 透明规则 gate 上为 25/96；Stage 8 SFT-v2 提升到 48/96；
DPO from v2 虽然 preference eval accuracy 达到 1.0，但 96 题行为为
44/96 且人工抽查存在事实漂移，因此最终保留表现更稳定的 SFT-v2 checkpoint。
```

不要把 48/96 包装成生产级高准确率模型。这里真正适合写进简历的是：

- 数据规模从 pilot 级别扩展到 1,500 / 160 SFT、1,500 / 160 DPO 和 96 条行为评测 prompt；
- 完整重跑了 SFT、DPO、固定行为评测和 badcase 复查；
- 能解释为什么拒绝 loss / preference accuracy 好看但行为不稳的 checkpoint；
- 最终保留 `outputs/sft_lora_qwen05b_stage8_expanded_v2`。

详细复盘：

```text
reports/stage8_retraining_final_report_zh.md
```
