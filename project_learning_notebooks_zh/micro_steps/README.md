# Micro Steps：从最小闭环开始学项目

这个子目录是给完全从底层入口开始学习用的。它比上一级 notebook 更小，每个文件只解决一个问题。

## 先学这一批

1. `00_从一个prompt开始_最小推理闭环.ipynb`
2. `01_tokenizer到底做了什么_文字到数字.ipynb`
3. `02_base_model到底怎么加载_模型从哪来.ipynb`
4. `03_generate到底做了什么_数字到回答.ipynb`

这四个吃透后，你就理解了项目的最小入口：

```text
用户 prompt -> tokenizer -> Qwen base model -> generate -> 文本回答
```

后面的 SFT、LoRA、DPO，本质上都是在改变这个回答过程。

## 安全说明

默认只读代码。真实推理单元都有 `RUN_INFERENCE = False` 或 `RUN_COMPARE = False`，你不手动改成 True 就不会加载模型运行。
