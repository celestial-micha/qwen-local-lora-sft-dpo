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
