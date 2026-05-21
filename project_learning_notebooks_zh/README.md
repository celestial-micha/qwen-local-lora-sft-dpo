# Project Learning Notebooks 中文学习导览

这个目录是专门为了学习和讲解本项目而创建的，不是训练产物目录，也不是必须运行的生产流程。它适合在上传 GitHub 后让读者按 notebook 顺序理解：项目整体架构、Qwen 如何加载、LoRA 如何实现、SFT loss 如何计算、DPO preference 数据如何训练，以及为什么最终使用行为门禁选择 checkpoint。

## 安全说明

默认情况下，这些 notebooks 只读取项目文件并打印解释，不覆盖 `scripts/`、`data/`、`outputs/` 或 `reports/`。真实推理格子都带有 `RUN = False` 或 `RUN_INFERENCE = False` 开关；只有你手动改成 `True` 才会加载模型做推理。

## 建议顺序

0. `00_START_项目总架构_入口出口和代码地图.ipynb`
1. `00_学习路线_先从问题而不是目录开始.ipynb`
2. `01_Qwen下载缓存加载和一次推理到底发生什么.ipynb`
3. `02_tokenizer和chat_template_文字怎么变成模型能懂的数字.ipynb`
4. `03_SFT数据集和loss_模型到底在学哪几个字.ipynb`
5. `04_LoRA怎么贴到Qwen上_代码里的adapter实现.ipynb`
6. `05_adapter保存加载和固定prompt对比_怎么判断真的变好.ipynb`
7. `06_DPO从偏好数据到DPOTrainer_为什么指标好也可能不接受.ipynb`
8. `07_面试复盘_把代码细节讲成工程闭环.ipynb`

## `notebooks/` 和本目录的区别

- `notebooks/`：原始实践/实验 notebook，记录早期环境检查、base 推理、demo 数据和 full pipeline 学习过程，建议保留。
- `project_learning_notebooks_zh/`：后来补充的中文学习导览，从读者视角解释项目结构和代码意义。

## 最重要的项目结论

- 推荐 checkpoint：`outputs/sft_lora_qwen05b_custom_v3_from_v1_patch`
- 最佳 DPO artifact：`outputs/dpo_lora_qwen05b_naive_v6`
- DPO artifact 有实验价值，但不是最终默认推荐，因为没有完全通过固定 prompt 行为门禁。
