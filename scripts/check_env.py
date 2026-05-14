"""Check the local Qwen LoRA environment.

This script deliberately avoids importing heavy ML libraries such as
transformers, peft, and trl. On Windows, native extension crashes can terminate
python.exe before a normal exception is raised. Package versions are read from
metadata instead.
"""

from __future__ import annotations

import os
import platform
import sys
from importlib import metadata

PACKAGES = [
    "torch",
    "transformers",
    "datasets",
    "accelerate",
    "peft",
    "trl",
    "gradio",
]


def package_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not installed"


def main() -> None:
    print("Python executable:", sys.executable, flush=True)
    print("Python:", platform.python_version(), flush=True)
    print("Platform:", platform.platform(), flush=True)
    print("HF_HOME:", os.environ.get("HF_HOME", "(default cache)"), flush=True)
    print("HF_HUB_DISABLE_SYMLINKS_WARNING:", os.environ.get("HF_HUB_DISABLE_SYMLINKS_WARNING", "(unset)"), flush=True)

    for package in PACKAGES:
        print(f"{package}: {package_version(package)}", flush=True)

    print("\nTorch CUDA quick check:", flush=True)
    print(
        "Run this separately if needed:\n"
        "python -c \"import torch; print(torch.__version__); "
        "print(torch.cuda.is_available()); "
        "print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda')\"",
        flush=True,
    )


if __name__ == "__main__":
    main()
