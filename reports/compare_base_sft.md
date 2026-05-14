# Base vs SFT Comparison

Use this report after SFT training. The comparison should eventually have two
passes:

- Stage 4A: base vs public-SFT
- Stage 4B: base vs public-SFT vs custom/mixed-SFT

| Prompt | Base Summary | SFT Summary | Improvement | Problem |
|---|---|---|---|---|
| 请用三点解释什么是LoRA微调。 | 把 LoRA 解释成权重共享、多模态学习等不准确概念。 | 更差，转向通信技术 LoRA/Long Range 和设备调参。 | 无。 | public-SFT 没有覆盖目标技术概念。 |
| 为什么小模型更适合第一次学习SFT？ | 回答很短，只说学习速度快。 | 更长，但跑偏到 Keras/TensorFlow、小型模型泛化叙述。 | 表达更完整一点。 | 没有讲清楚本项目关心的显存、迭代速度、链路验证。 |
| 请解释SFT和DPO的区别。 | 把 SFT/DPO 解释成网络安全/数据保护术语。 | 仍然错误，解释成 Short Form 和 Direct Phrasing。 | 无。 | 关键概念仍未修正。 |

Stage 4A conclusion:

The public-data LoRA SFT adapter trained and loaded successfully, but it did not
fix LoRA/SFT/DPO concept confusion. This is strong evidence for Stage 2B:
targeted self-collected technical data is needed.

## Three-Way Comparison Template

Use this after the custom-data loop is complete.

| Prompt | Base Summary | Public-SFT Summary | Custom/Mixed-SFT Summary | Best Output | Notes |
|---|---|---|---|---|---|

## Stage 4B Three-Way Comparison

Raw output:

```text
reports/compare_outputs_three_way_custom.jsonl
```

Summary report:

```text
reports/stage4b_three_way_comparison_report.md
```

| Prompt | Base Summary | Public-SFT Summary | Custom-SFT Summary | Best Output | Notes |
|---|---|---|---|---|---|
| 解释机器学习里的 LoRA，不要解释成无线通信 LoRa | 错误解释成 Local Recurrent Attention 等无关概念 | 错误解释成强化学习/数据清洗等无关概念 | 正确解释低秩适配、冻结基础模型、训练 adapter | Custom-SFT | 明显修正 Stage 4A badcase |
| SFT 是什么，它和 LoRA 什么关系 | 错误解释成网络路由类缩写 | 错误解释成神经网络结构/LoRA 子集 | 正确说明 SFT 是目标和数据形式，LoRA 是参数高效方法 | Custom-SFT | 回答简洁且符合项目术语 |
| DPO 和 SFT 的区别，为什么先 SFT 后 DPO | 错误解释成数据预处理/特征合成 | 错误解释成网络安全/隐私优化 | 正确说明 SFT 用标准答案打基础，DPO 用 chosen/rejected 偏好对 | Custom-SFT | 已达到当前学习目标 |
| 为什么 public-SFT 没修正概念反而说明 Stage 2B 有必要 | 离题 | 离题 | 仍然混乱，误说 public-SFT 不是基线 | None | 需要 Stage 2B.2 数据补丁 |
| 自采集数据从采集到 instruction-answer 转换 | 泛泛讲传感器/数据预处理 | 泛泛讲传统数据清洗 | 正确覆盖 source_id、清洗、去重、筛选、转 Qwen chat JSONL | Custom-SFT | 适合面试叙述 |
| 8GB 下 DPO 风险和降显存 | 泛泛讲显存压力 | 泛泛讲内存泄漏/性能下降 | 正确说明 DPO 比 SFT 吃显存，建议 LoRA、小 batch、短序列、少 pair、共享 reference | Custom-SFT | 贴合本机 4060 约束 |
| 为什么不能只看 loss 判断 SFT 是否成功 | 泛泛讲 loss 局限 | 泛泛讲 loss function | 有正确方向，但夹杂 `not-SFT` 等幻觉 | Partial | 需要更干净的 loss-vs-behavior 样本 |
| 面试官问项目数据管线怎么讲 | 泛泛讲数据分析流程 | 泛泛讲企业数据管线 | 正确串起公开数据基线、Stage 4A badcase、Stage 2B 自采集清洗、三方对比 | Custom-SFT | 面试可直接复用 |

Stage 4B conclusion:

The custom technical LoRA SFT adapter improved 6 of 8 fixed prompts, proving
that the self-collected/curated data loop is useful. The remaining 2 prompts are
not failures to hide; they are the next data-improvement targets.
