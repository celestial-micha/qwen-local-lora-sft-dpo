"""Interpolate two LoRA adapter checkpoints.

This is useful for tiny badcase patches: keep most weights from a stable
adapter and blend in a small amount of a focused patch adapter.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import torch
from safetensors.torch import load_file, save_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Linearly interpolate two LoRA adapters.")
    parser.add_argument("--base_adapter_path", required=True)
    parser.add_argument("--patch_adapter_path", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--alpha", type=float, required=True, help="0.0 keeps base, 1.0 keeps patch.")
    return parser.parse_args()


def copy_adapter_dir(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name == "adapter_model.safetensors" or item.is_dir():
            continue
        target = dst / item.name
        if item.is_file():
            shutil.copy2(item, target)


def main() -> None:
    args = parse_args()
    if not 0.0 <= args.alpha <= 1.0:
        raise ValueError("--alpha must be between 0.0 and 1.0")

    base_dir = Path(args.base_adapter_path)
    patch_dir = Path(args.patch_adapter_path)
    output_dir = Path(args.output_dir)
    base_file = base_dir / "adapter_model.safetensors"
    patch_file = patch_dir / "adapter_model.safetensors"

    base_state = load_file(str(base_file))
    patch_state = load_file(str(patch_file))
    if set(base_state) != set(patch_state):
        missing_base = sorted(set(patch_state) - set(base_state))
        missing_patch = sorted(set(base_state) - set(patch_state))
        raise ValueError(f"Adapter tensor keys differ. missing_base={missing_base}, missing_patch={missing_patch}")

    merged = {}
    for key, base_tensor in base_state.items():
        patch_tensor = patch_state[key]
        if base_tensor.shape != patch_tensor.shape:
            raise ValueError(f"Shape mismatch for {key}: {base_tensor.shape} != {patch_tensor.shape}")
        if torch.is_floating_point(base_tensor):
            merged[key] = (1.0 - args.alpha) * base_tensor + args.alpha * patch_tensor.to(base_tensor.dtype)
        else:
            merged[key] = base_tensor

    copy_adapter_dir(base_dir, output_dir)
    save_file(merged, str(output_dir / "adapter_model.safetensors"))
    print(f"Saved interpolated adapter to: {output_dir}")
    print(f"alpha: {args.alpha}")


if __name__ == "__main__":
    main()
