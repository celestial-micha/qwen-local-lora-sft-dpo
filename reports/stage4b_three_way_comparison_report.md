# Stage 4B Three-Way Comparison Report

Date: 2026-05-14

## Goal

Compare the same fixed technical prompts across three variants:

- Base `Qwen/Qwen2.5-0.5B-Instruct`
- Public-data LoRA SFT adapter: `outputs/sft_lora_qwen05b_public`
- Custom technical LoRA SFT adapter: `outputs/sft_lora_qwen05b_custom`

Raw output:

```text
reports/compare_outputs_three_way_custom.jsonl
```

Comparison script:

```text
scripts/compare_three_outputs.py
```

The script launches `scripts/infer.py` separately for each model variant, so it
does not keep multiple adapters in GPU memory at the same time.

## Command

```powershell
D:\conda-envs\qwen-lora-local\python.exe scripts\compare_three_outputs.py `
  --prompt_file data\samples\custom_technical_prompts.jsonl `
  --public_adapter_path outputs\sft_lora_qwen05b_public `
  --custom_adapter_path outputs\sft_lora_qwen05b_custom `
  --output_file reports\compare_outputs_three_way_custom.jsonl `
  --max_new_tokens 128 `
  --temperature 0 `
  --local_files_only
```

## Summary Table

| # | Prompt Focus | Base | Public-SFT | Custom-SFT | Result |
|---:|---|---|---|---|---|
| 1 | LoRA is parameter-efficient fine-tuning, not wireless LoRa | Wrong concept | Wrong concept | Correct and concise | Custom wins |
| 2 | SFT meaning and relation to LoRA | Wrong acronyms | Wrong acronyms | Correct relation: SFT objective, LoRA method | Custom wins |
| 3 | DPO vs SFT and why SFT first | Wrong acronyms | Wrong security/privacy meaning | Correct preference-pair explanation | Custom wins |
| 4 | Why public-SFT failure motivates Stage 2B | Wrong/off-topic | Wrong/off-topic | Still confused | Needs data patch |
| 5 | Custom data collection, cleaning, dedupe, filtering, conversion | Generic data answer | Generic answer | Project-specific and accurate | Custom wins |
| 6 | 8GB DPO VRAM risk and mitigation | Generic VRAM answer | Generic VRAM answer | Project-specific and accurate | Custom wins |
| 7 | Why loss alone is insufficient | Generic ML answer | Generic loss answer | Partially correct but has hallucinated wording | Needs data patch |
| 8 | Interview explanation of data pipeline | Generic data pipeline | Generic enterprise pipeline | Project-specific narrative | Custom wins |

Overall:

```text
Strong improvement: 6 / 8 prompts
Still weak: 2 / 8 prompts
```

## Main Finding

The custom technical dataset materially improved the model on the target
project concepts. This validates the project plan:

```text
public dataset baseline
  -> find target badcases
  -> build self-collected/curated technical data
  -> retrain custom adapter
  -> compare against base and public-SFT
```

The result is not perfect, and that is useful. The remaining badcases show how
the next data iteration should be designed.

## Remaining Badcases

Prompt 4:

```text
为什么 public-SFT adapter 没修正 LoRA/SFT/DPO 概念误解，反而说明 Stage 2B 有必要？
```

The custom adapter still produced a confused explanation. This means the dataset
needs more direct samples that say:

- Public-SFT is useful as a baseline.
- Its failure on target concepts is not a failure of the whole project.
- That failure motivates custom technical data because public general data did
  not cover the desired behavior.

Prompt 7:

```text
为什么不能只看 loss 判断一次 SFT 是否成功？
```

The custom adapter included the correct idea that behavior must be checked, but
also hallucinated phrases such as `not-SFT`. This needs cleaner examples that
separate:

- training loss
- eval loss
- fixed prompt behavior
- badcase review
- overfitting signs

## Interview Narrative

A good way to explain this stage:

> I first trained a public-data LoRA SFT adapter to prove the local training
> loop worked. The adapter saved and loaded correctly, but fixed-prompt testing
> showed it still misunderstood LoRA/SFT/DPO. I then built a small custom
> technical dataset from project notes and curated QA samples, cleaned and
> deduplicated it, retrained a custom adapter, and compared base vs public-SFT
> vs custom-SFT. The custom adapter fixed most target prompts, and the remaining
> badcases tell me exactly what data to add next.

## Next Recommendation

Do not jump straight to full DPO yet. The recommended next checkpoint is:

```text
Stage 2B.2 small targeted data patch
  -> add samples for prompt 4 and prompt 7
  -> optionally retrain a shorter custom adapter or select best checkpoint
  -> only then run tiny DPO smoke test
```
