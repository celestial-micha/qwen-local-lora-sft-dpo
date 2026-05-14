# GitHub Migration Guide

当前本地项目已经改成：

```text
qwen-local-lora-sft-dpo
```

旧 GitHub 仓库是：

```text
https://github.com/celestial-micha/qwen-military-posttraining.git
```

因为现在不做军事大模型，建议把 GitHub 仓库改名为：

```text
qwen-local-lora-sft-dpo
```

## 推荐做法

### 1. 在 GitHub 网页上改仓库名

打开旧仓库：

```text
https://github.com/celestial-micha/qwen-military-posttraining
```

进入：

```text
Settings -> General -> Repository name
```

把仓库名改为：

```text
qwen-local-lora-sft-dpo
```

改完后新地址应该是：

```text
https://github.com/celestial-micha/qwen-local-lora-sft-dpo
```

GitHub 通常会保留旧地址跳转，但本地最好使用新地址。

## 2. 把当前新项目初始化为 Git 仓库

进入项目目录：

```powershell
cd "D:\coding\qwen lorar sft\qwen-local-lora-sft-dpo"
```

初始化：

```powershell
git init
git add .
git commit -m "reset project to local qwen lora sft dpo"
git branch -M main
```

## 3. 连接新的 GitHub 地址

如果你已经在 GitHub 改名为 `qwen-local-lora-sft-dpo`：

```powershell
git remote add origin https://github.com/celestial-micha/qwen-local-lora-sft-dpo.git
```

如果你还没改名，仍然用旧仓库地址：

```powershell
git remote add origin https://github.com/celestial-micha/qwen-military-posttraining.git
```

## 4. 是否覆盖旧 GitHub 内容

因为旧仓库内容是已经废弃的军事大模型方向，而本地是全新项目，有两种选择。

### 选择 A：创建全新 GitHub 仓库

这是最安全的。

新建：

```text
qwen-local-lora-sft-dpo
```

然后：

```powershell
git push -u origin main
```

### 选择 B：覆盖旧仓库 main 分支

如果你确定旧内容不需要保留：

```powershell
git push -u origin main --force-with-lease
```

注意：

```text
--force-with-lease 会改写远程 main 分支。
```

如果你想保留旧方向，可以先在 GitHub 页面手动创建一个备份分支，或者先不要覆盖。

## 5. 本项目哪些文件不会上传

`.gitignore` 已经忽略：

```text
.hf_cache/
outputs/
data/raw/*
data/processed/*
```

所以不会上传：

- Hugging Face 模型缓存。
- LoRA adapter 权重。
- checkpoint。
- 本地生成的 processed 数据。

会上传：

- 代码。
- 配置。
- README。
- 报告。
- 小型 sample prompt。

这正是我们想要的。

## 6. 建议提交前检查

```powershell
git status
git add .
git status
git commit -m "reset project to local qwen lora sft dpo"
```

如果看到 `.hf_cache` 或 `outputs` 要被提交，先停下来，不要 commit。

## 7. 推荐最终仓库名

推荐：

```text
qwen-local-lora-sft-dpo
```

理由：

- 名字直接说明项目内容。
- 不再绑定军事领域。
- 面试官一眼能看懂：Qwen、本地、LoRA、SFT、DPO。
